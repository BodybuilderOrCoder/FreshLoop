const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/+$/, "");

export type Warehouse = {
  warehouse_id: string;
  code: string;
  name: string;
  location: string;
  service_zone: string;
  is_active: boolean;
};

export type ProductInventory = {
  product_id: string;
  sku: string;
  name: string;
  category: string;
  unit_price: number | string;
  unit: string;
  is_available: boolean;
  warehouse_id: string;
  quantity: number;
  reserved_quantity: number;
  available_stock: number;
};

async function fetchJson<T>(path: string): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
  } catch {
    throw new Error(
      "Cannot connect to the backend. Check that FastAPI is running.",
    );
  }

  if (!response.ok) {
    throw new Error(
      `Backend request failed (${response.status} ${response.statusText}).`,
    );
  }

  return (await response.json()) as T;
}

export function getWarehouses(): Promise<Warehouse[]> {
  return fetchJson<Warehouse[]>("/api/warehouses");
}

export function getWarehouseProducts(
  warehouseId: string,
): Promise<ProductInventory[]> {
  if (!warehouseId.trim()) {
    return Promise.reject(new Error("A warehouse must be selected."));
  }

  return fetchJson<ProductInventory[]>(
    `/api/warehouses/${encodeURIComponent(warehouseId)}/products`,
  );
}
