# FreshLoop Frontend

Customer storefront for FreshLoop, built with Next.js (App Router), React and TypeScript.

## Setup

```bash
cd frontend
npm install
cp .env.example .env.local   # then edit the values
npm run dev                  # http://localhost:3000
```

The storefront needs the FastAPI backend (default `http://localhost:8000`) with migrated and seeded data. See the backend and database READMEs.

| Variable | Purpose |
| --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | FastAPI base URL, no trailing slash. Defaults to `http://localhost:8000`. |
| `NEXT_PUBLIC_DEMO_USER_ID` | Optional seeded customer UUID for Quick Reorder while signed out. Signed-in customers use their own account. |

## Checks

```bash
npm test        # node --test: API client, session, cart, catalog and mapper logic
npm run lint
npm run build
```

## Structure

| Path | Contents |
| --- | --- |
| `app/` | Routes: home (`/`), sign-in (`/login`), product details (`/product/[productId]`), order status (`/orders/[orderId]`), favorites |
| `components/` | UI sections and reusable parts (header, product card, cart drawer, Quick Reorder) |
| `hooks/` | `useCatalog` (warehouses, stock, live SSE updates), `useCart`, `useFavorites`, `useAuth` |
| `lib/api.ts` | The only module that calls the backend; shared request types and error handling |
| `lib/auth.ts` | Session storage for the backend JWT |
| `lib/*-logic.ts`, `lib/product-mapper.ts` | Pure logic covered by `tests/` |

## Customer journey

1. Choose a warehouse. Catalog and stock come from `GET /api/warehouses/{id}/products`.
2. Stock badges update without reload via the warehouse SSE stream.
3. Add items from the catalog or a product page; quantities are capped at available stock.
4. Sign in or register at `/login` when checking out; the cart is kept.
5. Check out from the cart drawer (`POST /api/orders`), then land on `/orders/{id}?placed=1`.
6. Quick Reorder shows in-stock Top-10 picks from `GET /api/recommendations/{user_id}`.

The API contract the frontend relies on is in [docs/api-contract.md](docs/api-contract.md).

## Known limitations

- `GET /api/recommendations/{user_id}` is not registered in the backend yet, so Quick Reorder shows its fallback message.
- Next.js keeps visited pages mounted while hidden and re-runs their effects on return. Anything stored in a page's state must allow for this.
- Staff and admin actions have no storefront UI; use Swagger.
- No online payment.
