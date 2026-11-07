# FreshLoop — Week 3 Integration Log

**Cập nhật:** 07/11/2026 · **Phụ trách:** Hiếu (integration owner) · **Baseline:** `dev` tại `0625e49` cộng các thay đổi frontend của Task 1.1–1.3.

Tài liệu này ghi lại trạng thái tích hợp thực tế, ai chịu trách nhiệm phần nào, và bằng chứng đã chạy. Contract v1 nằm ở [api-contract.md](../../frontend/docs/api-contract.md). Contract khớp với code hiện tại nhưng **chưa được Tiến, Thắng và Ân xác nhận**, nên chưa tính là đã đóng băng.

## 1. Quyết định đã chốt

| Chủ đề | Quyết định | Người quyết định |
| --- | --- | --- |
| Phí giao hàng | Miễn phí cho mọi đơn. Tổng tiền là tổng tiền hàng do server tính; frontend không cộng thêm phí | Hiếu, 07/11 |
| Xác thực checkout | Bắt buộc `Authorization: Bearer <JWT>`. `user_id` lấy từ token, client không gửi | Theo code order API của Tiến |
| Phiên đăng nhập | JWT lưu trong `sessionStorage` (hết khi đóng tab), hết hạn sau 30 phút theo backend | Hiếu, 07/11 |
| Chống đặt trùng | `POST /api/orders` bắt buộc `Idempotency-Key`; frontend giữ nguyên key khi thử lại cùng một giỏ | Theo code order API |
| Phương thức thanh toán | Chỉ COD | Theo schema của Thắng |

## 2. Integration matrix

| Luồng | Frontend | Backend / dữ liệu | Trạng thái | Việc còn lại | Owner |
| --- | --- | --- | --- | --- | --- |
| Chọn kho → catalog | `useCatalog` | `GET /api/warehouses`, `/products` | ✅ Đã kiểm chứng | — | — |
| Đăng ký, đăng nhập | `/login`, `lib/auth.ts` | `/api/auth/*` | ✅ Đã kiểm chứng | — | — |
| Checkout → đơn hàng | `CartDrawer`, `/orders/[id]` | `POST`/`GET /api/orders` | ✅ Đã kiểm chứng | — | — |
| Giữ hàng (reserve) | Thấy qua `available_stock` | Transaction, row lock | ✅ Đã kiểm chứng | — | — |
| Staff đổi tồn → SSE | `useCatalog` | `PATCH .../stock`, SSE polling 2 s | ✅ Đã kiểm chứng | Đo chính thức ≥ 30 mẫu, test reconnect | Ân |
| Quick Reorder | `page.tsx`, `QuickReorder` | **Chưa có** `GET /api/recommendations` | ❌ Chưa có API | Thêm router; sửa lỗi import recommender | Tiến, Ân |
| Invalidate cache sau đặt đơn | — | Order service chưa gọi `invalidate()` | ❌ Chưa làm | Gọi sau khi commit đơn | Tiến |
| Staff/Admin UI | Chưa có | API đã có | ⏳ P1 | Hiện dùng Swagger | Quyết định ở Week 4 |
| Deploy | Chưa có | Chưa có | ⏳ Blocker ở mục 6 | Xem mục 6 | Hiếu, Tiến |

## 3. Kết quả kiểm thử (07/11/2026)

Môi trường: Windows 11, Docker Desktop (PostgreSQL 16, Redis 7), FastAPI trên `freshloop_test_db`, bản Next.js production, trình duyệt Edge headless qua Playwright.

| Bộ kiểm thử | Kết quả |
| --- | --- |
| Frontend unit test (`npm test`) | 43/43 pass |
| ESLint, `tsc --noEmit`, `npm run build` | Không lỗi |
| Backend, gồm integration và concurrency | 157/157 pass |
| Smoke E2E trên trình duyệt, vòng 1 | 37/37 pass ([log](evidence/week3/smoke-run1.json)) |
| Smoke E2E trên trình duyệt, vòng 2 | 37/37 pass ([log](evidence/week3/smoke-run2.json)) |

Smoke test bao phủ: đăng ký, sai mật khẩu, giữ giỏ khi đăng nhập, checkout thật, double-click, mất mạng, hết hàng (409), token bị từ chối, đơn của người khác, customer đổi tồn kho (403), SSE, giữ lựa chọn kho, responsive 360 px và 390 px.

**Lưu ý về độ tin cậy của bằng chứng:**
- `QR-3` và `QR-4` dùng **phản hồi giả lập** để kiểm tra frontend theo contract. Đây không phải bằng chứng Quick Reorder đã chạy. `QR-2` xác nhận API thật vẫn trả 404.
- Độ trễ SSE trên trình duyệt từ 324 ms đến 2.371 ms, chỉ có 10 mẫu trên máy local. Đây là số tham khảo, không thay thế phép đo của Ân.
- Bài test giả lập mất kết nối SSE để tạo tình huống hết hàng, vì bình thường UI đã tự loại sản phẩm hết hàng khỏi giỏ.

