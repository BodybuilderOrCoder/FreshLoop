import { useEffect, useRef } from "react";
import type { Category } from "../data/products";
import { products } from "../data/products";
import { money } from "../utils/presentation";
import type { Translate } from "../utils/presentation";
type Props = {
  tr: Translate;
  jumpToShop: (category?: Category) => void;
  count: number;
  setCartOpen: (value: boolean) => void;
  cart: Record<number, number>;
  changeQty: (id: number, delta: number) => void;
  checkout: boolean;
  setCheckout: (value: boolean) => void;
  address: string;
  setAddress: (value: string) => void;
  subtotal: number;
  delivery: number;
  setNotice: (value: string) => void;
};
export default function CartDrawer({
  tr,
  jumpToShop,
  count,
  setCartOpen,
  cart,
  changeQty,
  checkout,
  setCheckout,
  address,
  setAddress,
  subtotal,
  delivery,
  setNotice,
}: Props) {
  const cartDialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = cartDialogRef.current;
    if (!dialog) return;

    const previousFocus =
      document.activeElement instanceof HTMLElement ? document.activeElement : null;

    const previousOverflow = document.body.style.overflow;

    if (!dialog.open) {
      dialog.showModal();
    }

    document.body.style.overflow = "hidden";

    return () => {
      dialog.close();
      document.body.style.overflow = previousOverflow;

      if (previousFocus?.isConnected) {
        previousFocus.focus();
      }
    };
  }, []);

  return (
    <dialog
      ref={cartDialogRef}
      onCancel={() => {
        setCartOpen(false);
        setCheckout(false);
      }}
      aria-label="Shopping cart"
      className="drawer-overlay"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) {
          setCartOpen(false);
          setCheckout(false);
        }
      }}
    >
      <aside className="cart-drawer">
        <div className="drawer-header">
          <div>
            <span className="section-kicker">{tr("YOUR FRESH PICKS")}</span>
            <h2>{checkout ? "Checkout preview" : `My cart (${count})`}</h2>
          </div>
          <button
            className="close-button"
            onClick={() => {
              setCartOpen(false);
              setCheckout(false);
            }}
            aria-label="Close cart"
          >
            ×
          </button>
        </div>
        {checkout ? (
          <div className="checkout-preview">
            <p>
              This is a frontend-only checkout demo. No order or payment will be
              submitted.
            </p>
            <label>
              {tr("Delivery address")}
              <input
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder={tr("Enter delivery address")}
              />
            </label>
            <div className="checkout-summary">
              <span>Items</span>
              <strong>{money(subtotal)}</strong>
            </div>
            <div className="checkout-summary">
              <span>Delivery</span>
              <strong>{delivery ? money(delivery) : "Free"}</strong>
            </div>
            <div className="checkout-summary checkout-final">
              <span>Total</span>
              <strong>{money(subtotal + delivery)}</strong>
            </div>
            <button
              className="primary-button full"
              onClick={() => {
                setNotice("Checkout preview only — no order was placed");
                setCartOpen(false);
                setCheckout(false);
              }}
            >
              Finish demo →
            </button>
            <button className="back-button" onClick={() => setCheckout(false)}>
              ← Back to cart
            </button>
          </div>
        ) : (
          <>
            <div className="cart-items">
              {count === 0 ? (
                <div className="empty-cart">
                  <span>🛍</span>
                  <h3>{tr("Your basket is empty")}</h3>
                  <p>{tr("Fresh finds are waiting for you.")}</p>
                  <button
                    className="primary-button"
                    onClick={() => {
                      setCartOpen(false);
                      jumpToShop();
                    }}
                  >
                    Explore groceries →
                  </button>
                </div>
              ) : (
                products
                  .filter((p) => cart[p.id])
                  .map((p) => (
                    <div className="cart-row" key={p.id}>
                      <span className="cart-thumb" style={{ background: p.color }}>
                        {p.icon}
                      </span>
                      <div className="cart-row-info">
                        <strong>{tr(p.name)}</strong>
                        <small>
                          {money(p.price)} / {tr(p.unit)}
                        </small>
                        <div className="qty-control">
                          <button
                            onClick={() => changeQty(p.id, -1)}
                            aria-label={`Remove one ${tr(p.name)}`}
                          >
                            −
                          </button>
                          <span>{cart[p.id]}</span>
                          <button
                            onClick={() => changeQty(p.id, 1)}
                            disabled={cart[p.id] >= p.stock}
                            aria-label={`Add one ${tr(p.name)}`}
                          >
                            +
                          </button>
                        </div>
                      </div>
                      <strong>{money(p.price * cart[p.id])}</strong>
                    </div>
                  ))
              )}
            </div>
            {count > 0 && (
              <div className="drawer-footer">
                <div className="delivery-hint">
                  {subtotal >= 200000
                    ? "✓ You unlocked free delivery!"
                    : `Add ${money(200000 - subtotal)} for free delivery`}
                </div>
                <div className="checkout-summary">
                  <span>Subtotal</span>
                  <strong>{money(subtotal)}</strong>
                </div>
                <div className="checkout-summary">
                  <span>Delivery</span>
                  <strong>{delivery ? money(delivery) : "Free"}</strong>
                </div>
                <div className="checkout-summary checkout-final">
                  <span>Estimated total</span>
                  <strong>{money(subtotal + delivery)}</strong>
                </div>
                <button className="primary-button full" onClick={() => setCheckout(true)}>
                  Continue to checkout <span>→</span>
                </button>
                <small>Demo only · No real orders or payments</small>
              </div>
            )}
          </>
        )}
      </aside>
    </dialog>
  );
}
