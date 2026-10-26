
"use client";

import { useEffect, useState } from "react";
import {
  products as mockProducts,
  type Product,
} from "../data/products";

// Reconcile the cart whenever the selected warehouse's catalog changes.
export function useCart(catalogProducts: Product[] = mockProducts) {
  const [cart, setCart] = useState<Record<number, number>>({});

  useEffect(() => {
    setCart((previousCart) => {
      const nextCart: Record<number, number> = {};
      let changed = false;

      for (const [rawId, quantity] of Object.entries(previousCart)) {
        const id = Number(rawId);
        const product = catalogProducts.find((item) => item.id === id);

        // Remove products missing from the new catalog or out of stock.
        if (!product || product.stock <= 0) {
          changed = true;
          continue;
        }

        const safeQuantity = Math.min(
          Math.max(0, quantity),
          Math.floor(product.stock),
        );

        if (safeQuantity > 0) {
          nextCart[id] = safeQuantity;
        }

        if (safeQuantity !== quantity) {
          changed = true;
        } else if (safeQuantity === 0) {
          changed = true;
        }
      }

      return changed ? nextCart : previousCart;
    });
  }, [catalogProducts]);

  const count = Object.values(cart).reduce(
    (sum, quantity) => sum + quantity,
    0,
  );

  const subtotal = catalogProducts.reduce(
    (sum, product) =>
      sum + product.price * (cart[product.id] || 0),
    0,
  );

  const delivery =
    subtotal >= 200000 || subtotal === 0 ? 0 : 15000;

  const changeQty = (id: number, delta: number) => {
    const product = catalogProducts.find((item) => item.id === id);

    // Ignore unknown products and products without available stock.
    if (!product || product.stock <= 0) return;

    setCart((previousCart) => {
      const nextQuantity = Math.max(
        0,
        Math.min(
          Math.floor(product.stock),
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
