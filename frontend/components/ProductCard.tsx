import type { Product } from "../data/products";
import { money, type Translate } from "../utils/presentation";
type Props = {
  p: Product;
  tr: Translate;
  language: "en" | "vi";
  favorites: number[];
  favoritesLoaded: boolean;
  toggleFavorite: (id: number) => void;
  cart: Record<number, number>;
  changeQty: (id: number, delta: number) => void;
  add: (product: Product) => void;
};
export default function ProductCard({
  p,
  tr,
  language,
  favorites,
  favoritesLoaded,
  toggleFavorite,
  cart,
  changeQty,
  add,
}: Props) {
  return (
    <article className="product-card" key={p.id}>
      <div className="product-visual" style={{ background: p.color }}>
        <button
          type="button"
          className={`favorite-button ${favorites.includes(p.id) ? "is-favorite" : ""}`}
          disabled={!favoritesLoaded}
          aria-pressed={favorites.includes(p.id)}
          aria-label={
            favorites.includes(p.id)
              ? `Remove ${p.name} from favorites`
              : `Add ${p.name} to favorites`
          }
          onClick={() => toggleFavorite(p.id)}
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill={favorites.includes(p.id) ? "currentColor" : "none"}
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z" />
          </svg>
        </button>
        {p.tag && <span className="product-tag">{tr(p.tag)}</span>}
        <span className="product-emoji" role="img" aria-label={tr(p.name)}>
          {p.icon}
        </span>
        <span className={`stock-badge ${p.stock <= 7 ? "low" : ""}`}>
          {p.stock <= 7
            ? `${language === "vi" ? "Còn" : "Only"} ${p.stock} ${language === "vi" ? "sản phẩm" : "left"}`
            : `● ${tr("In stock")}`}
        </span>
      </div>
      <div className="product-info">
        <span className="product-category">{tr(p.category)}</span>
        <h3>{tr(p.name)}</h3>
        <p>{tr(p.detail)}</p>
        <div className="product-bottom">
          <div>
            <strong>{money(p.price)}</strong>
            <small>/ {tr(p.unit)}</small>
          </div>
          {cart[p.id] ? (
            <div className="qty-control">
              <button
                aria-label={`Remove one ${tr(p.name)}`}
                onClick={() => changeQty(p.id, -1)}
              >
                −
              </button>
              <span>{cart[p.id]}</span>
              <button
                aria-label={`Add one ${tr(p.name)}`}
                onClick={() => changeQty(p.id, 1)}
                disabled={cart[p.id] >= p.stock}
              >
                +
              </button>
            </div>
          ) : (
            <button
              className="add-button"
              onClick={() => add(p)}
              aria-label={`Add ${tr(p.name)} to cart`}
            >
              +
            </button>
          )}
        </div>
      </div>
    </article>
  );
}
