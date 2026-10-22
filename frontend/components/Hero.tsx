import type { Category } from "../data/products";
import type { Translate } from "../utils/presentation";
type Props = {
  tr: Translate;
  jumpToShop: (category?: Category) => void;
};
export default function Hero({ tr, jumpToShop }: Props) {
  return (
    <section className="hero container">
      <div className="hero-copy">
        <span className="eyebrow">
          <span className="live-dot" /> YOUR NEIGHBORHOOD, DELIVERED
        </span>
        <h1>
          {tr("Fresh picks.")}
          <br />
          <em>{tr("Less thinking.")}</em>
          <br />
          {tr("More living.")}
        </h1>
        <p>
          Everything your kitchen needs, thoughtfully picked and ready when you are.
          Discover a smarter way to shop for groceries.
        </p>
        <div className="hero-actions">
          <button className="primary-button" onClick={() => jumpToShop()}>
            Shop fresh groceries <span>↗</span>
          </button>
          <button
            className="text-button"
            onClick={() =>
              document.getElementById("reorder")?.scrollIntoView({ behavior: "smooth" })
            }
          >
            Explore quick reorder <span>→</span>
          </button>
        </div>
        <div className="hero-proof">
          <div className="avatar-stack">
            <span>🥑</span>
            <span>🍓</span>
            <span>🥦</span>
          </div>
          <div>
            <strong>Freshness first</strong>
            <small>Local stores. Everyday essentials.</small>
          </div>
        </div>
      </div>
      <div className="hero-art" aria-label="Illustration of fresh groceries">
        <div className="hero-circle circle-one" />
        <div className="hero-circle circle-two" />
        <div className="produce-basket">
          <div className="produce-top">🥬 🍅 🥕</div>
          <div className="produce-middle">🥑 🍋 🍎</div>
          <div className="basket-body">FRESH &amp; DAILY</div>
        </div>
        <div className="floating-card floating-top">
          <span>✓</span>
          <div>
            <strong>Picked fresh</strong>
            <small>Quality you can trust</small>
          </div>
        </div>
        <div className="floating-card floating-bottom">
          <span>🚚</span>
          <div>
            <strong>Same-day delivery</strong>
            <small>From nearby mini-marts</small>
          </div>
        </div>
        <span className="art-sparkle sparkle-one">•</span>
        <span className="art-sparkle sparkle-two">•</span>
      </div>
    </section>
  );
}
