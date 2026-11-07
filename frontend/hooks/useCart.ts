
"use client";

import { useEffect, useRef, useState } from "react";
import {
  products as mockProducts,
  type Product,
} from "../data/products";
import {
  calculateCartSummary,
  reconcileCart,
  updateCartQuantity,
} from "../lib/cart-logic";

export function useCart(catalogProducts: Product[] = mockProducts) {
  const [cart, setCart] = useState<Record<number, number>>({});
  const restored = useRef(false);

  useEffect(() => {
    const restore = window.setTimeout(() => {
      try {
        const saved = window.sessionStorage.getItem("freshloop:cart");
        if (saved) setCart(JSON.parse(saved) as Record<number, number>);
      } catch {
        // Session storage is a convenience; shopping still works without it.
      } finally {
        restored.current = true;
      }
    }, 0);
    return () => {
      window.clearTimeout(restore);
      // Next keeps visited pages mounted while hidden and re-runs effects when
      // they return, so this page must re-read the cart before saving it.
      restored.current = false;
    };
  }, []);

  useEffect(() => {
    if (!restored.current) return;
    try {
      window.sessionStorage.setItem("freshloop:cart", JSON.stringify(cart));
    } catch {
      // Ignore unavailable browser storage.
    }
  }, [cart]);

  // Reconcile during rendering when the catalog changes, before children use it.
  const [previousCatalog, setPreviousCatalog] = useState(catalogProducts);
  if (previousCatalog !== catalogProducts) {
    setPreviousCatalog(catalogProducts);
    setCart(reconcileCart(cart, catalogProducts));
  }

  const { count, subtotal } = calculateCartSummary(
    cart,
    catalogProducts,
  );

  const changeQty = (id: number, delta: number) => {
    setCart((previousCart) =>
      updateCartQuantity(
        previousCart,
        id,
        delta,
        catalogProducts,
      ),
    );
  };

  const clearCart = () => setCart({});

  return {
    cart,
    count,
    subtotal,
    changeQty,
    clearCart,
  };
}
