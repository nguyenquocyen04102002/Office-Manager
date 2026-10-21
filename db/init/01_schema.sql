-- =============================================================================
-- Schema PostgreSQL - Hệ thống Quản lý Văn phòng
-- Tự động chạy ở lần khởi tạo volume đầu tiên (docker-entrypoint-initdb.d).
-- Backend (SQLAlchemy) dùng cùng cấu trúc và chỉ tạo bảng nếu còn thiếu.
-- =============================================================================

CREATE TABLE IF NOT EXISTS departments (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(120) NOT NULL UNIQUE,
    description TEXT,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS employees (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(30)  NOT NULL UNIQUE,
    full_name       VARCHAR(150) NOT NULL,
    email           VARCHAR(190) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role            VARCHAR(20)  NOT NULL DEFAULT 'employee'
                    CHECK (role IN ('admin', 'manager', 'employee')),
    phone           VARCHAR(30),
    gender          VARCHAR(10),
    address         VARCHAR(255),
    position        VARCHAR(120),
    department_id   INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    manager_id      INTEGER REFERENCES employees(id)   ON DELETE SET NULL,
    hire_date       DATE,
    status          VARCHAR(20)  NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'inactive')),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_employees_department ON employees(department_id);
CREATE INDEX IF NOT EXISTS ix_employees_manager    ON employees(manager_id);

CREATE TABLE IF NOT EXISTS attendances (
    id          SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    work_date   DATE    NOT NULL,
    check_in    TIMESTAMP,
    check_out   TIMESTAMP,
    status      VARCHAR(20) NOT NULL DEFAULT 'present'
                CHECK (status IN ('present', 'late', 'early_leave', 'late_early', 'leave', 'absent')),
    note        VARCHAR(255),
    CONSTRAINT uq_attendance_employee_date UNIQUE (employee_id, work_date)
);
CREATE INDEX IF NOT EXISTS ix_attendances_date ON attendances(work_date);

CREATE TABLE IF NOT EXISTS leave_requests (
    id          SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    leave_type  VARCHAR(30) NOT NULL DEFAULT 'annual',
    start_date  DATE NOT NULL,
    end_date    DATE NOT NULL,
    days        NUMERIC(5,1) NOT NULL DEFAULT 1,
    reason      TEXT,
    status      VARCHAR(20) NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'approved', 'rejected')),
    reviewer_id INTEGER REFERENCES employees(id) ON DELETE SET NULL,
    review_note VARCHAR(255),
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    CHECK (end_date >= start_date)
);

CREATE TABLE IF NOT EXISTS tasks (
    id          SERIAL PRIMARY KEY,
    title       VARCHAR(200) NOT NULL,
    description TEXT,
    assignee_id INTEGER REFERENCES employees(id) ON DELETE SET NULL,
    creator_id  INTEGER REFERENCES employees(id) ON DELETE SET NULL,
    priority    VARCHAR(20) NOT NULL DEFAULT 'medium'
                CHECK (priority IN ('low', 'medium', 'high')),
    status      VARCHAR(20) NOT NULL DEFAULT 'todo'
                CHECK (status IN ('todo', 'in_progress', 'done')),
    due_date    DATE,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS assets (
    id             SERIAL PRIMARY KEY,
    code           VARCHAR(40)  NOT NULL UNIQUE,
    name           VARCHAR(150) NOT NULL,
    category       VARCHAR(80),
    status         VARCHAR(20)  NOT NULL DEFAULT 'available'
                   CHECK (status IN ('available', 'in_use', 'maintenance', 'retired')),
    assigned_to_id INTEGER REFERENCES employees(id) ON DELETE SET NULL,
    purchase_date  DATE,
    note           VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS rooms (
    id        SERIAL PRIMARY KEY,
    name      VARCHAR(100) NOT NULL UNIQUE,
    capacity  INTEGER NOT NULL DEFAULT 4,
    location  VARCHAR(150),
    equipment VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS bookings (
    id          SERIAL PRIMARY KEY,
    room_id     INTEGER NOT NULL REFERENCES rooms(id)     ON DELETE CASCADE,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    title       VARCHAR(200) NOT NULL,
    start_time  TIMESTAMP NOT NULL,
    end_time    TIMESTAMP NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    CHECK (end_time > start_time)
);
CREATE INDEX IF NOT EXISTS ix_bookings_room_time ON bookings(room_id, start_time, end_time);

CREATE TABLE IF NOT EXISTS announcements (
    id         SERIAL PRIMARY KEY,
    title      VARCHAR(200) NOT NULL,
    content    TEXT NOT NULL,
    author_id  INTEGER REFERENCES employees(id) ON DELETE SET NULL,
    pinned     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
