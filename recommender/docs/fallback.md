# Cold-Start and Fallback Strategy

| Situation | Behavior | `source` field |
|---|---|---|
| User has at least K purchased products | Top-K by personal score | `personal` |
| User has fewer than K purchased products | Personal items first, padded with popular products (no duplicates) | `personal` + `popular` |
| New user (no history) or unknown user id | Top-K most popular products | `popular` |

## Popularity definition

Products ranked by the total number of orders containing them across all customers
(cancelled orders excluded). Ties are broken by `product_id` so results are reproducible.

## Why a `source` field

The UI can show a "Based on your habits" label for `personal` items and a
"Popular right now" label for `popular` items.

## Future improvements

- Popularity per category or per warehouse.
- Popularity restricted to a recent time window (e.g. last 30 days).
- Filter out-of-stock products using real-time inventory.
- Use onboarding preferences for new users.