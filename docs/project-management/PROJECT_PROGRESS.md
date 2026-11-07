# FreshLoop — Báo cáo tiến độ dự án

**Baseline:** nhánh `dev`, HEAD `d31fd29`. **Ngày audit:** 03/11/2026 (Sprint Week 3: 02–08/11/2026).
Đây là báo cáo hồi cứu dựa trên `WBS_FreshLoop.md`. Mọi KPI trong Research Proposal là **mục tiêu**, không phải kết quả đã đạt.

> **Cập nhật 07/11/2026:** báo cáo bên dưới phản ánh ngày 03/11 và chưa được tính lại. Order API, đăng nhập trên storefront và checkout trên trình duyệt đã hoàn thành; API gợi ý vẫn chưa có. Trạng thái mới nhất và việc còn lại nằm ở [WEEK3_INTEGRATION_LOG.md](WEEK3_INTEGRATION_LOG.md).

## 1. Tóm tắt điều hành

FreshLoop đã hoàn thiện phần **nền tảng dữ liệu, catalog theo kho, cập nhật tồn kho có bảo vệ và realtime**. Cụ thể:
- Schema và migration chạy được trên DB sạch.
- API sản phẩm và tồn kho hoạt động.
- Staff cập nhật tồn kho được, có idempotency.
- SSE đẩy thay đổi tồn kho đến client.
- Recommender có baseline, ALS và cache Redis ở mức thư viện.

**Đường đi P0 của Week 3 chưa thông suốt.** Backend chưa có API đặt hàng (`POST /api/orders`, `GET /api/orders/{id}`) và chưa có API gợi ý (`GET /api/recommendations/...`); cả hai trả 404 khi kiểm tra ngày 03/11/2026. Frontend đã sẵn sàng gọi các endpoint này nhưng đang bị chặn. Chưa có deployment, load test hay đo KPI end-to-end.

**Ước lượng hoàn thành tổng thể: khoảng 62%** (khoảng kịch bản 58–64%), tính có trọng số theo mục 2.

## 2. Ước lượng mức độ hoàn thành

### 2.1 Phương pháp

```
Overall Completion = Σ(Weight × Progress) / Σ(Weight)
```

Mỗi work package lá được gán trọng số theo ba tiêu chí:
1. **Mức độ quan trọng với đường đi P0 của MVP.** Đặt hàng, tồn kho và gợi ý có trọng số cao, ví dụ 4.5.1 Order creation = 3 và 4.6 Recommendation API = 3.
2. **Khối lượng và độ phức tạp kỹ thuật.** Ví dụ transaction và concurrency nặng hơn trang tĩnh.
3. **Giá trị làm bằng chứng cho báo cáo** (test, đo đạc, tài liệu).

Các gói P2 hoặc phụ có trọng số thấp, ví dụ 5.9 = 0,5.

**Cách tính tiến độ từng gói:**
- 100% chỉ khi tiêu chí chấp nhận đã được kiểm chứng.
- Gói đã có code nhưng thiếu test hoặc kiểm tra trên trình duyệt bị giới hạn ở 80–90%.
- Gói BLOCKED được tính theo phần đã làm.

**NOT VERIFIED** (1.3, 7.4, 9.4, 11.3, 11.4; tổng trọng số 6) **bị loại khỏi con số chính** và chỉ dùng để tính khoảng kịch bản.

### 2.2 Kết quả

| Chỉ số | Giá trị |
| --- | --- |
| Tổng trọng số đã kiểm chứng | 96,5 |
| Tổng trọng số NOT VERIFIED | 6,0 |
| **Hoàn thành (chỉ phần đã kiểm chứng)** | **61,8%** |
| Kịch bản bi quan (NOT VERIFIED = 0%) | 58,1% |
| Kịch bản lạc quan (NOT VERIFIED = 100%) | 64,0% |

Phân bố trạng thái của 68 work package lá: 24 COMPLETED, 20 IN PROGRESS, 14 PENDING, 5 BLOCKED, 5 NOT VERIFIED.

