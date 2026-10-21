# Backend — FastAPI

API cho hệ thống Quản lý Văn phòng. Tài liệu tương tác (Swagger UI) có tại `http://localhost:18000/docs`.

## Công nghệ

- **FastAPI** + Uvicorn
- **SQLAlchemy 2.0** (ORM), driver `psycopg2` cho PostgreSQL
- **Pydantic v2** (validate dữ liệu, `EmailStr` cần gói `email-validator`)
- **JWT** bằng PyJWT, mật khẩu băm bằng **bcrypt**
- `tzdata` để dùng múi giờ `Asia/Ho_Chi_Minh` trong container `slim`

## Cấu trúc

```
app/
├── main.py        Khởi tạo app, CORS, tạo bảng còn thiếu, seed dữ liệu, đăng ký router
├── config.py      Đọc biến môi trường
├── database.py    Engine, SessionLocal, Base, get_db
├── models.py      9 bảng: Department, Employee, Attendance, LeaveRequest, Task,
│                  Asset, Room, Booking, Announcement
├── schemas.py     Pydantic schema (Create / Update / Out)
├── security.py    hash_password, verify_password, tạo/giải mã JWT
├── deps.py        get_current_user, require_roles, visible_employee_ids
├── seed.py        Dữ liệu mẫu
└── routers/       Mỗi nhóm chức năng một file
tests/test_smoke.py   Test toàn bộ luồng chính bằng SQLite
```

## Xác thực & phân quyền

1. `POST /api/auth/login` (form `username` = email, `password`) trả về `access_token`.
2. Gửi kèm header `Authorization: Bearer <token>` ở mọi request khác.
3. Phân quyền theo `role`: `admin` > `manager` > `employee`.
4. **Phạm vi quản lý** (`deps.visible_employee_ids`): `employee` chỉ thấy mình; `manager` thấy mình + toàn bộ cấp dưới (đệ quy theo `employees.manager_id`); `admin` thấy tất cả. Áp dụng cho điểm danh, nghỉ phép, công việc, báo cáo, dashboard.

Ví dụ dùng `curl` (Windows CMD — **một dòng**):

```bat
curl -X POST http://localhost:18000/api/auth/login -d "username=admin@congty.vn&password=Admin@123"
curl http://localhost:18000/api/employees -H "Authorization: Bearer <TOKEN>"
```

## Danh sách API

Ký hiệu quyền: 🔓 mọi người dùng đã đăng nhập · 👤 chỉ chủ sở hữu · 🧑‍💼 admin + manager · 👑 chỉ admin.

### Hệ thống & xác thực
| Method | Đường dẫn | Quyền | Mô tả |
|---|---|---|---|
| GET | `/api/health` | công khai | Kiểm tra sống (dùng cho healthcheck) |
| POST | `/api/auth/login` | công khai | Đăng nhập, trả JWT |
| GET | `/api/auth/me` | 🔓 | Thông tin tài khoản hiện tại |
| POST | `/api/auth/change-password` | 🔓 | Đổi mật khẩu |

### Tổng quan
| Method | Đường dẫn | Quyền | Mô tả |
|---|---|---|---|
| GET | `/api/dashboard/stats` | 🔓 | Số liệu tổng quan theo phạm vi quyền |

### Phòng ban
| Method | Đường dẫn | Quyền | Mô tả |
|---|---|---|---|
| GET | `/api/departments` | 🔓 | Danh sách + số nhân viên |
| GET | `/api/departments/{id}` | 🔓 | Chi tiết |
| POST | `/api/departments` | 👑 | Tạo |
| PUT | `/api/departments/{id}` | 👑 | Sửa |
| DELETE | `/api/departments/{id}` | 👑 | Xóa (nhân viên chuyển về chưa phân phòng) |

