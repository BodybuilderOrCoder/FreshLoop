**FRESHLOOP**

**Week 1 Task Assignment & Expected Deliverables**

# 1. Project Overview

**Project:** FreshLoop — Real-Time Predictive Inventory Grocery Platform

**Team size:** 4 members

### Project architecture

- Frontend: Next.js, React, TypeScript, Tailwind CSS

- Backend: Python, FastAPI, SQLAlchemy

- Database: PostgreSQL 16, Alembic

- Cache: Redis

- Recommendation: Python, Pandas, initial recommendation baseline; ALS considered after data preparation

- Real-time communication: Server-Sent Events (SSE)

- Version control: Git and GitHub

### Week 1 Main Objective

Establish a stable development foundation in which all four members can work independently while following a shared architecture and integration contract.

By the end of Week 1, the team should demonstrate:

1.  A functional Next.js frontend using mock data.

2.  A FastAPI backend exposing basic endpoints.

3.  A PostgreSQL database with working migrations and sample data.

4.  A basic recommendation module that produces testable outputs.

5.  A documented integration contract between frontend, backend, database, and recommendation components.

6.  Source code organized in a shared Git repository, with tested changes integrated into dev.

## 2. Member 1 — Hiếu

**Role:** Team Leader & Frontend Developer

**Primary responsibility:** Develop the customer-facing interface and coordinate integration requirements.

### Task 1.1 — Frontend Environment

- Verify the existing Next.js project.

- Confirm TypeScript and Tailwind CSS configuration.

- Organize frontend directories for components, pages, mock data, services, and types.

- Set up environment variables for the backend API URL.

- Ensure the application runs locally without errors.

**Expected output:**

- Working Next.js development environment.

- Clear frontend directory structure.

- npm run dev runs successfully.

- No unnecessary changes to backend or database files.

### Task 1.2 — Design System

Establish consistent UI standards for FreshLoop.

**Design direction:** Smart Grocery Tech — White + Fresh Green.

Define:

- Primary color: \#16A34A

- Dark green: \#14532D

- Light green: \#DCFCE7

- Main text: \#111827

- Typography, spacing, border radius, and button styles

- Responsive behavior for desktop and mobile

Create reusable components such as:

- Header / Navigation

- Button

- ProductCard

- SearchBar

- CategoryFilter

- CartDrawer

- StockBadge

**Expected output:**

- Consistent UI design system.

- Reusable React components.

- Responsive layouts.

- No duplicated UI logic where reusable components are appropriate.

**Branding note:** The Smart Basket logo has been selected, but final integration will occur after the complete UI feature set is reviewed. Remove the previous reload-style symbol and decorative ✦ icons during final UI cleanup.

### Task 1.3 — Customer Homepage

Develop a working homepage containing:

- Navigation and search

- Hero section

- Product categories

- Product listing

- Product filtering

- Product sorting

- Quick Reorder preview

- Shopping cart drawer

Use mock data until backend endpoints are ready.

**Expected output:**

- Interactive homepage accessible at localhost:3000.

- Search and category filters work.

- Products can be added to the cart.

- Cart quantity and total price update correctly.

- Quick Reorder preview displays recommendation mock data.

- Layout works on desktop and mobile.

### Task 1.4 — Frontend Integration Preparation

- Define TypeScript interfaces for products, inventory, cart items, and recommendations.

- Prepare a centralized API service layer.

- Separate mock data from UI components.

- Document the expected API response formats.

- Coordinate with Tiến on endpoint names and JSON schemas.

**Expected output:**

- Shared TypeScript types.

- API integration plan.

- Mock data that follows the agreed backend response structure.

- Frontend ready for subsequent API integration without major UI rewrites.

### Task 1.5 — Team Coordination

As team leader:

- Review commits and coordinate integration on dev.

- Confirm responsibilities and dependencies.

- Track blockers.

- Organize the Week 1 review meeting.

- Ensure changes are integrated into dev rather than directly into main.

**Expected output:**

- Updated task board.

- Weekly progress summary.

- Integration issues documented.

- Working frontend demonstration.

**Week 1 completion criteria:** The customer homepage is interactive and responsive, with documented data contracts and clean frontend code integrated into dev.

## 3. Member 2 — Tiến

**Role:** Backend Developer

**Primary responsibility:** Build the FastAPI application and establish reliable database-backed endpoints.

### Task 2.1 — Backend Application Structure

- Verify the existing FastAPI project.

- Organize API routes, schemas, services, and dependencies.

- Configure environment variables.

- Add basic application error handling.

- Enable CORS for the local frontend origin.

**Expected output:**

- Working FastAPI application.

- Swagger documentation available at /docs.

- Health-check endpoint returning a valid response.

