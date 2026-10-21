import { useMemo, useState } from "react";
import { api } from "../api";
import { useAuth } from "../AuthContext.jsx";
import FormModal from "../components/FormModal.jsx";
import { Badge, Card, Empty, Loading, PageHeader } from "../components/ui.jsx";
import { fmtDate, LABELS, options, useAsync } from "../utils";

export default function Assets() {
  const { canManage, isAdmin } = useAuth();
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [modal, setModal] = useState(null);
  const [msg, setMsg] = useState("");

  const { data: employees } = useAsync(() => api.get("/api/employees", { status: "active" }), []);
  const { data, loading, error, reload } = useAsync(() => api.get("/api/assets", { q, status }), [q, status]);

  const fields = useMemo(
    () => [
      { name: "code", label: "Mã tài sản", required: true },
      { name: "name", label: "Tên tài sản", required: true },
      { name: "category", label: "Danh mục" },
      { name: "purchase_date", label: "Ngày mua", type: "date" },
      { name: "status", label: "Trạng thái", type: "select", required: true, options: options(LABELS.assetStatus), defaultValue: "available" },
      {
        name: "assigned_to_id", label: "Người sử dụng", type: "select", numeric: true,
        options: (employees || []).map((e) => ({ value: e.id, label: `${e.full_name} (${e.code})` })),
      },
      { name: "note", label: "Ghi chú", span: 2 },
    ],
    [employees]
  );

  const remove = async (a) => {
    if (!window.confirm(`Xóa tài sản "${a.name}"?`)) return;
    try {
      await api.del(`/api/assets/${a.id}`);
      reload();
    } catch (e) {
      setMsg(e.message);
    }
  };

  return (
    <>
      <PageHeader title="Tài sản" subtitle="Quản lý thiết bị, cấp phát và bảo trì">
        {canManage && <button className="btn primary" onClick={() => setModal({})}>+ Thêm tài sản</button>}
      </PageHeader>
      <div className="filters">
        <input placeholder="Tìm theo mã hoặc tên..." value={q} onChange={(e) => setQ(e.target.value)} />
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">Mọi trạng thái</option>
          {options(LABELS.assetStatus).map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </div>
      {msg && <div className="alert red">{msg}</div>}
      <Card>
        <Loading loading={loading} error={error}>
          {data?.length ? (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>Mã</th><th>Tên tài sản</th><th>Danh mục</th><th>Trạng thái</th><th>Người sử dụng</th><th>Ngày mua</th><th>Ghi chú</th>{canManage && <th></th>}</tr>
                </thead>
                <tbody>
                  {data.map((a) => (
                    <tr key={a.id}>
                      <td>{a.code}</td>
                      <td><strong>{a.name}</strong></td>
                      <td>{a.category || "—"}</td>
                      <td><Badge value={a.status} label={LABELS.assetStatus[a.status]} /></td>
                      <td>{a.assigned_to_name || "—"}</td>
                      <td>{fmtDate(a.purchase_date)}</td>
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
            <Empty>Không có tài sản</Empty>
          )}
        </Loading>
      </Card>
      {modal && (
        <FormModal
          key={modal.id || "new"}
          title={modal.id ? "Sửa tài sản" : "Thêm tài sản"}
          fields={fields}
          initial={modal}
          onClose={() => setModal(null)}
          onSubmit={async (v) => {
            if (modal.id) await api.put(`/api/assets/${modal.id}`, v);
            else await api.post("/api/assets", v);
            reload();
          }}
        />
      )}
    </>
  );
}
