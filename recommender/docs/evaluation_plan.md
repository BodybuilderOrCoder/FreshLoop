# Offline Evaluation Plan (Precision@10)

## Goal

Measure how well the recommender predicts what a user buys next.
The 65% Precision@10 target is a goal for later weeks, not a Week 1 commitment.

## Data

Use `orders` + `order_items` (excluding `CANCELLED`), not `purchase_history`,
because `purchase_history` includes the last order and would cause data leakage.

## Split (temporal, not random)

- Only users with at least 2 orders are evaluated.
- For each user: the most recent order is the **test set**, all earlier orders are the **training set**.
- Interactions (`purchase_count`, `days_since_last`) are computed from training orders only,
  with `as_of` set to the last training order date.

## Metrics

- **Precision@10** = (number of Top-10 items that appear in the user's test order) / 10,
  averaged over evaluated users.
- **Recall@10** = (hits in Top-10) / (number of distinct items in the test order).
- **Hit Rate@10** = share of users with at least one hit.
- Optional: NDCG@10.

## Compared methods

1. Popularity only.
2. Frequency x recency baseline (this module).
3. `implicit_rating` from `purchase_history` (database team's score), computed only from training orders if possible.
4. ALS collaborative filtering (library `implicit`), once the data is large enough.

## Known data requirements

The dataset must contain repeated purchases per user (multiple orders over time).
If most user-product pairs appear only once, every method will score near zero and
the results will not be meaningful.

## Report format

A table of Precision@10 / Recall@10 / Hit Rate@10 per method, with the number of
evaluated users and the split date range.