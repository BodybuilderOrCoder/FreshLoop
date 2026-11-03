"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { getOrder, getProduct, type Order } from "../../../lib/api";
import { money } from "../../../utils/presentation";

type Props = {
  params: Promise<{ orderId: string }>;
  searchParams: Promise<{ placed?: string | string[] }>;
};

function formatStatus(status: string): string {
  const words = status.replace(/[_-]+/g, " ").trim().toLowerCase();
  return words.charAt(0).toUpperCase() + words.slice(1);
}

/** Looks up names the order response omits; unknown products keep their ID. */
async function loadProductNames(
  order: Order,
  signal?: AbortSignal,
): Promise<Record<string, string>> {
  const missing = [...new Set(
    order.items.filter((item) => !item.product_name).map((item) => item.product_id),
  )];
  const results = await Promise.allSettled(
    missing.map((productId) => getProduct(productId, signal)),
  );
  const names: Record<string, string> = {};
  results.forEach((result, index) => {
    if (result.status === "fulfilled") names[missing[index]] = result.value.name;
  });
  return names;
}

export default function OrderStatusPage({ params, searchParams }: Props) {
  const [orderId, setOrderId] = useState("");
  const [justPlaced, setJustPlaced] = useState(false);
  const [order, setOrder] = useState<Order | null>(null);
  const [names, setNames] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (id: string, signal?: AbortSignal) => {
    try {
      const result = await getOrder(id, signal);
      if (signal?.aborted) return;
      setOrder(result);
      setError("");
      const lookedUp = await loadProductNames(result, signal);
      if (!signal?.aborted) setNames((current) => ({ ...current, ...lookedUp }));
    } catch (reason) {
      if (signal?.aborted) return;
      setError(reason instanceof Error ? reason.message : "Unable to load this order.");
    }
  }, []);

  // Route params are read in the effect so the page can still prerender.
  useEffect(() => {
    const controller = new AbortController();
    void Promise.all([params, searchParams]).then(([{ orderId: id }, query]) => {
      if (controller.signal.aborted) return;
      setOrderId(id);
      setJustPlaced(query.placed === "1");
      return load(id, controller.signal);
    });
    return () => controller.abort();
  }, [params, searchParams, load]);

  const refresh = () => {
    setRefreshing(true);
    void load(orderId).finally(() => setRefreshing(false));
  };

  return (
    <main className="journey-page container">
      <Link href="/" className="journey-back">Back to shop</Link>
      <span className="section-kicker">ORDER STATUS</span>
      <h1>{order ? `Order ${order.order_id.slice(0, 8)}` : "Your order"}</h1>
      {justPlaced && order && (
        <p className="journey-success" role="status">
          Thank you! Your order has been placed.
        </p>
      )}
      {error && <p className="journey-error" role="alert">{error}</p>}
      {!error && !order && <p role="status">Loading order {orderId.slice(0, 8)}...</p>}
      {order && (
        <section className="journey-card">
          <p><strong>Status:</strong> {formatStatus(order.status)}</p>
          <p><strong>Placed:</strong> {new Date(order.created_at).toLocaleString()}</p>
          {order.delivery_address && <p><strong>Delivery:</strong> {order.delivery_address}</p>}
          <table className="journey-table">
            <thead>
              <tr>
                <th scope="col">Product</th>
                <th scope="col">Qty</th>
                <th scope="col">Amount</th>
              </tr>
            </thead>
            <tbody>
              {order.items.map((item) => {
                const lineTotal = item.line_total ?? (
                  item.unit_price === undefined
                    ? undefined
                    : Number(item.unit_price) * item.quantity
                );
                return (
                  <tr key={item.product_id}>
                    <td>{item.product_name ?? names[item.product_id] ?? item.product_id}</td>
                    <td>{item.quantity}</td>
                    <td>{lineTotal === undefined ? "—" : money(Number(lineTotal))}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <p className="journey-total">Total: {money(Number(order.total_amount))}</p>
          <div className="journey-actions">
            <button
              type="button"
              className="text-button"
              onClick={refresh}
              disabled={refreshing}
            >
              {refreshing ? "Refreshing..." : "Refresh status"}
            </button>
          </div>
        </section>
      )}
    </main>
  );
}
