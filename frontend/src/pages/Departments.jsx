import { useState } from "react";
import { api } from "../api";
import { useAuth } from "../AuthContext.jsx";
import FormModal from "../components/FormModal.jsx";
import { Card, Empty, Loading, PageHeader } from "../components/ui.jsx";
import { useAsync } from "../utils";

const FIELDS = [
  { name: "name", label: "Tên phòng ban", required: true, span: 2 },
  { name: "description", label: "Mô tả", type: "textarea" },
];

export default function Departments() {
  const { isAdmin } = useAuth();
  const { data, loading, error, reload } = useAsync(() => api.get("/api/departments"), []);
  const [modal, setModal] = useState(null); // null | {} (thêm) | item (sửa)
  const [msg, setMsg] = useState("");

  const remove = async (d) => {
    if (!window.confirm(`Xóa phòng ban "${d.name}"? Nhân viên sẽ chuyển về trạng thái chưa phân phòng.`)) return;
    try {
      await api.del(`/api/departments/${d.id}`);
      reload();
    } catch (e) {
      setMsg(e.message);
    }
  };

  return (
    <>
      <PageHeader title="Phòng ban" subtitle="Cơ cấu tổ chức của văn phòng">
        {isAdmin && <button className="btn primary" onClick={() => setModal({})}>+ Thêm phòng ban</button>}
      </PageHeader>
      {msg && <div className="alert red">{msg}</div>}
      <Card>
        <Loading loading={loading} error={error}>
          {data?.length ? (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>Tên phòng ban</th><th>Mô tả</th><th className="num">Nhân viên</th>{isAdmin && <th></th>}</tr>
                </thead>
                <tbody>
                  {data.map((d) => (
                    <tr key={d.id}>
                      <td><strong>{d.name}</strong></td>
                      <td className="wrap">{d.description || "—"}</td>
                      <td className="num">{d.employee_count}</td>
                      {isAdmin && (
                        <td>
                          <div className="row-actions">
                            <button className="btn sm" onClick={() => setModal(d)}>Sửa</button>
                            <button className="btn sm danger" onClick={() => remove(d)}>Xóa</button>
                          </div>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <Empty />
          )}
        </Loading>
      </Card>
      {modal && (
        <FormModal
          title={modal.id ? "Sửa phòng ban" : "Thêm phòng ban"}
          fields={FIELDS}
          initial={modal}
          onClose={() => setModal(null)}
          onSubmit={async (v) => {
            if (modal.id) await api.put(`/api/departments/${modal.id}`, v);
            else await api.post("/api/departments", v);
            reload();
          }}
        />
      )}
    </>
  );
}
