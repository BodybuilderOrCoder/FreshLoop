"use client";

import { useMemo, useState } from "react";

type Category = "All" | "Produce" | "Dairy & Eggs" | "Meat & Seafood" | "Bakery" | "Pantry";
type Product = { id: number; name: string; detail: string; price: number; unit: string; category: Exclude<Category, "All">; icon: string; color: string; tag?: string; stock: number; repeat?: boolean };

const products: Product[] = [
  { id: 1, name: "Fresh Avocado", detail: "Ripe & ready to eat", price: 32000, unit: "each", category: "Produce", icon: "🥑", color: "#eaf4d8", tag: "Best seller", stock: 24, repeat: true },
  { id: 2, name: "Organic Bananas", detail: "Locally sourced", price: 28000, unit: "bunch", category: "Produce", icon: "🍌", color: "#fff4d7", stock: 18, repeat: true },
  { id: 3, name: "Whole Milk", detail: "Fresh daily · 1L", price: 36000, unit: "bottle", category: "Dairy & Eggs", icon: "🥛", color: "#e9f3ff", tag: "Popular", stock: 9, repeat: true },
  { id: 4, name: "Farm Fresh Eggs", detail: "Free range · 10 pack", price: 42000, unit: "box", category: "Dairy & Eggs", icon: "🥚", color: "#fff0e5", stock: 30, repeat: true },
  { id: 5, name: "Cherry Tomatoes", detail: "Sweet & juicy · 250g", price: 26000, unit: "pack", category: "Produce", icon: "🍅", color: "#ffebea", tag: "Fresh pick", stock: 12 },
  { id: 6, name: "Sourdough Bread", detail: "Baked this morning", price: 59000, unit: "loaf", category: "Bakery", icon: "🍞", color: "#fff0dd", stock: 7 },
  { id: 7, name: "Chicken Breast", detail: "Skinless · 500g", price: 79000, unit: "pack", category: "Meat & Seafood", icon: "🍗", color: "#ffebe5", stock: 5 },
  { id: 8, name: "Jasmine Rice", detail: "Premium grain · 1kg", price: 39000, unit: "bag", category: "Pantry", icon: "🍚", color: "#f2f0e6", stock: 35 },
];
const categories: { name: Category; icon: string }[] = [
  { name: "All", icon: "✦" }, { name: "Produce", icon: "🥬" }, { name: "Dairy & Eggs", icon: "🥛" },
  { name: "Meat & Seafood", icon: "🍗" }, { name: "Bakery", icon: "🥐" }, { name: "Pantry", icon: "🫙" },
];
const money = (n: number) => `${n.toLocaleString("vi-VN")}₫`;

