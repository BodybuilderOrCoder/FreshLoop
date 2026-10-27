
"use client";

import { useState } from "react";
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

  // Reconcile during rendering when the catalog changes, before children use it.
  const [previousCatalog, setPreviousCatalog] = useState(catalogProducts);
  if (previousCatalog !== catalogProducts) {
    setPreviousCatalog(catalogProducts);
    setCart(reconcileCart(cart, catalogProducts));
  }

  const { count, subtotal, delivery } = calculateCartSummary(
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

  return {
    cart,
    count,
    subtotal,
    delivery,
    changeQty,
  };
}
