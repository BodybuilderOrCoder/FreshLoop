
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
  type Warehouse,
} from "../lib/api";

import { mapInventoryProducts } from "../lib/product-mapper";
import type { Product } from "../data/products";

import {
  chooseDefaultWarehouse,
  createLatestRequestGuard,
  getActiveWarehouses,
} from "../lib/catalog-logic";

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
      setError("");

      try {
        const result = await getWarehouses();
        const activeWarehouses = getActiveWarehouses(result);

        // Throws when there is no active warehouse.
        const defaultWarehouse = chooseDefaultWarehouse(result);

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

    const requestId = requestGuard.current.begin();

    setLoading(true);
    setError("");

    async function loadInventory() {
      try {
        const inventory = await getWarehouseProducts(warehouseId);
        const mappedProducts = mapInventoryProducts(inventory);

        // Ignore responses belonging to an older request.
        if (!requestGuard.current.isLatest(requestId)) {
          return;
        }

        setProducts(mappedProducts);
      } catch (err) {
        if (!requestGuard.current.isLatest(requestId)) {
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
        if (requestGuard.current.isLatest(requestId)) {
          setLoading(false);
        }
      }
    }

    void loadInventory();

    return () => {
      // Invalidate this request when the warehouse changes
      // or this effect is cleaned up.
      requestGuard.current.invalidate(requestId);
    };
  }, [warehouseId, warehouses]);

  const selectWarehouse = useCallback(
    (nextWarehouseId: string) => {
      const exists = warehouses.some(
        (item) => item.warehouse_id === nextWarehouseId,
      );

      if (exists && nextWarehouseId !== warehouseId) {
        setWarehouseId(nextWarehouseId);
      }
    },
    [warehouses, warehouseId],
  );

  const warehouse =
    warehouses.find(
      (item) => item.warehouse_id === warehouseId,
    ) ?? null;

  return {
    products,
    warehouses,
    warehouse,
    selectWarehouse,
    loading,
    error,
  };
}
