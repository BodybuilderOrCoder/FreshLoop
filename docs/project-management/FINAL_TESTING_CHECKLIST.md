# FreshLoop — Final Testing Checklist

**Baseline:** nhánh `dev`, HEAD `d31fd29`. **Lần cập nhật trạng thái:** 03/11/2026; các dòng có mã EV-E2E được cập nhật 07/11/2026 trên `0625e49` cộng thay đổi frontend Week 3. Những dòng khác chưa được rà lại, kể cả các dòng BLOCKED mà nay đã có API.

Một test chỉ được đánh **PASSED** khi có bằng chứng chạy thật (mã tham chiếu ở mục 1). Các trạng thái còn lại:

| Trạng thái | Ý nghĩa |
| --- | --- |
| PASSED | Đã chạy, đạt kết quả mong đợi |
| FAILED | Đã chạy, không đạt |
| BLOCKED | Không chạy được vì tính năng phụ thuộc chưa có |
| NOT RUN | Chưa chạy (tính năng có thể đã có) |

Ưu tiên: **P0** là bắt buộc cho demo MVP; **P1** nên có; **P2** là tuỳ chọn hoặc để làm sau.

## 1. Bằng chứng thực thi đã có (03/11/2026)

Các lần chạy đều trên Windows 11 với Docker Desktop (PostgreSQL 16-alpine, Redis 7-alpine). DB kiểm thử riêng là `freshloop_test_db` (migrate lên `head`, `seed_mock_data.py --clean`).

| Mã | Lệnh / hoạt động | Kết quả |
| --- | --- | --- |
| **EV-FE** | `cd frontend && npm test && npx eslint . && npm run build` | 35/35 pass; eslint 0 lỗi; build thành công |
| **EV-BE** | `cd backend && TEST_DATABASE_URL=… DATABASE_URL=… python -m pytest tests` | 96 pass, **13 lỗi** (`RuntimeError: Test database migration is missing or unexpected`) |
| **EV-BE-948** | Hạ DB test về `948e2297107f`, chạy `test_auth_integration.py`, `test_inventory_stock_integration.py`, `test_inventory_stock_concurrency.py` | 13/13 pass; sau đó nâng lại `head` |
| **EV-DB** | `DATABASE_URL=… PYTHONPATH=backend python -m unittest database.tests.test_integrity_constraints -v` | 13/13 pass |
| **EV-MIG** | `alembic upgrade head` trên DB sạch; `downgrade` `b22df6a0d648` → `948e2297107f` → `upgrade head` | Thành công |
| **EV-API** | Gọi API bằng `curl` tới `uvicorn app.main:app` (DB test), frontend `npm run dev` | Kết quả ghi ở từng test bên dưới |
| **EV-FE-W3** | `cd frontend && npm test`, `npx eslint .`, `npx tsc --noEmit`, `npm run build` (07/11) | 43/43 pass; không lỗi |
| **EV-BE-W3** | `pytest tests` với `TEST_DATABASE_URL` (07/11) | 157/157 pass |
| **EV-E2E** | Smoke trên Edge với FastAPI và PostgreSQL thật, chạy 2 vòng (07/11) | 37/37 pass mỗi vòng; xem [evidence/week3](evidence/week3/) và [integration log](WEEK3_INTEGRATION_LOG.md) |

## 2. Cách chạy lại

```bash
docker compose up -d
docker exec freshloop-postgres createdb -U freshloop_user freshloop_test_db   # lần đầu
export TURL=postgresql+psycopg2://<user>:<password>@localhost:5432/freshloop_test_db
cd backend
ALEMBIC_DATABASE_URL=$TURL alembic upgrade head
DATABASE_URL=$TURL python seed_mock_data.py --clean
TEST_DATABASE_URL=$TURL DATABASE_URL=$TURL python -m pytest tests -v
cd .. && DATABASE_URL=$TURL PYTHONPATH=backend python -m unittest database.tests.test_integrity_constraints -v
cd recommender && python -m pytest tests -v
cd ../frontend && npm test && npx eslint . && npm run build
```

