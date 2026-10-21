import { useState } from "react";
import { api } from "../api";
import { useAuth } from "../AuthContext.jsx";
import FormModal from "../components/FormModal.jsx";
import { Badge, Card, Empty, Loading, PageHeader } from "../components/ui.jsx";
import { fmtDate, LABELS, options, todayStr, useAsync } from "../utils";

const FIELDS = [
  { name: "leave_type", label: "Loại nghỉ", type: "select", required: true, options: options(LABELS.leaveType), defaultValue: "annual" },
  { name: "start_date", label: "Từ ngày", type: "date", required: true, defaultValue: todayStr() },
  { name: "end_date", label: "Đến ngày", type: "date", required: true, defaultValue: todayStr() },
  { name: "reason", label: "Lý do", type: "textarea" },
];

export default function Leaves() {
  const { canManage, user } = useAuth();
  const [tab, setTab] = useState("mine");
  const [modal, setModal] = useState(false);
  const [msg, setMsg] = useState("");
  const { data, loading, error, reload } = useAsync(
    () => api.get("/api/leaves", tab === "mine" ? { mine: true } : { status: tab === "pending" ? "pending" : "" }),
    [tab]
  );

  const review = async (leave, approve) => {
    const note = window.prompt(approve ? "Ghi chú duyệt (không bắt buộc):" : "Lý do từ chối:", "");
    if (note === null) return;
    try {
      await api.put(`/api/leaves/${leave.id}/review`, { approve, review_note: note || null });
      reload();
    } catch (e) {
      setMsg(e.message);
    }
  };

  const cancel = async (leave) => {
    if (!window.confirm("Hủy đơn nghỉ phép này?")) return;
    try {
      await api.del(`/api/leaves/${leave.id}`);
      reload();
    } catch (e) {
      setMsg(e.message);
    }
  };

  const tabs = [["mine", "Đơn của tôi"], ...(canManage ? [["pending", "Cần duyệt"], ["all", "Tất cả đơn"]] : [])];

  return (
    <>
      <PageHeader title="Nghỉ phép" subtitle="Gửi đơn và duyệt đơn nghỉ phép (chỉ tính ngày làm việc T2–T6)">
        <button className="btn primary" onClick={() => setModal(true)}>+ Tạo đơn nghỉ phép</button>
      </PageHeader>
      <div className="tabs">
        {tabs.map(([k, label]) => (
          <button key={k} className={`tab ${tab === k ? "active" : ""}`} onClick={() => setTab(k)}>{label}</button>
        ))}
      </div>
      {msg && <div className="alert red">{msg}</div>}
      <Card>
        <Loading loading={loading} error={error}>
          {data?.length ? (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>Nhân viên</th><th>Loại</th><th>Từ ngày</th><th>Đến ngày</th><th className="num">Số ngày</th><th>Lý do</th><th>Trạng thái</th><th>Người duyệt</th><th></th></tr>
                </thead>
                <tbody>
                  {data.map((l) => (
                    <tr key={l.id}>
                      <td><strong>{l.employee_name}</strong></td>
                      <td>{LABELS.leaveType[l.leave_type]}</td>
                      <td>{fmtDate(l.start_date)}</td>
                      <td>{fmtDate(l.end_date)}</td>
                      <td className="num">{l.days}</td>
                      <td className="wrap">{l.reason || "—"}</td>
                      <td><Badge value={l.status} label={LABELS.leaveStatus[l.status]} /></td>
                      <td className="wrap">{l.reviewer_name || "—"}{l.review_note && <><br /><small className="muted">{l.review_note}</small></>}</td>
                      <td>
                        <div className="row-actions">
                          {l.status === "pending" && canManage && l.employee_id !== user.id && (
                            <>
                              <button className="btn sm success" onClick={() => review(l, true)}>Duyệt</button>
                              <button className="btn sm danger" onClick={() => review(l, false)}>Từ chối</button>
                            </>
                          )}
                          {l.status === "pending" && l.employee_id === user.id && (
                            <button className="btn sm" onClick={() => cancel(l)}>Hủy đơn</button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <Empty>Không có đơn nghỉ phép</Empty>
          )}
        </Loading>
      </Card>
      {modal && (
        <FormModal
          title="Tạo đơn nghỉ phép"
          fields={FIELDS}
          onClose={() => setModal(false)}
          submitLabel="Gửi đơn"
          onSubmit={async (v) => {
            await api.post("/api/leaves", v);
            setTab("mine");
            reload();
          }}
        />
      )}
    </>
  );
}
