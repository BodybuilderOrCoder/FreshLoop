# FRESHLOOP

## Week 2 Task Assignment & Expected Deliverables

Proposed sprint: 26 October – 1 November 2026  |  Team: 4 members  |  Status: Proposed; pending Week 1 review

## 1. Sprint Overview

Objective: integrate the independently developed Week 1 modules into a demonstrable end-to-end minimum viable product (MVP), run functional and technical evaluations, and collect evidence for the final report. This plan assumes Week 1 foundations are substantially working; incomplete Week 1 tasks must be triaged on Day 1.

Core demonstration: a customer browses database-backed products, adds items to a cart, checks out, receives Quick Reorder recommendations, and sees inventory changes without refreshing. An authorized staff member can adjust warehouse stock.

Architecture: Next.js / TypeScript / Tailwind; FastAPI / SQLAlchemy; PostgreSQL / Alembic; Redis; Python recommendation baseline (ALS optional); Server-Sent Events (SSE).

## 2. Scope and Priorities

- P0 (required): real product data, functional cart and order creation, transactional inventory checks, baseline Top-10 recommendation via Redis, stock SSE, reproducible demo, tests and evidence.
- P1 (if feasible): complete JWT/RBAC flows, richer admin screens, ALS comparison, deployment, deeper performance tuning.
- P2 (future work if unfinished): Stripe test integration, scheduled delivery, external POS integration, sophisticated analytics, production-scale availability claims.
Proposal targets are evaluation goals, not assumed results: p95 Quick Reorder <150 ms, Precision@10 >=65%, inventory staleness <=5 s, and 99.5% availability under a simulated 500-session load. Record actual results and limitations.

## 3. Member 1 — Hiếu

Role: Team Leader & Frontend Developer

### Task 1.1 — Connect Real APIs

- Replace product mock data with backend API calls; integrate search, filtering, sorting and warehouse-specific stock.
- Provide loading, empty and error states; keep API access centralized.
### Task 1.2 — Complete Customer Journey

- Implement product details, cart, checkout, order confirmation and status views.
- Connect Quick Reorder to real Top-10 recommendation responses.
### Task 1.3 — Real-Time UI and Polish

- Subscribe to inventory SSE and update product stock badges without page reload.
- Check mobile/desktop layouts; integrate approved Smart Basket logo only after UI review and remove old decorative symbols.
### Task 1.4 — Coordinate Integration

- Freeze JSON/API contracts with Tiến and Ân; manage blockers and end-to-end testing.
- Coordinate deployment and review changes on dev; do not take over all infrastructure tasks.
Expected deliverable: Functional customer-facing frontend using actual API data, with a complete checkout demo.

## 4. Member 2 — Tiến

Role: Backend / Commerce Engineer

### Task 2.1 — Commerce Endpoints

- Implement cart and order APIs, order item persistence, totals and order retrieval.
- Document request/response formats in Swagger and share with frontend.
### Task 2.2 — Transactional Inventory

- Enforce warehouse-specific stock availability; prevent overselling using database transactions and concurrency tests.
- Agree reserve/deduct/release rules with Thắng and implement consistent order state transitions.
### Task 2.3 — Access Control

- Implement minimal customer/staff/admin authentication and protected inventory mutations where feasible.
- Provide authorized stock-update endpoint for SSE demonstration.
### Task 2.4 — Module Integration

- Expose recommendation results through API and integrate SSE events with Ân.
- Test invalid requests, insufficient stock, duplicate submissions and order persistence.
Expected deliverable: Tested commerce APIs and reliable checkout backed by PostgreSQL.

## 5. Member 3 — Thắng

Role: Database & Data Engineer

### Task 3.1 — Integrity and Performance

- Validate foreign keys, constraints, migrations, indexes and warehouse inventory semantics.
- Test concurrent updates and ensure quantity/reserved_quantity remain valid.
### Task 3.2 — Recommendation Data Pipeline

- Prepare purchase history and user-product interactions using Pandas.
- Document provenance, preprocessing and chronological train/test split; coordinate with Ân.
### Task 3.3 — Warehouse Test Data

- Provide realistic data for three warehouses and reproducible seed scripts.
- Verify checkout mutations and stock reads against PostgreSQL.
### Task 3.4 — Report Evidence

