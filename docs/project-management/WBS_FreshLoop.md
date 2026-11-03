# FreshLoop — Work Breakdown Structure (WBS)

> **Retrospective WBS:** tài liệu này được tái cấu trúc **trong giai đoạn triển khai**, không phải kế hoạch lập từ đầu dự án. Trạng thái và tiến độ dựa trên bằng chứng trong repository và các lần kiểm thử thực hiện ngày 03/11/2026. Ngày lập kế hoạch ban đầu, người phụ trách và ngày hoàn thành **không** được suy diễn khi không có bằng chứng.

## 1. Thông tin dự án và baseline audit

| Mục | Giá trị |
| --- | --- |
| Dự án | FreshLoop — Real-Time Predictive Inventory Grocery Platform |
| Học phần | IT for E-commerce (HK1-2026) |
| Kiến trúc | Modular monolith: Next.js (frontend), FastAPI (backend), PostgreSQL 16 + Alembic, Redis, SSE |
| Nhánh audit | `dev` (integration baseline) |
| HEAD audit | `d31fd29` — `feat(frontend): complete Week 2 customer journey and API contract` |
| Đồng bộ remote | `dev` trùng `origin/dev` tại thời điểm audit |
| Lịch sử Git | 62 commit, từ 17/10/2026 (`858c902`) đến 03/11/2026 |
| Ngày audit | 03/11/2026 (đang trong Sprint Week 3: 02–08/11/2026) |
| Thay đổi local không thuộc audit | `frontend/AGENTS.md` bị `next dev` tự thêm khối hướng dẫn; không được tính vào bằng chứng |

### 1.1 Nguồn bằng chứng

| Nguồn | Có trong repo | Ghi chú |
| --- | --- | --- |
| `README.md`, `RULE.md` | Có | `RULE.md` là quy tắc cộng tác, không phải danh sách task |
| `FreshLoop_Week1/2/3_Task_Assignment.md` | Có | Kế hoạch đề xuất, không phải xác nhận hoàn thành |
| Research Proposal (04/10/2026) | **Không** | Chỉ được trích dẫn gián tiếp trong Week 2/3 Task Assignment. Các KPI gốc lấy từ đề bài audit |
| `backend/TASK_DECOMPOSITION_M5.md` | Có | Phân rã task SSE |
| `database/README.md`, `database/docs/*` | Có | Có sai lệch với code (mục 7) |
| `recommender/README.md`, `recommender/docs/*` | Có | README còn ghi "Week 1", một phần đã lỗi thời |
| `frontend/README.md`, `frontend/docs/api-contract.md` | Có | Contract cho orders/recommendations ở trạng thái *Proposed* |
| Kết quả chạy test và E2E ngày 03/11/2026 | Ngoài repo | Ghi lại trong `FINAL_TESTING_CHECKLIST.md` |

### 1.2 Thang trạng thái

| Trạng thái | Ý nghĩa |
| --- | --- |
| **COMPLETED** | Đã triển khai và có bằng chứng đủ cho tiêu chí chấp nhận (test chạy, artifact hoặc kiểm tra thủ công có ghi nhận) |
| **IN PROGRESS** | Triển khai một phần, hoặc đã có code nhưng thiếu kiểm thử hay tài liệu theo tiêu chí |
| **PENDING** | Chưa triển khai |
| **BLOCKED** | Phần của work package đã xong nhưng không thể hoàn tất vì phụ thuộc chưa có |
| **NOT VERIFIED** | Không đủ bằng chứng để kết luận; không gán % |

Một file, route hay model tồn tại **không** đồng nghĩa với việc tính năng đã hoàn thành.

## 2. Cấu trúc phân cấp WBS

