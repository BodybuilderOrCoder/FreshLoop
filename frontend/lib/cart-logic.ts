
import type { Product } from "../data/products";

export type Cart = Record<number, number>;

export type CartSummary = {
  count: number;
  subtotal: number;
  delivery: number;
};

/**
 * Reconcile the cart with the currently selected warehouse catalog.
 * Remove missing/out-of-stock products and cap quantities at available stock.
 */
export function reconcileCart(
  cart: Cart,
  catalogProducts: Product[],
): Cart {
  const nextCart: Cart = {};

  for (const [rawId, rawQuantity] of Object.entries(cart)) {
    const id = Number(rawId);
    const product = catalogProducts.find((item) => item.id === id);

    if (
      !product ||
      !Number.isFinite(product.stock) ||
      product.stock <= 0 ||
      !Number.isFinite(rawQuantity)
    ) {
      continue;
    }

    const quantity = Math.min(
      Math.max(0, Math.floor(rawQuantity)),
      Math.floor(product.stock),
    );

    if (quantity > 0) {
      nextCart[id] = quantity;
    }
  }

  const previousEntries = Object.entries(cart);
  const nextEntries = Object.entries(nextCart);

  const unchanged =
    previousEntries.length === nextEntries.length &&
    nextEntries.every(([id, quantity]) => cart[Number(id)] === quantity);

  return unchanged ? cart : nextCart;
}

/**
 * Apply a quantity change while respecting the selected warehouse stock.
 */
export function updateCartQuantity(
  cart: Cart,
  id: number,
  delta: number,
  catalogProducts: Product[],
): Cart {
  const product = catalogProducts.find((item) => item.id === id);

  if (
    !product ||
    !Number.isFinite(product.stock) ||
    product.stock <= 0 ||
    !Number.isFinite(delta)
  ) {
    return cart;
  }

  const currentQuantity = Math.max(0, Math.floor(cart[id] || 0));
  const nextQuantity = Math.max(
    0,
    Math.min(
      Math.floor(product.stock),
      currentQuantity + Math.trunc(delta),
    ),
  );

  if (nextQuantity === currentQuantity) {
    return cart;
  }

  const nextCart = { ...cart };

  if (nextQuantity === 0) {
    delete nextCart[id];
  } else {
    nextCart[id] = nextQuantity;
  }

  return nextCart;
}

/**
 * Calculate cart count, subtotal and delivery fee from the current catalog.
 */
export function calculateCartSummary(
  cart: Cart,
  catalogProducts: Product[],
): CartSummary {
  const count = Object.values(cart).reduce(
    (sum, quantity) => sum + quantity,
    0,
  );

  const subtotal = catalogProducts.reduce(
    (sum, product) => sum + product.price * (cart[product.id] || 0),
    0,
  );

  const delivery =
    subtotal >= 200000 || subtotal === 0 ? 0 : 15000;

  return { count, subtotal, delivery };
}