- Clear separation of API, service, and database responsibilities.

### Task 2.2 — Product APIs

Implement initial read-only endpoints:

- GET /api/v1/products

- GET /api/v1/products/{product_id}

- GET /api/v1/categories (derived from available category data or agreed schema)

Product listing should support basic query parameters for search, filtering, sorting, and pagination where practical.

**Expected output:**

- Product endpoints return valid JSON.

- Data is retrieved from PostgreSQL.

- Missing products return appropriate HTTP errors.

- Request and response formats are documented.

### Task 2.3 — Inventory Read API

Implement:

- GET /api/v1/inventory/{product_id}

The endpoint should expose inventory information according to the agreed warehouse/stock schema.

**Expected output:**

- Inventory data can be retrieved from the database.

- Invalid product IDs are handled.

- Stock information is consistent with the underlying database.

### Task 2.4 — API Testing and Documentation

- Add basic endpoint tests.

- Test successful and unsuccessful requests.

- Verify database connectivity.

- Document required environment variables.

- Provide sample JSON responses for frontend integration.

**Expected output:**

- Runnable backend tests.

- Working Swagger documentation.

- API response examples shared with Hiếu.

- Backend startup instructions.

**Week 1 completion criteria:** FastAPI starts successfully, connects to PostgreSQL, and serves tested product and inventory read endpoints.

**Out of scope for Week 1:** Complete authentication, production payment processing, full order lifecycle, and production-grade SSE infrastructure.

## 4. Member 3 — Thắng

**Role:** Database Developer

**Primary responsibility:** Validate the database schema, migrations, seed data, and data integrity.

**Current status:** An initial database setup has already been merged into dev. Week 1 work should continue from that implementation rather than rebuilding it.

### Task 3.1 — Schema Review

Review existing SQLAlchemy models for:

- Users

- Products

- Warehouses

- Inventory levels

- Orders

- Order items

- Purchase history

Check:

- Primary keys

- Foreign keys

- Unique constraints

- Data types

- Inventory quantity constraints

- Relationship definitions

**Expected output:**

- Reviewed and corrected SQLAlchemy models.

- Documented table relationships.

- Schema ready for backend integration.

### Task 3.2 — Alembic Migration Verification

- Inspect the existing initial migration.

- Ensure migration upgrade() actually creates the required tables.

- Ensure downgrade() correctly reverses the migration.

- Test migrations on a fresh PostgreSQL database.

- Do not rely on Base.metadata.create_all() in the seed script as a substitute for migrations.

**Expected output:**

- Working initial migration.

- Successful alembic upgrade head.

- Verification that all seven required tables exist.

- Migration test evidence.

### Task 3.3 — Sample Data Preparation

Prepare sufficient development data for frontend/backend testing.

**Proposed initial targets:**

- 50 users

- 200 products

- 3 warehouses

- Inventory records for stocked products across warehouses

- Sample orders and order items

- Purchase history records suitable for testing recommendation interfaces

Use synthetic data or clearly licensed public datasets.

**Expected output:**

- Reproducible seed script.

- Realistic development data.

- Valid foreign-key relationships.

- No duplicate or inconsistent records caused by repeated seeding.

### Task 3.4 — Data Integrity and Database Documentation

- Test insert and query operations.

- Verify referential integrity.

- Document database startup and migration steps.

- Move credentials to environment-based configuration.

- Share schema details with Tiến and Ân.

**Expected output:**

- Database setup instructions.

- ER diagram or equivalent schema documentation.

- Tested database initialization process.

- Confirmed data availability for backend and recommendation development.

**Week 1 completion criteria:** A fresh development environment can initialize PostgreSQL, apply migrations, load sample data, and execute basic queries successfully.

## 5. Member 4 — Ân

**Role:** Recommendation & Cache Developer

**Primary responsibility:** Prepare the recommendation pipeline and establish a minimal Redis integration.

### Task 4.1 — Recommendation Data Preparation

- Review the purchase-history schema.

- Define required fields for recommendation training.

- Prepare a script to transform purchase history into user-product interaction data.

- Check missing values, duplicates, and invalid records.

- Coordinate with Thắng on data availability.

**Expected output:**

- Data preprocessing script.

- Clean interaction dataset.

- Documentation of required input columns.

- Sample transformed output.

### Task 4.2 — Initial Recommendation Baseline

Implement a simple recommendation baseline using purchase frequency and/or recency.

ALS can be explored if the dataset is sufficiently large and suitable, but it should not block the initial baseline.

Suggested interface: recommend(user_id, top_k=10)

**Expected output:**

- Python recommendation module.

- Function accepting a user ID.

- Top-10 product recommendation output.

- Reproducible test with sample data.

### Task 4.3 — Redis Setup

