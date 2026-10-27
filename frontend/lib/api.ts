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

async function fetchJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      signal,
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
  } catch (error) {
    if (signal?.aborted) throw error;
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

export function getWarehouses(signal?: AbortSignal): Promise<Warehouse[]> {
  return fetchJson<Warehouse[]>("/api/warehouses", signal);
}

export async function getWarehouseProducts(
  warehouseId: string,
  signal?: AbortSignal,
): Promise<ProductInventory[]> {
  if (!warehouseId.trim()) throw new Error("A warehouse must be selected.");

  const limit = 100;
  const products = new Map<string, ProductInventory>();
  for (let skip = 0; ; skip += limit) {
    const page = await fetchJson<ProductInventory[]>(
      `/api/warehouses/${encodeURIComponent(warehouseId)}/products?skip=${skip}&limit=${limit}`,
      signal,
    );
    for (const product of page) products.set(product.product_id, product);
    if (page.length < limit) return [...products.values()];
  }
}
