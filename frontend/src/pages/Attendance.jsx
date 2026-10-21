import { useMemo, useState } from "react";
import { api } from "../api";
import { useAuth } from "../AuthContext.jsx";
import FormModal from "../components/FormModal.jsx";
import { Badge, Card, Empty, Loading, PageHeader } from "../components/ui.jsx";
import { fmtDate, fmtTime, LABELS, options, toInputDateTime, todayStr, useAsync } from "../utils";

function monthStart() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-01`;
}

export default function Attendance() {
  const { canManage, isAdmin } = useAuth();
  const [from, setFrom] = useState(monthStart());
  const [to, setTo] = useState(todayStr());
  const [employeeId, setEmployeeId] = useState("");
  const [status, setStatus] = useState("");
  const [modal, setModal] = useState(null);
  const [msg, setMsg] = useState("");

  const { data: team } = useAsync(() => (canManage ? api.get("/api/employees/team") : Promise.resolve([])), [canManage]);
  const { data, loading, error, reload } = useAsync(
    () => api.get("/api/attendance", { date_from: from, date_to: to, employee_id: employeeId, status }),
    [from, to, employeeId, status]
  );

  const fields = useMemo(
    () => [
      ...(modal?.id
        ? []
        : [
            {
              name: "employee_id", label: "Nhân viên", type: "select", required: true, numeric: true,
              options: (team || []).map((e) => ({ value: e.id, label: `${e.full_name} (${e.code})` })),
            },
            { name: "work_date", label: "Ngày làm việc", type: "date", required: true, defaultValue: todayStr() },
          ]),
      { name: "check_in", label: "Giờ vào", type: "datetime-local" },
      { name: "check_out", label: "Giờ ra", type: "datetime-local" },
      { name: "status", label: "Trạng thái (bỏ trống để tự tính)", type: "select", options: options(LABELS.attendance) },
      { name: "note", label: "Ghi chú", span: 2 },
    ],
    [modal, team]
  );

  const remove = async (a) => {
    if (!window.confirm("Xóa bản ghi chấm công này?")) return;
    try {
      await api.del(`/api/attendance/${a.id}`);
      reload();
    } catch (e) {
      setMsg(e.message);
    }
  };

  return (
    <>
      <PageHeader title="Điểm danh" subtitle="Lịch sử chấm công theo phạm vi quản lý của bạn">
        {canManage && <button className="btn primary" onClick={() => setModal({})}>+ Chấm công thủ công</button>}
      </PageHeader>
      <p className="muted" style={{ marginTop: -8, marginBottom: 12 }}>
        Để điểm danh vào ca / ra về hãy dùng nút ở trang Tổng quan.
      </p>
      <div className="filters">
        <label>Từ ngày <input type="date" value={from} onChange={(e) => setFrom(e.target.value)} /></label>
        <label>Đến ngày <input type="date" value={to} onChange={(e) => setTo(e.target.value)} /></label>
        {canManage && (
          <select value={employeeId} onChange={(e) => setEmployeeId(e.target.value)}>
            <option value="">Tất cả nhân viên</option>
            {(team || []).map((e) => <option key={e.id} value={e.id}>{e.full_name}</option>)}
          </select>
        )}
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">Mọi trạng thái</option>
          {options(LABELS.attendance).map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </div>
      {msg && <div className="alert red">{msg}</div>}
      <Card>
        <Loading loading={loading} error={error}>
          {data?.length ? (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>Ngày</th><th>Nhân viên</th><th>Giờ vào</th><th>Giờ ra</th><th>Trạng thái</th><th>Ghi chú</th>{canManage && <th></th>}</tr>
                </thead>
                <tbody>
                  {data.map((a) => (
                    <tr key={a.id}>
                      <td>{fmtDate(a.work_date)}</td>
                      <td>{a.employee_name} <small className="muted">{a.employee_code}</small></td>
                      <td>{fmtTime(a.check_in)}</td>
                      <td>{fmtTime(a.check_out)}</td>
                      <td><Badge value={a.status} label={LABELS.attendance[a.status]} /></td>
                      <td className="wrap">{a.note || ""}</td>
                      {canManage && (
                        <td>
                          <div className="row-actions">
                            <button className="btn sm" onClick={() => setModal(a)}>Sửa</button>
                            {isAdmin && <button className="btn sm danger" onClick={() => remove(a)}>Xóa</button>}
                          </div>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <Empty>Không có bản ghi trong khoảng thời gian này</Empty>
          )}
        </Loading>
      </Card>
      {modal && (
        <FormModal
          key={modal.id || "new"}
          title={modal.id ? `Sửa chấm công ${fmtDate(modal.work_date)} — ${modal.employee_name}` : "Chấm công thủ công"}
          fields={fields}
          initial={{ ...modal, check_in: toInputDateTime(modal.check_in), check_out: toInputDateTime(modal.check_out) }}
          onClose={() => setModal(null)}
          onSubmit={async (v) => {
            if (modal.id) await api.put(`/api/attendance/${modal.id}`, v);
            else await api.post("/api/attendance", v);
            reload();
          }}
        />
      )}
    </>
  );
}
