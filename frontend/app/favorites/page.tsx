"use client";

import Link from "next/link";
import { products } from "../../data/products";
import { useFavorites } from "../../hooks/useFavorites";

export default function FavoritesPage() {
  const { favorites, favoritesLoaded, toggleFavorite } = useFavorites();

  const favoriteProducts = products.filter((product) =>
    favorites.includes(product.id)
  );

  return (
    <main className="favorites-page container">
      <Link href="/" className="favorites-back">
        ← Back to shop
      </Link>

      <div className="section-heading">
        <div>
          <span className="section-kicker">SAVED FOR LATER</span>
          <h1>Your favorites</h1>
          <p>Keep your favorite groceries in one place.</p>
        </div>

        {favoritesLoaded && (
          <span className="section-count">
            {favoriteProducts.length} saved products
          </span>
        )}
      </div>

      {!favoritesLoaded ? (
        <p role="status">Loading your favorites...</p>
      ) : favoriteProducts.length === 0 ? (
        <div className="empty-state">
          <h2>No favorites yet</h2>
          <p>Tap the heart on a product to save it here.</p>

          <Link href="/" className="primary-button">
            Explore groceries →
          </Link>
        </div>
      ) : (
        <div className="product-grid">
          {favoriteProducts.map((product) => (
            <article className="product-card" key={product.id}>
              <div
                className="product-visual"
                style={{ background: product.color }}
              >
                <span className="product-emoji" aria-hidden="true">
                  {product.icon}
                </span>

                <button
                  type="button"
                  className="favorite-button is-favorite"
                  onClick={() => toggleFavorite(product.id)}
                  aria-label={`Remove ${product.name} from favorites`}
                  aria-pressed={true}
                >
                  <span aria-hidden="true">♥</span>
                </button>
              </div>

              <div className="product-info">
                <span className="product-category">
                  {product.category}
                </span>

                <h3>{product.name}</h3>
                <p>{product.detail}</p>

                <div className="product-bottom">
                  <div>
                    <strong>
                      {product.price.toLocaleString("vi-VN")}₫
                    </strong>
                    <small> / {product.unit}</small>
                  </div>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </main>
  );
}