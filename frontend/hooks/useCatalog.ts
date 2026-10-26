
"use client";

import { useCallback, useEffect, useState } from "react";

import {
  getWarehouses,
  getWarehouseProducts,
  type Warehouse,
} from "../lib/api";

import { mapInventoryProducts } from "../lib/product-mapper";
import type { Product } from "../data/products";

export function useCatalog() {
  const [products, setProducts] = useState<Product[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [warehouseId, setWarehouseId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Load active warehouses and select HUB-01 by default.
  useEffect(() => {
    let cancelled = false;

    async function loadWarehouses() {
      try {
        const result = await getWarehouses();
        const activeWarehouses = result.filter(
          (item) => item.is_active,
        );

        if (activeWarehouses.length === 0) {
          throw new Error("No active warehouse is available.");
        }

        const defaultWarehouse =
          activeWarehouses.find((item) => item.code === "HUB-01") ??
          activeWarehouses[0];

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
        setProducts([]);
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

  // Reload inventory whenever the selected warehouse changes.
  useEffect(() => {
    if (!warehouseId || warehouses.length === 0) return;

    let cancelled = false;

    async function loadInventory() {
      setLoading(true);
      setError("");

      try {
        const inventory = await getWarehouseProducts(warehouseId);
        const mappedProducts = mapInventoryProducts(inventory);

        if (cancelled) return;

        setProducts(mappedProducts);
      } catch (err) {
        if (cancelled) return;

        setProducts([]);
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load warehouse inventory.",
        );
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadInventory();

    return () => {
      cancelled = true;
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
    warehouses.find((item) => item.warehouse_id === warehouseId) ?? null;

  return {
    products,
    warehouses,
    warehouse,
    selectWarehouse,
    loading,
    error,
  };
}
