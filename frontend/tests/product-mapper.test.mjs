
import test from "node:test";
import assert from "node:assert/strict";

import { mapInventoryProducts } from "../lib/product-mapper.ts";

function makeInventoryItem(overrides = {}) {
  return {
    product_id: "ad4c7afb-58ae-4af6-8091-25d8e4eb8268",
    sku: "FRUIT-AVOCADO-034-1KG",
    name: "Bo sap 034 Lam Dong",
    category: "Trai cay tuoi",
    unit_price: "60000.00",
    unit: "Kg",
    is_available: true,
    warehouse_id: "36e0fc5f-6d23-4a8f-8d35-3c2732bcb8ff",
    quantity: 220,
    reserved_quantity: 7,
    available_stock: 213,
    ...overrides,
  };
}

test("maps backend identity, price, and display fields", () => {
  const item = makeInventoryItem();
  const [product] = mapInventoryProducts([item]);

  assert.equal(product.backendProductId, item.product_id);
  assert.equal(product.sku, item.sku);
  assert.equal(product.name, item.name);
  assert.equal(product.price, 60000);
  assert.equal(product.unit, "Kg");
  assert.equal(product.detail, `SKU: ${item.sku}`);
  assert.ok(Number.isInteger(product.id));
});

test("maps backend categories to supported UI categories", () => {
  const fixtures = [
    { sku: "VEG-CABBAGE-1KG", category: "Rau cu qua", expected: "Produce" },
    { sku: "FRUIT-AVOCADO-1KG", category: "Trai cay tuoi", expected: "Produce" },
    { sku: "DAIRY-BUTTER-227G", category: "Sua & San pham tu sua", expected: "Dairy & Eggs" },
    { sku: "BEV-JUICE-1L", category: "Do uong", expected: "Beverages" },
    { sku: "BAKERY-BREAD-500G", category: "Banh mi & Ngu coc", expected: "Bakery" },
    { sku: "BAKERY-PEANUT-BUTTER-340G", category: "Banh mi & Ngu coc", expected: "Pantry" },
  ];

  for (const fixture of fixtures) {
    const [product] = mapInventoryProducts([
      makeInventoryItem({
        product_id: `test-${fixture.sku}`,
        sku: fixture.sku,
        category: fixture.category,
      }),
    ]);

    assert.equal(product.category, fixture.expected, fixture.sku);
  }
});

test("uses available_stock rather than total quantity", () => {
  const [product] = mapInventoryProducts([
    makeInventoryItem({
      quantity: 220,
      reserved_quantity: 7,
      available_stock: 213,
    }),
  ]);

  assert.equal(product.stock, 213);
});

test("sets stock to zero when the backend marks a product unavailable", () => {
  const [product] = mapInventoryProducts([
    makeInventoryItem({
      is_available: false,
      available_stock: 50,
    }),
  ]);

  assert.equal(product.stock, 0);
});

test("floors fractional inventory quantities", () => {
  const [product] = mapInventoryProducts([
    makeInventoryItem({ available_stock: 4.8 }),
  ]);

  assert.equal(product.stock, 4);
});

test("rejects invalid or negative prices", () => {
  assert.throws(
    () =>
      mapInventoryProducts([
        makeInventoryItem({ unit_price: "not-a-price" }),
      ]),
    /Invalid price/,
  );

  assert.throws(
    () =>
      mapInventoryProducts([
        makeInventoryItem({ unit_price: "-1" }),
      ]),
    /Invalid price/,
  );
});
