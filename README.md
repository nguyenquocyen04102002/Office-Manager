# 🏢 Hệ thống Quản lý Văn phòng (Office Manager)

Ứng dụng web quản lý văn phòng toàn diện: nhân sự, phòng ban, điểm danh, nghỉ phép, giao việc, tài sản, đặt phòng họp, thông báo nội bộ và báo cáo. Giao diện hoàn toàn bằng tiếng Việt.

| Thành phần | Công nghệ |
|---|---|
| Backend | Python 3.12, **FastAPI**, SQLAlchemy 2, JWT (PyJWT), bcrypt |
| Frontend | **React 18** + Vite + React Router, phục vụ bằng Nginx |
| Cơ sở dữ liệu | **PostgreSQL 16** (schema SQL tại `db/init/01_schema.sql`) |
| Triển khai | **Docker Compose** (3 service: `db`, `backend`, `frontend`) |

---

## 1. Chạy nhanh bằng Docker

Yêu cầu: Docker Desktop (Windows: bật WSL2 backend).

```bat
:: 1. Vào thư mục dự án
cd office-manager

:: 2. Tạo file cấu hình (file .env đã có sẵn nếu bạn nhận bản này; nếu chưa:)
copy .env.example .env

:: 3. Build và chạy
docker compose up -d --build

:: 4. Xem log (tùy chọn)
docker compose logs -f backend
```

Lần chạy đầu tiên mất vài phút để tải image và build. Khi các container báo `healthy`, mở trình duyệt:

| Dịch vụ | Địa chỉ |
|---|---|
| 🌐 Giao diện web | http://localhost:**18080** |
| 📚 Tài liệu API (Swagger) | http://localhost:**18000**/docs (hoặc http://localhost:18080/docs) |
| 🗄️ PostgreSQL | `localhost:`**15432** (user/password trong `.env`) |

### Cổng đã chọn để KHÔNG trùng các dự án trước

Các dự án trước thường dùng cổng `80`, `3000`, `5173`, `5432`, `6379`, `8000`, `8080`. Dự án này dùng dải cổng riêng:

| Service | Cổng trong container | Cổng publish ra máy host | Biến trong `.env` |
|---|---|---|---|
| frontend (Nginx) | 80 | **18080** | `FRONTEND_PORT` |
| backend (FastAPI) | 8000 | **18000** | `BACKEND_PORT` |
| db (PostgreSQL) | 5432 | **15432** | `DB_PORT` |

Tên container (`office_db`, `office_backend`, `office_frontend`), network (`office_manager_net`) và volume (`office_manager_pgdata`) cũng đều có tiền tố riêng nên không đụng các project khác. Muốn đổi cổng chỉ cần sửa trong `.env` rồi chạy lại `docker compose up -d`. Nếu đổi `FRONTEND_PORT`, nhớ cập nhật `CORS_ORIGINS` cho khớp.

> Kiểm tra cổng đang bị chiếm trên Windows: `netstat -ano | findstr :18080`

---

## 2. Tài khoản demo

Dữ liệu mẫu được tạo tự động khi database còn trống (`SEED_DEMO_DATA=true`).

| Vai trò | Email | Mật khẩu |
|---|---|---|
| Quản trị viên | `admin@congty.vn` | `Admin@123` |
| Quản lý (Trưởng phòng Kinh doanh) | `tuan.le@congty.vn` | `Quanly@123` |
| Quản lý khác | `lan.nguyen@congty.vn`, `hung.tran@congty.vn`, `bao.pham@congty.vn` | `Quanly@123` |
| Nhân viên | `khang.hoang@congty.vn` (và `ha.vo@`, `mai.dang@`, `thao.bui@`, `anh.ngo@`, `linh.do@congty.vn`) | `Nhanvien@123` |

⚠️ **Đổi mật khẩu và `SECRET_KEY` trước khi dùng thật** (xem mục 7).

---

## 3. Chức năng

| Nhóm | Mô tả |
|---|---|
| **Xác thực & phân quyền** | Đăng nhập JWT, đổi mật khẩu, 3 vai trò: `admin`, `manager`, `employee` |
| **Phòng ban** | Thêm / sửa / xóa, thống kê số nhân viên |
| **Nhân viên** | Hồ sơ, chức vụ, phòng ban, **quản lý trực tiếp** (cấp trên – cấp dưới), tìm kiếm, cho nghỉ việc (khóa tài khoản, giữ dữ liệu) |
| **Điểm danh** | Vào ca / ra về bằng 1 nút, tự tính **đi muộn / về sớm** theo giờ làm việc cấu hình, quản lý chấm công thủ công & chỉnh sửa |
| **Nghỉ phép** | Gửi đơn, tự tính số ngày làm việc (T2–T6), chống trùng đơn, quản lý duyệt/từ chối; khi duyệt tự ghi "nghỉ phép" vào bảng chấm công |
| **Công việc** | Giao việc cho cấp dưới, mức ưu tiên, hạn, theo dõi trạng thái; người được giao chỉ đổi được trạng thái |
| **Tài sản** | Mã tài sản, danh mục, cấp phát cho nhân viên, bảo trì/thanh lý |
| **Phòng họp** | Danh mục phòng, đặt lịch, **chặn trùng lịch** (HTTP 409), hủy lịch |
| **Thông báo** | Đăng, ghim, sửa, xóa thông báo nội bộ |
| **Báo cáo** | Chấm công theo tháng (ngày đi làm, muộn, về sớm, nghỉ phép, vắng, tổng giờ), **xuất CSV mở bằng Excel**, thống kê tổng quan |
| **Tổng quan (Dashboard)** | Số liệu theo phạm vi quyền: toàn công ty / nhóm quản lý / cá nhân |