```text
FreshLoop
├── 1.0 Project Management & Planning
│   ├── 1.1 Task assignment theo sprint (Week 1–3)
│   ├── 1.2 Quy tắc cộng tác & Git workflow
│   ├── 1.3 Theo dõi tiến độ (task board, progress log)
│   └── 1.4 Hợp đồng tích hợp (API/SSE contract)
├── 2.0 System Architecture & Infrastructure
│   ├── 2.1 Cấu trúc repository (modular monolith)
│   ├── 2.2 Hạ tầng local (Docker Compose: PostgreSQL, Redis)
│   ├── 2.3 Cấu hình môi trường (.env.example)
│   └── 2.4 Tài liệu kiến trúc & data flow
├── 3.0 Database & Data Management
│   ├── 3.1 Schema & SQLAlchemy models
│   ├── 3.2 Alembic migrations
│   ├── 3.3 Seed data tái lập
│   ├── 3.4 Integrity & concurrency tests (DB level)
│   ├── 3.5 ML data pipeline & chronological split
│   └── 3.6 Tài liệu DB & bằng chứng hiệu năng SQL
├── 4.0 Backend API & Business Logic
│   ├── 4.1 Nền tảng ứng dụng FastAPI
│   ├── 4.2 Product API
│   ├── 4.3 Inventory read API
│   ├── 4.4 Protected stock update & idempotency
│   ├── 4.5 Order Management
│   │   ├── 4.5.1 Order creation
│   │   ├── 4.5.2 Inventory reservation trong transaction
│   │   ├── 4.5.3 Order retrieval
│   │   ├── 4.5.4 Order confirmation & status transitions
│   │   ├── 4.5.5 Order cancellation & stock release
│   │   └── 4.5.6 COD payment lifecycle
│   ├── 4.6 Recommendation API (tích hợp recommender)
│   └── 4.7 Cart API (server-side)
├── 5.0 Frontend Application
│   ├── 5.1 Design system & reusable components
│   ├── 5.2 Homepage, tìm kiếm, lọc, sắp xếp
│   ├── 5.3 Chọn kho & catalog từ API
│   ├── 5.4 Giỏ hàng (client-side)
│   ├── 5.5 Trang chi tiết sản phẩm
│   ├── 5.6 Checkout UI & trang trạng thái đơn
│   ├── 5.7 Quick Reorder UI
│   ├── 5.8 Live stock UI (SSE client)
│   ├── 5.9 Favorites, ngôn ngữ/theme
│   ├── 5.10 Đăng nhập/đăng ký UI
│   └── 5.11 Admin/operator dashboard
├── 6.0 Predictive Inventory & Quick Reorder
│   ├── 6.1 Tiền xử lý interaction
│   ├── 6.2 Baseline frequency × recency + popularity fallback
│   ├── 6.3 ALS collaborative filtering
│   ├── 6.4 Redis cache-aside (key, TTL, HIT/MISS, degradation)
│   ├── 6.5 Lọc hết hàng & cache invalidation
│   ├── 6.6 Offline evaluation (Precision@10, Recall@10)
│   └── 6.7 Quick Reorder latency end-to-end (p95)
├── 7.0 Real-Time Communication
│   ├── 7.1 SSE endpoint (snapshot polling)
│   ├── 7.2 Event-driven delivery (Redis Pub/Sub)
│   ├── 7.3 Đo độ trễ lan truyền (staleness ≤ 5 s)
│   └── 7.4 Reconnect, disconnect & warehouse isolation
├── 8.0 Security & Access Control
│   ├── 8.1 Đăng ký & băm mật khẩu (Argon2)
│   ├── 8.2 Đăng nhập JWT
│   ├── 8.3 Role-based authorization cho stock mutation
│   ├── 8.4 Phân quyền staff theo kho
│   ├── 8.5 Quyền sở hữu đơn hàng
│   ├── 8.6 Quản lý secrets
│   └── 8.7 CORS & an toàn thông báo lỗi
├── 9.0 Testing & Quality Assurance
│   ├── 9.1 Frontend unit tests
│   ├── 9.2 Backend unit tests
│   ├── 9.3 Backend PostgreSQL integration tests
│   ├── 9.4 Recommender tests
│   ├── 9.5 End-to-end checkout test
│   └── 9.6 Load/performance test (500 sessions)
├── 10.0 Deployment & Monitoring
│   ├── 10.1 Frontend deployment (Vercel)
│   ├── 10.2 Backend + PostgreSQL + Redis deployment (Railway)
│   └── 10.3 Monitoring, logging & availability
└── 11.0 Documentation & Final Presentation
    ├── 11.1 README theo module
    ├── 11.2 Tài liệu API (Swagger + contract)
    ├── 11.3 Báo cáo cuối kỳ
    └── 11.4 Demo script & slide thuyết trình
```

Ghi chú về 100% Rule:
- Kiểm thử integrity của DB nằm ở 3.4, không lặp lại trong 9.0.
- Phần client SSE nằm ở 5.8, không lặp lại trong 7.0.
- Việc tích hợp recommender vào FastAPI nằm ở 4.6, không lặp lại trong 6.0.

## 3. Work Package Register

Cột **W** là trọng số dùng để ước lượng tiến độ tổng thể (xem `PROJECT_PROGRESS.md`, mục 2).

### 3.1 — 1.0 Project Management & Planning

| WBS ID | Work Package | Mô tả / Output | W | Trạng thái | % | Bằng chứng | Phụ thuộc | Tiêu chí chấp nhận |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1.1 | Task assignment theo sprint | Phân công, deliverable và DoD cho Week 1–3 | 2 | COMPLETED | 100 | `FreshLoop_Week1/2/3_Task_Assignment.md` (`1bd4ab2`, `ce6e7a3`) | — | Có kế hoạch cho từng sprint, có tiêu chí chấp nhận |
| 1.2 | Quy tắc cộng tác & Git workflow | Quy tắc nhánh `main`/`dev`, commit, an toàn | 1 | COMPLETED | 100 | `RULE.md` (`de94a0e`) | — | Quy tắc được commit lên `dev` |
| 1.3 | Theo dõi tiến độ | Task board, sprint progress log, biên bản review | 1 | NOT VERIFIED | — | Không có trong repo; có thể nằm ở công cụ khác | 1.1 | Có task board hoặc log tiến độ truy vết được |
| 1.4 | Hợp đồng tích hợp | Contract API/SSE được các bên xác nhận | 1 | IN PROGRESS | 60 | `frontend/docs/api-contract.md` (`d31fd29`): endpoint hiện có đã ghi; orders và recommendations còn *Proposed* | 4.5, 4.6 | Contract orders, recommendations và SSE được các bên liên quan xác nhận và đóng băng |

