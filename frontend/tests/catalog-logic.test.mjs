
import test from "node:test";
import assert from "node:assert/strict";

import {
  getActiveWarehouses,
  chooseDefaultWarehouse,
  createLatestRequestGuard,
} from "../lib/catalog-logic.ts";

function makeWarehouse(code, isActive = true) {
  return {
    warehouse_id: `id-${code}`,
    code,
    name: `Warehouse ${code}`,
    location: "Test location",
    service_zone: "TEST_ZONE",
    is_active: isActive,
  };
}

test("filters out inactive warehouses", () => {
  const result = getActiveWarehouses([
    makeWarehouse("HUB-01"),
    makeWarehouse("MART-02", false),
    makeWarehouse("MART-03"),
  ]);

  assert.deepEqual(
    result.map((warehouse) => warehouse.code),
    ["HUB-01", "MART-03"],
  );
});

test("prefers HUB-01 as the default warehouse", () => {
  const result = chooseDefaultWarehouse([
    makeWarehouse("MART-02"),
    makeWarehouse("HUB-01"),
    makeWarehouse("MART-03"),
  ]);

  assert.equal(result.code, "HUB-01");
});

test("falls back to the first active warehouse when HUB-01 is missing", () => {
  const result = chooseDefaultWarehouse([
    makeWarehouse("MART-02"),
    makeWarehouse("MART-03"),
  ]);

  assert.equal(result.code, "MART-02");
});

test("does not select an inactive preferred warehouse", () => {
  const result = chooseDefaultWarehouse([
    makeWarehouse("HUB-01", false),
    makeWarehouse("MART-02"),
  ]);

  assert.equal(result.code, "MART-02");
});

test("throws when there are no active warehouses", () => {
  assert.throws(
    () => chooseDefaultWarehouse([
      makeWarehouse("HUB-01", false),
    ]),
    /No active warehouse is available/,
  );
});

test("ignores an older request after a newer request begins", () => {
  const guard = createLatestRequestGuard();

  const firstRequest = guard.begin();
  const secondRequest = guard.begin();

  assert.equal(guard.isLatest(firstRequest), false);
  assert.equal(guard.isLatest(secondRequest), true);
});

test("invalidating a request prevents it from updating state", () => {
  const guard = createLatestRequestGuard();
  const request = guard.begin();

  guard.invalidate(request);

  assert.equal(guard.isLatest(request), false);
});

test("invalidating an old request does not invalidate a newer request", () => {
  const guard = createLatestRequestGuard();

  const firstRequest = guard.begin();
  const secondRequest = guard.begin();

  guard.invalidate(firstRequest);

  assert.equal(guard.isLatest(secondRequest), true);
});
