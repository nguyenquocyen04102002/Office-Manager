import { useState } from "react";
import { useAuth } from "../AuthContext.jsx";
import { Alert } from "../components/ui.jsx";

const DEMO = [
  { label: "Quản trị viên", email: "admin@congty.vn", password: "Admin@123" },
  { label: "Quản lý (Trưởng phòng Kinh doanh)", email: "tuan.le@congty.vn", password: "Quanly@123" },
  { label: "Nhân viên", email: "khang.hoang@congty.vn", password: "Nhanvien@123" },
];

export default function Login() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(email, password);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={submit}>
        <h1>Quản lý Văn phòng</h1>
        <p className="muted">Đăng nhập để tiếp tục</p>
        <label className="field">
          <span>Email</span>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus />
        </label>
        <label className="field">
          <span>Mật khẩu</span>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </label>
        <Alert>{error}</Alert>
        <button className="btn primary" disabled={busy}>
          {busy ? "Đang đăng nhập..." : "Đăng nhập"}
        </button>
        <div className="demo-box">
          Tài khoản demo (bấm để điền sẵn):
          {DEMO.map((d) => (
            <button type="button" key={d.email} onClick={() => { setEmail(d.email); setPassword(d.password); }}>
              <strong>{d.label}</strong> — {d.email}
            </button>
          ))}
        </div>
      </form>
    </div>
  );
}
