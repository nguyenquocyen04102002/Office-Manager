import { useState } from "react";
import { api } from "../api";
import { useAuth } from "../AuthContext.jsx";
import FormModal from "../components/FormModal.jsx";
import { Card, Empty, Loading, PageHeader } from "../components/ui.jsx";
import { fmtDateTime, useAsync } from "../utils";

const FIELDS = [
  { name: "title", label: "Tiêu đề", required: true, span: 2 },
  { name: "content", label: "Nội dung", type: "textarea", required: true },
  { name: "pinned", label: "Ghim lên đầu", type: "checkbox" },
];

export default function Announcements() {
  const { canManage, user, isAdmin } = useAuth();
  const { data, loading, error, reload } = useAsync(() => api.get("/api/announcements"), []);
  const [modal, setModal] = useState(null);
  const [msg, setMsg] = useState("");

  const remove = async (a) => {
    if (!window.confirm(`Xóa thông báo "${a.title}"?`)) return;
    try {
      await api.del(`/api/announcements/${a.id}`);
      reload();
    } catch (e) {
      setMsg(e.message);
    }
  };

  return (
    <>
      <PageHeader title="Thông báo" subtitle="Thông tin nội bộ văn phòng">
        {canManage && <button className="btn primary" onClick={() => setModal({})}>+ Đăng thông báo</button>}
      </PageHeader>
      {msg && <div className="alert red">{msg}</div>}
      <Card>
        <Loading loading={loading} error={error}>
          {data?.length ? (
            data.map((a) => (
              <div className="announce" key={a.id}>
                <div className="card-head" style={{ marginBottom: 0 }}>
                  <h3>{a.title}{a.pinned && <span className="pin">📌 Ghim</span>}</h3>
                  {canManage && (isAdmin || a.author_id === user.id) && (
                    <div className="row-actions">
                      <button className="btn sm" onClick={() => setModal(a)}>Sửa</button>
                      <button className="btn sm danger" onClick={() => remove(a)}>Xóa</button>
                    </div>
                  )}
                </div>
                <small className="muted">{a.author_name || "Hệ thống"} · {fmtDateTime(a.created_at)}</small>
                <p>{a.content}</p>
              </div>
            ))
          ) : (
            <Empty>Chưa có thông báo</Empty>
          )}
        </Loading>
      </Card>
      {modal && (
        <FormModal
          key={modal.id || "new"}
          title={modal.id ? "Sửa thông báo" : "Đăng thông báo"}
          fields={FIELDS}
          initial={modal}
          onClose={() => setModal(null)}
          onSubmit={async (v) => {
            if (modal.id) await api.put(`/api/announcements/${modal.id}`, v);
            else await api.post("/api/announcements", v);
            reload();
          }}
        />
      )}
    </>
  );
}