- Configure Redis for local development.

- Establish a basic Python Redis connection.

- Define a cache-key convention for recommendations.

- Implement basic read/write operations.

- Add a configurable time-to-live (TTL).

**Expected output:**

- Working Redis connection.

- Demonstrated cache hit and cache miss.

- Recommendation results can be cached and retrieved.

- Environment-based Redis configuration.

### Task 4.4 — Recommendation Testing

- Test users with purchase history.

- Test users without purchase history.

- Define fallback recommendations for cold-start users.

- Document the planned offline evaluation method for Precision@10.

**Expected output:**

- Basic recommendation tests.

- Example outputs for multiple users.

- Documented fallback strategy.

- Evaluation plan for future weeks.

**Week 1 completion criteria:** A recommendation baseline returns Top-10 results from sample data, and Redis can cache those results successfully.

**Out of scope for Week 1:** Guaranteed 65% Precision@10, production model serving, and advanced collaborative filtering optimization.

# 6. Git Workflow

All team members will collaborate using a shared GitHub repository and two permanent branches.

**Branch Structure:**

- **main:** Stable project branch used for tested releases and final demonstrations.

- **dev:** Shared development and integration branch where all four members commit and push their work.

**Development Rules:**

1.  All members must clone the existing FreshLoop repository and switch to the dev branch before starting development.

2.  Members work directly on dev without creating additional feature branches.

3.  Each member should primarily modify files within their assigned responsibility:

    - Hiếu: frontend/

    - Tiến: backend/

    - Thắng: database/ and existing database-related files

    - Ân: recommender/ and assigned Redis integration files

4.  Always check git status and pull the latest changes from dev before starting work.

5.  Use descriptive commit messages and stage only relevant files.

6.  Before pushing, synchronize with the latest remote dev and resolve any conflicts.

7.  Do not push unfinished or untested changes directly to main.

8.  Coordinate with other members before modifying shared files, API contracts, database models, or configuration files.

9.  Never commit passwords, API keys, .env files, or other sensitive credentials.

10. Do not force-push to shared branches. Changes from dev should be merged into main only after team review and successful testing.

**Integration Policy:**

The dev branch serves as the team's shared integration environment. Each member is responsible for testing their changes before pushing. The team leader coordinates integration issues and reviews the stability of dev before promoting changes to main.

# 7. Integration Dependencies

| **Dependency**                  | **Responsible members** | **Agreement required**                         |
|---------------------------------|-------------------------|------------------------------------------------|
| Product JSON schema             | Hiếu + Tiến             | Fields, IDs, pricing, images, categories       |
| Database models and API queries | Thắng + Tiến            | Relationships and column names                 |
| Purchase-history format         | Thắng + Ân              | User-product interactions                      |
| Recommendation response         | Ân + Hiếu + Tiến        | Top-10 SKU/product format                      |
| Redis connection and caching    | Ân + Tiến               | Cache keys, TTL, invalidation responsibilities |

Members should agree on these contracts early rather than waiting until the end of the week.

# 8. Week 1 Expected Final Deliverables

| **Member** | **Main deliverable**                    | **Demonstration**                            |
|------------|-----------------------------------------|----------------------------------------------|
| Hiếu       | Interactive Next.js homepage            | Search, filters, cart, Quick Reorder preview |
| Tiến       | FastAPI product/inventory endpoints     | Swagger and successful API requests          |
| Thắng      | Working PostgreSQL schema and seed data | Fresh migration, seeding, SQL queries        |
| Ân         | Recommendation baseline and Redis cache | Top-10 output, cache hit/miss                |

### Definition of Done

A task is considered complete only when:

- Its source code is committed.

- The relevant functionality runs successfully.

- Required tests or manual verification are completed.

- Setup instructions are provided.

- Known limitations are documented.

- The changes are tested, reviewed, and successfully pushed to dev.

# 9. Week 1 Review Meeting Agenda

Each member should prepare a 5–10 minute demonstration.

- **Hiếu:** Demonstrate the customer homepage and explain the frontend component structure.

- **Tiến:** Start the API and demonstrate database-backed requests through Swagger.

- **Thắng:** Demonstrate database initialization, migrations, and seeded data.

- **Ân:** Run the recommendation script and show Redis caching.

The meeting should conclude with:

- Completed and incomplete task review.

- Technical blockers.

- Integration contract confirmation.

- Commit and integration review.

- Week 2 priorities.

**Final Week 1 success condition:** The team has four independently testable components, documented interfaces, and a clear path to integration. Full end-to-end production functionality is not required yet.

**NOTE:** Each member must be able to explain the implementation, demonstrate its functionality, and independently debug at least one relevant issue. AI-generated code must be reviewed and understood before being pushed to dev.
