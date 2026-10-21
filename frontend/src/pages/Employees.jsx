import { useMemo, useState } from "react";
import { api } from "../api";
import { useAuth } from "../AuthContext.jsx";
import FormModal from "../components/FormModal.jsx";
import { Badge, Card, Empty, Loading, PageHeader } from "../components/ui.jsx";
import { LABELS, options, ROLE_LABEL, useAsync } from "../utils";

export default function Employees() {
  const { isAdmin } = useAuth();
  const [q, setQ] = useState("");
  const [dep, setDep] = useState("");
  const [status, setStatus] = useState("active");
  const [modal, setModal] = useState(null);
  const [msg, setMsg] = useState("");

  const { data: deps } = useAsync(() => api.get("/api/departments"), []);
  const { data: allEmployees, reload: reloadAll } = useAsync(() => api.get("/api/employees"), []);
  const { data, loading, error, reload } = useAsync(
    () => api.get("/api/employees", { q, department_id: dep, status }),
    [q, dep, status]
  );

  const refresh = () => {
    reload();
    reloadAll();
  };

  const fields = useMemo(() => {
    const editing = !!modal?.id;
    return [
      { name: "code", label: "Mã nhân viên", required: true },
      { name: "full_name", label: "Họ và tên", required: true },
      { name: "email", label: "Email (dùng để đăng nhập)", type: "email", required: true },
      {
        name: "password",
        label: editing ? "Mật khẩu mới (bỏ trống nếu không đổi)" : "Mật khẩu",
        type: "password",
        required: !editing,
        omitEmpty: true,
      },
      { name: "role", label: "Vai trò", type: "select", required: true, options: options(ROLE_LABEL), defaultValue: "employee" },
      { name: "status", label: "Trạng thái", type: "select", required: true, options: options(LABELS.empStatus), defaultValue: "active" },
      { name: "position", label: "Chức vụ" },
      { name: "phone", label: "Số điện thoại" },
      { name: "gender", label: "Giới tính", type: "select", options: [{ value: "Nam", label: "Nam" }, { value: "Nữ", label: "Nữ" }, { value: "Khác", label: "Khác" }] },
      { name: "hire_date", label: "Ngày vào làm", type: "date" },
      {
        name: "department_id", label: "Phòng ban", type: "select", numeric: true,
        options: (deps || []).map((d) => ({ value: d.id, label: d.name })),
      },
      {
        name: "manager_id", label: "Quản lý trực tiếp", type: "select", numeric: true,
        options: (allEmployees || [])
          .filter((e) => e.id !== modal?.id && e.status === "active" && e.role !== "employee")
          .map((e) => ({ value: e.id, label: `${e.full_name} (${e.code})` })),
      },
      { name: "address", label: "Địa chỉ", span: 2 },
    ];
  }, [modal, deps, allEmployees]);

  const deactivate = async (e) => {
    if (!window.confirm(`Cho nhân viên "${e.full_name}" nghỉ việc? Tài khoản sẽ bị khóa, dữ liệu chấm công vẫn được giữ.`)) return;
    try {
      await api.del(`/api/employees/${e.id}`);
      refresh();
    } catch (err) {
      setMsg(err.message);
    }
  };

  return (
    <>
      <PageHeader title="Nhân viên" subtitle="Hồ sơ nhân sự và cấp quản lý">
        {isAdmin && <button className="btn primary" onClick={() => setModal({})}>+ Thêm nhân viên</button>}
      </PageHeader>
      <div className="filters">
        <input placeholder="Tìm theo tên, mã, email..." value={q} onChange={(e) => setQ(e.target.value)} />
        <select value={dep} onChange={(e) => setDep(e.target.value)}>
          <option value="">Tất cả phòng ban</option>
          {(deps || []).map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">Mọi trạng thái</option>
          {options(LABELS.empStatus).map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </div>
      {msg && <div className="alert red">{msg}</div>}
      <Card>
        <Loading loading={loading} error={error}>
          {data?.length ? (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Mã</th><th>Họ tên</th><th>Chức vụ</th><th>Phòng ban</th><th>Quản lý</th>
                    <th>Liên hệ</th><th>Vai trò</th><th>Trạng thái</th>{isAdmin && <th></th>}
                  </tr>
                </thead>
                <tbody>
                  {data.map((e) => (
                    <tr key={e.id}>
                      <td>{e.code}</td>
                      <td><strong>{e.full_name}</strong></td>
                      <td>{e.position || "—"}</td>
                      <td>{e.department_name || "—"}</td>
                      <td>{e.manager_name || "—"}</td>
                      <td>{e.email}<br /><small className="muted">{e.phone}</small></td>
                      <td><Badge value={e.role} label={ROLE_LABEL[e.role]} /></td>
                      <td><Badge value={e.status} label={LABELS.empStatus[e.status]} /></td>
                      {isAdmin && (
                        <td>
                          <div className="row-actions">
                            <button className="btn sm" onClick={() => setModal(e)}>Sửa</button>
                            {e.status === "active" && <button className="btn sm danger" onClick={() => deactivate(e)}>Nghỉ việc</button>}
                          </div>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <Empty>Không tìm thấy nhân viên</Empty>
          )}
        </Loading>
      </Card>
      {modal && (
        <FormModal
          key={modal.id || "new"}
          title={modal.id ? `Sửa nhân viên: ${modal.full_name}` : "Thêm nhân viên"}
          fields={fields}
          initial={modal}
          onClose={() => setModal(null)}
          onSubmit={async (v) => {
            if (modal.id) await api.put(`/api/employees/${modal.id}`, v);
            else await api.post("/api/employees", v);
            refresh();
          }}
        />
      )}
    </>
  );
}
