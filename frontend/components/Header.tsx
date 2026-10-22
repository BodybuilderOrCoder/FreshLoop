import type { Category } from "../data/products";
import type { Translate } from "../utils/presentation";
import Link from "next/link";
type Props = {
  tr: Translate;
  jumpToShop: (category?: Category) => void;
  menuOpen: boolean;
  setMenuOpen: (value: boolean) => void;
  count: number;
  setCartOpen: (value: boolean) => void;
};
export default function Header({
  tr,
  jumpToShop,
  menuOpen,
  setMenuOpen,
  count,
  setCartOpen,
}: Props) {
  return (
    <header className="header">
      <div className="header-inner container">
        <button
          className="brand"
          onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
          aria-label="FreshLoop home"
        >
          {/* Preserve the existing logo asset and rendering. */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img className="brand-logo" src="/freshloop-logo.png" alt="FreshLoop" />
        </button>
        <nav className={`nav ${menuOpen ? "nav-open" : ""}`} aria-label="Main navigation">
          <button
            onClick={() => {
              setMenuOpen(false);
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
          >
            {tr("Home")}
          </button>
          <button onClick={() => jumpToShop()}>{tr("Shop groceries")}</button>
          <button
            onClick={() => {
              document.getElementById("reorder")?.scrollIntoView({ behavior: "smooth" });
              setMenuOpen(false);
            }}
          >
            {tr("Quick reorder")}
          </button>
          <button
            onClick={() => {
              document.getElementById("about")?.scrollIntoView({ behavior: "smooth" });
              setMenuOpen(false);
            }}
          >
            About
          </button>

          <button
            onClick={() => {
              document.getElementById("contact")?.scrollIntoView({ behavior: "smooth" });
              setMenuOpen(false);
            }}
          >
            Contact
          </button>
        </nav>
        <div className="header-actions">
          <span className="delivery-location">
            📍{" "}
            <span>
              Delivering in
              <br />
              <strong>Ho Chi Minh City</strong>
            </span>
          </span>

          <Link href="/favorites" className="favorites-link">
            <span aria-hidden="true">♡</span>
            <span>Favorites</span>
          </Link>

          <button
            className="cart-button"
            onClick={() => setCartOpen(true)}
            aria-label={`Open cart with ${count} items`}
          >
            🛍 <span>{tr("My cart")}</span>
            <b>{count}</b>
          </button>
          <button
            className="menu-toggle"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="Toggle navigation"
          >
            ☰
          </button>
        </div>
      </div>
    </header>
  );
}