| Nhóm | Trọng số | Tiến độ | Nhận xét |
| --- | --- | --- | --- |
| 1.0 Project Management | 5 | 90% | Có kế hoạch sprint; contract chưa đóng băng |
| 2.0 Architecture & Infra | 6 | 72% | Thiếu sơ đồ kiến trúc; credentials còn hard-code |
| 3.0 Database | 12 | 92% | Mạnh nhất; còn lỗi password seed và tài liệu lệch |
| 4.0 Backend | 20 | 37% | **Thiếu orders và recommendation API** |
| 5.0 Frontend | 16,5 | 73% | Customer journey sẵn sàng; thiếu auth UI và admin |
| 6.0 Predictive | 10 | 77% | Thư viện xong; evaluation cần chạy lại |
| 7.0 Real-time | 7 | 63% | SSE chạy; chưa đo staleness |
| 8.0 Security | 7 | 59% | Có JWT/RBAC; thiếu phân quyền theo kho và quyền sở hữu đơn |
| 9.0 Testing | 9 | 55% | Unit test tốt; integration lỗi ở `head`; chưa có E2E và load test |
| 10.0 Deployment | 5 | 0% | Chưa bắt đầu |
| 11.0 Documentation | 5 | 60% | Nhiều tài liệu nhưng một số lệch so với code |

### 2.3 Vì sao con số này hợp lý

Khoảng 62% phản ánh việc phần lớn **khối lượng** đã có, nhưng **giá trị nghiệp vụ cốt lõi** (đặt hàng thật, gợi ý thật qua API, deploy) chưa hoàn tất. Week 3 Task Assignment quy định không được tính ≥ 90% khi bất kỳ trong 5 cổng P0 đầu tiên chưa đạt. Hiện cổng 2 (checkout lưu đơn), cổng 3 (xem đơn) và cổng 4 (Top-10 qua API) đều **chưa đạt**.

## 3. Deliverable đã hoàn thành

| Deliverable | WBS | Bằng chứng chính |
| --- | --- | --- |
| Schema 9 bảng và 3 migration | 3.1, 3.2 | `backend/app/models/schema.py`; `upgrade head` trên DB sạch và `downgrade` thành công (03/11) |
| Integrity và concurrency test DB | 3.4 | 13/13 pass (03/11) |
| Catalog và tồn kho theo kho | 4.3, 5.2, 5.3 | E2E: 3 kho, 200 sản phẩm; test frontend pass |
| Stock update có bảo vệ và idempotency | 4.4, 8.3 | E2E: 401 / 200 / replay / 409 |
| Đăng ký Argon2, đăng nhập JWT | 8.1, 8.2 | E2E: register 201, login có token |
| SSE tồn kho | 7.1 | E2E: `inventory.changed` 112 → 107 sau PATCH |
| Recommender: preprocess, baseline, ALS, cache Redis | 6.1–6.4 | `recommender/*`, `sample_output/*` |
| Giỏ hàng client-side và design system | 5.1, 5.4 | `frontend/components/*`, `lib/cart-logic.ts` |
| Kế hoạch sprint và quy tắc cộng tác | 1.1, 1.2 | `FreshLoop_Week*_Task_Assignment.md`, `RULE.md` |

## 4. Deliverable đang thực hiện

| WBS | Deliverable | Còn thiếu |
| --- | --- | --- |
| 1.4 | Contract tích hợp | Xác nhận contract orders và recommendations |
| 3.3 | Seed data | Password hash thật cho tài khoản demo |
| 3.5, 6.6 | Dataset và evaluation | Chạy lại evaluation trên dataset mới (01–02/11) |
| 3.6, 11.1 | Tài liệu | Cập nhật 9 bảng; sửa kết luận benchmark; chuyển log sang UTF-8 |
| 4.2 | Product API | Test tự động; `GET /api/categories` |
| 4.5.2, 4.5.5 | Reservation / release | Service backend (hiện chỉ có đặc tả và test DB) |
| 5.5, 5.8 | Product page, live stock UI | Kiểm tra trên trình duyệt và ghi hình |
| 6.5 | Lọc hết hàng, invalidation | Tích hợp theo kho; gọi `invalidate()` |
| 7.3 | Đo staleness | Có số liệu đo thực tế |
| 8.6, 8.7, 2.3 | Secrets, CORS | Bỏ credentials hard-code; thêm `Idempotency-Key` vào CORS nếu cần |
| 9.3 | Integration tests | Cập nhật `EXPECTED_REVISION`; thêm `pytest` vào requirements |

## 5. Deliverable chưa bắt đầu và bị chặn

