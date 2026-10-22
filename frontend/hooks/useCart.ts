"use client";
import { useState } from "react";
import { products } from "../data/products";

// Demo cart, held in memory; no backend checkout or persistence.
export function useCart() {
  const [cart, setCart] = useState<Record<number, number>>({});
  const count = Object.values(cart).reduce((a, b) => a + b, 0);
  const subtotal = products.reduce((sum, p) => sum + p.price * (cart[p.id] || 0), 0);
  const delivery = subtotal >= 200000 || subtotal === 0 ? 0 : 15000;
  const changeQty = (id: number, delta: number) => {
    const product = products.find((p) => p.id === id)!;
    setCart((prev) => ({
      ...prev,
      [id]: Math.max(0, Math.min(product.stock, (prev[id] || 0) + delta)),
    }));
  };
  return { cart, count, subtotal, delivery, changeQty };
}
