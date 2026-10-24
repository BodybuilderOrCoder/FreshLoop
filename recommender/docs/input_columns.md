# Recommendation Input Columns

## Source tables (PostgreSQL)

| Table | Column | Type | Description |
|---|---|---|---|
| orders | order_id | UUID | Order identifier |
| orders | user_id | UUID | Customer who placed the order |
| orders | created_at | timestamp | Order time (used for recency) |
| orders | status | text | Orders with status `CANCELLED` are excluded |
| order_items | order_id | UUID | Link to the order |
| order_items | product_id | UUID | Purchased product |
| order_items | quantity | integer | Must be > 0 |

## Output: user-product interaction table

| Column | Type | Description |
|---|---|---|
| user_id | string | Customer id (UUID as string) |
| product_id | string | Product id (UUID as string) |
| purchase_count | int | Number of distinct orders containing the product |
| total_qty | float | Total units purchased |
| last_purchased_at | timestamp | Most recent purchase time |
| days_since_last | float | Days between the last purchase and the latest order in the dataset |

Sample output: `sample_output/interactions_sample.csv`

## Cleaning rules

1. Drop rows with missing `order_id`, `user_id`, `product_id`, `quantity` or `created_at`.
2. Drop rows with `quantity <= 0`.
3. Drop rows with an unparseable date.
4. Merge duplicate `(order_id, product_id)` rows by summing `quantity`.
5. Convert all UUIDs to strings.

Each step is counted and logged in the cleaning report printed by `python -m recommender.preprocess`.

## Why `purchase_history` is not used as the input

`purchase_history` is a pre-aggregated table (one row per user-product) and has no purchase date.
Using it would make it impossible to split data by time and would leak information from the
last order into the features. It is kept only as a comparison baseline (`implicit_rating`).