| WBS | Deliverable | Trạng thái | Bị chặn bởi |
| --- | --- | --- | --- |
| 4.5.1, 4.5.3, 4.5.4, 4.5.6 | Orders, trạng thái đơn, COD | PENDING | Contract (1.4) |
| 4.6 | Recommendation API | PENDING | Quyết định nguồn dữ liệu và cold-start |
| 4.7 | Cart API | PENDING | Quyết định client-side hay server-side |
| 5.6, 5.7 | Checkout UI, Quick Reorder UI | BLOCKED | 4.5.1, 4.5.3, 4.6 |
| 5.10, 5.11 | Auth UI, admin dashboard | PENDING | 8.2, 8.4 |
| 6.7 | p95 Quick Reorder | BLOCKED | 4.6 |
| 7.2 | Redis Pub/Sub | PENDING | Có thể ghi là giới hạn MVP |
| 8.4, 8.5 | Phân quyền theo kho, quyền sở hữu đơn | PENDING / BLOCKED | 4.5.x |
| 9.5, 9.6 | E2E checkout, load test | BLOCKED / PENDING | 4.5.1, 10.2 |
| 10.1–10.3 | Deployment và monitoring | PENDING | Ổn định P0 |

## 6. Phụ thuộc trọng yếu

```text
1.4 Contract ──► 4.5.1 Order creation ──► 4.5.3 Retrieval ──► 5.6 Checkout UI ──► 9.5 E2E
                     │                                              │
                     ├──► 4.5.2 Reservation ──► 4.5.5 Release       └──► 11.4 Demo
                     └──► 6.5 Cache invalidation
6.2/6.4 Recommender ──► 4.6 Recommendation API ──► 5.7 Quick Reorder UI ──► 6.7 p95 latency
P0 ổn định ──► 10.1/10.2 Deployment ──► 9.6 Load test ──► 10.3 Monitoring
```

## 7. Rủi ro chính

| # | Rủi ro | Mức | Tác động | Giảm thiểu |
| --- | --- | --- | --- | --- |
| R1 | API orders chưa có ngày 03/11, đúng ngưỡng rủi ro "Orders remain missing" trong Week 3 | Cao | Không có checkout cho demo P0 | Áp dụng kế hoạch Week 3: dừng P1, pair-program phần transaction |
| R2 | Recommendation API chưa được tích hợp (hạn 04/11 theo Week 3) | Cao | Quick Reorder chỉ là UI | Ưu tiên baseline; ALS là tuỳ chọn |
| R3 | Precision@10 được trích dẫn từ kết quả cũ, trên dữ liệu synthetic | Trung bình | Báo cáo đưa ra kết luận sai | Chạy lại `evaluate.py`; ghi rõ dữ liệu là synthetic |
| R4 | Integration test lỗi ở `head` | Trung bình | Không có bằng chứng regression | Sửa `EXPECTED_REVISION`; chạy lại |
| R5 | Tài khoản seed không đăng nhập được | Trung bình | Không demo được staff/customer | Seed bằng `hash_password` cùng mật khẩu demo |
| R6 | Chưa deploy | Trung bình | Không có URL demo; không đo được availability | Thử deploy sớm; ghi lại blocker |
| R7 | Credentials dev trong repo | Thấp–Trung bình | Thói quen bảo mật kém, bị trừ điểm | Chuyển sang env |
| R8 | Tài liệu lệch so với code | Trung bình | Báo cáo mâu thuẫn | Rà soát theo mục 8 |

## 8. Sai lệch giữa tài liệu và triển khai

1. `recommender/README.md` có đoạn ví dụ gọi "Endpoint lấy Top-10 gợi ý", nhưng backend chưa có endpoint này. Phần "Known limitations" (ghi "Week 1") vẫn nói chưa lọc hàng hết và Redis lỗi sẽ raise, trong khi `service.py` hiện đã có `exclude_product_ids` và graceful degradation.
2. `database/README.md` và `data_dictionary.md` mô tả 7 bảng; schema thực tế có 9 bảng.
3. `database/README.md` nói PurchaseHistory tính đơn `DELIVERED` **và** `CONFIRMED`; code seed và pipeline chỉ tính `DELIVERED`.
4. `database/README.md` khẳng định dữ liệu được tạo "để đảm bảo" Precision@10 ≥ 65%. Đây là mục tiêu, chưa được kiểm chứng trên dataset hiện tại.
5. `query_timing_benchmarks.txt` kết luận thời gian SQL dưới 1 ms "đạt p95 dưới 150 ms", tức là đánh đồng SQL time với HTTP latency. README mô tả tra cứu SKU là "O(1)" qua index, nhưng EXPLAIN cho thấy Seq Scan (hợp lý với 200 dòng, nhưng mô tả sai).
6. `offline_evaluation.csv` (26/10) được tạo trước khi dataset được sinh lại (01–02/11).
7. Seed ghi `password_hash` giả, không tương thích với cơ chế Argon2 của backend.
8. Week 2 Task 2.1 yêu cầu "cart and order APIs"; giỏ hàng hiện chỉ ở client.
9. Commit `3fe347b` thêm toggle ngôn ngữ/theme; UI hiện tại không còn nút chuyển.
10. Commit `c38e5dd` nhắc "COD", nhưng schema chưa có trường hay trạng thái thanh toán.
11. Kiến trúc dự kiến Vercel/Railway, nhưng repo không có cấu hình deploy.
12. `README.md` gốc công khai connection string có mật khẩu.

