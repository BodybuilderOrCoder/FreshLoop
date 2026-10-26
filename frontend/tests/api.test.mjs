
import test from "node:test";
import assert from "node:assert/strict";

import {
  getWarehouses,
  getWarehouseProducts,
} from "../lib/api.ts";

async function withMockFetch(mockFetch, callback) {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = mockFetch;

  try {
    await callback();
  } finally {
    globalThis.fetch = originalFetch;
  }
}

test("getWarehouses returns the warehouse list", async () => {
  const warehouses = [
    {
      warehouse_id: "warehouse-1",
      code: "HUB-01",
      name: "Central Hub",
      location: "District 1",
      service_zone: "ZONE_CENTRAL",
      is_active: true,
    },
  ];

  await withMockFetch(
    async (url, options) => {
      assert.equal(
        new URL(String(url)).pathname,
        "/api/warehouses",
      );
      assert.equal(options.headers.Accept, "application/json");

      return {
        ok: true,
        json: async () => warehouses,
      };
    },
    async () => {
      assert.deepEqual(await getWarehouses(), warehouses);
    },
  );
});

test("getWarehouseProducts returns inventory for the selected warehouse", async () => {
  const inventory = [
    {
      product_id: "product-1",
      sku: "TEST-001",
      name: "Test product",
      category: "Rau cu qua",
      unit_price: "25000.00",
      unit: "Kg",
      is_available: true,
      warehouse_id: "warehouse-1",
      quantity: 20,
      reserved_quantity: 3,
      available_stock: 17,
    },
  ];

  await withMockFetch(
    async (url) => {
      assert.equal(
        new URL(String(url)).pathname,
        "/api/warehouses/warehouse-1/products",
      );

      return {
        ok: true,
        json: async () => inventory,
      };
    },
    async () => {
      assert.deepEqual(
        await getWarehouseProducts("warehouse-1"),
        inventory,
      );
    },
  );
});

test("getWarehouseProducts rejects an empty warehouse ID without fetching", async () => {
  let fetchCalled = false;

  await withMockFetch(
    async () => {
      fetchCalled = true;
      throw new Error("Fetch should not be called");
    },
    async () => {
      await assert.rejects(
        getWarehouseProducts("  "),
        /A warehouse must be selected/,
      );
    },
  );

  assert.equal(fetchCalled, false);
});

test("API HTTP errors include the status code", async () => {
  await withMockFetch(
    async () => ({
      ok: false,
      status: 503,
      statusText: "Service Unavailable",
    }),
    async () => {
      await assert.rejects(
        getWarehouses(),
        /Backend request failed \(503 Service Unavailable\)/,
      );
    },
  );
});

test("network failures return a connection error", async () => {
  await withMockFetch(
    async () => {
      throw new Error("Network unavailable");
    },
    async () => {
      await assert.rejects(
        getWarehouses(),
        /Cannot connect to the backend/,
      );
    },
  );
});
