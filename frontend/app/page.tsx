"use client";
import { useCallback, useMemo, useState } from "react";
import { products, type Category, type Product } from "../data/products";
import { useCart } from "../hooks/useCart";
import { useFavorites } from "../hooks/useFavorites";
import { vi } from "../utils/presentation";
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
  const { cart, count, subtotal, delivery, changeQty } = useCart();
  const [cartOpen, setCartOpen] = useState(false);
  const [onlyAvailable, setOnlyAvailable] = useState(false);
  const [sort, setSort] = useState("featured");
  const [notice, setNotice] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const [checkout, setCheckout] = useState(false);
  const [address, setAddress] = useState("");
  const [language] = useState<"en" | "vi">("en");
  const [theme] = useState<"light" | "dark">("light");
  const tr = useCallback(
    (value: string) => (language === "vi" ? vi[value] || value : value),
    [language],
  );

  const [onlyFavorites, setOnlyFavorites] = useState(false);
  const { favorites, favoritesLoaded, toggleFavorite } = useFavorites();

  const filtered = useMemo(() => {
    const list = products.filter(
      (p) =>
        (category === "All" || p.category === category) &&
        `${tr(p.name)} ${tr(p.detail)}`.toLowerCase().includes(search.toLowerCase()) &&
        (!onlyAvailable || p.stock > 0) &&
        (!onlyFavorites || favorites.includes(p.id)),
    );
    if (sort === "price-asc") list.sort((a, b) => a.price - b.price);
    if (sort === "price-desc") list.sort((a, b) => b.price - a.price);
    if (sort === "name") list.sort((a, b) => a.name.localeCompare(b.name));
    return list;
  }, [category, search, onlyAvailable, sort, onlyFavorites, favorites, tr]);
  const add = (p: Product) => {
    changeQty(p.id, 1);
    setNotice(`${tr(p.name)} added to your cart`);
    window.setTimeout(() => setNotice(""), 2500);
  };
  const jumpToShop = (cat: Category = "All") => {
    setCategory(cat);
    document.getElementById("shop")?.scrollIntoView({ behavior: "smooth" });
    setMenuOpen(false);
  };
  const addReorder = () => {
    products.filter((p) => p.repeat).forEach((p) => changeQty(p.id, 1));
    setCartOpen(true);
  };

  return (
    <div className={`site-shell ${theme === "dark" ? "theme-dark" : ""}`} lang={language}>
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
        <QuickReorder tr={tr} addReorder={addReorder} />
        <About />
        <Contact />
      </main>
      <Footer />
      {notice && (
        <div className="toast" role="status">
          ✓ {notice}
        </div>
      )}
      {cartOpen && (
        <CartDrawer
          tr={tr}
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
          setNotice={setNotice}
        />
      )}
    </div>
  );
}
