
"use client";

import { useEffect, useState } from "react";
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

  useEffect(() => {
    setCart((previousCart) =>
      reconcileCart(previousCart, catalogProducts),
    );
  }, [catalogProducts]);

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
