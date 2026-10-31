"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getOrder, type Order } from "../../../lib/api";
import { money } from "../../../utils/presentation";

type Props = { params: Promise<{ orderId: string }> };

export default function OrderStatusPage({ params }: Props) {
  const [orderId, setOrderId] = useState("");
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    void params.then(({ orderId: value }) => {
      if (!active) return;
      setOrderId(value);
      return getOrder(value)
        .then((result) => active && setOrder(result))
        .catch((reason) => active && setError(
          reason instanceof Error ? reason.message : "Unable to load this order.",
        ));
    });
    return () => { active = false; };
  }, [params]);

  return (
    <main className="journey-page container">
      <Link href="/" className="journey-back">Back to shop</Link>
      <span className="section-kicker">ORDER STATUS</span>
      <h1>{order ? `Order ${order.order_id.slice(0, 8)}` : "Your order"}</h1>
      {error && <p className="journey-error" role="alert">{error}</p>}
      {!error && !order && <p role="status">Loading order {orderId.slice(0, 8)}...</p>}
      {order && (
        <section className="journey-card">
          <p><strong>Status:</strong> {order.status}</p>
          <p><strong>Placed:</strong> {new Date(order.created_at).toLocaleString()}</p>
          {order.delivery_address && <p><strong>Delivery:</strong> {order.delivery_address}</p>}
          <ul className="journey-list">
            {order.items.map((item) => (
              <li key={item.product_id}>{item.quantity} x {item.product_id}</li>
            ))}
          </ul>
          <p className="journey-total">Total: {money(Number(order.total_amount))}</p>
        </section>
      )}
    </main>
  );
}
