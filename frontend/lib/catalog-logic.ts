
import type { Warehouse } from "./api";

export function getActiveWarehouses(
  warehouses: Warehouse[],
): Warehouse[] {
  return warehouses.filter((warehouse) => warehouse.is_active);
}

export function chooseDefaultWarehouse(
  warehouses: Warehouse[],
  preferredCode = "HUB-01",
): Warehouse {
  const activeWarehouses = getActiveWarehouses(warehouses);

  const selected =
    activeWarehouses.find(
      (warehouse) => warehouse.code === preferredCode,
    ) ?? activeWarehouses[0];

  if (!selected) {
    throw new Error("No active warehouse is available.");
  }

  return selected;
}

/**
 * Allows only the most recent inventory request to update UI state.
 */
export function createLatestRequestGuard() {
  let latestRequestId = 0;

  return {
    begin(): number {
      latestRequestId += 1;
      return latestRequestId;
    },

    isLatest(requestId: number): boolean {
      return requestId === latestRequestId;
    },

    invalidate(requestId: number): void {
      if (requestId === latestRequestId) {
        latestRequestId += 1;
      }
    },
  };
}