> Integration test ở backend chỉ chấp nhận DB tên `freshloop_test_db`. **Không** chạy `seed --clean` trên DB dev nếu chưa được nhóm đồng ý.

## 3. Authentication & RBAC

| Test ID | Kịch bản | Kết quả mong đợi | Ưu tiên | Trạng thái | Bằng chứng |
| --- | --- | --- | --- | --- | --- |
| AUTH-01 | Đăng ký với `email`, `password`, `name`, `phone` hợp lệ | 201; mật khẩu lưu dạng Argon2 | P0 | PASSED | EV-API (201); EV-BE |
| AUTH-02 | Đăng ký trùng email hoặc số điện thoại | 409; transaction rollback | P0 | PASSED | EV-BE-948 (`test_postgres_unique_*`) |
| AUTH-03 | Đăng ký có trường thừa (`full_name`) | 422 | P1 | PASSED | EV-API (422 `extra_forbidden`) |
| AUTH-04 | Đăng nhập đúng | 200; có `access_token` JWT | P0 | PASSED | EV-API |
| AUTH-05 | Đăng nhập sai mật khẩu | 401, thông báo không lộ thông tin nội bộ | P0 | PASSED | EV-E2E (`AUTH-2`: 401, UI báo sai email hoặc mật khẩu) |
| AUTH-06 | Đăng nhập bằng tài khoản seed (`staff@freshloop.vn`, `admin@freshloop.vn`) | Đăng nhập thành công | P0 | FAILED | `seed_mock_data.py` ghi `password_hash` giả (`pbkdf2:sha256:staff_secret_hash`), không phải hash Argon2 |
| AUTH-07 | Gọi API stock mutation không có token | 401 | P0 | PASSED | EV-API |
| AUTH-08 | Customer gọi API stock mutation | 403 | P0 | PASSED | EV-E2E (`SEC-1`: 403) |
| AUTH-09 | Staff sửa tồn kho của kho không được phân công | 403 | P1 | FAILED | Router chỉ kiểm tra role; chưa dùng `staff_warehouse_assignments` (xem WBS 8.4) |
| AUTH-10 | Token hết hạn hoặc bị sửa | 401 | P1 | PASSED | EV-E2E (`AUTH-6`: token bị sửa, chuyển về đăng nhập). Chưa test token hết hạn thật |

## 4. Product API

| Test ID | Kịch bản | Kết quả mong đợi | Ưu tiên | Trạng thái | Bằng chứng |
| --- | --- | --- | --- | --- | --- |
| PROD-01 | `GET /api/products/{id}` với ID hợp lệ | 200, đủ trường của `ProductResponse` | P0 | PASSED | EV-API |
| PROD-02 | `GET /api/products/abc` | 422 `Invalid product ID format` | P1 | PASSED | EV-API |
| PROD-03 | `GET /api/products/{uuid-không-tồn-tại}` | 404 `Product not found` | P1 | NOT RUN | — |
| PROD-04 | `GET /api/products?skip&limit` với `limit` > 100 | 422 | P2 | NOT RUN | — |
| PROD-05 | `GET /api/categories` (Week 1 Task 2.2) | 200 | P2 | BLOCKED | Chưa triển khai |

## 5. Inventory API

| Test ID | Kịch bản | Kết quả mong đợi | Ưu tiên | Trạng thái | Bằng chứng |
| --- | --- | --- | --- | --- | --- |
| INV-01 | `GET /api/warehouses` | 3 kho active (HUB-01, MART-02, MART-03) | P0 | PASSED | EV-API |
| INV-02 | `GET /api/warehouses/{HUB-01}/products` qua 2 trang (`limit=100`) | 200 sản phẩm; `available_stock = quantity − reserved_quantity` | P0 | PASSED | EV-API (200 sản phẩm) |
| INV-03 | Kho không tồn tại hoặc inactive | 404 | P1 | NOT RUN | — |
| INV-04 | Staff `PATCH …/stock` với `quantity_delta = −5` | 200; `available_stock` 112 → 107 | P0 | PASSED | EV-API |
| INV-05 | `PATCH` làm tồn kho thấp hơn `reserved_quantity` | 409; tồn kho không đổi | P0 | PASSED | EV-API (409 `Quantity cannot be lower than reserved quantity.`) |
| INV-06 | `quantity_delta = 0` hoặc thiếu `Idempotency-Key` | 422 | P1 | NOT RUN | Có test schema (EV-BE) |

