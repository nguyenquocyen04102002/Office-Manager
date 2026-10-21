import { useState } from "react";
import { api } from "../api";
import { useAuth } from "../AuthContext.jsx";
import { Alert, Badge, Card, PageHeader } from "../components/ui.jsx";
import { fmtDate, LABELS, ROLE_LABEL } from "../utils";

export default function Profile() {
  const { user } = useAuth();
  const [form, setForm] = useState({ old_password: "", new_password: "", confirm: "" });
  const [msg, setMsg] = useState({ tone: "green", text: "" });

  const submit = async (e) => {
    e.preventDefault();
    if (form.new_password !== form.confirm) return setMsg({ tone: "red", text: "Mật khẩu xác nhận không khớp" });
    try {
      await api.post("/api/auth/change-password", { old_password: form.old_password, new_password: form.new_password });
      setMsg({ tone: "green", text: "Đổi mật khẩu thành công" });
      setForm({ old_password: "", new_password: "", confirm: "" });
    } catch (err) {
      setMsg({ tone: "red", text: err.message });
    }
  };

  const rows = [
    ["Mã nhân viên", user.code],
    ["Email", user.email],
    ["Vai trò", ROLE_LABEL[user.role]],
    ["Chức vụ", user.position || "—"],
    ["Phòng ban", user.department_name || "—"],
    ["Quản lý trực tiếp", user.manager_name || "—"],
    ["Số điện thoại", user.phone || "—"],
    ["Ngày vào làm", fmtDate(user.hire_date)],
  ];

  return (
    <>
      <PageHeader title="Tài khoản của tôi" />
      <div className="grid cols-2">
        <Card title="Thông tin cá nhân">
          <table>
            <tbody>
              {rows.map(([k, v]) => (
                <tr key={k}>
                  <th style={{ width: 160 }}>{k}</th>
                  <td>{v}</td>
                </tr>
              ))}
              <tr>
                <th>Trạng thái</th>
                <td><Badge value={user.status} label={LABELS.empStatus[user.status]} /></td>
              </tr>
            </tbody>
          </table>
        </Card>
        <Card title="Đổi mật khẩu">
          <form onSubmit={submit} className="grid">
            <label className="field"><span>Mật khẩu hiện tại</span>
              <input type="password" required value={form.old_password} onChange={(e) => setForm({ ...form, old_password: e.target.value })} />
            </label>
            <label className="field"><span>Mật khẩu mới (tối thiểu 6 ký tự)</span>
              <input type="password" required minLength={6} value={form.new_password} onChange={(e) => setForm({ ...form, new_password: e.target.value })} />
            </label>
            <label className="field"><span>Nhập lại mật khẩu mới</span>
              <input type="password" required value={form.confirm} onChange={(e) => setForm({ ...form, confirm: e.target.value })} />
            </label>
            <Alert tone={msg.tone}>{msg.text}</Alert>
            <button className="btn primary">Cập nhật mật khẩu</button>
          </form>
        </Card>
      </div>
    </>
  );
}
