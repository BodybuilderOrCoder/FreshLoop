"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useCart } from "../../../hooks/useCart";
import { useCatalog } from "../../../hooks/useCatalog";
import { getProduct, type ProductDetails } from "../../../lib/api";
import { money } from "../../../utils/presentation";

type Props = { params: Promise<{ productId: string }> };

export default function ProductDetailsPage({ params }: Props) {
  const [productId, setProductId] = useState("");
  const [product, setProduct] = useState<ProductDetails | null>(null);
  const [error, setError] = useState("");

  // The catalog gives warehouse-specific stock and keeps it live over SSE.
  const {
    products,
    warehouse,
    loading: stockLoading,
    error: stockError,
  } = useCatalog();
  const { cart, count, changeQty } = useCart(products);
  const stocked = products.find((item) => item.backendProductId === productId);
  const inCart = stocked ? cart[stocked.id] ?? 0 : 0;

  // Route params are read in the effect so the page can still prerender.
  useEffect(() => {
    const controller = new AbortController();
    void params
      .then(({ productId: id }) => {
        if (controller.signal.aborted) return;
        setProductId(id);
        return getProduct(id, controller.signal).then((result) => setProduct(result));
      })
      .catch((reason) => {
        if (controller.signal.aborted) return;
        setError(reason instanceof Error ? reason.message : "Unable to load this product.");
      });
    return () => controller.abort();
  }, [params]);

  let stockMessage: string;
  if (stockLoading) {
    stockMessage = "Checking warehouse stock...";
  } else if (stockError) {
    stockMessage = "Stock is unavailable right now.";
  } else if (!stocked || stocked.stock <= 0) {
    stockMessage = `Out of stock at ${warehouse?.code ?? "the selected warehouse"}.`;
  } else {
    stockMessage = `${stocked.stock} available at ${warehouse?.code ?? "the selected warehouse"}.`;
  }

  return (
    <main className="journey-page container">
      <Link href="/" className="journey-back">Back to shop</Link>
      {error && <p className="journey-error" role="alert">{error}</p>}
      {!error && !product && <p role="status">Loading product...</p>}
      {product && (
        <section className="journey-card">
          <span className="section-kicker">{product.category}</span>
          <h1>{product.name}</h1>
          <p>SKU: {product.sku}</p>
          <p className="journey-total">{money(Number(product.unit_price))} / {product.unit}</p>
          <p
            className={`journey-stock ${stocked && stocked.stock > 0 ? "" : "is-out"}`}
            role="status"
            aria-live="polite"
          >
            {product.is_available ? stockMessage : "This product is currently unavailable."}
          </p>

          {product.is_available && stocked && stocked.stock > 0 && (
            <div className="journey-actions">
              {inCart > 0 ? (
                <div className="qty-control">
                  <button
                    onClick={() => changeQty(stocked.id, -1)}
                    aria-label={`Remove one ${product.name}`}
                  >
                    −
                  </button>
                  <span>{inCart}</span>
                  <button
                    onClick={() => changeQty(stocked.id, 1)}
                    disabled={inCart >= stocked.stock}
                    aria-label={`Add one ${product.name}`}
                  >
                    +
                  </button>
                </div>
              ) : (
                <button
                  className="primary-button"
                  onClick={() => changeQty(stocked.id, 1)}
                >
                  Add to cart
                </button>
              )}
              {count > 0 && (
                <Link href="/?cart=open" className="text-button">
                  Go to cart ({count}) →
                </Link>
              )}
            </div>
          )}
        </section>
      )}
    </main>
  );
}
