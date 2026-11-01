**WEEK 3 TASK ASSIGNMENT & FEATURE-FREEZE PLAN**

Sprint: 02–08 November 2026 \| Team: 4 members \| Working branch: dev

Status: Proposed execution plan based on the official research proposal, Week 1–2 assignments, and reviewed dev-branch implementation as of 01 November 2026.

# 1. Sprint objective and completion target

Complete approximately 90% of the agreed MVP feature scope by Sunday, 08 November. Week 4 (09–15 November) is reserved primarily for integration testing, defect remediation, reproducibility, and report drafting; 16–19 November is buffer for final validation, submission packaging and presentation.

The 90% target is a scope-completion goal, not a measured current status or a claim that research KPIs have already been met. A feature counts as complete only after end-to-end verification and its evidence is committed to dev.

## 1.1 Mandatory P0 release path

- Customer chooses warehouse → loads PostgreSQL-backed catalog → adds to cart → checks out → order and order_items persist atomically → stock updates correctly → order status can be retrieved.

- Returning/demo customer receives actual Top-10 recommendation response via FastAPI → Redis HIT/MISS behavior is demonstrated → out-of-stock recommendations are excluded.

- Staff can perform a protected stock update → storefront receives warehouse-scoped stock changes without refresh through SSE.

- Every teammate can reproduce the demo from clean setup instructions; test failures and limitations are documented.

## 1.2 Scope limits and carry-over policy

P0 is non-negotiable. P1 may be reduced to a minimal but usable implementation. P2 is deliberately deferred rather than being represented as “90% done.” Do not spend Week 3 building optional UI before the commerce flow works.

| **Priority** | **Required in Week 3**                                                                                                   | **Can remain for Week 4 / later**                                                                                         |
|--------------|--------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------|
| P0           | Orders + atomic inventory; recommendation API + Redis; SSE demonstration; customer journey; tests and setup              | Only defect fixes and hardening after feature freeze                                                                      |
| P1           | Minimum customer/staff/admin access protection; usable staff inventory action; deployment attempt; practical KPI scripts | Visual polish, broader admin dashboard, tuning and incomplete deployment troubleshooting                                  |
| P2           | Document exclusions transparently                                                                                        | Stripe test mode, external POS, scheduled delivery, multi-warehouse fulfillment, advanced analytics, production SLO claim |

# 2. Starting-point assessment (not verified completion)

The dev branch contains a Next.js catalog and cart UI, product/warehouse FastAPI routes, auth routes, Alembic and seed data, recommendation code with baseline/ALS/Redis, and an SSE route. However, the reviewed backend router registration did not include /api/orders or /api/recommendations; the SSE implementation compares database snapshots periodically rather than using Redis Pub/Sub. Therefore the main sprint risk is incomplete end-to-end integration, not lack of UI pages.

# 3. Member 1 — Hiếu \| Team Leader & Full-Stack Developer

## Task 1.1 — Complete production-shaped customer journey (P0)

- Integrate create-order and get-order endpoints using the backend-agreed schema; render actual order number/status, totals, and server-side error messages.

- Preserve warehouse selection across catalog, cart, checkout and order requests; prevent checkout with unavailable/invalid products.

- Handle loading, empty, network failure, 401/403, insufficient stock (409), validation and double-submission states; clear cart only on confirmed success.

- Ensure product listing, detail, cart, Quick Reorder and order status work on mobile and desktop.

**Expected deliverable:** Customer can complete a database-backed checkout from the storefront; confirmation and order status use persisted server data.

**Acceptance evidence:** Screen recording/screenshots of full checkout; API Network traces; frontend test results; errors and empty-state evidence.

## Task 1.2 — Connect personalized Quick Reorder & real-time inventory (P0)

- Consume the agreed recommendation endpoint (not mock-only IDs), show top-10 in stock for the selected warehouse, and display an honest fallback/loading/error state.

- Validate SSE event names and payloads with Tiến and Ân; update the selected warehouse catalog and product details without refreshing.

- Prevent stale warehouse selection or late responses from overwriting another warehouse’s stock.