## 6. Cart (client-side)

| Test ID | Kịch bản | Kết quả mong đợi | Ưu tiên | Trạng thái | Bằng chứng |
| --- | --- | --- | --- | --- | --- |
| CART-01 | Thêm vượt số lượng tồn kho | Bị giới hạn ở `available_stock` | P0 | PASSED | EV-FE (`cart-logic.test.mjs`) |
| CART-02 | Đổi kho khi giỏ có hàng không có ở kho mới | Hàng bị loại hoặc giảm số lượng | P0 | PASSED | EV-FE |
| CART-03 | Tổng tiền giỏ bằng tổng tiền server (miễn phí giao hàng) | Đúng | P0 | PASSED | EV-E2E (`CHK-4`), EV-FE |
| CART-04 | Reload trang | Giỏ được khôi phục từ `sessionStorage` | P1 | NOT RUN | Cần kiểm tra trên trình duyệt |
| CART-05 | Thêm hàng từ trang chi tiết sản phẩm rồi mở `/?cart=open` | Giỏ mở với đúng số lượng | P1 | PASSED | EV-E2E (`CART-NAV`) |

## 7. Order / Checkout lifecycle

| Test ID | Kịch bản | Kết quả mong đợi | Ưu tiên | Trạng thái | Bằng chứng |
| --- | --- | --- | --- | --- | --- |
| ORD-01 | `POST /api/orders` hợp lệ | 201; `orders` và `order_items` được lưu; server tính tổng | P0 | PASSED | EV-E2E (`CHK-3`, `CHK-6`: đơn trong DB khớp trang đơn hàng) |
| ORD-02 | Đặt số lượng vượt tồn kho | 409; không tạo đơn; tồn kho không đổi | P0 | PASSED | EV-E2E (`CHK-9`: 409, giữ giỏ), EV-BE-W3 |
| ORD-03 | Body không hợp lệ (items rỗng, quantity ≤ 0) | 422 | P1 | BLOCKED | Phụ thuộc ORD-01 |
| ORD-04 | `GET /api/orders/{id}` của chính mình | 200, dữ liệu khớp DB | P0 | PASSED | EV-E2E (`ORD-1`, `ORD-2`) |
| ORD-05 | Đọc đơn của người khác | 403 hoặc 404 | P0 | PASSED | EV-E2E (`SEC-2`: 404) |
| ORD-06 | Chuyển trạng thái hợp lệ / không hợp lệ | Chỉ cho phép theo state machine | P1 | BLOCKED | Chỉ có CHECK `chk_order_status` |
| ORD-07 | Huỷ đơn | `CANCELLED`; trả lại `reserved_quantity` | P1 | BLOCKED | Có test DB `test_order_cancellation_releases_inventory` (EV-DB) nhưng chưa có API |
| ORD-08 | Frontend: checkout khi mất kết nối backend | Hiện lỗi kết nối, không xoá giỏ | P1 | PASSED | EV-E2E (`CHK-2`) |
| ORD-09 | Frontend: lỗi 409 từ backend | Hiện `detail` (tên sản phẩm hết hàng) | P0 | PASSED | EV-FE (unit test với mock) |

## 8. COD payment state

| Test ID | Kịch bản | Kết quả mong đợi | Ưu tiên | Trạng thái | Bằng chứng |
| --- | --- | --- | --- | --- | --- |
| COD-01 | Đơn mới ở trạng thái chưa thanh toán | Trạng thái thanh toán được lưu | P1 | BLOCKED | Schema chưa có trường payment |
| COD-02 | Chỉ đơn `DELIVERED` được tính vào `purchase_history` | Đúng | P1 | NOT RUN | Quy tắc có trong `seed_mock_data.py` và `extract_interactions.py`; chưa có test riêng |

