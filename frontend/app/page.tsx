
"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import type { Category, Product } from "../data/products";
import { useCatalog } from "../hooks/useCatalog";
import { useCart } from "../hooks/useCart";
import { useFavorites } from "../hooks/useFavorites";
import { vi } from "../utils/presentation";
import { getRecommendations } from "../lib/api";

import Header from "../components/Header";
import Hero from "../components/Hero";
import Benefits from "../components/Benefits";
import ShopSection from "../components/ShopSection";
import QuickReorder from "../components/QuickReorder";
import About from "../components/About";
import Contact from "../components/Contact";
import Footer from "../components/Footer";
import CartDrawer from "../components/CartDrawer";

export default function Home() {
  const [category, setCategory] = useState<Category>("All");
  const [search, setSearch] = useState("");
  const [cartOpen, setCartOpen] = useState(false);
  const [onlyAvailable, setOnlyAvailable] = useState(false);
  const [sort, setSort] = useState("featured");
  const [notice, setNotice] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const [checkout, setCheckout] = useState(false);
  const [address, setAddress] = useState("");
  const [onlyFavorites, setOnlyFavorites] = useState(false);

  const [language] = useState<"en" | "vi">("en");
  const [theme] = useState<"light" | "dark">("light");

  const {
    products: catalogProducts,
    warehouses,
    warehouse,
    selectWarehouse,
    loading: catalogLoading,
    error: catalogError,
    liveStatus,
  } = useCatalog();

  const { cart, count, subtotal, delivery, changeQty, clearCart } =
    useCart(catalogProducts);
  const [recommendationIds, setRecommendationIds] = useState<string[]>([]);
  const [recommendationError, setRecommendationError] = useState("");
  const [recommendationsLoading, setRecommendationsLoading] = useState(false);
  const router = useRouter();

  const {
    favorites,
    favoritesLoaded,
    toggleFavorite,
  } = useFavorites();

  const tr = useCallback(
    (value: string) =>
      language === "vi" ? vi[value] || value : value,
    [language],
  );

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();

    const list = catalogProducts.filter(
      (product) =>
        (category === "All" || product.category === category) &&
        `${tr(product.name)} ${tr(product.detail)}`
          .toLowerCase()
          .includes(query) &&
        (!onlyAvailable || product.stock > 0) &&
        (!onlyFavorites || favorites.includes(product.id)),
    );

    if (sort === "price-asc") {
      list.sort((a, b) => a.price - b.price);
    }

    if (sort === "price-desc") {
      list.sort((a, b) => b.price - a.price);
    }

    if (sort === "name") {
      list.sort((a, b) => a.name.localeCompare(b.name));
    }

    return list;
  }, [
    catalogProducts,
    category,
    search,
    onlyAvailable,
    onlyFavorites,
    favorites,
    sort,
    tr,
  ]);

  // Product pages link to "/?cart=open" so shoppers land in their cart.
  useEffect(() => {
    const url = new URL(window.location.href);
    if (url.searchParams.get("cart") !== "open") return;
    url.searchParams.delete("cart");
    window.history.replaceState(null, "", `${url.pathname}${url.search}${url.hash}`);
    void Promise.resolve().then(() => setCartOpen(true));
  }, []);

  useEffect(() => {
    if (!warehouse?.warehouse_id) return;
    const userId = process.env.NEXT_PUBLIC_DEMO_USER_ID;

    if (!userId) return;

    const controller = new AbortController();
    void Promise.resolve().then(() => {
      if (controller.signal.aborted) return [];
      setRecommendationsLoading(true);
      setRecommendationError("");
      return getRecommendations(userId, warehouse.warehouse_id, controller.signal);
    })
      .then((items) => {
        if (!controller.signal.aborted) {
          setRecommendationIds(items.map((item) => item.product_id));
        }
      })
      .catch((error) => {
        if (!controller.signal.aborted) {
          setRecommendationIds([]);
          setRecommendationError(
            error instanceof Error ? error.message : "Recommendations are unavailable.",
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setRecommendationsLoading(false);
      });

    return () => controller.abort();
  }, [warehouse?.warehouse_id]);

  const recommendedProducts = useMemo(
    () => recommendationIds
      .map((id) => catalogProducts.find((product) => product.backendProductId === id))
      .filter((product): product is Product => Boolean(product && product.stock > 0)),
    [catalogProducts, recommendationIds],
  );

  const add = (product: Product) => {
    if (product.stock <= 0) {
      setNotice(`${tr(product.name)} is out of stock`);
      window.setTimeout(() => setNotice(""), 2500);
      return;
    }

    if ((cart[product.id] ?? 0) >= product.stock) {
      setNotice(`Stock limit reached for ${tr(product.name)}`);
      window.setTimeout(() => setNotice(""), 2500);
      return;
    }

    changeQty(product.id, 1);
    setNotice(`${tr(product.name)} added to your cart`);
    window.setTimeout(() => setNotice(""), 2500);
  };

  const jumpToShop = (nextCategory: Category = "All") => {
    setCategory(nextCategory);
    document.getElementById("shop")?.scrollIntoView({
      behavior: "smooth",
    });
    setMenuOpen(false);
  };

  const addReorder = () => {
    if (recommendedProducts.length === 0) {
      setNotice("No available Quick Reorder items yet.");
      window.setTimeout(() => setNotice(""), 2500);
      return;
    }

    recommendedProducts.forEach((product) => {
      changeQty(product.id, 1);
    });

    setCartOpen(true);
  };

  return (
    <div
      className={`site-shell ${theme === "dark" ? "theme-dark" : ""}`}
      lang={language}
    >
      <div className="announcement">
        {tr("Fresh groceries, smarter shopping")} <span>·</span>{" "}
        {tr("Free delivery on orders over 200,000₫")}
      </div>

      <Header
        tr={tr}
        jumpToShop={jumpToShop}
        menuOpen={menuOpen}
        setMenuOpen={setMenuOpen}
        count={count}
        setCartOpen={setCartOpen}
      />

      <main>
        <Hero tr={tr} jumpToShop={jumpToShop} />
        <Benefits />
        {warehouses.length > 0 && (
          <section
            className="container warehouse-selector"
            aria-label="Warehouse selection"
          >
            <div className="warehouse-selector__inner">
              <div className="warehouse-selector__field">
                <label htmlFor="warehouse-selector">
                  Choose warehouse
                </label>

                <select
                  id="warehouse-selector"
                  value={warehouse?.warehouse_id ?? ""}
                  onChange={(event) => {
                    setCartOpen(false);
                    setCheckout(false);
                    selectWarehouse(event.target.value);
                  }}
                  disabled={catalogLoading}
                >
                  {warehouses.map((item) => (
                    <option
                      key={item.warehouse_id}
                      value={item.warehouse_id}
                    >
                      {item.code} — {item.name}
                    </option>
                  ))}
                </select>
              </div>

              <p className="warehouse-selector__note">
                {catalogLoading
                  ? "Loading inventory..."
                  : catalogError
                    ? "Inventory unavailable for the selected warehouse."
                    : warehouse
                    ? `Showing stock for ${warehouse.code}`
                    : "Select a warehouse to view inventory."}
              </p>

              {warehouse && !catalogLoading && !catalogError && (
                <p
                  className={`live-status live-status--${liveStatus}`}
                  role="status"
                  aria-live="polite"
                >
                  {liveStatus === "live"
                    ? "Live stock updates on"
                    : liveStatus === "offline"
                      ? "Live updates unavailable"
                      : liveStatus === "reconnecting"
                        ? "Reconnecting to live stock..."
                        : "Connecting to live stock..."}
                </p>
              )}
            </div>
          </section>
        )}
        {catalogLoading ? (
          <section className="container" role="status" aria-live="polite">
            Loading products and warehouse stock...
          </section>
        ) : catalogError ? (
          <section className="container" role="alert">
            <h2>Unable to load products</h2>
            <p>{catalogError}</p>
            <button
              type="button"
              className="primary-button"
              onClick={() => window.location.reload()}
            >
              Retry
            </button>
          </section>
        ) : (
          <>
            {warehouse && (
              <div className="container">
                <p role="status">
                  Stock location: {warehouse.code} — {warehouse.name}
                </p>
              </div>
            )}

            <ShopSection
              tr={tr}
              language={language}
              category={category}
              setCategory={setCategory}
              search={search}
              setSearch={setSearch}
              sort={sort}
              setSort={setSort}
              onlyAvailable={onlyAvailable}
              setOnlyAvailable={setOnlyAvailable}
              onlyFavorites={onlyFavorites}
              setOnlyFavorites={setOnlyFavorites}
              favorites={favorites}
              favoritesLoaded={favoritesLoaded}
              toggleFavorite={toggleFavorite}
              filtered={filtered}
              cart={cart}
              changeQty={changeQty}
              add={add}
            />

            <QuickReorder
              tr={tr}
              products={recommendedProducts}
              addReorder={addReorder}
              loading={recommendationsLoading}
              error={recommendationError || (!process.env.NEXT_PUBLIC_DEMO_USER_ID ? "Sign in to see your Quick Reorder picks." : "")}
            />
          </>
        )}

        <About />
        <Contact />
      </main>

      <Footer />

      {notice && (
        <div className="toast" role="status" aria-live="polite">
          ✓ {notice}
        </div>
      )}

      {cartOpen && !catalogLoading && !catalogError && (
        <CartDrawer
          tr={tr}
          products={catalogProducts}
            warehouseId={warehouse?.warehouse_id ?? ""}
          jumpToShop={jumpToShop}
          count={count}
          setCartOpen={setCartOpen}
          cart={cart}
          changeQty={changeQty}
          checkout={checkout}
          setCheckout={setCheckout}
          address={address}
          setAddress={setAddress}
          subtotal={subtotal}
          delivery={delivery}
            onOrderCreated={(orderId) => {
              clearCart();
              router.push(`/orders/${encodeURIComponent(orderId)}?placed=1`);
            }}
        />
      )}
    </div>
  );
}
