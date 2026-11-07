
"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  getWarehouses,
  getWarehouseProducts,
  getInventoryEventsUrl,
  type Warehouse,
} from "../lib/api";

import { mapInventoryProducts } from "../lib/product-mapper";
import type { Product } from "../data/products";

import {
  chooseDefaultWarehouse,
  createLatestRequestGuard,
  getActiveWarehouses,
} from "../lib/catalog-logic";

export type LiveStatus = "connecting" | "live" | "reconnecting" | "offline";

export function useCatalog() {
  const [products, setProducts] = useState<Product[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [warehouseId, setWarehouseId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Track the newest inventory request.
  const requestGuard = useRef(createLatestRequestGuard());

  // Load active warehouses and select HUB-01 by default.
  useEffect(() => {
    let cancelled = false;

    async function loadWarehouses() {

      try {
        const result = await getWarehouses();
        const activeWarehouses = getActiveWarehouses(result);

        // Throws when there is no active warehouse.
        let savedId: string | null = null;
        try { savedId = sessionStorage.getItem("freshloop:warehouse"); } catch { /* Storage is optional. */ }
        const defaultWarehouse = activeWarehouses.find((item) => item.warehouse_id === savedId)
          ?? chooseDefaultWarehouse(result);

        if (cancelled) return;

        setWarehouses(activeWarehouses);

        setWarehouseId((currentId) => {
          const currentStillExists = activeWarehouses.some(
            (item) => item.warehouse_id === currentId,
          );

          return currentStillExists
            ? currentId
            : defaultWarehouse.warehouse_id;
        });
      } catch (err) {
        if (cancelled) return;

        setWarehouses([]);
        setWarehouseId("");

        setError(
          err instanceof Error
            ? err.message
            : "Failed to load warehouses.",
        );

        setLoading(false);
      }
    }

    void loadWarehouses();

    return () => {
      cancelled = true;
    };
  }, []);

  // Load inventory for the currently selected warehouse.
  useEffect(() => {
    if (!warehouseId || warehouses.length === 0) {
      return;
    }

    const guard = requestGuard.current;
    const requestId = guard.begin();
    const controller = new AbortController();

    async function loadInventory() {
      try {
        const inventory = await getWarehouseProducts(warehouseId, controller.signal);
        const mappedProducts = mapInventoryProducts(inventory);

        // Ignore responses belonging to an older request.
        if (!guard.isLatest(requestId)) {
          return;
        }

        setProducts(mappedProducts);
      } catch (err) {
        if (!guard.isLatest(requestId)) {
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : "Failed to load warehouse inventory.",
        );

        // Keep the last successful catalog in memory.
        // Clearing it here could cause useCart to remove every item
        // after a temporary network or API failure.
      } finally {
        // Only the latest request may finish the loading state.
        if (guard.isLatest(requestId)) {
          setLoading(false);
        }
      }
    }

    void loadInventory();

    return () => {
      // Invalidate this request when the warehouse changes
      // or this effect is cleaned up.
      guard.invalidate(requestId);
      controller.abort();
    };
  }, [warehouseId, warehouses]);

  const selectWarehouse = useCallback(
    (nextWarehouseId: string) => {
      const exists = warehouses.some(
        (item) => item.warehouse_id === nextWarehouseId,
      );

      if (exists && nextWarehouseId !== warehouseId) {
        setLoading(true);
        setError("");
        try { sessionStorage.setItem("freshloop:warehouse", nextWarehouseId); } catch { /* Storage is optional. */ }
        setWarehouseId(nextWarehouseId);
      }
    },
    [warehouses, warehouseId],
  );

  const warehouse =
    warehouses.find(
      (item) => item.warehouse_id === warehouseId,
    ) ?? null;

  // Keyed by warehouse so switching warehouses reads as "connecting"
  // without resetting state inside the effect.
  const [liveState, setLiveState] = useState<{
    warehouseId: string;
    status: LiveStatus;
  }>({ warehouseId: "", status: "connecting" });

  const liveStatus: LiveStatus =
    liveState.warehouseId === warehouseId ? liveState.status : "connecting";

  // Inventory events are authoritative. Refreshing after each event keeps
  // product metadata and stock correct while the event payload evolves.
  useEffect(() => {
    if (!warehouseId) return;

    const events = new EventSource(getInventoryEventsUrl(warehouseId));
    const controller = new AbortController();
    let refreshTimer: ReturnType<typeof setTimeout> | undefined;

    // EventSource reconnects by itself; a new snapshot then refreshes stock.
    events.onopen = () => setLiveState({ warehouseId, status: "live" });
    events.onerror = () => setLiveState({
      warehouseId,
      status: events.readyState === EventSource.CLOSED ? "offline" : "reconnecting",
    });

    const refresh = () => {
      if (refreshTimer) clearTimeout(refreshTimer);
      refreshTimer = setTimeout(() => {
        void getWarehouseProducts(warehouseId, controller.signal)
          .then(mapInventoryProducts)
          .then((nextProducts) => {
            // A late response must not replace another warehouse's stock.
            if (!controller.signal.aborted) setProducts(nextProducts);
          })
          .catch(() => {
            // Preserve the last usable catalog after a transient failure.
          });
      }, 150);
    };

    events.addEventListener("inventory.snapshot", refresh);
    events.addEventListener("inventory.changed", refresh);

    return () => {
      if (refreshTimer) clearTimeout(refreshTimer);
      controller.abort();
      events.close();
    };
  }, [warehouseId]);

  return {
    products,
    warehouses,
    warehouse,
    selectWarehouse,
    loading,
    error,
    liveStatus,
  };
}