### Nhân viên
| Method | Đường dẫn | Quyền | Mô tả |
|---|---|---|---|
| GET | `/api/employees` | 🔓 | Danh sách. Tham số: `q`, `department_id`, `status`, `role` |
| GET | `/api/employees/team` | 🔓 | Nhân viên thuộc phạm vi quản lý của tôi |
| GET | `/api/employees/{id}` | 🔓 | Chi tiết |
| POST | `/api/employees` | 👑 | Tạo (kèm mật khẩu) |
| PUT | `/api/employees/{id}` | 👑 | Sửa (có thể đặt lại mật khẩu bằng trường `password`) |
| DELETE | `/api/employees/{id}` | 👑 | Cho nghỉ việc: đặt `status=inactive`, khóa đăng nhập, giữ dữ liệu lịch sử |

### Điểm danh
| Method | Đường dẫn | Quyền | Mô tả |
|---|---|---|---|
| POST | `/api/attendance/check-in` | 🔓 | Vào ca (mỗi ngày 1 lần). Sau `WORK_START` → `late` |
| POST | `/api/attendance/check-out` | 🔓 | Ra về. Trước `WORK_END` → `early_leave` (cả hai → `late_early`) |
| GET | `/api/attendance/today` | 🔓 | Bản ghi hôm nay của tôi (hoặc `null`) |
| GET | `/api/attendance` | 🔓 | Lịch sử theo phạm vi quản lý. Tham số: `date_from`, `date_to`, `employee_id`, `department_id`, `status`, `limit` |
| POST | `/api/attendance` | 🧑‍💼 | Chấm công thủ công cho nhân viên thuộc quyền |
| PUT | `/api/attendance/{id}` | 🧑‍💼 | Sửa giờ/ trạng thái/ ghi chú |
| DELETE | `/api/attendance/{id}` | 👑 | Xóa bản ghi |

Trạng thái: `present`, `late`, `early_leave`, `late_early`, `leave`, `absent`.

### Nghỉ phép
| Method | Đường dẫn | Quyền | Mô tả |
|---|---|---|---|
| POST | `/api/leaves` | 🔓 | Gửi đơn (`leave_type`, `start_date`, `end_date`, `reason`). Số ngày = số ngày T2–T6; chặn trùng đơn |
| GET | `/api/leaves` | 🔓 | Danh sách theo phạm vi quản lý. Tham số: `status`, `mine=true` |
| PUT | `/api/leaves/{id}/review` | 🧑‍💼 | Duyệt/từ chối `{approve, review_note}`. Không tự duyệt đơn của mình (trừ admin). Khi duyệt → ghi `leave` vào chấm công |
| DELETE | `/api/leaves/{id}` | 👤 | Hủy đơn đang `pending` |

Loại nghỉ: `annual`, `sick`, `unpaid`, `maternity`, `other`.

### Công việc
| Method | Đường dẫn | Quyền | Mô tả |
|---|---|---|---|
| GET | `/api/tasks` | 🔓 | Danh sách theo phạm vi. Tham số: `status`, `assignee_id`, `mine=true` |
| POST | `/api/tasks` | 🧑‍💼 | Giao việc (chỉ cho nhân viên thuộc quyền) |
| GET | `/api/tasks/{id}` | 🔓 | Chi tiết |
| PUT | `/api/tasks/{id}` | người giao / admin / người được giao | Người được giao **chỉ** đổi được `status` |
| DELETE | `/api/tasks/{id}` | người giao / admin | Xóa |

### Tài sản
| Method | Đường dẫn | Quyền | Mô tả |
|---|---|---|---|
| GET | `/api/assets` | 🔓 | Danh sách. Tham số: `q`, `status`, `category` |
| POST | `/api/assets` | 🧑‍💼 | Thêm. Gán `assigned_to_id` → tự đặt `in_use` |
| PUT | `/api/assets/{id}` | 🧑‍💼 | Sửa / cấp phát / thu hồi |
| DELETE | `/api/assets/{id}` | 👑 | Xóa |