### Phạm vi dữ liệu theo vai trò

| Vai trò | Xem dữ liệu | Quyền thao tác chính |
|---|---|---|
| `employee` | Của chính mình | Điểm danh, gửi/hủy đơn nghỉ, cập nhật trạng thái việc được giao, đặt phòng họp |
| `manager` | Bản thân + **toàn bộ cấp dưới** (đệ quy theo `manager_id`) | Duyệt nghỉ phép, giao việc, sửa chấm công, quản lý tài sản, đăng thông báo, xem báo cáo |
| `admin` | Toàn bộ | Mọi thao tác, gồm quản lý phòng ban, nhân viên, phòng họp |

---

## 4. Cấu trúc thư mục

```
office-manager/
├── docker-compose.yml        # Cấu hình 3 service, cổng, volume, healthcheck
├── .env.example              # Mẫu biến môi trường (copy thành .env)
├── .env                      # Biến môi trường thực tế (không commit)
├── README.md                 # Tài liệu này
├── db/
│   ├── README.md             # Tài liệu database
│   └── init/01_schema.sql    # Schema PostgreSQL, tự chạy lần đầu
├── backend/
│   ├── README.md             # Tài liệu backend + danh sách API
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py           # Khởi tạo FastAPI, CORS, đăng ký router
│   │   ├── config.py         # Đọc biến môi trường
│   │   ├── database.py       # Engine / session SQLAlchemy
│   │   ├── models.py         # ORM models
│   │   ├── schemas.py        # Pydantic schemas
│   │   ├── security.py       # Băm mật khẩu, JWT
│   │   ├── deps.py           # Xác thực, phân quyền, phạm vi quản lý
│   │   ├── seed.py           # Dữ liệu mẫu
│   │   └── routers/          # auth, departments, employees, attendance, leaves,
│   │                         # tasks, assets, rooms, announcements, reports, dashboard
│   └── tests/test_smoke.py   # Test toàn bộ luồng API (SQLite)
└── frontend/
    ├── README.md             # Tài liệu frontend
    ├── Dockerfile            # Build đa giai đoạn: Node -> Nginx
    ├── nginx.conf            # Phục vụ SPA + proxy /api -> backend
    ├── package.json, vite.config.js, index.html
    └── src/
        ├── main.jsx, App.jsx, api.js, AuthContext.jsx, utils.js, styles.css
        ├── components/       # Layout, FormModal, ui
        └── pages/            # Login, Dashboard, Attendance, Leaves, Tasks, Rooms,
                              # Assets, Announcements, Employees, Departments, Reports, Profile
```

---

## 5. Kiến trúc & luồng request

```
Trình duyệt ──► Nginx (frontend:80, host 18080)
                  ├─ /            → file tĩnh React (SPA)
                  └─ /api, /docs  → proxy → FastAPI (backend:8000, host 18000)
                                               └─► PostgreSQL (db:5432, host 15432)
```

- Trình duyệt chỉ gọi **cùng origin** (`/api/...`), nên không gặp lỗi CORS khi dùng qua cổng 18080.
- Backend nói chuyện với DB qua tên service `db` và cổng nội bộ `5432` trong network Docker (không phụ thuộc cổng host `15432`).
- Backend chỉ khởi động khi DB `healthy`; frontend chỉ khởi động khi backend `healthy`.

---

## 6. Lệnh Docker thường dùng

```bat
docker compose up -d --build          :: build + chạy nền
docker compose ps                     :: trạng thái các container
docker compose logs -f backend        :: log backend (đổi tên service để xem db / frontend)
docker compose restart backend        :: khởi động lại 1 service
docker compose down                   :: dừng và xóa container (GIỮ dữ liệu)
docker compose down -v                :: dừng và XÓA CẢ DỮ LIỆU database (volume)
```

### Reset database về dữ liệu mẫu

```bat
docker compose down -v
docker compose up -d --build
```

### Sao lưu / phục hồi database

```bat
:: Sao lưu
docker compose exec -T db pg_dump -U office_user office_db > backup.sql

:: Phục hồi (vào database trống)
docker compose exec -T db psql -U office_user -d office_db < backup.sql
```

