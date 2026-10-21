import { useMemo, useState } from "react";
import { api } from "../api";
import { useAuth } from "../AuthContext.jsx";
import FormModal from "../components/FormModal.jsx";
import { Badge, Card, Empty, Loading, PageHeader } from "../components/ui.jsx";
import { fmtDate, LABELS, options, todayStr, useAsync } from "../utils";

export default function Tasks() {
  const { canManage, user, isAdmin } = useAuth();
  const [tab, setTab] = useState("mine");
  const [status, setStatus] = useState("");
  const [modal, setModal] = useState(null);
  const [msg, setMsg] = useState("");

  const { data: team } = useAsync(() => (canManage ? api.get("/api/employees/team") : Promise.resolve([])), [canManage]);
  const { data, loading, error, reload } = useAsync(
    () => api.get("/api/tasks", { mine: tab === "mine" ? true : "", status }),
    [tab, status]
  );

  const fields = useMemo(
    () => [
      { name: "title", label: "Tiêu đề", required: true, span: 2 },
      { name: "description", label: "Mô tả", type: "textarea" },
      {
        name: "assignee_id", label: "Giao cho", type: "select", numeric: true,
        options: (team || []).map((e) => ({ value: e.id, label: `${e.full_name} (${e.code})` })),
      },
      { name: "due_date", label: "Hạn hoàn thành", type: "date", defaultValue: todayStr() },
      { name: "priority", label: "Mức ưu tiên", type: "select", required: true, options: options(LABELS.priority), defaultValue: "medium" },
      { name: "status", label: "Trạng thái", type: "select", required: true, options: options(LABELS.taskStatus), defaultValue: "todo" },
    ],
    [team]
  );

  const changeStatus = async (t, value) => {
    try {
      await api.put(`/api/tasks/${t.id}`, { status: value });
      reload();
    } catch (e) {
      setMsg(e.message);
    }
  };

  const remove = async (t) => {
    if (!window.confirm(`Xóa công việc "${t.title}"?`)) return;
    try {
      await api.del(`/api/tasks/${t.id}`);
      reload();
    } catch (e) {
      setMsg(e.message);
    }
  };

  const overdue = (t) => t.due_date && t.status !== "done" && t.due_date < todayStr();

  return (
    <>
      <PageHeader title="Công việc" subtitle="Giao việc và theo dõi tiến độ">
        {canManage && <button className="btn primary" onClick={() => setModal({})}>+ Giao việc</button>}
      </PageHeader>
      <div className="filters">
        {canManage && (
          <div className="tabs" style={{ margin: 0 }}>
            <button className={`tab ${tab === "mine" ? "active" : ""}`} onClick={() => setTab("mine")}>Việc của tôi</button>
            <button className={`tab ${tab === "all" ? "active" : ""}`} onClick={() => setTab("all")}>Nhóm / toàn bộ</button>
          </div>
        )}
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">Mọi trạng thái</option>
          {options(LABELS.taskStatus).map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </div>
      {msg && <div className="alert red">{msg}</div>}
      <Card>
        <Loading loading={loading} error={error}>
          {data?.length ? (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>Công việc</th><th>Người thực hiện</th><th>Người giao</th><th>Hạn</th><th>Ưu tiên</th><th>Trạng thái</th><th></th></tr>
                </thead>
                <tbody>
                  {data.map((t) => {
                    const canEdit = isAdmin || t.creator_id === user.id;
                    const canChangeStatus = canEdit || t.assignee_id === user.id || canManage;
                    return (
                      <tr key={t.id}>
                        <td className="wrap"><strong>{t.title}</strong>{t.description && <><br /><small className="muted">{t.description}</small></>}</td>
                        <td>{t.assignee_name || "—"}</td>
                        <td>{t.creator_name || "—"}</td>
                        <td>{fmtDate(t.due_date)} {overdue(t) && <Badge value="high" label="Quá hạn" />}</td>
                        <td><Badge value={t.priority} label={LABELS.priority[t.priority]} /></td>
                        <td>
                          {canChangeStatus ? (
                            <select value={t.status} onChange={(e) => changeStatus(t, e.target.value)} style={{ width: 130 }}>
                              {options(LABELS.taskStatus).map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                            </select>
                          ) : (
                            <Badge value={t.status} label={LABELS.taskStatus[t.status]} />
                          )}
                        </td>
                        <td>
                          {canManage && canEdit && (
                            <div className="row-actions">
                              <button className="btn sm" onClick={() => setModal(t)}>Sửa</button>
                              <button className="btn sm danger" onClick={() => remove(t)}>Xóa</button>
                            </div>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <Empty>Không có công việc</Empty>
          )}
        </Loading>
      </Card>
      {modal && (
        <FormModal
          key={modal.id || "new"}
          title={modal.id ? "Sửa công việc" : "Giao việc mới"}
          fields={fields}
          initial={modal}
          onClose={() => setModal(null)}
          onSubmit={async (v) => {
            if (modal.id) await api.put(`/api/tasks/${modal.id}`, v);
            else await api.post("/api/tasks", v);
            reload();
          }}
        />
      )}
    </>
  );
}
