"""Smoke test toàn bộ API bằng SQLite (không cần PostgreSQL).

Chạy:  cd backend && DATABASE_URL=sqlite:///./test.db pytest -q
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

from datetime import datetime, timedelta  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


def login(client, email, password):
    r = client.post("/api/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_full_flow():
    Base.metadata.drop_all(bind=engine)
    with TestClient(app) as c:
        assert c.get("/api/health").json() == {"status": "ok"}

        admin = login(c, "admin@congty.vn", "Admin@123")
        manager = login(c, "tuan.le@congty.vn", "Quanly@123")
        staff = login(c, "khang.hoang@congty.vn", "Nhanvien@123")

        assert c.post("/api/auth/login", data={"username": "admin@congty.vn", "password": "sai"}).status_code == 401
        assert c.get("/api/employees").status_code == 401

        me = c.get("/api/auth/me", headers=admin).json()
        assert me["role"] == "admin"

        # Phòng ban + nhân viên
        deps = c.get("/api/departments", headers=admin).json()
        assert len(deps) == 5
        r = c.post("/api/departments", json={"name": "Pháp chế"}, headers=admin)
        assert r.status_code == 201
        assert c.post("/api/departments", json={"name": "Pháp chế"}, headers=admin).status_code == 400
        assert c.post("/api/departments", json={"name": "X"}, headers=staff).status_code == 403

        r = c.post(
            "/api/employees",
            json={"code": "NV100", "full_name": "Nhân viên Mới", "email": "moi@congty.vn", "password": "Matkhau1", "department_id": r.json()["id"]},
            headers=admin,
        )
        assert r.status_code == 201, r.text
        new_id = r.json()["id"]
        assert c.put(f"/api/employees/{new_id}", json={"position": "Pháp chế viên"}, headers=admin).json()["position"] == "Pháp chế viên"
        assert c.get("/api/employees?q=Mới", headers=staff).json()[0]["code"] == "NV100"

        # Điểm danh
        assert c.get("/api/attendance/today", headers=staff).json() is None
        r = c.post("/api/attendance/check-in", headers=staff)
        assert r.status_code == 200, r.text
        assert c.post("/api/attendance/check-in", headers=staff).status_code == 400
        assert c.post("/api/attendance/check-out", headers=staff).status_code == 200
        assert c.get("/api/attendance/today", headers=staff).json()["check_out"] is not None
        assert len(c.get("/api/attendance", headers=manager).json()) > 0

        # Sửa chấm công (status rỗng -> tự tính lại, không được gây lỗi)
        att = c.get("/api/attendance/today", headers=staff).json()
        r = c.put(f"/api/attendance/{att['id']}", json={"status": None, "note": "Đã chỉnh"}, headers=manager)
        assert r.status_code == 200 and r.json()["note"] == "Đã chỉnh", r.text
        assert c.put(f"/api/attendance/{att['id']}", json={"note": "x"}, headers=staff).status_code == 403

        # Nghỉ phép: nhân viên gửi, quản lý duyệt
        start = datetime.now().date() + timedelta(days=30)
        r = c.post("/api/leaves", json={"leave_type": "annual", "start_date": str(start), "end_date": str(start + timedelta(days=2))}, headers=staff)
        assert r.status_code == 201, r.text
        leave_id = r.json()["id"]
        assert c.put(f"/api/leaves/{leave_id}/review", json={"approve": True}, headers=staff).status_code == 403
        r = c.put(f"/api/leaves/{leave_id}/review", json={"approve": True, "review_note": "OK"}, headers=manager)
        assert r.status_code == 200 and r.json()["status"] == "approved"

        # Công việc
        me_staff = c.get("/api/auth/me", headers=staff).json()
        r = c.post("/api/tasks", json={"title": "Việc thử", "assignee_id": me_staff["id"]}, headers=manager)
        assert r.status_code == 201, r.text
        task_id = r.json()["id"]
        assert c.put(f"/api/tasks/{task_id}", json={"status": "done"}, headers=staff).json()["status"] == "done"
        assert c.put(f"/api/tasks/{task_id}", json={"title": "Đổi"}, headers=staff).status_code == 403
        assert c.post("/api/tasks", json={"title": "x"}, headers=staff).status_code == 403

        # Tài sản
        r = c.post("/api/assets", json={"code": "TS-T1", "name": "Bàn", "assigned_to_id": me_staff["id"]}, headers=manager)
        assert r.status_code == 201 and r.json()["status"] == "in_use"

        # Phòng họp: chống trùng lịch
        rooms = c.get("/api/rooms", headers=staff).json()
        t0 = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=2)
        body = {"room_id": rooms[0]["id"], "title": "Họp", "start_time": t0.isoformat(), "end_time": (t0 + timedelta(hours=1)).isoformat()}
        assert c.post("/api/bookings", json=body, headers=staff).status_code == 201
        assert c.post("/api/bookings", json=body, headers=manager).status_code == 409

        # Thông báo
        assert c.post("/api/announcements", json={"title": "A", "content": "B"}, headers=staff).status_code == 403
        assert c.post("/api/announcements", json={"title": "A", "content": "B"}, headers=manager).status_code == 201

        # Báo cáo + dashboard
        rep = c.get("/api/reports/attendance-monthly", headers=manager).json()
        assert rep["rows"]
        assert c.get("/api/reports/attendance-monthly", headers=staff).status_code == 403
        csv_resp = c.get("/api/reports/attendance-monthly/export", headers=admin)
        assert csv_resp.status_code == 200 and "Mã NV" in csv_resp.content.decode("utf-8-sig")
        assert "employees_by_department" in c.get("/api/reports/overview", headers=admin).json()
        stats = c.get("/api/dashboard/stats", headers=admin).json()
        assert stats["total_employees"] >= 11
        assert c.get("/api/dashboard/stats", headers=staff).json()["scope"] == "me"
