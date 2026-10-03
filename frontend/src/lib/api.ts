export type Product = {
  id: string;
  sku: string;
  name: string;
  price_cents: number;
  available_quantity: number;
  reserved_quantity: number;
  version: number;
};

export type Order = {
  id: string;
  customer_email: string;
  status: string;
  total_cents: number;
  created_at: string | null;
  items: Array<{ sku: string; product_name: string; quantity: number; unit_price_cents: number }>;
};

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(body.detail ?? "Request failed");
  }
  return response.json() as Promise<T>;
}

export const api = {
  products: () => request<Product[]>("/products"),
  createProduct: (payload: object, adminKey: string) =>
    request<Product>("/products", {
      method: "POST",
      headers: { "X-Admin-Api-Key": adminKey },
      body: JSON.stringify(payload),
    }),
  createOrder: (payload: object) =>
    request<Order>("/orders", {
      method: "POST",
      headers: { "Idempotency-Key": crypto.randomUUID() },
      body: JSON.stringify(payload),
    }),
};

export const dollars = (cents: number) => `$${(cents / 100).toFixed(2)}`;
