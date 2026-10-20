# FreshLoop

FreshLoop: a headless grocery e-commerce platform that pre-loads each returning customer's likely purchases using ALS collaborative filtering cached in Redis, with real-time inventory sync over SSE. Built with Next.js, FastAPI, PostgreSQL and Redis. IT for E-commerce course project.

---

## 1. Thông Tin Kết Nối PostgreSQL (Database Information)
- **Host**: `localhost`
- **Port**: `5432`
- **Database**: `freshloop_db`
- **User**: `freshloop_user`
- **Password**: `freshloop_password123`
- **Connection String (SQLAlchemy / Python)**:
  ```text
  postgresql+psycopg2://freshloop_user:freshloop_password123@localhost:5432/freshloop_db
  ```

## 2. Thông Tin Redis Cache
- **Host**: `localhost`
- **Port**: `6379`

## 3. Các Lệnh Quản Lý Thường Dùng (Docker Compose)
- Khởi động DB và Redis:
  ```bash
  docker compose up -d
  ```
- Kiểm tra trạng thái:
  ```bash
  docker ps
  ```
- Dừng DB:
  ```bash
  docker compose down
  ```

## 4. Quản Lý Migration Bằng Alembic
- Tạo migration mới khi sửa `schema.py`:
  ```bash
  alembic -c backend/alembic.ini revision --autogenerate -m "mo ta thay doi"
  ```
- Cập nhật database:
  ```bash
  alembic -c backend/alembic.ini upgrade head
  ```

## 5. Nạp Lại Dữ Liệu Mẫu (Seed Data)
```bash
python backend/seed_mock_data.py
```