## 9. Khuyến nghị ưu tiên

| Ưu tiên | Hành động | WBS |
| --- | --- | --- |
| 1 | Hoàn thành `POST /api/orders` và `GET /api/orders/{id}`: transaction và row lock theo `inventory_lifecycle_spec.md` | 4.5.1–4.5.3 |
| 2 | Tích hợp recommender vào FastAPI: lọc theo kho, HIT/MISS, fallback | 4.6, 6.5 |
| 3 | Sửa integration test ở `head` và seed password; chạy lại toàn bộ test | 9.3, 3.3 |
| 4 | Chạy E2E checkout và SSE trên trình duyệt, có ghi hình | 9.5, 5.5–5.8 |
| 5 | Chạy lại evaluation; đo staleness SSE và p95 Quick Reorder qua HTTP | 6.6, 6.7, 7.3 |
| 6 | Thử deploy (Vercel, Railway) hoặc ghi lại blocker | 10.1, 10.2 |
| 7 | Rà soát tài liệu theo mục 8; bổ sung `backend/README.md` và sơ đồ kiến trúc | 11.1, 2.4 |

## 10. Bằng chứng triển khai từ Git

| Giai đoạn | Commit tiêu biểu | Nội dung |
| --- | --- | --- |
| 17–20/10 | `858c902`, `5ab5f82`, `93130fa`, `85d64a5`, `edac54b` | Khởi tạo repo, schema, migration, seed, homepage |
| 21–22/10 | `3fe347b`, `b65182e`, `b505d14` | Toggle, Prettier, favorites, tách component |
| 25/10 | `9566d98`, `d637609`, `e5339aa`, `1cdec73`, `9a26588`, `7c88400` | FastAPI, products, inventory, baseline, cache, seed thói quen |
| 26/10 | `ccf504a`, `0650f51`, `702844f`…`35a5a78`, `0c286d5`, `de963bb`, `8448d0a`, `1c77730`…`fd8e233` | Pipeline, constraint, auth, ALS, evaluation, SSE, tích hợp kho ở frontend, test |
| 27–31/10 | `78db507`, `a93d538`, `aa6ad9f` | Phân trang catalog; lọc hết hàng bị revert |
| 01/11 | `fe1ebc9`, `25b95b0`, `4f2affe`, `1bd4ab2`, `ce6e7a3` | Trang journey, UUIDv5, stock update idempotent, task assignment |
| 02/11 | `08a6669`, `ccae168`, `4815019`, `c38e5dd` | Test DB mở rộng, benchmark cache, bảng phân công staff |
| 03/11 | `d31fd29` | Hoàn thiện customer journey, API contract |

Tổng 62 commit. Đếm theo tên tác giả Git: `tienmai1304-cmd` 24, `Thang Tran` 11, `Hong An` 9, `ZhuHieu` 9, `BodybuilderOrCoder` 5, `Tên của bạn` 4. Số commit **không** đo khối lượng hay đóng góp thực tế.

## 11. Giới hạn audit và các nhận định chưa kiểm chứng

- **Research Proposal không có trong repo.** KPI được lấy theo đề bài audit và Week 2/3 Task Assignment.
- **Test đã chạy** (03/11/2026, trên DB riêng `freshloop_test_db`): frontend, backend, database và kiểm tra E2E API (xem `FINAL_TESTING_CHECKLIST.md`). **Test recommender chưa chạy.**
- **Giao diện chưa được kiểm tra trên trình duyệt.** Chỉ xác nhận build thành công, các trang trả HTTP 200 và logic đã có unit test.
- **Không có bằng chứng** về task board, biên bản họp, báo cáo cuối hay slide.
- **Các KPI chưa được đo:** p95 < 150 ms, staleness ≤ 5 s, availability ≥ 99,5% với 500 phiên. Precision@10 ≥ 65% **chưa được kiểm chứng trên dataset hiện tại**.
- **Thay đổi môi trường trong quá trình audit** (không phải mã nguồn):
  - DB dev `freshloop_db` được `alembic upgrade head` (chỉ thêm 2 bảng).
  - Tạo DB `freshloop_test_db`.
  - Cài `pytest` vào `backend/.venv`.
  - Thêm một tài khoản test vào DB test.