### 3.2 — 2.0 System Architecture & Infrastructure

| WBS ID | Work Package | Mô tả / Output | W | Trạng thái | % | Bằng chứng | Phụ thuộc | Tiêu chí chấp nhận |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2.1 | Cấu trúc repository | Tách `frontend/`, `backend/`, `database/`, `recommender/` | 1 | COMPLETED | 100 | `git ls-files`; `5ab5f82` | — | Mỗi module có thư mục, cấu hình và test riêng |
| 2.2 | Hạ tầng local | PostgreSQL 16 và Redis 7 qua Docker Compose | 2 | COMPLETED | 100 | `docker-compose.yml`; container `freshloop-postgres`, `freshloop-redis` chạy ngày 03/11/2026 | — | `docker compose up -d` khởi động được DB và cache |
| 2.3 | Cấu hình môi trường | `.env.example` cho mọi module; không hard-code secrets | 1 | IN PROGRESS | 70 | `.env.example` (gốc: `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`), `frontend/.env.example`. Mật khẩu DB vẫn hard-code trong `backend/alembic.ini`, `docker-compose.yml`, `backend/app/database.py` (giá trị mặc định), `README.md` | 8.6 | Mọi module đọc cấu hình từ env; không còn credentials trong file được commit |
| 2.4 | Tài liệu kiến trúc & data flow | Sơ đồ kiến trúc, deployment và data flow cho báo cáo | 2 | IN PROGRESS | 30 | Chỉ có ERD (Mermaid) trong `database/README.md` và mô tả SSE trong `backend/TASK_DECOMPOSITION_M5.md` | 10.x | Có sơ đồ kiến trúc tổng thể, data flow và deployment |

### 3.3 — 3.0 Database & Data Management

| WBS ID | Work Package | Mô tả / Output | W | Trạng thái | % | Bằng chứng | Phụ thuộc | Tiêu chí chấp nhận |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3.1 | Schema & models | 9 bảng: users, products, warehouses, inventory_levels, orders, order_items, purchase_history, idempotency_records, staff_warehouse_assignments | 3 | COMPLETED | 100 | `backend/app/models/schema.py`; ràng buộc `chk_reserved_le_quantity`, `chk_order_status` | — | PK, FK, UNIQUE, CHECK được định nghĩa và kiểm thử |
| 3.2 | Alembic migrations | 3 revision: `3305bfd1be66` → `948e2297107f` → `b22df6a0d648` | 2 | COMPLETED | 100 | `upgrade head` thành công trên DB sạch `freshloop_test_db` và DB dev; `downgrade` `b22df6a0d648` → `948e2297107f` thành công (03/11/2026) | 3.1 | `upgrade head` và `downgrade` chạy được trên DB sạch |
| 3.3 | Seed data tái lập | 50 users, 200 products, 3 kho, 600 dòng tồn kho, đơn hàng lịch sử; UUIDv5 cố định | 2 | IN PROGRESS | 80 | `backend/seed_mock_data.py` (`25b95b0`, `ccae168`); seed `--clean` trên DB test thành công. **Lỗi:** `password_hash` của mọi user seed là chuỗi giả (`pbkdf2:sha256:staff_secret_hash`), nên không đăng nhập được | 8.1 | Seed chạy lặp lại được, và tài khoản demo đăng nhập được |
| 3.4 | Integrity & concurrency tests | Test CHECK, UNIQUE, FK, `FOR UPDATE`, rollback, release | 2 | COMPLETED | 100 | `database/tests/test_integrity_constraints.py`: 13/13 pass ngày 03/11/2026 | 3.1, 3.2 | Mọi test pass trên DB sạch |
| 3.5 | ML data pipeline & split | Trích interaction, split theo thời gian ở mức order, kiểm tra leakage | 2 | IN PROGRESS | 90 | `database/pipeline/extract_interactions.py` (invariant chống leakage); `database/data/train_interactions.csv` (1.379 cặp), `test_ground_truth.csv` (517 dòng) (`c38e5dd`). Audit không chạy lại pipeline | 3.3 | Pipeline chạy lại trên seed mới cho cùng artifact; có log row count |
| 3.6 | Tài liệu DB & bằng chứng SQL | Data dictionary, ERD, migration log, EXPLAIN ANALYZE | 1 | IN PROGRESS | 60 | `database/docs/data_dictionary.md` chỉ có 7/9 bảng; `migration_log.txt` lưu UTF-16 (GitHub hiển thị như binary); `query_timing_benchmarks.txt` kết luận nhầm SQL time với p95 HTTP, và truy vấn SKU thực tế là Seq Scan | 3.1 | Tài liệu khớp schema hiện tại; benchmark ghi đúng phạm vi đo |