## 9. Inventory reservation consistency

| Test ID | Kịch bản | Kết quả mong đợi | Ưu tiên | Trạng thái | Bằng chứng |
| --- | --- | --- | --- | --- | --- |
| RES-01 | CHECK `reserved_quantity <= quantity`, `quantity >= 0` | Vi phạm bị từ chối | P0 | PASSED | EV-DB |
| RES-02 | Hai giao dịch đồng thời có `SELECT … FOR UPDATE` | Không oversell | P0 | PASSED | EV-DB (`test_concurrent_inventory_reservation`) |
| RES-03 | Không có row lock (mô phỏng race condition) | Chứng minh lost update | P1 | PASSED | EV-DB |
| RES-04 | Thiếu hàng thì rollback toàn bộ | Không còn dữ liệu dở dang | P0 | PASSED | EV-DB |
| RES-05 | Cập nhật tồn kho đồng thời qua service backend | Không mất cập nhật | P0 | PASSED | EV-BE-948 (`test_concurrent_different_keys_do_not_lose_updates`) |
| RES-06 | Checkout đồng thời qua API orders | Không oversell | P0 | BLOCKED | Phụ thuộc ORD-01 |

## 10. Idempotency

| Test ID | Kịch bản | Kết quả mong đợi | Ưu tiên | Trạng thái | Bằng chứng |
| --- | --- | --- | --- | --- | --- |
| IDEM-01 | Gửi lại cùng key và cùng payload | Trả lại response cũ; tồn kho không bị trừ lần hai | P0 | PASSED | EV-API (vẫn 107); EV-BE-948 |
| IDEM-02 | Cùng key nhưng payload khác | 409 | P0 | PASSED | EV-BE-948 (`test_same_key_with_different_payload_returns_conflict`) |
| IDEM-03 | Cùng key, đồng thời | Chỉ cập nhật một lần | P0 | PASSED | EV-BE-948 (`test_concurrent_same_key_updates_stock_only_once`) |
| IDEM-04 | User khác dùng cùng key | Được xử lý độc lập | P1 | PASSED | EV-BE-948 |
| IDEM-05 | Idempotency cho `POST /api/orders` | Không tạo đơn trùng | P1 | BLOCKED | Phụ thuộc ORD-01 và quyết định contract |

## 11. Real-time inventory / SSE

| Test ID | Kịch bản | Kết quả mong đợi | Ưu tiên | Trạng thái | Bằng chứng |
| --- | --- | --- | --- | --- | --- |
| SSE-01 | Kết nối tới `/api/warehouses/{id}/inventory/events` | Nhận `inventory.snapshot` | P0 | PASSED | EV-API |
| SSE-02 | Staff PATCH khi đang kết nối | Nhận `inventory.changed` với before/after đúng | P0 | PASSED | EV-API (112 → 107, `poll_interval_seconds=1`) |
| SSE-03 | Trình duyệt cập nhật stock badge mà không reload | Badge đổi | P0 | PASSED | EV-E2E (`LIVE-2`, trên trang chi tiết sản phẩm) |
| SSE-04 | Đo staleness (≥ 30 mẫu, mặc định `poll_interval_seconds=2`) | p95 ≤ 5 s | P0 | NOT RUN | `recommender/measure_sse_delay.py` có, chưa có output |
| SSE-05 | Ngắt kết nối rồi kết nối lại | Nhận snapshot mới; UI hiện "Reconnecting…" rồi "Live" | P1 | NOT RUN | — |
| SSE-06 | Thay đổi ở kho A không gửi tới client đang nghe kho B | Không có event | P1 | NOT RUN | — |
| SSE-07 | Kho inactive | `inventory.error` hoặc 404 | P2 | PASSED | EV-BE (`test_sse_route_rejects_inactive_warehouse`, `test_stream_reports_inactive_warehouse`) |

## 12. Quick Reorder prediction quality

