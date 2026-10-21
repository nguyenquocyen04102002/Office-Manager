"""Tạo dữ liệu mẫu khi database còn trống (SEED_DEMO_DATA=true)."""
from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from .config import settings
from .models import (
    Announcement,
    Asset,
    Attendance,
    Booking,
    Department,
    Employee,
    LeaveRequest,
    Room,
    Task,
)
from .security import hash_password


def seed_admin_only(db: Session) -> None:
    db.add(
        Employee(
            code="NV000",
            full_name="Quản trị viên",
            email=settings.SEED_ADMIN_EMAIL.lower(),
            hashed_password=hash_password(settings.SEED_ADMIN_PASSWORD),
            role="admin",
            position="Quản trị hệ thống",
        )
    )
    db.commit()


def seed_database(db: Session) -> None:
    if db.query(Employee).count() > 0:
        return
    if not settings.SEED_DEMO_DATA:
        seed_admin_only(db)
        return

    deps = {
        name: Department(name=name, description=desc)
        for name, desc in [
            ("Ban Giám đốc", "Điều hành và định hướng chiến lược"),
            ("Hành chính - Nhân sự", "Tuyển dụng, chấm công, hành chính văn phòng"),
            ("Kế toán", "Tài chính, kế toán, thuế"),
            ("Kinh doanh", "Bán hàng và chăm sóc khách hàng"),
            ("Kỹ thuật", "Phát triển sản phẩm và hạ tầng IT"),
        ]
    }
    db.add_all(deps.values())
    db.flush()

    def make(code, name, email, role, position, dep, manager=None, password="Nhanvien@123", hired=None, gender=None, phone=None):
        e = Employee(
            code=code,
            full_name=name,
            email=email,
            hashed_password=hash_password(password),
            role=role,
            position=position,
            department_id=deps[dep].id,
            manager_id=manager.id if manager else None,
            hire_date=hired or date(2024, 1, 15),
            gender=gender,
            phone=phone,
        )
        db.add(e)
        db.flush()
        return e

    admin = make("NV000", "Quản trị viên", settings.SEED_ADMIN_EMAIL.lower(), "admin", "Giám đốc", "Ban Giám đốc",
                 password=settings.SEED_ADMIN_PASSWORD, gender="Nam", phone="0900000000")
    hr = make("NV001", "Nguyễn Thị Lan", "lan.nguyen@congty.vn", "manager", "Trưởng phòng Hành chính - Nhân sự",
              "Hành chính - Nhân sự", admin, password="Quanly@123", gender="Nữ", phone="0901111111")
    kt = make("NV002", "Trần Văn Hùng", "hung.tran@congty.vn", "manager", "Kế toán trưởng", "Kế toán", admin,
              password="Quanly@123", gender="Nam", phone="0902222222")
    kd = make("NV003", "Lê Minh Tuấn", "tuan.le@congty.vn", "manager", "Trưởng phòng Kinh doanh", "Kinh doanh", admin,
              password="Quanly@123", gender="Nam", phone="0903333333")
    kyth = make("NV004", "Phạm Quốc Bảo", "bao.pham@congty.vn", "manager", "Trưởng nhóm Kỹ thuật", "Kỹ thuật", admin,
                password="Quanly@123", gender="Nam", phone="0904444444")
    staff = [
        make("NV005", "Võ Thu Hà", "ha.vo@congty.vn", "employee", "Chuyên viên nhân sự", "Hành chính - Nhân sự", hr, gender="Nữ"),
        make("NV006", "Đặng Ngọc Mai", "mai.dang@congty.vn", "employee", "Kế toán viên", "Kế toán", kt, gender="Nữ"),
        make("NV007", "Hoàng Gia Khang", "khang.hoang@congty.vn", "employee", "Nhân viên kinh doanh", "Kinh doanh", kd, gender="Nam"),
        make("NV008", "Bùi Thanh Thảo", "thao.bui@congty.vn", "employee", "Nhân viên kinh doanh", "Kinh doanh", kd, gender="Nữ"),
        make("NV009", "Ngô Đức Anh", "anh.ngo@congty.vn", "employee", "Lập trình viên", "Kỹ thuật", kyth, gender="Nam"),
        make("NV010", "Đỗ Khánh Linh", "linh.do@congty.vn", "employee", "Lập trình viên", "Kỹ thuật", kyth, gender="Nữ"),
    ]

    # Chấm công 7 ngày làm việc gần nhất
    everyone = [hr, kt, kd, kyth] + staff
    today = datetime.now().date()
    day, filled = today - timedelta(days=1), 0
    while filled < 7:
        if day.weekday() < 5:
            for i, e in enumerate(everyone):
                late = (i + day.day) % 5 == 0
                early = (i + day.day) % 7 == 0
                cin = datetime.combine(day, time(8, 45 if late else 20 + (i % 8)))
                cout = datetime.combine(day, time(16, 40 if early else 17 + (i % 3), 0 if early else 40))
                if late and early:
                    st = "late_early"
                elif late:
                    st = "late"
                elif early:
                    st = "early_leave"
                else:
                    st = "present"
                db.add(Attendance(employee_id=e.id, work_date=day, check_in=cin, check_out=cout, status=st))
            filled += 1
        day -= timedelta(days=1)

    # Đơn nghỉ phép
    db.add(LeaveRequest(employee_id=staff[3].id, leave_type="annual", start_date=today + timedelta(days=3),
                        end_date=today + timedelta(days=4), days=2, reason="Việc gia đình", status="pending"))
    db.add(LeaveRequest(employee_id=staff[4].id, leave_type="sick", start_date=today - timedelta(days=20),
                        end_date=today - timedelta(days=20), days=1, reason="Khám sức khỏe", status="approved",
                        reviewer_id=kyth.id, review_note="Đồng ý"))

    # Công việc
    db.add_all([
        Task(title="Chuẩn bị báo cáo doanh thu quý", description="Tổng hợp số liệu bán hàng quý hiện tại",
             assignee_id=staff[2].id, creator_id=kd.id, priority="high", status="in_progress", due_date=today + timedelta(days=5)),
        Task(title="Cập nhật hồ sơ nhân sự", assignee_id=staff[0].id, creator_id=hr.id, priority="medium",
             status="todo", due_date=today + timedelta(days=7)),
        Task(title="Đối soát công nợ tháng", assignee_id=staff[1].id, creator_id=kt.id, priority="high",
             status="todo", due_date=today + timedelta(days=2)),
        Task(title="Triển khai tính năng đăng nhập", assignee_id=staff[4].id, creator_id=kyth.id, priority="medium",
             status="done", due_date=today - timedelta(days=1)),
    ])

    # Tài sản
    db.add_all([
        Asset(code="TS-LAP-001", name="Laptop Dell Latitude 5440", category="Máy tính", status="in_use",
              assigned_to_id=staff[4].id, purchase_date=date(2024, 3, 10)),
        Asset(code="TS-LAP-002", name="Laptop Dell Latitude 5440", category="Máy tính", status="in_use",
              assigned_to_id=staff[5].id, purchase_date=date(2024, 3, 10)),
        Asset(code="TS-MON-001", name="Màn hình LG 24 inch", category="Thiết bị ngoại vi", status="available",
              purchase_date=date(2023, 11, 2)),
        Asset(code="TS-PRN-001", name="Máy in HP LaserJet Pro", category="Thiết bị văn phòng", status="maintenance",
              purchase_date=date(2022, 6, 20), note="Đang thay trống mực"),
        Asset(code="TS-PRJ-001", name="Máy chiếu Epson", category="Thiết bị văn phòng", status="available",
              purchase_date=date(2023, 1, 12)),
    ])

    # Phòng họp
    r1 = Room(name="Phòng họp A", capacity=10, location="Tầng 2", equipment="Máy chiếu, bảng trắng")
    r2 = Room(name="Phòng họp B", capacity=6, location="Tầng 2", equipment="TV 55 inch")
    r3 = Room(name="Phòng đào tạo", capacity=30, location="Tầng 3", equipment="Máy chiếu, micro, loa")
    db.add_all([r1, r2, r3])
    db.flush()
    start = datetime.combine(today, time(14, 0))
    db.add(Booking(room_id=r1.id, employee_id=kd.id, title="Họp kinh doanh tuần",
                   start_time=start, end_time=start + timedelta(hours=1, minutes=30)))

    # Thông báo
    db.add_all([
        Announcement(title="Chào mừng đến với hệ thống quản lý văn phòng", pinned=True, author_id=admin.id,
                     content="Vui lòng điểm danh hằng ngày, gửi đơn nghỉ phép trước ít nhất 1 ngày và cập nhật tiến độ công việc."),
        Announcement(title="Lịch nghỉ lễ sắp tới", author_id=hr.id,
                     content="Phòng Hành chính - Nhân sự sẽ thông báo lịch nghỉ lễ chi tiết qua email."),
    ])
    db.commit()