### 3.4 — 4.0 Backend API & Business Logic

| WBS ID | Work Package | Mô tả / Output | W | Trạng thái | % | Bằng chứng | Phụ thuộc | Tiêu chí chấp nhận |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4.1 | Nền tảng FastAPI | App, CORS theo env, `/health`, Swagger | 1 | COMPLETED | 100 | `backend/app/main.py` (`9566d98`); `/health` trả `ok` ngày 03/11/2026 | — | App khởi động, `/docs` và `/health` hoạt động |
| 4.2 | Product API | `GET /api/products`, `GET /api/products/{id}` | 2 | IN PROGRESS | 80 | `backend/app/routers/products.py` (`d637609`); E2E: 200 cho ID hợp lệ, 422 cho ID sai. Chưa có test tự động riêng; chưa có `GET /api/categories` và search/filter phía server (yêu cầu Week 1 Task 2.2) | 3.1 | Có test tự động; các query parameter đã thống nhất được hỗ trợ hoặc được chính thức loại khỏi phạm vi |
| 4.3 | Inventory read API | `GET /api/warehouses`, `GET /api/warehouses/{id}/products` (phân trang, `available_stock`) | 2 | COMPLETED | 100 | `backend/app/routers/inventory.py` (`e5339aa`); E2E: 3 kho, 200 sản phẩm của HUB-01 | 3.1 | Trả đúng tồn kho theo kho; kho không tồn tại trả 404 |
| 4.4 | Protected stock update & idempotency | `PATCH /api/warehouses/{w}/products/{p}/stock`, có `Idempotency-Key` | 2 | COMPLETED | 100 | `backend/app/services/inventory_stock.py`, `backend/app/services/idempotency.py` (`4f2affe`); E2E: 401 khi không có token, 200 khi là staff, replay không trừ lại, 409 khi thấp hơn `reserved_quantity` | 8.2, 8.3 | Cập nhật an toàn, idempotent và có test concurrency |
| 4.5.1 | Order creation | `POST /api/orders`: tạo order và order_items, server tính tổng | 3 | PENDING | 0 | Không có router orders trong `backend/app/routers/`; `POST /api/orders` trả 404 (03/11/2026) | 1.4, 3.1 | Đơn được lưu atomically; 400/401/404/409/422 được xử lý |
| 4.5.2 | Inventory reservation | Reserve/deduct trong cùng transaction với tạo đơn | 2 | IN PROGRESS | 30 | Đặc tả `database/docs/inventory_lifecycle_spec.md`; test DB mô phỏng `FOR UPDATE`. Chưa có service ở backend | 4.5.1 | Không oversell dưới đặt hàng đồng thời; có test integration |
| 4.5.3 | Order retrieval | `GET /api/orders/{id}` | 1 | PENDING | 0 | Không có route; frontend đã gọi sẵn | 4.5.1, 8.5 | Trả dữ liệu đơn đã lưu; chặn đọc đơn của người khác |
| 4.5.4 | Confirmation & status transitions | PENDING → CONFIRMED → DELIVERED / CANCELLED | 1 | PENDING | 0 | Chỉ có CHECK constraint `chk_order_status` | 4.5.1 | Chỉ cho phép chuyển trạng thái hợp lệ; có test |
| 4.5.5 | Cancellation & stock release | Huỷ đơn và trả lại `reserved_quantity` | 1 | IN PROGRESS | 20 | Test DB `test_order_cancellation_releases_inventory`; chưa có API | 4.5.2 | API huỷ đơn trả lại tồn kho đúng |
| 4.5.6 | COD payment lifecycle | Trạng thái thanh toán khi giao hàng | 1 | PENDING | 0 | Schema không có trường payment. Quy tắc "COD, chỉ tính DELIVERED" chỉ áp dụng trong seed và pipeline (`c38e5dd`) | 4.5.4 | Mô hình hoá và kiểm thử trạng thái thanh toán COD, hoặc ghi rõ là ngoài phạm vi |
| 4.6 | Recommendation API | `GET /api/recommendations/{user_id}?warehouse_id=`, gọi `recommender.service` | 3 | PENDING | 0 | `backend/app` không import `recommender`; endpoint trả 404 (03/11/2026) | 6.2, 6.4, 6.5 | Top-10 lọc theo tồn kho; có HIT/MISS và fallback; có test |
| 4.7 | Cart API (server-side) | Cart API theo Week 2 Task 2.1 | 1 | PENDING | 0 | Giỏ hàng hiện chỉ ở client (`frontend/hooks/useCart.ts`) | — | Triển khai, hoặc chính thức quyết định giữ cart ở client-side |

### 3.5 — 5.0 Frontend Application

