import { useEffect, useState } from "react";
import { api } from "../api";
import { useAuth } from "../AuthContext.jsx";
import { Alert, Badge, Card, Empty, Loading, PageHeader, StatCard } from "../components/ui.jsx";
import { fmtDate, fmtTime, LABELS, useAsync } from "../utils";

function CheckInBox() {
  const { data: today, loading, reload } = useAsync(() => api.get("/api/attendance/today"), []);
  const [now, setNow] = useState(new Date());
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const act = async (kind) => {
    setBusy(true);
    setError("");
    try {
      await api.post(`/api/attendance/${kind}`);
      reload();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const checkedIn = !!today?.check_in;
  const checkedOut = !!today?.check_out;

  return (
    <Card title="Điểm danh hôm nay">
      <div className="checkin-box">
        <div className="clock">{now.toLocaleTimeString("vi-VN")}</div>
        <div>
          <div>{now.toLocaleDateString("vi-VN", { weekday: "long", day: "2-digit", month: "2-digit", year: "numeric" })}</div>
          {!loading && (
            <div className="muted">
              Vào: <strong>{fmtTime(today?.check_in)}</strong> · Ra: <strong>{fmtTime(today?.check_out)}</strong>{" "}
              {today && <Badge value={today.status} label={LABELS.attendance[today.status]} />}
            </div>
          )}
        </div>
        <div className="actions">
          <button className="btn success" disabled={busy || checkedIn} onClick={() => act("check-in")}>
            Vào ca
          </button>
          <button className="btn primary" disabled={busy || !checkedIn || checkedOut} onClick={() => act("check-out")}>
            Ra về
          </button>
        </div>
      </div>
      <Alert>{error}</Alert>
    </Card>
  );
}

export default function Dashboard() {
  const { user, canManage } = useAuth();
  const { data: s, loading, error } = useAsync(() => api.get("/api/dashboard/stats"), []);
  const scopeText = { all: "toàn công ty", team: "nhóm bạn quản lý", me: "cá nhân" };

  return (
    <>
      <PageHeader title={`Xin chào, ${user.full_name}`} subtitle={s ? `Số liệu ${scopeText[s.scope]}` : ""} />
      <CheckInBox />
      <Loading loading={loading} error={error}>
        {s && (
          <>
            <div className="grid cols-4" style={{ marginBottom: 16 }}>
              {canManage && <StatCard label="Nhân viên" value={s.total_employees} hint={`${s.total_departments} phòng ban`} />}
              {canManage && <StatCard label="Có mặt hôm nay" value={s.present_today} tone="green" hint={`${s.late_today} đi muộn · ${s.on_leave_today} nghỉ phép`} />}
              <StatCard label={canManage ? "Đơn nghỉ chờ duyệt" : "Đơn nghỉ đang chờ"} value={s.pending_leaves} tone="amber" />
              <StatCard label="Việc của tôi chưa xong" value={s.my_open_tasks} tone="blue" />
              {canManage && <StatCard label="Việc đang mở (nhóm)" value={s.open_tasks} tone="gray" />}
              <StatCard label="Lịch họp hôm nay" value={s.bookings_today} tone="blue" />
              <StatCard label="Tài sản sẵn sàng" value={s.assets_available} tone="green" />
            </div>
            <Card title="Thông báo mới">
              {s.announcements.length === 0 ? (
                <Empty>Chưa có thông báo</Empty>
              ) : (
                s.announcements.map((a) => (
                  <div className="announce" key={a.id}>
                    <h3>
                      {a.title}
                      {a.pinned && <span className="pin">📌 Ghim</span>}
                    </h3>
                    <small className="muted">{fmtDate(a.created_at)}</small>
                    <p>{a.content}</p>
                  </div>
                ))
              )}
            </Card>
          </>
        )}
      </Loading>
    </>
  );
}