**Expected deliverable:** Real recommendations and stock updates visibly affect the customer UI.

**Acceptance evidence:** Demo using actual seeded user and staff stock adjustment, recording before/after stock and recommendation response.

## Task 1.3 — Integration owner, UI freeze and delivery (P0/P1)

- Publish one frozen API contract (paths, sample JSON, status codes, auth, warehouse semantics) and an integration matrix with owners.

- Review and merge teammates’ tested changes to dev; never overwrite other modules. Run the complete smoke test twice before feature freeze.

- Finalize responsive visual QA and approved Smart Basket branding only after all P0 journeys pass; no decorative legacy symbols.

- Coordinate Vercel frontend deployment if feasible and document required environment variables.

**Expected deliverable:** One demonstrable integrated storefront, shared checklist, sprint progress log and integration notes.

**Acceptance evidence:** Build/lint/test output, shared demo checklist, relevant commits, deployment URL or documented blocker.

# 4. Member 2 — Tiến \| Backend / Commerce Engineer

## Task 2.1 — Order and checkout API (CRITICAL P0)

- Implement POST /api/orders and GET /api/orders/{order_id} (or freeze a consistently versioned alternative with Hiếu). Persist order and order_items, calculate total on the server.

- Apply one-warehouse-per-order fulfillment. Validate user, address, product availability and requested quantities.

- Execute order creation and stock mutation in a single transaction with row-level locking or an equivalent safe concurrency strategy; enforce available = quantity - reserved_quantity.

- Define and implement one consistent reserve/deduct/release policy; handle insufficient stock, duplicate requests and rollback.

**Expected deliverable:** Reliable persisted checkout with no overselling under tested concurrent attempts.

**Acceptance evidence:** Swagger samples; success/400/401/403/404/409 cases; transaction tests; order and inventory SQL before/after.

## Task 2.2 — Recommendation/stock integration endpoints (CRITICAL P0)

- Expose GET /api/recommendations/{user_id}?warehouse_id=... or an agreed authenticated equivalent and connect to Ân’s recommender service.

- Filter results against selected warehouse availability, return stable product IDs and ranking metadata; set fallback behavior for cold users and Redis errors.

- Provide a staff-authorized stock mutation endpoint that persists changes and triggers the SSE detection/event mechanism.

- Keep routes, status codes and JSON contracts consistent with frontend; update Swagger.

**Expected deliverable:** Actual recommendation and authorized inventory mutation APIs consumed by the frontend.

**Acceptance evidence:** Endpoint tests, example JSON payloads and successful browser integration demonstration.

## Task 2.3 — Minimal security and regression testing (P0/P1)

- Enforce authentication/role authorization on order ownership and stock mutation; ensure a customer cannot modify warehouse stock or read another customer’s private orders.

- Validate CORS, secrets via environment, safe error responses and no leaked credential values.

- Run product, authentication, inventory and order regression tests; prioritize correct transactions over expanded auth UI.

**Expected deliverable:** Minimally protected commerce flow with repeatable automated tests.

**Acceptance evidence:** Test logs for unauthorized access, invalid input, concurrent checkout and regression cases.

# 5. Member 3 — Thắng \| Database & Data Engineer

## Task 3.1 — Transactional inventory and data integrity (CRITICAL P0)

- Agree with Tiến on a single warehouse per order and document status transitions and quantity/reserved_quantity lifecycle.

- Validate and revise SQLAlchemy/Alembic constraints where needed (including reserved_quantity \<= quantity), indexes and rollback behavior.

- Write database integration tests for concurrent orders, insufficient stock, cancellations/releases as applicable, and foreign-key integrity.

- Confirm migration from a clean database and idempotent/reproducible seeding.

**Expected deliverable:** Database supports real checkout safely and can be initialized reliably by another member.

**Acceptance evidence:** Migration logs, concurrent test logs, before/after inventory queries, updated schema dictionary.

## Task 3.2 — Final dataset and leakage-safe ML inputs (P0)

- Freeze provenance and versioned files for training/test interactions; define chronological split at order level and prohibit future purchase data in training features.