| WBS ID | Work Package | Mô tả / Output | W | Trạng thái | % | Bằng chứng | Phụ thuộc | Tiêu chí chấp nhận |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5.1 | Design system & components | Header, ProductCard, CartDrawer, QuickReorder; logo Smart Basket | 2 | COMPLETED | 100 | `frontend/components/*`, `frontend/styles/*`, `public/freshloop-logo.png` (`b505d14`, `d31fd29`) | — | Component tái sử dụng; đã bỏ ký hiệu trang trí cũ |
| 5.2 | Homepage, tìm kiếm, lọc, sắp xếp | Catalog có lọc theo category, còn hàng, favorites | 2 | COMPLETED | 100 | `frontend/app/page.tsx`; `tests/catalog-logic.test.mjs`; trang `/` trả 200 | 5.3 | Lọc, tìm và sắp xếp hoạt động; có test logic |
| 5.3 | Chọn kho & catalog từ API | Lấy tồn kho theo kho, phân trang, chống race condition | 2 | COMPLETED | 100 | `frontend/hooks/useCatalog.ts`, `lib/catalog-logic.ts` (`1c77730`, `86d59fd`, `78db507`); test pass | 4.3 | Catalog lấy từ PostgreSQL qua FastAPI |
| 5.4 | Giỏ hàng client-side | Giới hạn theo tồn kho, đối soát khi đổi kho, lưu session | 2 | COMPLETED | 100 | `frontend/lib/cart-logic.ts`, `hooks/useCart.ts` (`899ee89`); `tests/cart-logic.test.mjs` | 5.3 | Không vượt tồn kho; tổng tiền đúng |
| 5.5 | Trang chi tiết sản phẩm | Hiện tồn kho theo kho, live update, thêm vào giỏ | 1 | IN PROGRESS | 85 | `frontend/app/product/[productId]/page.tsx` (`d31fd29`); build OK; trang trả 200. Chưa kiểm tra trên trình duyệt | 4.2, 4.3 | Kiểm tra thủ công trên trình duyệt (desktop và mobile) |
| 5.6 | Checkout UI & trang trạng thái đơn | Form checkout, xử lý lỗi 401/403/409/422, trang `/orders/{id}` | 2 | BLOCKED | 70 | `frontend/components/CartDrawer.tsx`, `app/orders/[orderId]/page.tsx`, `lib/api.ts` (`fe1ebc9`, `d31fd29`); có test lỗi API | 4.5.1, 4.5.3 | Checkout thật lưu đơn và hiển thị đơn đã lưu |
| 5.7 | Quick Reorder UI | Hiện Top-10 còn hàng, có fallback | 1 | BLOCKED | 70 | `frontend/components/QuickReorder.tsx`; dùng `NEXT_PUBLIC_DEMO_USER_ID` | 4.6 | Hiển thị gợi ý thật từ API |
| 5.8 | Live stock UI (SSE client) | `EventSource`, refresh khi có event, chỉ báo live/reconnecting | 1 | IN PROGRESS | 85 | `frontend/hooks/useCatalog.ts`; backend SSE đã kiểm chứng bằng curl. Chưa quan sát trên trình duyệt | 7.1 | Tồn kho đổi trên UI không cần reload, có ghi hình làm bằng chứng |
| 5.9 | Favorites, ngôn ngữ/theme | Trang favorites; chuyển ngôn ngữ/theme | 0.5 | IN PROGRESS | 60 | `app/favorites/page.tsx`. Toggle ngôn ngữ/theme có từ `3fe347b`, nhưng code hiện tại cố định `useState("en")`/`useState("light")`, không có nút chuyển | — | Hoặc khôi phục toggle, hoặc loại khỏi phạm vi |
| 5.10 | Đăng nhập/đăng ký UI | Form đăng nhập, lưu token, gửi `Authorization` | 1 | PENDING | 0 | Không có trang auth ở frontend | 8.2 | Người dùng đăng nhập được; token được gửi kèm API |
| 5.11 | Admin/operator dashboard | Màn hình staff điều chỉnh tồn kho | 2 | PENDING | 0 | Không có route admin ở frontend | 4.4, 8.4 | Staff đăng nhập và cập nhật tồn kho qua UI |

### 3.6 — 6.0 Predictive Inventory & Quick Reorder

