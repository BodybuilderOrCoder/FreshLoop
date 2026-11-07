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

export type LoginResponse = {
  access_token: string;
  token_type: string;
  expires_in: number;
};

export type RegisterInput = {
  email: string;
  password: string;
  name: string;
  phone: string;
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
  product_name?: string;
  quantity: number;
  unit_price?: number | string;
  line_total?: number | string;
};

export type Order = {
  order_id: string;
  order_number: string;
  status: "PENDING" | "CONFIRMED" | "DELIVERED" | "CANCELLED";
  payment_method: "COD";
  payment_status: "UNPAID" | "PAID";
  warehouse_id?: string;
  total_amount: number | string;
  delivery_address?: string;
  created_at: string;
  items: OrderItem[];
};

/** An HTTP error from the backend; `status` lets the UI choose a fallback. */
export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

const CONNECTION_ERROR =
  "Cannot connect to the backend. Check that FastAPI is running.";

/** Reads FastAPI's `detail` field, which is a string or a validation list. */
async function readErrorDetail(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as {
      detail?: string | { msg?: string }[];
    };
    if (typeof payload.detail === "string") return payload.detail;
    if (Array.isArray(payload.detail)) {
      return payload.detail
        .map((item) => item.msg)
        .filter(Boolean)
        .join("; ");
    }
  } catch {
    // The status still provides a useful error if the body is not JSON.
  }
  return "";
}

function describeError(
  status: number,
  statusText: string | undefined,
  detail: string,
  notFoundMessage?: string,
  unauthorizedMessage?: string,
): string {
  const suffix = detail ? `: ${detail}` : "";

  switch (status) {
    case 401:
      return unauthorizedMessage ?? "Please sign in to continue.";
    case 403:
      return "Your account is not allowed to perform this action.";
    case 404:
      // FastAPI answers "Not Found" for a missing route; any other detail
      // comes from a handler (for example "Product not found").
      if (detail && detail !== "Not Found") return detail;
      return notFoundMessage ?? "The requested resource was not found.";
    case 409:
      return detail || "Some items no longer have enough stock. Please review your cart.";
    case 422:
      return `Invalid request${suffix}`;
    default:
      return `Backend request failed (${status}${statusText ? ` ${statusText}` : ""})${suffix}.`;
  }
}

type RequestOptions = {
  method?: "GET" | "POST";
  body?: unknown;
  headers?: Record<string, string>;
  signal?: AbortSignal;
  accessToken?: string;
  notFoundMessage?: string;
  unauthorizedMessage?: string;
};

async function requestJson<T>(
  path: string,
  {
    method = "GET",
    body,
    headers,
    signal,
    accessToken,
    notFoundMessage,
    unauthorizedMessage,
  }: RequestOptions = {},
): Promise<T> {
  const requestHeaders: Record<string, string> = {
    Accept: "application/json",
    ...headers,
  };
  if (body !== undefined) requestHeaders["Content-Type"] = "application/json";
  if (accessToken) requestHeaders.Authorization = `Bearer ${accessToken}`;

  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      signal,
      headers: requestHeaders,
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: "no-store",
    });
  } catch (error) {
    if (signal?.aborted) throw error;
    throw new Error(CONNECTION_ERROR);
  }

  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new ApiError(
      response.status,
      describeError(
        response.status,
        response.statusText,
        detail,
        notFoundMessage,
        unauthorizedMessage,
      ),
    );
  }

  return (await response.json()) as T;
}

function fetchJson<T>(
  path: string,
  signal?: AbortSignal,
  notFoundMessage?: string,
): Promise<T> {
  return requestJson<T>(path, { signal, notFoundMessage });
}

export function login(email: string, password: string): Promise<LoginResponse> {
  return requestJson<LoginResponse>("/api/auth/login", {
    method: "POST",
    body: { email, password },
    unauthorizedMessage: "Invalid email or password.",
  });
}

export function registerCustomer(input: RegisterInput): Promise<unknown> {
  return requestJson<unknown>("/api/auth/register", {
    method: "POST",
    body: input,
  });
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
  return fetchJson<ProductDetails>(
    `/api/products/${encodeURIComponent(productId)}`,
    signal,
    "This product could not be found.",
  );
}

export async function getRecommendations(
  userId: string,
  warehouseId: string,
  signal?: AbortSignal,
  accessToken?: string,
): Promise<RecommendationItem[]> {
  const result = await requestJson<RecommendationItem[] | { items: RecommendationItem[] }>(
    `/api/recommendations/${encodeURIComponent(userId)}?warehouse_id=${encodeURIComponent(warehouseId)}`,
    {
      signal,
      accessToken,
      notFoundMessage: "Quick Reorder is not connected to the recommendation service yet.",
    },
  );
  return Array.isArray(result) ? result : result.items;
}

export function createOrder(
  input: CreateOrderInput,
  idempotencyKey: string,
  accessToken: string,
): Promise<Order> {
  return requestJson<Order>("/api/orders", {
    method: "POST",
    body: input,
    headers: { "Idempotency-Key": idempotencyKey },
    accessToken,
  });
}

export function getOrder(
  orderId: string,
  accessToken: string,
  signal?: AbortSignal,
): Promise<Order> {
  return requestJson<Order>(`/api/orders/${encodeURIComponent(orderId)}`, {
    signal,
    accessToken,
    notFoundMessage: "This order could not be found.",
  });
}