- Produce final ERD, schema dictionary, migration logs, SQL test evidence and basic query timing results.
Expected deliverable: Reliable database and ML input data, plus database evaluation artifacts for report.

## 6. Member 4 — Ân

Role: Recommendation, Redis & Real-Time Engineer

### Task 4.1 — Recommendation Service

- Complete frequency/recency Top-10 baseline with cold-start fallback.
- Try ALS only if dataset and remaining time permit; do not block the baseline.
### Task 4.2 — Cache-First Serving

- Cache user recommendations in Redis with agreed key, TTL and HIT/MISS behavior.
- Invalidate unavailable products after stock-out; coordinate API integration with Tiến.
### Task 4.3 — SSE Inventory

- Publish inventory events and expose them to clients through SSE with Tiến.
- Demonstrate stock changes in browser without reload; handle reconnection.
### Task 4.4 — Evaluation

- Measure Precision@10/Recall@10 on held-out data, and cache HIT/MISS p50/p95 latency.
- Measure stock update propagation delay and preserve scripts, outputs and limitations.
Expected deliverable: Working predictive Quick Reorder, cache and SSE demo, with measured technical results.

## 7. Integration Decisions to Freeze on Day 1

- Order fulfillment: one warehouse per order for MVP; multi-warehouse fulfillment deferred.
- Available stock: quantity minus reserved_quantity, subject to agreed reserve/deduct/release lifecycle.
- Recommendation API: agree user ID, product IDs/SKUs, ranking scores, cache key format and fallback.
- Cache policy: proposal varies on retraining interval and cache format; adopt and document one implementation contract.
- Security and payments: do not describe mock checkout or omitted Stripe/JWT flows as production complete.
## 8. Seven-Day Execution Plan

| Day | Milestone |
| --- | --- |
| Day 1 | Week 1 review; close blockers; freeze contracts and MVP scope |
| Day 2 | Product API integration; order API; recommendation endpoint |
| Day 3 | End-to-end checkout; transaction and stock validation |
| Day 4 | Redis cache + SSE integration; warehouse stock demo |
| Day 5 | Feature freeze; integration tests; performance and model evaluation |
| Day 6 | Deployment attempt; documentation, screenshots and evidence |
| Day 7 | Full demonstration; review limitations; promote tested dev to main |

## 9. Acceptance Criteria / Definition of Done

☐ Products and inventory originate from PostgreSQL through FastAPI, not only mocks.

☐ Cart → checkout → order creation persists data and rejects insufficient stock.

☐ Quick Reorder returns a Top-10 list via API with Redis HIT/MISS and fallback behavior.

☐ Inventory changes reach the customer UI over SSE without manual refresh.

☐ Warehouse-level stock semantics and concurrent checkout behavior are tested.

☐ Relevant permissions, API errors and failure states are demonstrated or explicitly documented as limitations.

☐ Migrations and seed scripts work from a clean environment.

☐ Source, tests, README and evidence are committed to dev; final tested release merged into main.

## 10. Final Report Evidence Package

- Architecture: final deployment and data-flow diagrams.
- Backend: Swagger endpoints, test logs, order workflow screenshots.
- Database: ERD, migrations, data dictionary, integrity and query results.
- Recommendation: dataset provenance, train/test methodology, baseline vs ALS if available, Precision@10/Recall@10.
- Caching: cache HIT/MISS timing and p95 Quick Reorder response.
- Real-time: SSE sequence and measured propagation delay.
- Delivery: running URLs or reproducible local instructions, screenshots and known limitations.
- Contribution: task board, commit history and individual demonstrations.
Measurement caution: a short load test cannot establish long-term 99.5% availability. Report load level, duration, environment and actual observed outcome. Do not claim unmeasured proposal KPIs as achieved.

## 11. Git Workflow and Review

Retain Week 1 workflow: main is stable release; dev is shared integration. Team members work directly on dev, pull before editing, stage only owned files, coordinate shared contract changes, never force-push, and never commit secrets. Merge dev into main only after integration review and testing.

At the final review each member should provide a 5–10 minute demonstration, test evidence, blockers and a short statement of what remains incomplete.

## 12. Source Basis and Status

Prepared from FreshLoop Research Proposal (official), 4 October 2026, and FreshLoop Week 1 Task Assignment. This Week 2 document is a proposed sprint plan, not an instructor-approved requirement or a verification of current implementation progress.
