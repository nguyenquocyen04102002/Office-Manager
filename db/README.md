# Database — PostgreSQL 16

Schema nằm ở `init/01_schema.sql`. Docker image `postgres` tự chạy mọi file `.sql` trong `/docker-entrypoint-initdb.d` **chỉ ở lần khởi tạo volume đầu tiên** (khi thư mục dữ liệu còn trống).

## Thông tin kết nối

| | Từ máy host (DBeaver, pgAdmin, psql) | Từ container backend |
|---|---|---|
| Host | `localhost` | `db` |
| Cổng | `15432` | `5432` |
| Database | `office_db` | `office_db` |
| User / Password | `office_user` / `office_password` (theo `.env`) | giống bên trái |

Vào `psql` nhanh:

```bat
docker compose exec db psql -U office_user -d office_db
```

## Sơ đồ quan hệ (rút gọn)

```
departments 1───* employees *───1 employees (manager_id: cấp trên - cấp dưới)
employees 1───* attendances        (duy nhất theo employee_id + work_date)
employees 1───* leave_requests     (reviewer_id → employees)
employees 1───* tasks              (assignee_id, creator_id → employees)
employees 1───* assets             (assigned_to_id → employees)
rooms     1───* bookings *───1 employees
employees 1───* announcements      (author_id)
```

## Các bảng

| Bảng | Mục đích | Cột / ràng buộc đáng chú ý |
|---|---|---|
| `departments` | Phòng ban | `name` UNIQUE |
| `employees` | Nhân viên + tài khoản đăng nhập | `code`, `email` UNIQUE; `role` ∈ admin/manager/employee; `status` ∈ active/inactive; `department_id`, `manager_id` (tự tham chiếu, `ON DELETE SET NULL`) |
| `attendances` | Chấm công mỗi ngày | UNIQUE (`employee_id`, `work_date`); `status` ∈ present/late/early_leave/late_early/leave/absent |
| `leave_requests` | Đơn nghỉ phép | `status` ∈ pending/approved/rejected; CHECK `end_date >= start_date`; `days` NUMERIC(5,1) |
| `tasks` | Công việc được giao | `priority` ∈ low/medium/high; `status` ∈ todo/in_progress/done |
| `assets` | Tài sản | `code` UNIQUE; `status` ∈ available/in_use/maintenance/retired |
| `rooms` | Phòng họp | `name` UNIQUE; `capacity` |
| `bookings` | Lịch đặt phòng | CHECK `end_time > start_time`; chỉ mục (`room_id`, `start_time`, `end_time`). Việc chống trùng lịch do backend kiểm tra |
| `announcements` | Thông báo nội bộ | `pinned` BOOLEAN |

Quy ước xóa: xóa nhân viên **không** xóa cứng qua API (chỉ chuyển `inactive`) để giữ lịch sử chấm công; `ON DELETE CASCADE` chỉ dùng cho dữ liệu con thuần túy (chấm công, đơn nghỉ, lịch đặt) khi xóa trực tiếp trong DB.

## Dữ liệu mẫu

Không nằm trong SQL: backend tự tạo (có băm mật khẩu bằng bcrypt) khi bảng `employees` rỗng và `SEED_DEMO_DATA=true`. Xem `backend/app/seed.py`.

## Sao lưu / phục hồi

```bat
docker compose exec -T db pg_dump -U office_user office_db > backup.sql
docker compose exec -T db psql -U office_user -d office_db < backup.sql
```

## Làm lại database từ đầu

```bat
docker compose down -v
docker compose up -d --build
```

`-v` xóa volume `office_manager_pgdata` → **mất toàn bộ dữ liệu**.

## Thay đổi schema khi đã có dữ liệu

Sửa `01_schema.sql` không ảnh hưởng DB đang chạy. Hãy tự chạy lệnh `ALTER TABLE` qua `psql`, ví dụ:

```sql
ALTER TABLE employees ADD COLUMN birthday DATE;
```

rồi cập nhật cả `backend/app/models.py` và `backend/app/schemas.py` cho khớp.
