import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext.jsx";
import { ROLE_LABEL } from "../utils";

const NAV = [
  { to: "/", label: "Tổng quan", icon: "▦", end: true },
  { to: "/attendance", label: "Điểm danh", icon: "◔" },
  { to: "/leaves", label: "Nghỉ phép", icon: "✈" },
  { to: "/tasks", label: "Công việc", icon: "☑" },
  { to: "/rooms", label: "Phòng họp", icon: "▣" },
  { to: "/assets", label: "Tài sản", icon: "⚙" },
  { to: "/announcements", label: "Thông báo", icon: "✉" },
  { to: "/employees", label: "Nhân viên", icon: "☺" },
  { to: "/departments", label: "Phòng ban", icon: "▤" },
  { to: "/reports", label: "Báo cáo", icon: "▥", manage: true },
];

export default function Layout({ children }) {
  const { user, logout, canManage } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  return (
    <div className="shell">
      <aside className={`sidebar ${open ? "open" : ""}`}>
        <div className="brand">
          <span className="logo">QL</span>
          <div>
            <strong>Quản lý Văn phòng</strong>
            <small>Office Manager</small>
          </div>
        </div>
        <nav onClick={() => setOpen(false)}>
          {NAV.filter((n) => !n.manage || canManage).map((n) => (
            <NavLink key={n.to} to={n.to} end={n.end} className={({ isActive }) => (isActive ? "active" : "")}>
              <span className="nav-icon">{n.icon}</span>
              {n.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="main">
        <header className="topbar">
          <button className="icon-btn menu-btn" onClick={() => setOpen((o) => !o)} aria-label="Menu">
            ☰
          </button>
          <div className="spacer" />
          <button className="user-chip" onClick={() => navigate("/profile")} title="Tài khoản của tôi">
            <span className="avatar">{user.full_name.split(" ").pop()[0]}</span>
            <span>
              <strong>{user.full_name}</strong>
              <small>{ROLE_LABEL[user.role]}</small>
            </span>
          </button>
          <button className="btn ghost" onClick={logout}>
            Đăng xuất
          </button>
        </header>
        <main className="content">{children}</main>
      </div>
    </div>
  );
}
