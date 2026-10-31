import type { Product } from "../data/products";
import { money } from "../utils/presentation";
import type { Translate } from "../utils/presentation";
type Props = {
  products: Product[];
  tr: Translate;
  addReorder: () => void;
  loading?: boolean;
  error?: string;
};
export default function QuickReorder({
  tr,
  products,
  addReorder,
  loading = false,
  error = "",
}: Props) {
  const repeatProducts = products.filter((product) => product.stock > 0);
  return (
    <section className="reorder-section" id="reorder">
      <div className="container reorder-inner">
        <div className="reorder-copy">
          <span className="section-kicker">{tr("THE SMARTER WAY TO SHOP")}</span>
          <h2>
            {tr("Your usuals.")}
            <br />
            <em>{tr("Ready when you are.")}</em>
          </h2>
          <p>
            Skip the repeat searching. Your favorite essentials are one tap away with
            Quick Reorder.
          </p>
          <div className="reorder-note">
            {loading ? "Loading your recommendations..." : error || "Personalized from your purchase history"}
          </div>
          <button className="primary-button" onClick={addReorder} disabled={loading || repeatProducts.length === 0}>
            Add my usuals <span>↗</span>
          </button>
        </div>
        <div className="reorder-panel">
          <div className="reorder-panel-head">
            <span>↻ Your quick reorder</span>
            <span className="reorder-demo">TOP PICKS</span>
          </div>
          {repeatProducts
            .map((p) => (
              <div className="reorder-row" key={p.id}>
                <span className="reorder-thumb" style={{ background: p.color }}>
                  {p.icon}
                </span>
                <span className="reorder-name">
                  <strong>{tr(p.name)}</strong>
                  <small>{tr(p.detail)}</small>
                </span>
                <strong>{money(p.price)}</strong>
              </div>
            ))}
          <div className="reorder-total">
            <span>{repeatProducts.length} everyday favorites</span>
            <strong>
              {money(repeatProducts.reduce((s, p) => s + p.price, 0))}
            </strong>
          </div>
        </div>
      </div>
    </section>
  );
}
