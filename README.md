# FreshLoop

**FreshLoop — A Real-Time Predictive Inventory Grocery Application.** A *headless* grocery e-commerce platform (decoupled storefront and backend). It pre-loads each returning customer's usual basket (Quick Reorder) and keeps stock across several mini-marts in sync in real time.

> **IT for E-commerce** course project · Group 6 · Class MSIS4133.R12.CTTT · Instructor: Trần Văn Hải Triều · Direction I: Advanced & Next-Gen E-Commerce Web Development

## Table of Contents

1. [Overview](#1-overview)
2. [Features](#2-features)
3. [Engineering Objectives](#3-engineering-objectives)
4. [Architecture and Tech Stack](#4-architecture-and-tech-stack)
5. [Repository Structure](#5-repository-structure)
6. [Getting Started](#6-getting-started)
7. [Environment Variables](#7-environment-variables)
8. [Testing](#8-testing)
9. [Core API](#9-core-api)
10. [Current Status and Limitations](#10-current-status-and-limitations)
11. [Changes from the Proposal](#11-changes-from-the-proposal)
12. [Team](#12-team)
13. [Related Documents](#13-related-documents)

## 1. Overview

FreshLoop serves a network of 3–5 affiliated mini-marts in a mixed residential–commercial ward of Ho Chi Minh City. It is built for three groups of users:
- **Customers** who order on a schedule or for same-day delivery.
- **Warehouse and mini-mart operators** who manage stock in real time.
- **The platform operator** who monitors orders and prediction accuracy.

Traditional grocery platforms share three bottlenecks. FreshLoop addresses them as follows:

| Problem | FreshLoop's approach |
| --- | --- |
| Monolithic architecture: storefront, stock and order logic deployed as one block | Headless: Next.js and FastAPI communicate only over REST and SSE and deploy independently |
| Cold-start cart: loyal customers re-search the same 15–20 items every visit | **Quick Reorder**: predicts the Top-10 products a customer is likely to buy again, served from a Redis cache |
| Stock is queried synchronously on every page load, causing latency spikes at peak hours (5–7 p.m.) | Per-warehouse inventory pushed over **Server-Sent Events**; recommendations are cached ahead of time |

## 2. Features

Status of the `dev` branch, verified on 3 Nov 2026. Details are in [docs/project-management/](docs/project-management/).

| Area | Feature | Status |
| --- | --- | --- |
| Catalog | Warehouse selection; per-warehouse product and stock list; search, category filter, sorting; product detail page; favorites | ✅ Working |
| Cart | Client-side cart, capped at available stock, reconciled when the warehouse changes | ✅ Working |
| Inventory | Staff/Admin stock updates with JWT auth and `Idempotency-Key`; cannot drop below reserved quantity | ✅ Working |
| Real-time | Per-warehouse SSE (`inventory.snapshot`, `inventory.changed`); stock badges update live with a connection indicator | ✅ Working (DB snapshot polling) |
| Accounts | Registration (Argon2), login (JWT), CUSTOMER / STAFF / ADMIN roles | ✅ API working · ⏳ no UI yet |
| Recommendations | Frequency × recency baseline, ALS (`implicit`), popularity fallback, Redis HIT/MISS cache | ✅ Library level · ⏳ no API yet |
| Orders | Checkout, order persistence, stock reservation, order status | ⏳ UI ready · ❌ no API yet |
| Administration | Admin/operator dashboard | ❌ Not started |
| Deployment | Vercel (frontend), Railway (backend, DB, Redis) | ❌ Not started |

## 3. Engineering Objectives

These are the targets set in the proposal (4 Oct 2026). **They are not achieved results.** Measured values will be reported in the final report.

| Objective | Target | Current state |
| --- | --- | --- |
| Quick Reorder API latency (p95) | < 150 ms | Not measurable yet: endpoint does not exist |
| Precision@10 on held-out orders | ≥ 65% | Must be re-run on the current (synthetic) dataset |
| Inventory staleness | ≤ 5 seconds | SSE works; not measured yet |
| Availability under 500 concurrent sessions | ≥ 99.5% | No load test yet |
| Independently deployable frontend and backend | Headless | Decoupled; not deployed yet |

## 4. Architecture and Tech Stack

FreshLoop is a **modular monolith**: one FastAPI process contains the Commerce, Real-time and Prediction modules. The frontend talks to the backend only through REST and SSE.

```text
┌──────────────────────────┐      REST (JSON)      ┌──────────────────────────────────────┐
│  Next.js storefront      │ ────────────────────► │  FastAPI backend                     │
│  (frontend/)             │ ◄──────────────────── │  ├─ auth: JWT, RBAC                  │
│  catalog · cart · SSE UI │   SSE (text/event-    │  ├─ products, warehouses, inventory  │
└──────────────────────────┘    stream)            │  ├─ inventory events (SSE)           │
                                                   │  └─ (planned) orders, recommendations│
                                                   └───────────┬───────────────┬──────────┘
                                                               │ SQLAlchemy    │
                                                   ┌───────────▼──────┐  ┌─────▼──────────────┐
                                                   │ PostgreSQL 16    │  │ Redis 7            │
                                                   │ source of truth  │  │ recommendation     │
                                                   │ (Alembic)        │  │ cache (cache-aside)│
                                                   └───────────┬──────┘  └─────▲──────────────┘
                                                               │ Pandas ETL    │
                                                   ┌───────────▼───────────────┴──────────┐
                                                   │ recommender/: baseline · ALS · eval  │
                                                   └──────────────────────────────────────┘
```

| Layer | Technology |
| --- | --- |
| Frontend | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS |
| Backend | FastAPI, SQLAlchemy 2.0, Pydantic 2, PyJWT, pwdlib (Argon2) |
| Database | PostgreSQL 16, Alembic |
| Cache | Redis 7 |
| Recommendations | Python, Pandas, NumPy, `implicit` (ALS) |
| Real-time | Server-Sent Events |
| Local infrastructure | Docker Compose |
| Deployment (planned) | Vercel + Railway |

## 5. Repository Structure

```text
FreshLoop/
├── frontend/              # Next.js storefront          → frontend/README.md
│   ├── app/               #   routes: /, /product/[id], /orders/[id], /favorites
│   ├── components/ hooks/ lib/ styles/ tests/
│   └── docs/api-contract.md
├── backend/               # FastAPI
│   ├── app/               #   routers, schemas, services, models, security, dependencies
│   ├── alembic/           #   migrations
│   ├── seed_mock_data.py  #   reproducible seed data (UUIDv5)
│   └── tests/
├── database/              # DB docs, ML data pipeline, train/test data, integrity tests → database/README.md
├── recommender/           # baseline, ALS, Redis cache, evaluation → recommender/README.md
├── docs/project-management/  # WBS, progress report, testing checklist
├── docker-compose.yml     # PostgreSQL + Redis for local development
└── .env.example           # environment variables for backend and recommender
```

## 6. Getting Started

### 6.1 Prerequisites

- **Docker Desktop** (PostgreSQL and Redis).
- **Python 3.10+**. The team uses 3.12.
- **Node.js and npm**. Tested with Node 24.
- **Git**.

The commands below use bash syntax (Git Bash, macOS, Linux). In PowerShell, use `copy` instead of `cp`, and `.venv\Scripts\Activate.ps1` to activate the virtual environment.

### 6.2 Clone and configure

```bash
git clone https://github.com/BodybuilderOrCoder/FreshLoop.git
cd FreshLoop
git checkout dev

cp .env.example .env
```

Open `.env` and set `JWT_SECRET` to a random string of **at least 32 bytes**; the backend refuses to start without it. You can generate one with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 6.3 Start PostgreSQL and Redis

```bash
docker compose up -d
docker ps        # expect freshloop-postgres (5432) and freshloop-redis (6379)
```

### 6.4 Backend

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

alembic upgrade head                 # create the schema
python seed_mock_data.py --clean     # load sample data: 50 users, 200 products, 3 warehouses
uvicorn app.main:app --reload --port 8000
```

> `--clean` **deletes all existing data** before seeding. Omit it to keep your current data.

Check the backend:
- http://localhost:8000/health returns `{"status":"ok"}`.
- Swagger UI is at http://localhost:8000/docs.

### 6.5 Frontend

In a new terminal:

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev                          # http://localhost:3000
```

Quick Reorder needs `NEXT_PUBLIC_DEMO_USER_ID` in `.env.local`: the UUID of a seeded customer. To find one:

```bash
docker exec freshloop-postgres psql -U freshloop_user -d freshloop_db \
  -c "SELECT user_id, email FROM users WHERE role = 'CUSTOMER' LIMIT 3;"
```

### 6.6 Recommender (optional, standalone)

Run from the repository root:

```bash
pip install -r recommender/requirements.txt
python -m recommender.demo           # Top-10 for several users + cache MISS/HIT demo
python -m recommender.evaluate       # Precision@10 / Recall@10 → recommender/sample_output/offline_evaluation.csv
```

### 6.7 Try the real-time flow

1. Open http://localhost:3000. The status line next to the warehouse selector shows *Live stock updates on*.
2. Register an account with `POST /api/auth/register` in Swagger.
3. Promote it to STAFF:
   ```bash
   docker exec freshloop-postgres psql -U freshloop_user -d freshloop_db -c "UPDATE users SET role = 'STAFF' WHERE email = '<email>';"
   ```
4. Log in with `POST /api/auth/login` to get a token.
5. Call `PATCH /api/warehouses/{warehouse_id}/products/{product_id}/stock` with body `{"quantity_delta": -5}` and an `Idempotency-Key` header. The storefront updates the stock within a few seconds.

## 7. Environment Variables

| Variable | File | Required | Description |
| --- | --- | --- | --- |
| `DATABASE_URL` | `.env` | Yes | SQLAlchemy connection string for PostgreSQL |
| `REDIS_URL` | `.env` | No | Defaults to `redis://localhost:6379/0` (recommender) |
| `JWT_SECRET` | `.env` | **Yes** | JWT signing key, at least 32 bytes |
| `CORS_ORIGINS` | `.env` | No | Comma-separated origins; defaults allow `localhost:3000` and `localhost:5173` |
| `REC_MODEL`, `REC_TOP_K`, `REC_CACHE_TTL_SECONDS`, `REC_HALF_LIFE_DAYS` | `.env` | No | Recommender settings |
| `NEXT_PUBLIC_API_BASE_URL` | `frontend/.env.local` | No | Defaults to `http://localhost:8000` |
| `NEXT_PUBLIC_DEMO_USER_ID` | `frontend/.env.local` | No | Customer UUID used for Quick Reorder |

Default connection details for local development are in `docker-compose.yml`. **Never commit `.env` or `.env.local`.**

## 8. Testing

```bash
# Frontend
cd frontend && npm test && npx eslint . && npm run build

# Backend (unit tests; integration tests need TEST_DATABASE_URL pointing at a database named freshloop_test_db)
cd backend && pip install pytest && python -m pytest tests -v

# Database constraints and concurrency (needs a migrated and seeded database)
PYTHONPATH=backend python -m unittest database.tests.test_integrity_constraints -v

# Recommender
python -m pytest recommender/tests -v
```

How to set up the separate test database, and the latest results, are in [FINAL_TESTING_CHECKLIST.md](docs/project-management/FINAL_TESTING_CHECKLIST.md).

## 9. Core API

| Method | Endpoint | Description | Status |
| --- | --- | --- | --- |
| GET | `/health` | Health check | ✅ |
| POST | `/api/auth/register` | Customer registration | ✅ |
| POST | `/api/auth/login` | Login, returns a JWT | ✅ |
| GET | `/api/products`, `/api/products/{id}` | Product list and detail | ✅ |
| GET | `/api/warehouses` | Active warehouses | ✅ |
| GET | `/api/warehouses/{id}/products` | Products and stock for one warehouse | ✅ |
| PATCH | `/api/warehouses/{id}/products/{product_id}/stock` | Stock update (STAFF/ADMIN, `Idempotency-Key`) | ✅ |
| GET | `/api/warehouses/{id}/inventory/events` | SSE stream of stock changes | ✅ |
| POST / GET | `/api/orders`, `/api/orders/{id}` | Place and view orders | ⏳ Proposed |
| GET | `/api/recommendations/{user_id}?warehouse_id=` | Quick Reorder Top-10 | ⏳ Proposed |

Request and response details are in [frontend/docs/api-contract.md](frontend/docs/api-contract.md) and in Swagger at `/docs`.

## 10. Current Status and Limitations

Estimated completion is about **62%** (assessed on 3 Nov 2026; see [PROJECT_PROGRESS.md](docs/project-management/PROJECT_PROGRESS.md)). Main limitations:

- The order and recommendation APIs do not exist yet, so checkout and Quick Reorder are not complete in the UI.
- Seeded accounts have placeholder `password_hash` values and **cannot log in**. Register a new account instead (see section 6.7).
- SSE currently polls database snapshots (every 2 seconds by default); Redis Pub/Sub is not used yet.
- Staff can update stock in any warehouse; the `staff_warehouse_assignments` restriction is not enforced yet.
- No login UI, admin dashboard or online payment yet.
- Not deployed; the targets in section 3 have not been measured.

## 11. Changes from the Proposal

The proposal (4 Oct 2026) was the initial design. During implementation the team made these adjustments:

| Proposal | Current implementation | Reason / note |
| --- | --- | --- |
| Versioned endpoints `/api/v1/...` (`storefront`, `predicted-cart`, `cart/items`) | Resource-based `/api/...`: `products`, `warehouses`, `orders`, `recommendations` | Follows the existing FastAPI routers |
| SSE at `/api/v1/stream/inventory`, fed by Redis Pub/Sub | Per-warehouse SSE at `/api/warehouses/{id}/inventory/events`, using periodic DB snapshot comparison | Interim MVP approach (Week 3 Task Assignment) |
| Server-side cart (`POST /api/v1/cart/items`) | Client-side cart (`sessionStorage`) | Simpler MVP |
| Stripe payments (test mode) | Not integrated | Deferred to P2 |
| POS webhook for stock updates | Authenticated, idempotent staff stock `PATCH` | Simulates a warehouse operator's action |
| Cache key `predicted_cart:{user_id}` as a Hash, 24 h TTL | `freshloop:rec:v2:user:{user_id}:model:{model}:k:{top_k}`, configurable TTL (default 3600 s) | See `recommender/cache.py` |
| ALS as the main model, blended with the baseline | Frequency × recency baseline is the default (`REC_MODEL=baseline`); ALS can be selected via `REC_MODEL` | Weeks 2–3: baseline first, ALS must not block progress |
| 7 tables | 9 tables: added `idempotency_records` and `staff_warehouse_assignments` | Support idempotency and per-warehouse permissions |
| CI/CD with GitHub Actions, Docker images | Not set up | Still planned |
| Hiếu: Frontend Engineer | Hiếu: Full-Stack Developer from Week 3 | Lets the team lead control end-to-end integration |

## 12. Team

| Member | Current role | Role in proposal |
| --- | --- | --- |
| Nguyễn Vũ Hiếu | Team Leader / Integration Architect / Full-Stack Developer (from Week 3) | Project Lead / Integration Architect / Frontend Engineer |
| Mai Danh Tiến | Backend Engineer | Backend Engineer |
| Trần Hữu Thắng | Data Engineer / Database Engineer | Data Engineer / Database Engineer |
| Ngô Hồng Ân | ML / Cache / Real-Time Engineer | ML / Cache / Real-Time Engineer |

## 13. Related Documents

- Modules: [frontend/README.md](frontend/README.md) · [database/README.md](database/README.md) · [recommender/README.md](recommender/README.md)
- API: [frontend/docs/api-contract.md](frontend/docs/api-contract.md)
- Project management (Vietnamese): [WBS](docs/project-management/WBS_FreshLoop.md) · [Progress](docs/project-management/PROJECT_PROGRESS.md) · [Testing checklist](docs/project-management/FINAL_TESTING_CHECKLIST.md)
- Sprint plans: [Week 1](FreshLoop_Week1_Task_Assignment.md) · [Week 2](FreshLoop_Week2_Task_Assignment.md) · [Week 3](FreshLoop_Week3_Task_Assignment.md)
- Collaboration rules: [RULE.md](RULE.md)