export default function Home() {
  const [category, setCategory] = useState<Category>("All");
  const [search, setSearch] = useState("");
  const [cart, setCart] = useState<Record<number, number>>({});
  const [cartOpen, setCartOpen] = useState(false);
  const [onlyAvailable, setOnlyAvailable] = useState(false);
  const [sort, setSort] = useState("featured");
  const [notice, setNotice] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const [checkout, setCheckout] = useState(false);
  const [address, setAddress] = useState("");

  const filtered = useMemo(() => {
    const list = products.filter((p) => (category === "All" || p.category === category) && `${p.name} ${p.detail}`.toLowerCase().includes(search.toLowerCase()) && (!onlyAvailable || p.stock > 0));
    if (sort === "price-asc") list.sort((a, b) => a.price - b.price);
    if (sort === "price-desc") list.sort((a, b) => b.price - a.price);
    if (sort === "name") list.sort((a, b) => a.name.localeCompare(b.name));
    return list;
  }, [category, search, onlyAvailable, sort]);
  const count = Object.values(cart).reduce((a, b) => a + b, 0);
  const subtotal = products.reduce((sum, p) => sum + p.price * (cart[p.id] || 0), 0);
  const delivery = subtotal >= 200000 || subtotal === 0 ? 0 : 15000;
  const changeQty = (id: number, delta: number) => {
    const product = products.find((p) => p.id === id)!;
    setCart((prev) => ({ ...prev, [id]: Math.max(0, Math.min(product.stock, (prev[id] || 0) + delta)) }));
  };
  const add = (p: Product) => { changeQty(p.id, 1); setNotice(`${p.name} added to your cart`); window.setTimeout(() => setNotice(""), 2500); };
  const jumpToShop = (cat: Category = "All") => { setCategory(cat); document.getElementById("shop")?.scrollIntoView({ behavior: "smooth" }); setMenuOpen(false); };
  const addReorder = () => { products.filter((p) => p.repeat).forEach((p) => changeQty(p.id, 1)); setCartOpen(true); };

  return (
    <div className="site-shell">
      <div className="announcement">✦ Fresh groceries, smarter shopping <span>·</span> Free delivery on orders over 200,000₫ <span>✦</span></div>
      <header className="header">
        <div className="header-inner container">
          <button className="brand" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })} aria-label="FreshLoop home"><span className="brand-icon">↻</span><span>fresh<span className="brand-green">loop</span><small>SMART GROCERY</small></span></button>
          <nav className={`nav ${menuOpen ? "nav-open" : ""}`} aria-label="Main navigation"><button onClick={() => { setMenuOpen(false); window.scrollTo({ top: 0, behavior: "smooth" }); }}>Home</button><button onClick={() => jumpToShop()}>Shop groceries</button><button onClick={() => { document.getElementById("reorder")?.scrollIntoView({ behavior: "smooth" }); setMenuOpen(false); }}>Quick reorder</button><button onClick={() => { document.getElementById("about")?.scrollIntoView({ behavior: "smooth" }); setMenuOpen(false); }}>How it works</button></nav>
          <div className="header-actions"><span className="delivery-location">📍 <span>Delivering in<br /><strong>Ho Chi Minh City</strong></span></span><button className="cart-button" onClick={() => setCartOpen(true)} aria-label={`Open cart with ${count} items`}>🛍 <span>My cart</span><b>{count}</b></button><button className="menu-toggle" onClick={() => setMenuOpen(!menuOpen)} aria-label="Toggle navigation">☰</button></div>
        </div>
      </header>
      <main>
        <section className="hero container">
          <div className="hero-copy"><span className="eyebrow"><span className="live-dot"/> YOUR NEIGHBORHOOD, DELIVERED</span><h1>Fresh picks.<br /><em>Less thinking.</em><br />More living.</h1><p>Everything your kitchen needs, thoughtfully picked and ready when you are. Discover a smarter way to shop for groceries.</p><div className="hero-actions"><button className="primary-button" onClick={() => jumpToShop()}>Shop fresh groceries <span>↗</span></button><button className="text-button" onClick={() => document.getElementById("reorder")?.scrollIntoView({ behavior: "smooth" })}>Explore quick reorder <span>→</span></button></div><div className="hero-proof"><div className="avatar-stack"><span>🥑</span><span>🍓</span><span>🥦</span></div><div><strong>Freshness first</strong><small>Local stores. Everyday essentials.</small></div></div></div>
          <div className="hero-art" aria-label="Illustration of fresh groceries"><div className="hero-circle circle-one"/><div className="hero-circle circle-two"/><div className="produce-basket"><div className="produce-top">🥬 🍅 🥕</div><div className="produce-middle">🥑 🍋 🍎</div><div className="basket-body">FRESH <span>✳</span> DAILY</div></div><div className="floating-card floating-top"><span>✦</span><div><strong>Picked fresh</strong><small>Quality you can trust</small></div></div><div className="floating-card floating-bottom"><span>🚚</span><div><strong>Same-day delivery</strong><small>From nearby mini-marts</small></div></div><span className="art-sparkle sparkle-one">✳</span><span className="art-sparkle sparkle-two">✦</span></div>
        </section>
        <section className="benefits"><div className="container benefits-inner"><div><span className="benefit-icon">✳</span><span><strong>Always fresh</strong><small>Picked from local stores</small></span></div><div><span className="benefit-icon">↗</span><span><strong>Fast & convenient</strong><small>Same-day delivery options</small></span></div><div><span className="benefit-icon">♡</span><span><strong>Made for your routine</strong><small>Easy reorders, less effort</small></span></div><div><span className="benefit-icon">✓</span><span><strong>Stock you can trust</strong><small>Inventory-aware shopping</small></span></div></div></section>
        <section className="shop-section container" id="shop"><div className="section-heading"><div><span className="section-kicker">GOOD FOOD, GOOD DAYS</span><h2>Explore the <em>freshest.</em></h2><p>Everyday essentials, just a few clicks away.</p></div><div className="section-count">{filtered.length} products available</div></div>
          <div className="shop-controls"><div className="categories" role="group" aria-label="Product categories">{categories.map((c) => <button key={c.name} className={`category-chip ${category === c.name ? "selected" : ""}`} onClick={() => setCategory(c.name)}><span>{c.icon}</span>{c.name}</button>)}</div><div className="filters"><label className="search-box"><span>⌕</span><input aria-label="Search products" placeholder="Search for something fresh..." value={search} onChange={(e) => setSearch(e.target.value)}/>{search && <button onClick={() => setSearch("")} aria-label="Clear search">×</button>}</label><select aria-label="Sort products" value={sort} onChange={(e) => setSort(e.target.value)}><option value="featured">Featured</option><option value="price-asc">Price: low to high</option><option value="price-desc">Price: high to low</option><option value="name">Name: A–Z</option></select><label className="stock-filter"><input type="checkbox" checked={onlyAvailable} onChange={(e) => setOnlyAvailable(e.target.checked)}/> In stock</label></div></div>
          <div className="product-grid">{filtered.map((p) => <article className="product-card" key={p.id}><div className="product-visual" style={{ background: p.color }}>{p.tag && <span className="product-tag">{p.tag}</span>}<span className="product-emoji" role="img" aria-label={p.name}>{p.icon}</span><span className={`stock-badge ${p.stock <= 7 ? "low" : ""}`}>{p.stock <= 7 ? `Only ${p.stock} left` : "● In stock"}</span></div><div className="product-info"><span className="product-category">{p.category}</span><h3>{p.name}</h3><p>{p.detail}</p><div className="product-bottom"><div><strong>{money(p.price)}</strong><small>/ {p.unit}</small></div>{cart[p.id] ? <div className="qty-control"><button aria-label={`Remove one ${p.name}`} onClick={() => changeQty(p.id, -1)}>−</button><span>{cart[p.id]}</span><button aria-label={`Add one ${p.name}`} onClick={() => changeQty(p.id, 1)} disabled={cart[p.id] >= p.stock}>+</button></div> : <button className="add-button" onClick={() => add(p)} aria-label={`Add ${p.name} to cart`}>+</button>}</div></div></article>)}</div>
          {filtered.length === 0 && <div className="empty-state"><span>🔎</span><h3>No groceries found</h3><p>Try another search or browse all categories.</p><button className="primary-button" onClick={() => { setSearch(""); setCategory("All"); }}>Show all products →</button></div>}
        </section>
        <section className="reorder-section" id="reorder"><div className="container reorder-inner"><div className="reorder-copy"><span className="section-kicker">THE SMARTER WAY TO SHOP</span><h2>Your usuals.<br /><em>Ready when you are.</em></h2><p>Skip the repeat searching. Your favorite essentials are one tap away with Quick Reorder.</p><div className="reorder-note">✦ Demo preview using sample repeat purchases</div><button className="primary-button" onClick={addReorder}>Add my usuals <span>↗</span></button></div><div className="reorder-panel"><div className="reorder-panel-head"><span>↻ Your quick reorder</span><span className="reorder-demo">DEMO</span></div>{products.filter((p) => p.repeat).map((p) => <div className="reorder-row" key={p.id}><span className="reorder-thumb" style={{ background: p.color }}>{p.icon}</span><span className="reorder-name"><strong>{p.name}</strong><small>{p.detail}</small></span><strong>{money(p.price)}</strong></div>)}<div className="reorder-total"><span>4 everyday favorites</span><strong>{money(products.filter((p) => p.repeat).reduce((s, p) => s + p.price, 0))}</strong></div></div></div></section>
        <section className="about-section container" id="about"><span className="section-kicker">SIMPLE BY DESIGN</span><h2>Groceries, minus the hassle.</h2><div className="steps"><div><span>01</span><div className="step-emoji">🛒</div><h3>Pick your favorites</h3><p>Browse fresh essentials and add what you need to your basket.</p></div><div><span>02</span><div className="step-emoji">✳</div><h3>We check availability</h3><p>Shop with confidence using store-level inventory information.</p></div><div><span>03</span><div className="step-emoji">🚚</div><h3>Enjoy your day</h3><p>Choose convenient delivery and get back to what matters.</p></div></div></section>
      </main>
      <footer className="footer"><div className="container footer-inner"><div><div className="footer-logo">↻ fresh<span>loop</span></div><p>Better groceries. Brighter everyday.</p></div><div className="footer-right"><span>FreshLoop · Student project demo</span><span>Ho Chi Minh City, Vietnam</span></div></div></footer>
      {notice && <div className="toast" role="status">✓ {notice}</div>}
      {cartOpen && <div className="drawer-overlay" onMouseDown={(e) => { if (e.target === e.currentTarget) { setCartOpen(false); setCheckout(false); } }}><aside className="cart-drawer" aria-label="Shopping cart" role="dialog" aria-modal="true"><div className="drawer-header"><div><span className="section-kicker">YOUR FRESH PICKS</span><h2>{checkout ? "Checkout preview" : `My cart (${count})`}</h2></div><button className="close-button" onClick={() => { setCartOpen(false); setCheckout(false); }} aria-label="Close cart">×</button></div>{checkout ? <div className="checkout-preview"><p>This is a frontend-only checkout demo. No order or payment will be submitted.</p><label>Delivery address<input value={address} onChange={(e) => setAddress(e.target.value)} placeholder="Enter delivery address"/></label><div className="checkout-summary"><span>Items</span><strong>{money(subtotal)}</strong></div><div className="checkout-summary"><span>Delivery</span><strong>{delivery ? money(delivery) : "Free"}</strong></div><div className="checkout-summary checkout-final"><span>Total</span><strong>{money(subtotal + delivery)}</strong></div><button className="primary-button full" onClick={() => { setNotice("Checkout preview only — no order was placed"); setCartOpen(false); setCheckout(false); }}>Finish demo →</button><button className="back-button" onClick={() => setCheckout(false)}>← Back to cart</button></div> : <><div className="cart-items">{count === 0 ? <div className="empty-cart"><span>🛍</span><h3>Your basket is empty</h3><p>Fresh finds are waiting for you.</p><button className="primary-button" onClick={() => { setCartOpen(false); jumpToShop(); }}>Explore groceries →</button></div> : products.filter((p) => cart[p.id]).map((p) => <div className="cart-row" key={p.id}><span className="cart-thumb" style={{ background: p.color }}>{p.icon}</span><div className="cart-row-info"><strong>{p.name}</strong><small>{money(p.price)} / {p.unit}</small><div className="qty-control"><button onClick={() => changeQty(p.id, -1)} aria-label={`Remove one ${p.name}`}>−</button><span>{cart[p.id]}</span><button onClick={() => changeQty(p.id, 1)} disabled={cart[p.id] >= p.stock} aria-label={`Add one ${p.name}`}>+</button></div></div><strong>{money(p.price * cart[p.id])}</strong></div>)}</div>{count > 0 && <div className="drawer-footer"><div className="delivery-hint">{subtotal >= 200000 ? "✓ You unlocked free delivery!" : `Add ${money(200000 - subtotal)} for free delivery`}</div><div className="checkout-summary"><span>Subtotal</span><strong>{money(subtotal)}</strong></div><div className="checkout-summary"><span>Delivery</span><strong>{delivery ? money(delivery) : "Free"}</strong></div><div className="checkout-summary checkout-final"><span>Estimated total</span><strong>{money(subtotal + delivery)}</strong></div><button className="primary-button full" onClick={() => setCheckout(true)}>Continue to checkout <span>→</span></button><small>Demo only · No real orders or payments</small></div>}</>}</aside></div>}
    </div>
  );
}
