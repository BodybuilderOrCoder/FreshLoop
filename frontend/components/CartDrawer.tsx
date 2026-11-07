import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import type { Category, Product } from "../data/products";
import { useAuth } from "../hooks/useAuth";
import { ApiError, createOrder } from "../lib/api";
import { clearSession } from "../lib/auth";
import { money } from "../utils/presentation";
import type { Translate } from "../utils/presentation";
type Props = {
  products: Product[];
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
  warehouseId: string;
  onOrderCreated: (orderId: string) => void;
};
export default function CartDrawer({
  tr,
  products,
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
  warehouseId,
  onOrderCreated,
}: Props) {
  const { session } = useAuth();
  const cartDialogRef = useRef<HTMLDialogElement>(null);
  const checkoutRequest = useRef<{ fingerprint: string; key: string } | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [canStartNewAttempt, setCanStartNewAttempt] = useState(false);

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

  const submitOrder = async (startNewAttempt = false) => {
    if (!session) return;

    if (!address.trim()) {
      setSubmitError("Please enter a delivery address.");
      return;
    }

    const items = products
      .filter((product) => cart[product.id] && product.backendProductId)
      .map((product) => ({
        product_id: product.backendProductId!,
        quantity: cart[product.id],
      }));

    if (!warehouseId || items.length !== Object.keys(cart).length) {
      setSubmitError("This cart contains an unavailable product. Refresh the catalog and try again.");
      return;
    }

    setSubmitting(true);
    setSubmitError("");
    setCanStartNewAttempt(false);
    try {
      const input = {
        warehouse_id: warehouseId,
        delivery_address: address.trim(),
        items,
      };
      const fingerprint = JSON.stringify(input);
      let request = checkoutRequest.current;
      if (
        startNewAttempt ||
        !request ||
        request.fingerprint !== fingerprint
      ) {
        request = {
          fingerprint,
          key: crypto.randomUUID(),
        };
        checkoutRequest.current = request;
      }
      const order = await createOrder(input, request.key, session.accessToken);
      onOrderCreated(order.order_id);
      checkoutRequest.current = null;
      setCartOpen(false);
      setCheckout(false);
    } catch (error) {
      // An expired session returns the drawer to its sign-in prompt.
      if (error instanceof ApiError && error.status === 401) clearSession();
      setSubmitError(error instanceof Error ? error.message : "Unable to place the order.");
      setCanStartNewAttempt(
        error instanceof ApiError && error.status === 409,
      );
    } finally {
      setSubmitting(false);
    }
  };

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
            <h2>{checkout ? "Checkout" : `My cart (${count})`}</h2>
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
            <p>Review your delivery details before placing the order.</p>
            {session ? (
              <>
            <label>
              {tr("Delivery address")}
              <input
                value={address}
                onChange={(e) => {
                  setAddress(e.target.value);
                  setSubmitError("");
                }}
                placeholder={tr("Enter delivery address")}
              />
            </label>
            <div className="checkout-summary checkout-final">
              <span>Total</span>
              <strong>{money(subtotal)}</strong>
            </div>
            {submitError && <p className="checkout-error" role="alert">{submitError}</p>}
            {canStartNewAttempt && (
              <button
                className="back-button"
                onClick={() => void submitOrder(true)}
                disabled={submitting}
              >
                Retry as a new checkout attempt
              </button>
            )}
            <button
              className="primary-button full"
              onClick={() => void submitOrder()}
              disabled={submitting}
            >
              {submitting ? "Placing order..." : "Place order"}
            </button>
              </>
            ) : (
              <div className="auth-prompt">
                {submitError && <p className="checkout-error" role="alert">{submitError}</p>}
                <p>Sign in to place your order. Your cart will be kept.</p>
                <Link
                  href={`/login?next=${encodeURIComponent("/?cart=open")}`}
                  className="primary-button full"
                >
                  Sign in to continue
                </Link>
              </div>
            )}
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
                <div className="checkout-summary checkout-final">
                  <span>Total</span>
                  <strong>{money(subtotal)}</strong>
                </div>
                <button className="primary-button full" onClick={() => setCheckout(true)}>
                  Continue to checkout <span>→</span>
                </button>
                <small>No online payment in this demo</small>
              </div>
            )}
          </>
        )}
      </aside>
    </dialog>
  );
}
