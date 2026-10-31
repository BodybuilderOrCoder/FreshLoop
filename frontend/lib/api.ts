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

export type ProductDetails = {
  product_id: string;
  sku: string;
  name: string;
  category: string;
  unit_price: number | string;
  unit: string;
  is_available: boolean;
};

export type RecommendationItem = {
  product_id: string;
  score?: number;
};

export type OrderLineInput = {
  product_id: string;
  quantity: number;
};

export type CreateOrderInput = {
  warehouse_id: string;
  delivery_address: string;
  items: OrderLineInput[];
};

export type OrderItem = {
  product_id: string;
  quantity: number;
  unit_price?: number | string;
  line_total?: number | string;
};

export type Order = {
  order_id: string;
  status: string;
  total_amount: number | string;
  delivery_address?: string;
  created_at: string;
  items: OrderItem[];
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

async function sendJson<T>(path: string, body: unknown): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });
  } catch {
    throw new Error("Cannot connect to the backend. Check that FastAPI is running.");
  }

  if (!response.ok) {
    let detail = "";
    try {
      const payload = (await response.json()) as { detail?: string };
      detail = payload.detail ? `: ${payload.detail}` : "";
    } catch {
      // The status still provides a useful error if the body is not JSON.
    }

    if (response.status === 404) {
      throw new Error("This API is not available yet. The backend commerce service has not been deployed.");
    }

    throw new Error(`Backend request failed (${response.status})${detail}`);
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

export function getInventoryEventsUrl(warehouseId: string): string {
  return `${API_BASE_URL}/api/warehouses/${encodeURIComponent(warehouseId)}/inventory/events`;
}

export function getProduct(productId: string, signal?: AbortSignal): Promise<ProductDetails> {
  return fetchJson<ProductDetails>(`/api/products/${encodeURIComponent(productId)}`, signal);
}

export async function getRecommendations(
  userId: string,
  warehouseId: string,
  signal?: AbortSignal,
): Promise<RecommendationItem[]> {
  const result = await fetchJson<RecommendationItem[] | { items: RecommendationItem[] }>(
    `/api/recommendations/${encodeURIComponent(userId)}?warehouse_id=${encodeURIComponent(warehouseId)}`,
    signal,
  );
  return Array.isArray(result) ? result : result.items;
}

export function createOrder(input: CreateOrderInput): Promise<Order> {
  return sendJson<Order>("/api/orders", input);
}

export function getOrder(orderId: string, signal?: AbortSignal): Promise<Order> {
  return fetchJson<Order>(`/api/orders/${encodeURIComponent(orderId)}`, signal);
}