### Kết nối database bằng công cụ ngoài (DBeaver, pgAdmin...)

`Host: localhost` · `Port: 15432` · `Database: office_db` · `User: office_user` · `Password: office_password` (hoặc giá trị bạn đặt trong `.env`).

---

## 7. Cấu hình (`.env`)

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `FRONTEND_PORT` / `BACKEND_PORT` / `DB_PORT` | 18080 / 18000 / 15432 | Cổng publish ra máy host |
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | office_db / office_user / office_password | Thông tin PostgreSQL. **Chỉ có hiệu lực khi volume được tạo lần đầu** |
| `SECRET_KEY` | (mẫu) | Khóa ký JWT. **Bắt buộc đổi** khi dùng thật |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 720 | Thời hạn đăng nhập (phút) |
| `CORS_ORIGINS` | http://localhost:18080 | Danh sách origin được phép, ngăn cách bằng dấu phẩy |
| `TIMEZONE` | Asia/Ho_Chi_Minh | Múi giờ tính điểm danh |
| `WORK_START` / `WORK_END` | 08:30 / 17:30 | Giờ vào/ra chuẩn: vào sau `WORK_START` = đi muộn, ra trước `WORK_END` = về sớm |
| `SEED_DEMO_DATA` | true | `true`: tạo dữ liệu demo khi DB trống. `false`: chỉ tạo 1 tài khoản admin |
| `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` | admin@congty.vn / Admin@123 | Tài khoản admin khởi tạo |

### Triển khai thật (production) — checklist

1. Đặt `SECRET_KEY` ngẫu nhiên: `python -c "import secrets; print(secrets.token_hex(32))"`.
2. Đổi `POSTGRES_PASSWORD`, đặt `SEED_DEMO_DATA=false`, đặt `SEED_ADMIN_PASSWORD` mạnh, rồi **đăng nhập đổi mật khẩu**.
3. Bỏ publish cổng DB (xóa mục `ports` của service `db`) để chỉ backend truy cập được.
4. Đặt Nginx/Traefik có HTTPS phía trước và cập nhật `CORS_ORIGINS` theo tên miền.
5. Sao lưu định kỳ volume `office_manager_pgdata`.

---

## 8. Chạy chế độ phát triển (không build lại image)

Chạy riêng DB bằng Docker, còn backend/frontend chạy trực tiếp để có hot-reload:

```bat
:: Terminal 1 - database
docker compose up -d db

:: Terminal 2 - backend (cần Python 3.12)
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set DATABASE_URL=postgresql+psycopg2://office_user:office_password@localhost:15432/office_db
uvicorn app.main:app --reload --port 18000

:: Terminal 3 - frontend (cần Node 20+)
cd frontend
npm install
npm run dev
```

Frontend dev chạy ở http://localhost:15173 và tự proxy `/api` sang `http://localhost:18000`.

Chạy test backend (không cần PostgreSQL, dùng SQLite):

```bat
cd backend
set DATABASE_URL=sqlite:///./test.db
pip install pytest
pytest -q
```

---

## 9. Xử lý sự cố

| Triệu chứng | Nguyên nhân / Cách xử lý |
|---|---|
| `port is already allocated` / `bind: Only one usage of each socket` | Cổng đã bị dự án khác chiếm. Đổi `FRONTEND_PORT` / `BACKEND_PORT` / `DB_PORT` trong `.env` |
| Backend báo không kết nối được DB | Đợi DB `healthy` (`docker compose ps`). Xem `docker compose logs db` |
| Đổi `POSTGRES_PASSWORD` nhưng vẫn lỗi đăng nhập DB | Mật khẩu chỉ áp dụng khi tạo volume lần đầu. Chạy `docker compose down -v` (mất dữ liệu) hoặc đổi mật khẩu bằng `ALTER USER` |
| Sửa `01_schema.sql` mà bảng không đổi | Script init chỉ chạy khi volume còn trống. Dùng `docker compose down -v` hoặc tự `ALTER TABLE` |
| Trang web trắng / lỗi 502 ở `/api` | Backend chưa `healthy`: `docker compose logs backend`. Nginx dùng DNS nội bộ Docker (`127.0.0.11`) để tìm service `backend` |
| Lỗi CORS khi gọi API trực tiếp từ cổng khác | Thêm origin vào `CORS_ORIGINS` rồi `docker compose up -d backend` |
| File `.env` / config bị lỗi ký tự lạ trên Windows | Tạo/sửa bằng VS Code (UTF-8 **không BOM**), tránh PowerShell `>` ghi file UTF-16/BOM |
| `docker compose` không tìm thấy | Dùng Docker Desktop mới (có `docker compose`), hoặc thử `docker-compose` |

---

## 10. Tài liệu chi tiết

- 📘 [Backend & danh sách API](backend/README.md)
- 🎨 [Frontend](frontend/README.md)
- 🗄️ [Database](db/README.md)
