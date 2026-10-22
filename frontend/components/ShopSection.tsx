import type { Category } from "../data/products";
import type { Product } from "../data/products";
import ProductCard from "./ProductCard";
import type { Translate } from "../utils/presentation";
const categories: { name: Category; icon: string }[] = [
  { name: "All", icon: "🛒" },
  { name: "Produce", icon: "🥬" },
  { name: "Dairy & Eggs", icon: "🥛" },
  { name: "Meat & Seafood", icon: "🍗" },
  { name: "Bakery", icon: "🥐" },
  { name: "Pantry", icon: "🫙" },
];
type Props = {
  tr: Translate;
  language: "en" | "vi";
  category: Category;
  setCategory: (value: Category) => void;
  search: string;
  setSearch: (value: string) => void;
  sort: string;
  setSort: (value: string) => void;
  onlyAvailable: boolean;
  setOnlyAvailable: (value: boolean) => void;
  onlyFavorites: boolean;
  setOnlyFavorites: (value: boolean) => void;
  favorites: number[];
  favoritesLoaded: boolean;
  toggleFavorite: (id: number) => void;
  filtered: Product[];
  cart: Record<number, number>;
  changeQty: (id: number, delta: number) => void;
  add: (product: Product) => void;
};
export default function ShopSection({
  tr,
  language,
  category,
  setCategory,
  search,
  setSearch,
  sort,
  setSort,
  onlyAvailable,
  setOnlyAvailable,
  onlyFavorites,
  setOnlyFavorites,
  favorites,
  favoritesLoaded,
  toggleFavorite,
  filtered,
  cart,
  changeQty,
  add,
}: Props) {
  return (
    <section className="shop-section container" id="shop">
      <div className="section-heading">
        <div>
          <span className="section-kicker">{tr("GOOD FOOD, GOOD DAYS")}</span>
          <h2>
            Explore the <em>freshest.</em>
          </h2>
          <p>{tr("Everyday essentials, just a few clicks away.")}</p>
        </div>
        <div className="section-count">{filtered.length} products available</div>
      </div>
      <div className="shop-controls">
        <div
          className="categories"
          role="group"
          aria-label={language === "vi" ? "Danh mục sản phẩm" : "Product categories"}
        >
          {categories.map((c) => (
            <button
              key={tr(c.name)}
              className={`category-chip ${category === c.name ? "selected" : ""}`}
              onClick={() => setCategory(c.name)}
            >
              <span>{c.icon}</span>
              {tr(c.name)}
            </button>
          ))}
        </div>
        <div className="filters">
          <label className="search-box">
            <span>⌕</span>
            <input
              aria-label={language === "vi" ? "Tìm sản phẩm" : "Search products"}
              placeholder={tr("Search for something fresh...")}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            {search && (
              <button onClick={() => setSearch("")} aria-label="Clear search">
                ×
              </button>
            )}
          </label>
          <select
            aria-label={language === "vi" ? "Sắp xếp sản phẩm" : "Sort products"}
            value={sort}
            onChange={(e) => setSort(e.target.value)}
          >
            <option value="featured">{tr("Featured")}</option>
            <option value="price-asc">{tr("Price: low to high")}</option>
            <option value="price-desc">{tr("Price: high to low")}</option>
            <option value="name">{tr("Name: A–Z")}</option>
          </select>
          <label className="stock-filter">
            <input
              type="checkbox"
              checked={onlyAvailable}
              onChange={(e) => setOnlyAvailable(e.target.checked)}
            />{" "}
            In stock
          </label>
          <label className="stock-filter">
            <input
              type="checkbox"
              checked={onlyFavorites}
              onChange={(e) => setOnlyFavorites(e.target.checked)}
            />
            Favorites ({favorites.length})
          </label>
        </div>
      </div>
      <div className="product-grid">
        {filtered.map((p) => (
          <ProductCard
            key={p.id}
            p={p}
            tr={tr}
            language={language}
            favorites={favorites}
            favoritesLoaded={favoritesLoaded}
            toggleFavorite={toggleFavorite}
            cart={cart}
            changeQty={changeQty}
            add={add}
          />
        ))}
      </div>
      {filtered.length === 0 && (
        <div className="empty-state">
          <span>🔎</span>
          <h3>{tr("No groceries found")}</h3>
          <p>{tr("Try another search or browse all categories.")}</p>
          <button
            className="primary-button"
            onClick={() => {
              setSearch("");
              setCategory("All");
              setOnlyFavorites(false);
              setOnlyAvailable(false);
            }}
          >
            {tr("Show all products")} →
          </button>
        </div>
      )}
    </section>
  );
}