| WBS ID | Work Package | Mô tả / Output | W | Trạng thái | % | Bằng chứng | Phụ thuộc | Tiêu chí chấp nhận |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6.1 | Tiền xử lý interaction | Làm sạch dữ liệu, tạo ma trận user–product | 1 | COMPLETED | 100 | `recommender/preprocess.py` (`ca1efea`); `sample_output/interactions_sample.csv` | 3.5 | Output đúng cột theo `docs/input_columns.md` |
| 6.2 | Baseline + fallback | Frequency × recency; popularity cho cold-start | 2 | COMPLETED | 100 | `recommender/baseline.py` (`1cdec73`); `docs/fallback.md`; `sample_output/example_recommendations.json` | 6.1 | Top-10 cố định; có fallback cold-start |
| 6.3 | ALS | Mô hình collaborative filtering (P1, tuỳ chọn) | 1 | COMPLETED | 100 | `recommender/als_model.py` (`0c286d5`, `cb48561`) | 6.1 | Huấn luyện và trả Top-K được |
| 6.4 | Redis cache-aside | Key và TTL; HIT/MISS/BYPASS; graceful degradation | 2 | COMPLETED | 100 | `recommender/cache.py`, `service.py` (`9a26588`, `4815019`); `sample_output/cache_latency_benchmark.csv` (đo ở mức hàm, không phải HTTP) | 2.2 | Có HIT/MISS; Redis lỗi không làm hỏng kết quả |
| 6.5 | Lọc hết hàng & invalidation | Loại sản phẩm hết hàng; xoá cache khi tồn kho hoặc đơn hàng đổi | 1 | IN PROGRESS | 50 | Có tham số `exclude_product_ids` và hàm `cache.invalidate()`. Commit lọc theo `warehouse_id` (`a93d538`) đã bị revert (`aa6ad9f`); chưa có nơi gọi `invalidate()` | 4.5.1, 4.6 | Gợi ý không chứa hàng hết; cache bị xoá sau đơn hàng hoặc khi hết hàng |
| 6.6 | Offline evaluation | Precision@10, Recall@10 theo split thời gian | 2 | IN PROGRESS | 60 | `recommender/evaluate.py`; `sample_output/offline_evaluation.csv` (`de963bb`, 26/10/2026, 48 user): frequency_recency P@10 = 0,696; ALS = 0,508; popularity = 0,098. **Tạo trước khi dataset được sinh lại (01–02/11/2026)**; trên dữ liệu tổng hợp | 3.5 | Chạy lại trên dataset hiện tại; ghi seed, ngày dữ liệu, số user; nêu rõ đây là dữ liệu synthetic |
| 6.7 | Latency Quick Reorder end-to-end | p95 HTTP < 150 ms (KPI đề xuất) | 1 | BLOCKED | 0 | Chưa có endpoint để đo | 4.6 | Đo p50/p95 qua HTTP, có sample size và mô tả môi trường |

### 3.7 — 7.0 Real-Time Communication

| WBS ID | Work Package | Mô tả / Output | W | Trạng thái | % | Bằng chứng | Phụ thuộc | Tiêu chí chấp nhận |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7.1 | SSE endpoint | `GET /api/warehouses/{id}/inventory/events`; event `inventory.snapshot`, `inventory.changed`, `inventory.error`; heartbeat | 3 | COMPLETED | 100 | `backend/app/services/inventory_events.py` (`8448d0a`); `tests/test_inventory_sse*.py`; E2E 03/11/2026: staff PATCH −5 sinh `inventory.changed` (112 → 107) | 4.4 | Thay đổi được lưu sinh event cho đúng kho |
| 7.2 | Redis Pub/Sub | Đẩy event theo sự kiện thay vì polling | 1 | PENDING | 0 | Hiện dùng polling snapshot (mặc định 2 s), đã ghi nhận trong Week 3 Task Assignment | 7.1 | Triển khai, hoặc ghi chính thức là giới hạn của MVP |
| 7.3 | Đo độ trễ lan truyền | Staleness ≤ 5 s (KPI đề xuất) | 2 | IN PROGRESS | 40 | `recommender/measure_sse_delay.py` có trong repo nhưng không có kết quả đo được commit | 7.1 | Có mẫu đo độ trễ (≥ 30 lần), p50/p95 và môi trường đo |
| 7.4 | Reconnect & warehouse isolation | Kết nối lại; event không lẫn giữa các kho | 1 | NOT VERIFIED | — | Có test SSE ở backend; audit chưa đối chiếu test với từng kịch bản | 7.1 | Có test hoặc bản ghi chứng minh reconnect và cô lập theo kho |

### 3.8 — 8.0 Security & Access Control

