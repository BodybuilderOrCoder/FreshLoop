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
| `NEXT_PUBLIC_DEMO_USER_ID` | Seeded customer UUID used for Quick Reorder until storefront sign-in exists. |

## Checks

```bash
npm test        # node --test: API client, cart, catalog and mapper logic
npm run lint
npm run build
```

## Structure

| Path | Contents |
| --- | --- |
| `app/` | Routes: home (`/`), product details (`/product/[productId]`), order status (`/orders/[orderId]`), favorites |
| `components/` | UI sections and reusable parts (header, product card, cart drawer, Quick Reorder) |
| `hooks/` | `useCatalog` (warehouses, stock, live SSE updates), `useCart`, `useFavorites` |
| `lib/api.ts` | The only module that calls the backend; shared request types and error handling |
| `lib/*-logic.ts`, `lib/product-mapper.ts` | Pure logic covered by `tests/` |

## Customer journey

1. Choose a warehouse. Catalog and stock come from `GET /api/warehouses/{id}/products`.
2. Stock badges update without reload via the warehouse SSE stream.
3. Add items from the catalog or a product page; quantities are capped at available stock.
4. Check out from the cart drawer (`POST /api/orders`), then land on `/orders/{id}?placed=1`.
5. Quick Reorder shows in-stock Top-10 picks from `GET /api/recommendations/{user_id}`.

The API contract the frontend relies on is in [docs/api-contract.md](docs/api-contract.md).

## Known limitations

- `POST /api/orders`, `GET /api/orders/{id}` and `GET /api/recommendations/{user_id}` are not registered in the backend yet. Checkout and Quick Reorder show a clear "not available yet" message until they are.
- No storefront sign-in yet; Quick Reorder uses `NEXT_PUBLIC_DEMO_USER_ID` and orders are sent without an `Authorization` header.
- No online payment.