- Provide enough repeated-user behavior for meaningful baseline/ALS comparison; distinguish synthetic results from real-world generalization.

- Align warehouse/product IDs and purchase-history fields with Ân and Tiến; document preprocessing transformations.

**Expected deliverable:** Reproducible dataset and traceable model evaluation input.

**Acceptance evidence:** Data dictionary, exact split script/parameters, data-quality checks, row counts, seed and extraction commands.

## Task 3.3 — Database report evidence (P1)

- Capture ERD, key constraints, query plans and SQL latency measurements with methodology and environment.

- Do not equate sub-millisecond SQL query time with p95 end-to-end HTTP response time; label each benchmark accurately.

- Assist Tiến in diagnosing transaction, locking and migration defects immediately.

**Expected deliverable:** Report-ready database section with realistic limitations.

**Acceptance evidence:** ERD, EXPLAIN ANALYZE outputs, measured environment and test commands.

# 6. Member 4 — Ân \| ML / Redis / Real-Time Engineer

## Task 4.1 — Integrate recommendation service (CRITICAL P0)

- Freeze one response format, cache key naming convention and TTL with Tiến and Hiếu; update stale README examples.

- Expose baseline/ALS through backend-compatible service functions; deliver deterministic Top-10 and cold-start fallback using user-product interactions.

- Exclude out-of-stock products for selected warehouse and prevent stale cached results after a stock-out or order.

- Provide a graceful response when Redis is temporarily unavailable, rather than failing the entire UI.

**Expected deliverable:** Working cache-first recommendation pipeline through FastAPI with warehouse-aware product availability.

**Acceptance evidence:** Live HIT/MISS trace, Redis key/TTL evidence, cold-start and stock-out tests, API output.

## Task 4.2 — Finish inventory event flow (P0)

- Coordinate with Tiến to connect stock mutation → persisted database update → client SSE update and cache invalidation.

- If Redis Pub/Sub event-driven delivery cannot be completed safely by feature freeze, retain the existing snapshot-polling SSE as an explicitly documented temporary implementation.

- Measure actual propagation delay and test disconnect/reconnect, warehouse isolation and stock-out behavior.

**Expected deliverable:** Browser updates stock without refresh with clearly documented transport and limitations.

**Acceptance evidence:** Timed event demo, measured delay samples, reconnect test and explanatory sequence diagram.

## Task 4.3 — Defensible recommendation and latency evaluation (P0/P1)

- Run a chronological held-out comparison of popularity, frequency/recency and ALS using identical eligible users and candidate rules.

- Record Precision@10, Recall@10, evaluated user count, data dates, random seed, cold-start results and leakage checks.

- Measure cached/missed API p50/p95 latency end-to-end, separating Redis operation latency from HTTP API latency; record sample size and environment.

- If Precision@10 ≥65% is reached only on synthetic data, state this clearly and avoid generalizing the claim.

**Expected deliverable:** Reproducible evaluation scripts, figures and limitations for the final report.

**Acceptance evidence:** CSV/logs, execution commands, versioned artifacts and measured numerical outcomes.

# 7. Cross-team integration contracts — freeze by 02 November

| **Contract**    | **Decision to confirm**                                                                          | **Owners**          |
|-----------------|--------------------------------------------------------------------------------------------------|---------------------|
| Warehouse/order | One warehouse per order; stock = quantity − reserved_quantity; reserve/deduct/release transition | Tiến + Thắng + Hiếu |
| Commerce        | Exact create/get order payload, authentication, server-calculated totals and error codes         | Tiến + Hiếu         |
| Recommendations | Response IDs and scores, top_k, warehouse filtering, user identity, key/TTL/fallback             | Ân + Tiến + Hiếu    |
| SSE             | Event name, payload, selected warehouse, delivery mechanism, reconnection policy                 | Ân + Tiến + Hiếu    |
| Data evaluation | Provenance, chronological split, excluded products and same candidate policy                     | Thắng + Ân          |

# 8. Seven-day execution schedule