### Phòng họp & đặt phòng
| Method | Đường dẫn | Quyền | Mô tả |
|---|---|---|---|
| GET | `/api/rooms` | 🔓 | Danh sách phòng |
| POST / PUT / DELETE | `/api/rooms`, `/api/rooms/{id}` | 👑 | Quản lý phòng |
| GET | `/api/bookings` | 🔓 | Lịch đặt. Tham số: `day`, `room_id`, `upcoming` |
| POST | `/api/bookings` | 🔓 | Đặt phòng. Trùng giờ → **409** |
| DELETE | `/api/bookings/{id}` | 👤 / 👑 | Hủy lịch của mình |

### Thông báo
| Method | Đường dẫn | Quyền | Mô tả |
|---|---|---|---|
| GET | `/api/announcements` | 🔓 | Ghim lên trước, mới nhất trước |
| POST | `/api/announcements` | 🧑‍💼 | Đăng |
| PUT / DELETE | `/api/announcements/{id}` | tác giả / 👑 | Sửa / xóa |

### Báo cáo
| Method | Đường dẫn | Quyền | Mô tả |
|---|---|---|---|
| GET | `/api/reports/attendance-monthly` | 🧑‍💼 | Tham số: `year`, `month`, `department_id`. Trả ngày công chuẩn, đi làm, muộn, về sớm, nghỉ phép, vắng, tổng giờ |
| GET | `/api/reports/attendance-monthly/export` | 🧑‍💼 | Tải CSV (UTF-8 BOM, mở đúng tiếng Việt trong Excel) |
| GET | `/api/reports/overview` | 🧑‍💼 | Thống kê nhân sự / công việc / nghỉ phép / tài sản |

Quy ước tính chấm công: ngày công chuẩn = số ngày T2–T6 trong tháng (tháng hiện tại tính đến hôm nay); vắng = ngày công chuẩn − ngày đi làm − ngày nghỉ phép.

## Mã lỗi thường gặp

| Mã | Ý nghĩa |
|---|---|
| 400 | Dữ liệu không hợp lệ / vi phạm quy tắc nghiệp vụ (thông báo bằng tiếng Việt trong `detail`) |
| 401 | Chưa đăng nhập hoặc token hết hạn |
| 403 | Không đủ quyền hoặc nhân viên ngoài phạm vi quản lý |
| 404 | Không tìm thấy |
| 409 | Trùng lịch đặt phòng |
| 422 | Sai định dạng dữ liệu (Pydantic) |

## Biến môi trường

Xem bảng ở [README gốc](../README.md#7-cấu-hình-env). Backend đọc: `DATABASE_URL`, `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `CORS_ORIGINS`, `TIMEZONE`, `WORK_START`, `WORK_END`, `SEED_DEMO_DATA`, `SEED_ADMIN_EMAIL`, `SEED_ADMIN_PASSWORD`.

## Khởi tạo database

Khi khởi động, `app/main.py` chạy `Base.metadata.create_all()` (chỉ tạo bảng còn thiếu) rồi `seed_database()` (chỉ chạy khi bảng `employees` trống). Với PostgreSQL trong Docker, bảng thực tế được tạo bởi `db/init/01_schema.sql`.

> Khi thêm/sửa cột trong `models.py`, hãy cập nhật cả `db/init/01_schema.sql` và tự chạy `ALTER TABLE` trên DB đang có (dự án chưa dùng Alembic). Nếu muốn quản lý migration chuyên nghiệp, có thể bổ sung Alembic.

## Chạy test

```bat
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt pytest
set DATABASE_URL=sqlite:///./test.db
pytest -q
```

Test `tests/test_smoke.py` đăng nhập 3 vai trò và kiểm tra: phân quyền, CRUD phòng ban/nhân viên, điểm danh, duyệt nghỉ phép, giao việc, tài sản, chống trùng lịch phòng, thông báo, báo cáo CSV và dashboard.

## Chạy backend riêng (không Docker)

```bat
pip install -r requirements.txt
set DATABASE_URL=postgresql+psycopg2://office_user:office_password@localhost:15432/office_db
uvicorn app.main:app --reload --port 18000
```
