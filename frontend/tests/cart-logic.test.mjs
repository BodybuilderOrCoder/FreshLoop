
import test from "node:test";
import assert from "node:assert/strict";

import {
  reconcileCart,
  updateCartQuantity,
  calculateCartSummary,
} from "../lib/cart-logic.ts";

function makeProduct(id, price, stock) {
  return {
    id,
    backendProductId: `uuid-${id}`,
    sku: `TEST-${id}`,
    name: `Test product ${id}`,
    detail: "Test fixture",
    price,
    unit: "unit",
    category: "Produce",
    icon: "test",
    color: "#ffffff",
    stock,
  };
}

test("preserves cart quantities when stock is sufficient", () => {
  const cart = { 1: 2 };
  const result = reconcileCart(cart, [makeProduct(1, 100000, 5)]);

  assert.deepEqual(result, { 1: 2 });
});

test("reduces quantity when new warehouse has less stock", () => {
  const result = reconcileCart(
    { 1: 18 },
    [makeProduct(1, 84550, 17)],
  );

  assert.deepEqual(result, { 1: 17 });
});

test("removes products that are missing or out of stock", () => {
  const result = reconcileCart(
    { 1: 2, 2: 3 },
    [
      makeProduct(1, 84550, 0),
      // Product 2 is absent from the new warehouse catalog.
    ],
  );

  assert.deepEqual(result, {});
});

test("does not allow quantity to exceed available stock", () => {
  const result = updateCartQuantity(
    { 1: 2 },
    1,
    1,
    [makeProduct(1, 100000, 2)],
  );

  assert.deepEqual(result, { 1: 2 });
});

test("removes an item when its quantity reaches zero", () => {
  const result = updateCartQuantity(
    { 1: 1 },
    1,
    -1,
    [makeProduct(1, 84550, 5)],
  );

  assert.deepEqual(result, {});
});

test("calculates subtotal and delivery below the free-delivery threshold", () => {
  const result = calculateCartSummary(
    { 1: 2 },
    [makeProduct(1, 84550, 5)],
  );

  assert.deepEqual(result, {
    count: 2,
    subtotal: 169100,
    delivery: 15000,
  });
});

test("waives delivery when subtotal reaches 200000", () => {
  const result = calculateCartSummary(
    { 1: 2 },
    [makeProduct(1, 100000, 5)],
  );

  assert.deepEqual(result, {
    count: 2,
    subtotal: 200000,
    delivery: 0,
  });
});