| WBS ID | Work Package | Mô tả / Output | W | Trạng thái | % | Bằng chứng | Phụ thuộc | Tiêu chí chấp nhận |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8.1 | Đăng ký & Argon2 | `POST /api/auth/register`; hash bằng `pwdlib[argon2]` | 1 | COMPLETED | 100 | `backend/app/security/passwords.py` (`92d71cc`, `450cf52`); E2E: 201 | — | Mật khẩu được hash; email/phone trùng trả 409 |
| 8.2 | Đăng nhập JWT | `POST /api/auth/login`; HS256, hết hạn sau 30 phút; `JWT_SECRET` ≥ 32 byte | 1 | COMPLETED | 100 | `backend/app/security/tokens.py` (`35a5a78`); E2E: lấy được access token | 8.1 | Token hợp lệ; sai mật khẩu trả 401 |
| 8.3 | RBAC cho stock mutation | `require_staff_or_admin` | 1 | COMPLETED | 100 | `backend/app/dependencies/auth.py`; `tests/test_auth_dependencies.py`; E2E: không có token trả 401 | 8.2 | Customer bị chặn (403), không có token bị chặn (401) |
| 8.4 | Phân quyền staff theo kho | Staff chỉ sửa được kho được phân công | 1 | PENDING | 10 | Có bảng `staff_warehouse_assignments` (`c38e5dd`), nhưng `update_warehouse_product_stock` không kiểm tra | 8.3, 3.1 | Staff sửa kho không được phân công thì nhận 403 |
| 8.5 | Quyền sở hữu đơn hàng | Customer chỉ đọc được đơn của mình | 1 | BLOCKED | 0 | Chưa có API orders | 4.5.3 | Đọc đơn người khác bị chặn; có test |
| 8.6 | Quản lý secrets | Không có credentials trong repo | 1 | IN PROGRESS | 50 | `JWT_SECRET` bắt buộc qua env (tốt). Mật khẩu DB dev hard-code ở 4 nơi (xem 2.3) | 2.3 | Credentials chỉ có trong `.env` (không commit) |
| 8.7 | CORS & an toàn lỗi | Origin theo env; không lộ lỗi nội bộ ra client | 1 | IN PROGRESS | 50 | `CORS_ORIGINS` theo env; `allow_headers` chưa có `Idempotency-Key` (chặn mutation từ trình duyệt nếu cần header này) | 4.4 | Review bảo mật có ghi nhận kết quả |

### 3.9 — 9.0 Testing & Quality Assurance

| WBS ID | Work Package | Mô tả / Output | W | Trạng thái | % | Bằng chứng | Phụ thuộc | Tiêu chí chấp nhận |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9.1 | Frontend unit tests | API client, cart, catalog, mapper | 1 | COMPLETED | 100 | `npm test`: 35/35 pass; `eslint` sạch; `npm run build` OK (03/11/2026) | — | Toàn bộ pass trên `dev` |
| 9.2 | Backend unit tests | Auth, idempotency, inventory, SSE | 2 | COMPLETED | 100 | `pytest backend/tests`: 96 pass (03/11/2026) | — | Toàn bộ pass |
| 9.3 | Backend PostgreSQL integration tests | Auth, stock update, concurrency trên `freshloop_test_db` | 2 | IN PROGRESS | 70 | 13 test **lỗi ở `head`** vì `EXPECTED_REVISION = "948e2297107f"` được hard-code trong 3 file test. Khi DB test ở revision đó: 13/13 pass. `pytest` không có trong `backend/requirements.txt` | 3.2 | Pass ở `head`; dependency test được khai báo |
| 9.4 | Recommender tests | 27 test (baseline, cache, ALS, evaluate, service) | 1 | NOT VERIFIED | — | `recommender/tests/*`; audit không chạy | — | Có log chạy và toàn bộ pass |
| 9.5 | E2E checkout test | Chọn kho → giỏ hàng → đặt hàng → xem đơn → tồn kho giảm | 2 | BLOCKED | 0 | Phụ thuộc 4.5.1 | 4.5.1, 5.6 | Chạy được và có bản ghi màn hình |
| 9.6 | Load/performance test | 500 phiên đồng thời; availability (KPI 99,5%) | 1 | PENDING | 0 | Không có script load test | 10.2 | Có báo cáo tải, thời lượng, môi trường và kết quả thực đo |

### 3.10 — 10.0 Deployment & Monitoring

| WBS ID | Work Package | Mô tả / Output | W | Trạng thái | % | Bằng chứng | Phụ thuộc | Tiêu chí chấp nhận |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10.1 | Frontend lên Vercel | Deploy frontend và cấu hình env | 2 | PENDING | 0 | Không có cấu hình Vercel hay URL trong repo | 5.x | Có URL chạy được, hoặc ghi lại blocker |
| 10.2 | Backend, DB, Redis lên Railway | Deploy API, PostgreSQL và Redis | 2 | PENDING | 0 | Không có Dockerfile, Procfile hay cấu hình Railway | 4.x, 2.3 | API công khai chạy migration và seed được |
| 10.3 | Monitoring & logging | Log tập trung; health check; theo dõi uptime | 1 | PENDING | 0 | Chỉ có `/health` và logging trong recommender | 10.2 | Có dashboard hoặc log và số liệu uptime thực đo |

### 3.11 — 11.0 Documentation & Final Presentation

| WBS ID | Work Package | Mô tả / Output | W | Trạng thái | % | Bằng chứng | Phụ thuộc | Tiêu chí chấp nhận |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11.1 | README theo module | Hướng dẫn cài đặt, chạy và giới hạn cho từng module | 1 | IN PROGRESS | 60 | Có `frontend/README.md`, `database/README.md`, `recommender/README.md`. Chưa có `backend/README.md`; README recommender còn ghi "Week 1" với giới hạn đã lỗi thời; `README.md` gốc lộ mật khẩu DB | — | Một thành viên mới tự chạy được dự án chỉ từ README |
| 11.2 | Tài liệu API | Swagger và contract cho frontend | 1 | IN PROGRESS | 60 | Swagger tự sinh tại `/docs`; `frontend/docs/api-contract.md` | 1.4 | Contract đóng băng khớp với Swagger |
| 11.3 | Báo cáo cuối kỳ | Báo cáo theo yêu cầu học phần | 2 | NOT VERIFIED | — | Không có trong repo | Tất cả | Nộp đúng hạn; số liệu là số đo thật |
| 11.4 | Demo script & slide | Kịch bản demo và slide thuyết trình | 1 | NOT VERIFIED | — | Không có trong repo | 9.5 | Diễn tập demo thành công |