Ảnh chụp ở [evidence/week3/](evidence/week3/). Chạy lại bằng [smoke.mjs](evidence/week3/smoke.mjs): cần backend ở cổng 8000, frontend ở cổng 3000, `npm i playwright-core` trong một thư mục ngoài repo, rồi `node smoke.mjs <lần-chạy> <thư-mục-kết-quả>`. Script chỉ được chạy với `freshloop_test_db` vì nó đổi role và tồn kho.

## 4. Lỗi phát hiện và đã sửa trong đợt này

| Lỗi | Hướng sửa |
| --- | --- |
| Storefront không gửi token nên checkout và trang đơn hàng bị 401 | Thêm đăng nhập và gắn token vào order API |
| Tổng tiền trên giỏ khác tổng tiền server | Bỏ phí giao ở frontend |
| Sản phẩm thêm ở trang chi tiết bị mất khi quay lại giỏ | `useCart` đọc lại storage trước khi ghi |
| Phản hồi SSE đến muộn có thể ghi đè tồn kho của kho vừa chọn | Huỷ request cũ khi đổi kho |
| Trang chủ tràn ngang trên mobile | Thu gọn header ở màn hình ≤ 420 px |
| Mật khẩu còn trong state của trang đăng nhập đã ẩn | Xoá ngay sau khi đăng nhập |
| Tiêu đề trang không có style, lỗi checkout màu xám và không tự mất | Sửa CSS và xoá lỗi khi nhập lại |

## 5. Việc cần thành viên khác xử lý trước khi freeze

| Ưu tiên | Việc | Owner | Vị trí |
| --- | --- | --- | --- |
| 0 | Xác nhận contract v1 | Tiến, Thắng, Ân | `frontend/docs/api-contract.md` |
| 1 | Sửa lỗi import: thêm `from __future__ import annotations` | Ân | `recommender/als_model.py:23` |
| 2 | Thêm `GET /api/recommendations/{user_id}` theo contract | Tiến | Mẫu trong `recommender/README.md` |
| 3 | Gọi `invalidate()` sau khi tạo đơn | Tiến | `backend/app/services/orders.py` |
| 4 | Xoá `idempotency_records` trong `seed --clean` | Thắng | `backend/seed_mock_data.py:190` |
| 5 | Sửa tên event, thêm phép đo delay, chạy ≥ 30 mẫu, test reconnect | Ân | `recommender/measure_sse_delay.py` |
| 6 | Chạy lại `evaluate` trên dataset mới; đo p50/p95 qua HTTP | Ân | `recommender/sample_output/` |
| 7 | Kiểm tra staff theo kho khi đổi tồn kho | Tiến | `backend/app/routers/inventory.py` |

Khi mục 1–3 xong, Hiếu chạy lại smoke test với API gợi ý thật trước khi gắn tag release candidate.

## 6. Deployment: blocker

Chưa deploy. Trong repo không có cấu hình Vercel hay Railway, và việc deploy cần tài khoản của nhóm.

Frontend (Vercel) cần backend có URL công khai trước, vì `NEXT_PUBLIC_API_BASE_URL` được gắn lúc build.

| Biến | Nơi đặt | Giá trị |
| --- | --- | --- |
| Root Directory | Vercel | `frontend` |
| `NEXT_PUBLIC_API_BASE_URL` | Vercel | URL HTTPS của backend, không có `/` cuối |
| `NEXT_PUBLIC_DEMO_USER_ID` | Vercel | Để trống |
| `DATABASE_URL`, `REDIS_URL` | Railway | Từ dịch vụ PostgreSQL và Redis |
| `JWT_SECRET` | Railway | Chuỗi ngẫu nhiên ≥ 32 byte, không dùng lại giá trị local |
| `CORS_ORIGINS` | Railway | Domain Vercel chính xác |

## 7. Trạng thái task của Hiếu

| Task | Trạng thái | Ghi chú |
| --- | --- | --- |
| 1.1 Customer journey | ✅ Xong trong phạm vi có API | Checkout chạy thật trên trình duyệt; đủ trạng thái lỗi. Chưa có video màn hình |
| 1.2 Quick Reorder và realtime | ⏳ Phần frontend xong | SSE đã kiểm chứng. Quick Reorder chờ API thật |
| 1.3 Tích hợp và bàn giao | ⏳ Một phần | Có contract v1 (chờ xác nhận), matrix, smoke test 2 lần. Chưa deploy, chưa tag, chưa tích hợp logo Smart Basket |

Tag release candidate nên chờ, vì theo tiêu chí Week 3, cổng Quick Reorder chưa đạt thì chưa đủ điều kiện.
