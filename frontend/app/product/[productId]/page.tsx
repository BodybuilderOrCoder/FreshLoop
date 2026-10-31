"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getProduct, type ProductDetails } from "../../../lib/api";
import { money } from "../../../utils/presentation";

type Props = { params: Promise<{ productId: string }> };

export default function ProductDetailsPage({ params }: Props) {
  const [product, setProduct] = useState<ProductDetails | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    void params.then(({ productId }) => getProduct(productId)
      .then((result) => active && setProduct(result))
      .catch((reason) => active && setError(
        reason instanceof Error ? reason.message : "Unable to load this product.",
      )));
    return () => { active = false; };
  }, [params]);

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
          <p>{product.is_available ? "Available to order from a selected warehouse." : "Currently unavailable."}</p>
          <Link className="primary-button" href="/#shop">Choose this product in the shop</Link>
        </section>
      )}
    </main>
  );
}
