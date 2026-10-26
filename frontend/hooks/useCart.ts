"use client";

import { useState } from "react";
import {
  products as mockProducts,
  type Product,
} from "../data/products";

// The fallback preserves compatibility while the API catalog is integrated.
export function useCart(catalogProducts: Product[] = mockProducts) {
  const [cart, setCart] = useState<Record<number, number>>({});

  const count = Object.values(cart).reduce((sum, quantity) => {
    return sum + quantity;
  }, 0);

  const subtotal = catalogProducts.reduce((sum, product) => {
    return sum + product.price * (cart[product.id] || 0);
  }, 0);

  const delivery = subtotal >= 200000 || subtotal === 0 ? 0 : 15000;

  const changeQty = (id: number, delta: number) => {
    const product = catalogProducts.find((item) => item.id === id);

    // Ignore unknown IDs instead of accidentally adding invalid cart items.
    if (!product) return;

    setCart((previousCart) => {
      const nextQuantity = Math.max(
        0,
        Math.min(
          product.stock,
          (previousCart[id] || 0) + delta,
        ),
      );

      if (nextQuantity === 0) {
        const nextCart = { ...previousCart };
        delete nextCart[id];
        return nextCart;
      }

      return {
        ...previousCart,
        [id]: nextQuantity,
      };
    });
  };

  return {
    cart,
    count,
    subtotal,
    delivery,
    changeQty,
  };
}