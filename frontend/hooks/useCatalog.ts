"use client";

import { useEffect, useState } from "react";

import {
  getWarehouses,
  getWarehouseProducts,
  type Warehouse,
} from "../lib/api";

import { mapInventoryProducts } from "../lib/product-mapper";
import type { Product } from "../data/products";

export function useCatalog() {
  const [products, setProducts] = useState<Product[]>([]);
  const [warehouse, setWarehouse] = useState<Warehouse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadCatalog() {
      setLoading(true);
      setError("");

      try {
        const warehouses = await getWarehouses();

        const activeWarehouses = warehouses.filter(
          (item) => item.is_active,
        );

        const selectedWarehouse =
          activeWarehouses.find((item) => item.code === "HUB-01") ??
          activeWarehouses[0];

        if (!selectedWarehouse) {
          throw new Error("No active warehouse is available.");
        }

        const inventory = await getWarehouseProducts(
          selectedWarehouse.warehouse_id,
        );

        const mappedProducts = mapInventoryProducts(inventory);

        if (cancelled) return;

        setWarehouse(selectedWarehouse);
        setProducts(mappedProducts);
      } catch (err) {
        if (cancelled) return;

        setProducts([]);
        setWarehouse(null);

        setError(
          err instanceof Error
            ? err.message
            : "Failed to load products.",
        );
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadCatalog();

    return () => {
      cancelled = true;
    };
  }, []);

  return {
    products,
    warehouse,
    loading,
    error,
  };
}