| Test ID | Kịch bản | Kết quả mong đợi | Ưu tiên | Trạng thái | Bằng chứng |
| --- | --- | --- | --- | --- | --- |
| REC-01 | Chạy test recommender | Toàn bộ pass | P0 | NOT RUN | `recommender/tests/*` (27 test) |
| REC-02 | Chạy lại `python -m recommender.evaluate` trên dataset hiện tại | Ghi Precision@10, Recall@10, số user, khoảng ngày, seed | P0 | NOT RUN | `offline_evaluation.csv` hiện có là bản 26/10, **trước** khi dataset được sinh lại |
| REC-03 | So sánh popularity, frequency_recency và ALS trên cùng tập user | Có bảng so sánh | P1 | NOT RUN | Kết quả cũ: 0,098 / 0,696 / 0,508 (không dùng làm bằng chứng cuối) |
| REC-04 | Kiểm tra leakage của split | Không trùng order; thời gian train < test | P0 | NOT RUN | Có assertion trong `database/pipeline/extract_interactions.py` |
| REC-05 | User cold-start | Trả danh sách popularity fallback | P0 | NOT RUN | `docs/fallback.md` |
| REC-06 | `GET /api/recommendations/{user}?warehouse_id=` | Top-10 còn hàng tại kho | P0 | BLOCKED | EV-API: 404 |
| REC-07 | Cache HIT/MISS qua API | Lần đầu MISS, lần sau HIT; có TTL | P0 | BLOCKED | Mới đo ở mức hàm: `cache_latency_benchmark.csv` |
| REC-08 | Redis tắt | Trả kết quả (BYPASS), không lỗi 500 | P1 | NOT RUN | Có logic trong `service.py` |
| REC-09 | Sản phẩm hết hàng sau khi đặt đơn | Không còn trong gợi ý; cache bị xoá | P0 | BLOCKED | Phụ thuộc 4.6, 6.5 |

## 13. Frontend / Backend integration

| Test ID | Kịch bản | Kết quả mong đợi | Ưu tiên | Trạng thái | Bằng chứng |
| --- | --- | --- | --- | --- | --- |
| INT-01 | CORS preflight từ `http://localhost:3000` | 200 | P0 | PASSED | EV-API |
| INT-02 | Các trang `/`, `/product/{id}`, `/orders/{id}` | HTTP 200 | P0 | PASSED | EV-API |
| INT-03 | Catalog trên UI khớp `GET /api/warehouses/{id}/products` | Khớp | P0 | NOT RUN | Cần kiểm tra trên trình duyệt |
| INT-04 | Hành trình: chọn kho → thêm giỏ → checkout → trang đơn hàng | Thành công, giỏ được xoá sau khi đặt | P0 | PASSED | EV-E2E (`CHK-3` đến `CHK-8`) |
| INT-05 | Responsive trên mobile và desktop | Không vỡ layout | P1 | PASSED | EV-E2E (`UI-1` đến `UI-3`: không tràn ngang ở 360 và 390 px) |
| INT-06 | Quick Reorder hiện fallback khi API lỗi | Thông báo rõ ràng | P1 | PASSED | EV-FE (unit test thông báo 404) |

## 14. Database migrations

| Test ID | Kịch bản | Kết quả mong đợi | Ưu tiên | Trạng thái | Bằng chứng |
| --- | --- | --- | --- | --- | --- |
| MIG-01 | `alembic upgrade head` trên DB rỗng | 9 bảng, revision `b22df6a0d648` | P0 | PASSED | EV-MIG |
| MIG-02 | `downgrade` một bước rồi `upgrade` lại | Thành công | P1 | PASSED | EV-MIG |
| MIG-03 | `downgrade base` | Xoá sạch schema | P2 | NOT RUN | — |
| MIG-04 | Seed `--clean` lặp lại hai lần | Kết quả giống nhau (UUIDv5) | P1 | NOT RUN | Mới chạy một lần (EV-MIG) |
| MIG-05 | Integration test chạy ở `head` | Pass | P0 | FAILED | EV-BE: 13 lỗi vì `EXPECTED_REVISION = "948e2297107f"` |

## 15. Security

