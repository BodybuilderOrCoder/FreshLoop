
import test from "node:test";
import assert from "node:assert/strict";

import {
  createOrder,
  getRecommendations,
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

test("createOrder sends the commerce payload and idempotency key", async () => {
  const input = {
    warehouse_id: "warehouse-1",
    delivery_address: "1 Fresh Street",
    items: [{ product_id: "product-1", quantity: 2 }],
  };
  const order = { order_id: "order-1", status: "PENDING", total_amount: 50000, created_at: "2026-11-01", items: [] };

  await withMockFetch(async (url, options) => {
    assert.equal(new URL(String(url)).pathname, "/api/orders");
    assert.equal(options.method, "POST");
    assert.equal(options.headers["Idempotency-Key"], "checkout-key-1");
    assert.deepEqual(JSON.parse(options.body), input);
    return { ok: true, json: async () => order };
  }, async () => {
    assert.deepEqual(await createOrder(input, "checkout-key-1"), order);
  });
});

test("a new checkout attempt uses a new idempotency key after conflict", async () => {
  const input = {
    warehouse_id: "warehouse-1",
    delivery_address: "1 Fresh Street",
    items: [{ product_id: "product-1", quantity: 2 }],
  };
  const keys = [];
  let stockAvailable = false;

  await withMockFetch(async (_url, options) => {
    const key = options.headers["Idempotency-Key"];
    keys.push(key);
    if (key === "first-attempt-key") {
      return errorResponse(409, { detail: "Insufficient available stock." });
    }
    assert.equal(stockAvailable, true);
    return {
      ok: true,
      json: async () => ({ order_id: "order-1" }),
    };
  }, async () => {
    await assert.rejects(
      createOrder(input, "first-attempt-key"),
      /Insufficient available stock/,
    );
    await assert.rejects(
      createOrder(input, "first-attempt-key"),
      /Insufficient available stock/,
    );
    stockAvailable = true;
    await createOrder(input, "new-attempt-key");
  });

  assert.deepEqual(
    keys,
    ["first-attempt-key", "first-attempt-key", "new-attempt-key"],
  );
});

test("getRecommendations accepts an items response envelope", async () => {
  await withMockFetch(async (url) => {
    const parsed = new URL(String(url));
    assert.equal(parsed.pathname, "/api/recommendations/customer-1");
    assert.equal(parsed.searchParams.get("warehouse_id"), "warehouse-1");
    return { ok: true, json: async () => ({ items: [{ product_id: "product-1", score: 0.9 }] }) };
  }, async () => {
    assert.deepEqual(
      await getRecommendations("customer-1", "warehouse-1"),
      [{ product_id: "product-1", score: 0.9 }],
    );
  });
});


test("loads all inventory pages and deduplicates product IDs", async () => {
  const offsets = [];
  await withMockFetch(async (url) => {
    const query = new URL(url).searchParams;
    assert.equal(query.get("limit"), "100");
    const skip = Number(query.get("skip"));
    offsets.push(skip);
    return { ok: true, json: async () => skip === 0
      ? Array.from({ length: 100 }, (_, i) => ({ product_id: `p${i}` }))
      : [{ product_id: "p99" }, { product_id: "p100" }] };
  }, async () => {
    assert.equal((await getWarehouseProducts("warehouse-1")).length, 101);
    assert.deepEqual(offsets, [0, 100]);
  });
});

test("does not return partial inventory when a later page fails", async () => {
  await withMockFetch(async (url) => ({
    ok: new URL(url).searchParams.get("skip") === "0",
    status: 503, statusText: "Service Unavailable",
    json: async () => Array.from({ length: 100 }, (_, i) => ({ product_id: `p${i}` })),
  }), async () => {
    await assert.rejects(getWarehouseProducts("warehouse-1"), /503/);
  });
});

function errorResponse(status, body) {
  return {
    ok: false,
    status,
    statusText: "",
    json: async () => body,
  };
}

test("createOrder surfaces the backend insufficient-stock detail", async () => {
  const { ApiError } = await import("../lib/api.ts");
  await withMockFetch(
    async () => errorResponse(409, { detail: "Insufficient stock for TEST-001" }),
    async () => {
      await assert.rejects(
        createOrder(
          { warehouse_id: "w", delivery_address: "a", items: [] },
          "conflict-key",
        ),
        (error) => error instanceof ApiError
          && error.status === 409
          && error.message === "Insufficient stock for TEST-001",
      );
    },
  );
});

test("a missing route returns the endpoint-specific message", async () => {
  await withMockFetch(
    async () => errorResponse(404, { detail: "Not Found" }),
    async () => {
      await assert.rejects(
        getRecommendations("customer-1", "warehouse-1"),
        /Quick Reorder is not connected/,
      );
    },
  );
});

test("a handler 404 keeps the backend detail", async () => {
  const { getOrder } = await import("../lib/api.ts");
  await withMockFetch(
    async () => errorResponse(404, { detail: "Order not found" }),
    async () => {
      await assert.rejects(getOrder("order-1"), /: Order not found$/);
    },
  );
});

test("validation errors join FastAPI messages", async () => {
  await withMockFetch(
    async () => errorResponse(422, {
      detail: [{ msg: "Field required" }, { msg: "Input should be greater than 0" }],
    }),
    async () => {
      await assert.rejects(
        createOrder(
          { warehouse_id: "w", delivery_address: "a", items: [] },
          "validation-key",
        ),
        /Invalid request: Field required; Input should be greater than 0/,
      );
    },
  );
});

test("authentication errors ask the user to sign in", async () => {
  await withMockFetch(
    async () => errorResponse(401, { detail: "Not authenticated" }),
    async () => {
      await assert.rejects(
        createOrder(
          { warehouse_id: "w", delivery_address: "a", items: [] },
          "authentication-key",
        ),
        /Please sign in to continue/,
      );
    },
  );
});