| **Day**    | **Mandatory milestone**                                                  | **Release gate**                                 |
|------------|--------------------------------------------------------------------------|--------------------------------------------------|
| Mon 02 Nov | Freeze scope/contracts; checkout transaction design; distribute blockers | Contract v1 accepted by all four                 |
| Tue 03 Nov | Order endpoints + database constraints; recommendation API skeleton      | Real test order persisted; response shape stable |
| Wed 04 Nov | Cart → order UI integrated; recommendation Redis HIT/MISS integrated     | First complete checkout demo                     |
| Thu 05 Nov | Staff stock update → SSE UI; stock-out invalidation; concurrency tests   | Real inventory change visible in browser         |
| Fri 06 Nov | End-to-end regression; cold-start, errors, permissions; data evaluation  | No unresolved P0 integration blocker             |
| Sat 07 Nov | Clean setup, evidence capture, deployment attempt, report figures        | Reproducible demo by teammate                    |
| Sun 08 Nov | Feature freeze; final walkthrough; mark incomplete P1/P2 honestly        | P0 acceptance signed; release candidate tagged   |

# 9. Week 3 acceptance checklist / Definition of Done

☐ Products and inventory originate from PostgreSQL via FastAPI for a selected warehouse.

☐ Authenticated/identified user can checkout; an order and its items persist atomically; stock cannot become negative or oversell.

☐ Order confirmation and retrieval display correct server-stored data; duplicate and insufficient-stock paths are verified.

☐ Top-10 real recommendations are available through API with Redis HIT/MISS, fallbacks and stock filtering.

☐ Authorized staff stock mutation is visible on customer UI via SSE without refresh; mechanism and measured delay are documented.

☐ Migrations and seed work from clean environment; four members can start app from README.

☐ Automated tests cover critical endpoints, database constraints, relevant frontend helpers and recommendation behavior.

☐ Report artifacts exist for architecture, SQL, model evaluation, cache/API latency and SSE propagation.

☐ No secrets committed; changes reviewed in dev; stable release candidate ready for Week 4.

☐ Unfinished P1/P2 items and limitations are explicitly listed, not represented as complete.

Scoring rule: Count an acceptance item as DONE only with passing demonstration/test evidence and a commit reference. A suggested 90% threshold is at least 9 of 10 items complete, but the first five P0-critical gates must all pass; percentage alone never overrides a failed checkout or recommendation path.

# 10. Risk control and escalation

| **Risk**                            | **Trigger**                                         | **Mitigation / owner**                                                   |
|-------------------------------------|-----------------------------------------------------|--------------------------------------------------------------------------|
| Orders remain missing               | No successful persisted order by 03 Nov EOD         | Tiến + Thắng pause P1, pair on transaction until fixed                   |
| Recommender API integration blocked | No real response by 04 Nov                          | Ân + Tiến switch to baseline first; ALS remains optional                 |
| SSE complexity grows                | Redis Pub/Sub cannot be safely integrated by 05 Nov | Use existing polling-backed SSE for MVP; record deviation and latency    |
| Scope creep                         | New features requested after 05 Nov                 | Hiếu rejects/defer unless they repair a P0 acceptance failure            |
| Unreliable KPI claims               | Only synthetic or small-scale measurement           | Report measured conditions and limitations; do not assert production SLO |

# 11. Handover to Week 4 (09–15 November) and final buffer

- Week 4: run full regression, integration and concurrent checkout tests; repair P0/P1 defects; improve security and accessibility; produce reproducible results; draft report chapters and screenshots.

- 16–19 November: final review, instructor-specific formatting, presentation/demo rehearsal and submission packaging; do not introduce architecture changes unless a blocking defect requires them.

- Handover package: feature checklist, commit/tag, README, .env.example, API specification, ERD, evaluation outputs, demo script, known issues and assigned bug owners.

# 12. Source basis and interpretation

Prepared from FreshLoop Research Proposal (official, 04 October 2026), Week 1 Task Assignment, Week 2 Task Assignment (26 October–01 November 2026), and inspection of the FreshLoop dev branch on 01 November 2026. These assignments are planning documents; repository files establish implementation presence but do not prove tests have passed. The proposed Week 3 plan intentionally prioritizes missing integrations and verifiable completion over additional features.