## 4. WBS Dictionary (các work package trọng yếu)

**4.5.1 Order creation.** Đây là deliverable chặn đường đi P0 của Week 3. Phạm vi: endpoint `POST /api/orders`, mỗi đơn chỉ lấy hàng từ một kho, server tự tính giá từ `products.unit_price`, và lưu `orders`/`order_items` cùng cập nhật `inventory_levels` trong một transaction có row lock. Ngoài phạm vi: thanh toán online và giao hàng theo lịch. Đầu vào: contract trong `frontend/docs/api-contract.md` và đặc tả `database/docs/inventory_lifecycle_spec.md`.

**4.6 Recommendation API.** Lớp transport mỏng ở FastAPI gọi `recommender.service.get_recommendations_with_meta`, truyền danh sách sản phẩm hết hàng của kho được chọn, và trả `items` (`product_id`, `score`) cùng trạng thái cache. Hiện bị chặn bởi quyết định nguồn interaction (CSV snapshot hay đọc DB) và chiến lược cold-start.

**6.6 Offline evaluation.** Kết quả chỉ có giá trị khi chạy trên đúng bộ `train_interactions.csv` / `test_ground_truth.csv` hiện tại. Phải ghi rõ dữ liệu là synthetic, nên Precision@10 ≥ 65% (nếu đạt) không được khái quát hoá cho dữ liệu thực.

**7.1 SSE endpoint.** Đây là triển khai tạm thời bằng so sánh snapshot DB định kỳ (không phải Redis Pub/Sub). Độ trễ lý thuyết bị chặn trên bởi `poll_interval_seconds` cộng thời gian truy vấn. KPI staleness ≤ 5 s phải được đo, không được suy ra.

## 5. Retrospective WBS Reconstruction

**Bản chất tài liệu.** WBS này được dựng lại trong giai đoạn triển khai (Sprint Week 3), sau khi phần lớn công việc đã được thực hiện. Nó không phản ánh kế hoạch ban đầu của nhóm.

**Có thể tái dựng từ Git history:**
- **Database (17–26/10):** `93130fa` → `edac54b` → `7c88400` → `ccf504a`/`d9f3b76`/`0650f51` → `25b95b0`/`08a6669`/`ccae168`/`c38e5dd` (UUIDv5, mở rộng test, bảng phân công staff).
- **Backend (25/10–01/11):** `9566d98` (nền tảng) → `d637609` (products) → `e5339aa` (inventory) → `702844f`…`35a5a78` (đăng ký, Argon2, JWT) → `8448d0a` (SSE) → `4f2affe` (stock update có idempotency).
- **Recommender (25/10–02/11):** `db444ec`…`b41f95f` (baseline, cache, docs) → `0c286d5`/`cb48561`/`de963bb` (ALS, evaluation) → `a93d538` bị revert bởi `aa6ad9f` → `4815019` (benchmark cache, đo SSE).
- **Frontend (20/10–03/11):** `85d64a5` (homepage) → `3fe347b`, `b505d14` (toggle, favorites, tách component) → `1c77730`, `86d59fd`, `899ee89` (tích hợp kho) → `78db507` → `fe1ebc9` → `d31fd29`.

**Đã triển khai trước khi lập WBS:** toàn bộ các work package COMPLETED trong mục 3, cùng phần đã làm của các gói IN PROGRESS và BLOCKED.

**Còn lại:** 4.5.x (orders), 4.6, 6.5, 6.6 (chạy lại), 7.3, 8.4–8.6, 9.3, 9.5, 9.6, 10.x, 11.x.

**Không thể tái dựng tin cậy:**
- Ngày lập kế hoạch và ước lượng effort ban đầu.
- Ai thực hiện review hay pair-programming.
- Công việc làm ngoài Git (task board, họp, Research Proposal, báo cáo).
- Người thực hiện thực tế: tên tác giả commit không nhất thiết trùng người được giao task. Ví dụ, các commit backend/recommender ngày 26/10 có tác giả `tienmai1304-cmd`, trong khi Week 1 giao recommender cho thành viên khác. Ngoài ra ba danh tính tác giả `ZhuHieu`, `BodybuilderOrCoder`, `Tên của bạn` dùng chung một email.

Tài liệu này không gán người phụ trách ngoài những gì đã ghi trong các file Task Assignment.

## 6. Ghi chú sai lệch giữa tài liệu và code

Danh sách đầy đủ nằm trong `PROJECT_PROGRESS.md`, mục 8.