| Test ID | Kịch bản | Kết quả mong đợi | Ưu tiên | Trạng thái | Bằng chứng |
| --- | --- | --- | --- | --- | --- |
| SEC-01 | Backend không khởi động khi thiếu `JWT_SECRET` (≥ 32 byte) | Báo lỗi cấu hình | P1 | NOT RUN | Logic trong `app/security/tokens.py` |
| SEC-02 | Không có credentials trong file được commit | Không có | P1 | FAILED | Mật khẩu DB dev nằm trong `README.md`, `docker-compose.yml`, `backend/alembic.ini`, `backend/app/database.py` |
| SEC-03 | Lỗi 500 không lộ stack trace hay SQL | Thông báo chung | P1 | NOT RUN | — |
| SEC-04 | `allow_headers` của CORS có đủ header cần dùng (`Idempotency-Key` nếu frontend gửi) | Preflight thành công | P1 | NOT RUN | Hiện chỉ cho phép `Authorization`, `Content-Type` |
| SEC-05 | SQL injection qua tham số path/query | Bị chặn (UUID validation, ORM) | P2 | NOT RUN | — |

## 16. Performance

| Test ID | Kịch bản | Kết quả mong đợi | Ưu tiên | Trạng thái | Bằng chứng |
| --- | --- | --- | --- | --- | --- |
| PERF-01 | EXPLAIN ANALYZE các truy vấn chính | Dùng index phù hợp, ghi đúng loại scan | P1 | NOT RUN | `query_timing_benchmarks.txt` (26/10) có kết luận cần sửa; không chạy lại trong audit |
| PERF-02 | Quick Reorder qua HTTP: p50/p95 (MISS và HIT), ≥ 100 mẫu | p95 < 150 ms (mục tiêu) | P0 | BLOCKED | Phụ thuộc REC-06 |
| PERF-03 | Latency cache ở mức hàm | Ghi nhận, tách biệt với HTTP | P2 | NOT RUN | Có `cache_latency_benchmark.csv` (miss p95 8,05 ms; hit p95 1,28 ms), audit không chạy lại |
| PERF-04 | Load test 500 phiên đồng thời | Ghi availability, error rate, thời lượng | P1 | NOT RUN | Chưa có script; không được khẳng định 99,5% |

## 17. Deployment & environment configuration

| Test ID | Kịch bản | Kết quả mong đợi | Ưu tiên | Trạng thái | Bằng chứng |
| --- | --- | --- | --- | --- | --- |
| DEP-01 | Thành viên khác tự cài đặt từ README trên máy sạch | Chạy được frontend, backend, DB | P0 | NOT RUN | Chưa có `backend/README.md` |
| DEP-02 | `.env.example` đủ biến cho mọi module | Đủ | P1 | NOT RUN | Có `.env.example` gốc và `frontend/.env.example`; cần đối chiếu |
| DEP-03 | Dependency test được khai báo | `pytest` có trong requirements | P1 | FAILED | `backend/requirements.txt` không có `pytest` |
| DEP-04 | Frontend trên Vercel | Có URL hoạt động | P1 | BLOCKED | Chưa có cấu hình hay URL |
| DEP-05 | Backend, DB, Redis trên Railway | API công khai, migration chạy | P1 | BLOCKED | Chưa có cấu hình |
| DEP-06 | `/health` trên môi trường deploy | 200 | P1 | BLOCKED | Phụ thuộc DEP-05 |

## 18. Tổng hợp trạng thái

| Trạng thái | Số test |
| --- | --- |
| PASSED | 44 |
| FAILED | 5 |
| BLOCKED | 14 |
| NOT RUN | 27 |
| **Tổng** | **90** |

**Các FAILED cần xử lý trước:** AUTH-06 (password seed), MIG-05 (revision hard-code), AUTH-09 (phân quyền theo kho), SEC-02 (credentials), DEP-03 (pytest).

**P0 đang BLOCKED bởi orders và recommendation API:** ORD-01, ORD-02, ORD-04, ORD-05, RES-06, REC-06, REC-07, REC-09, INT-04, PERF-02.
