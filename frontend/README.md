# Frontend — React + Vite

Giao diện web tiếng Việt cho hệ thống Quản lý Văn phòng. Build ra file tĩnh và được **Nginx** phục vụ; Nginx đồng thời proxy `/api` sang backend.

## Công nghệ

- React 18, React Router 6, Vite 5
- Không dùng thư viện UI ngoài: CSS thuần trong `src/styles.css`
- Gọi API bằng `fetch` (`src/api.js`), lưu JWT trong `localStorage`

## Cấu trúc

```
src/
├── main.jsx           Điểm vào, BrowserRouter + AuthProvider
├── App.jsx            Định tuyến; chưa đăng nhập → trang Login
├── api.js             api.get/post/put/del, đăng nhập, tải file; tự bắt lỗi 401
├── AuthContext.jsx    user hiện tại, login/logout, cờ isAdmin / isManager / canManage
├── utils.js           Nhãn tiếng Việt, định dạng ngày giờ, hook useAsync
├── styles.css         Giao diện (sidebar, bảng, modal, responsive)
├── components/
│   ├── Layout.jsx     Sidebar + thanh trên; menu "Báo cáo" chỉ hiện với admin/manager
│   ├── FormModal.jsx  Modal biểu mẫu dùng chung, khai báo bằng mảng fields
│   └── ui.jsx         Badge, Card, PageHeader, Alert, Empty, Loading, StatCard
└── pages/
    ├── Login.jsx          Đăng nhập + nút điền sẵn tài khoản demo
    ├── Dashboard.jsx      Đồng hồ + nút Vào ca / Ra về, thẻ số liệu, thông báo mới
    ├── Attendance.jsx     Lịch sử chấm công, bộ lọc, chấm công thủ công/sửa (quản lý)
    ├── Leaves.jsx         Đơn của tôi / Cần duyệt / Tất cả, duyệt – từ chối – hủy
    ├── Tasks.jsx          Giao việc, đổi trạng thái, cảnh báo quá hạn
    ├── Rooms.jsx          Lịch đặt phòng theo ngày, đặt phòng, quản lý phòng (admin)
    ├── Assets.jsx         Tài sản, cấp phát, bảo trì
    ├── Announcements.jsx  Đăng/ghim thông báo
    ├── Employees.jsx      Hồ sơ nhân viên, phòng ban, quản lý trực tiếp (admin chỉnh sửa)
    ├── Departments.jsx    Phòng ban
    ├── Reports.jsx        Báo cáo chấm công tháng, xuất CSV, biểu đồ thanh tổng quan
    └── Profile.jsx        Thông tin cá nhân, đổi mật khẩu
```

## Hiển thị theo vai trò

Giao diện ẩn/hiện nút theo `role` (backend vẫn kiểm tra quyền lần nữa, đây chỉ là tiện lợi cho người dùng):

| Màn hình | employee | manager | admin |
|---|---|---|---|
| Tổng quan, Điểm danh, Nghỉ phép, Công việc, Phòng họp, Tài sản, Thông báo (xem) | ✅ | ✅ | ✅ |
| Duyệt nghỉ phép, giao việc, sửa chấm công, thêm tài sản, đăng thông báo | — | ✅ | ✅ |
| Báo cáo | — | ✅ | ✅ |
| Thêm/sửa nhân viên, phòng ban, phòng họp, xóa bản ghi | — | — | ✅ |

## Kết nối tới backend

- **Docker (mặc định):** Nginx proxy `/api/*`, `/docs`, `/openapi.json` sang `http://backend:8000` (xem `nginx.conf`). Trình duyệt chỉ gọi cùng origin nên không cần CORS.
- **`npm run dev`:** Vite proxy `/api` sang `http://localhost:18000` (đổi bằng biến `VITE_PROXY_TARGET`). Frontend dev chạy ở cổng **15173**.
- **Backend ở domain khác:** đặt `VITE_API_URL=https://api.example.com` khi build, và thêm origin web vào `CORS_ORIGINS` của backend.

## Chạy phát triển

```bat
cd frontend
npm install
npm run dev
```

Mở http://localhost:15173 (cần backend đang chạy ở cổng 18000, ví dụ `docker compose up -d db backend`).

## Build production

```bat
npm run build      :: tạo thư mục dist/
npm run preview    :: xem thử bản build
```

Docker build đa giai đoạn (`Dockerfile`): giai đoạn 1 chạy `npm install` + `npm run build` trong `node:20-alpine`; giai đoạn 2 chép `dist/` vào `nginx:alpine` cùng `nginx.conf`.

## Thêm một màn hình quản lý mới

1. Tạo `src/pages/TenMoi.jsx` — dùng `useAsync(() => api.get("/api/..."))` để tải dữ liệu, `PageHeader`/`Card` để bố cục.
2. Với biểu mẫu thêm/sửa, dùng `FormModal` và khai báo `fields` (kiểu `text`, `email`, `password`, `number`, `date`, `datetime-local`, `select`, `textarea`, `checkbox`). Trường `select` rỗng được gửi là `null`; `numeric: true` ép số; `omitEmpty: true` bỏ qua trường khi để trống.
3. Thêm `<Route>` trong `App.jsx` và mục menu trong `NAV` của `components/Layout.jsx`.

## Lưu ý

- Token lưu trong `localStorage` (khóa `office_token`); khi API trả 401, ứng dụng tự đăng xuất.
- Giờ hiển thị lấy trực tiếp từ chuỗi thời gian của backend (đã theo múi giờ `TIMEZONE`), không chuyển đổi theo máy người dùng.
