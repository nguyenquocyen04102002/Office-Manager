import { useMemo, useState } from "react";
import { api } from "../api";
import { useAuth } from "../AuthContext.jsx";
import FormModal from "../components/FormModal.jsx";
import { Card, Empty, Loading, PageHeader } from "../components/ui.jsx";
import { fmtTime, todayStr, useAsync } from "../utils";

const ROOM_FIELDS = [
  { name: "name", label: "Tên phòng", required: true },
  { name: "capacity", label: "Sức chứa (người)", type: "number", numeric: true, required: true, min: 1, defaultValue: 8 },
  { name: "location", label: "Vị trí" },
  { name: "equipment", label: "Trang thiết bị" },
];

export default function Rooms() {
  const { user, isAdmin } = useAuth();
  const [day, setDay] = useState(todayStr());
  const [bookingModal, setBookingModal] = useState(false);
  const [roomModal, setRoomModal] = useState(null);
  const [msg, setMsg] = useState("");

  const { data: rooms, loading, error, reload: reloadRooms } = useAsync(() => api.get("/api/rooms"), []);
  const { data: bookings, reload: reloadBookings } = useAsync(() => api.get("/api/bookings", { day }), [day]);

  const bookingFields = useMemo(
    () => [
      { name: "room_id", label: "Phòng họp", type: "select", required: true, numeric: true, options: (rooms || []).map((r) => ({ value: r.id, label: `${r.name} (${r.capacity} chỗ)` })) },
      { name: "title", label: "Nội dung cuộc họp", required: true },
      { name: "start_time", label: "Bắt đầu", type: "datetime-local", required: true, defaultValue: `${day}T09:00` },
      { name: "end_time", label: "Kết thúc", type: "datetime-local", required: true, defaultValue: `${day}T10:00` },
    ],
    [rooms, day]
  );

  const cancel = async (b) => {
    if (!window.confirm("Hủy lịch đặt phòng này?")) return;
    try {
      await api.del(`/api/bookings/${b.id}`);
      reloadBookings();
    } catch (e) {
      setMsg(e.message);
    }
  };

  const removeRoom = async (r) => {
    if (!window.confirm(`Xóa phòng "${r.name}" và toàn bộ lịch đặt của phòng?`)) return;
    try {
      await api.del(`/api/rooms/${r.id}`);
      reloadRooms();
      reloadBookings();
    } catch (e) {
      setMsg(e.message);
    }
  };

  return (
    <>
      <PageHeader title="Phòng họp" subtitle="Danh mục phòng và lịch đặt phòng (hệ thống tự chặn trùng lịch)">
        {isAdmin && <button className="btn" onClick={() => setRoomModal({})}>+ Thêm phòng</button>}
        <button className="btn primary" onClick={() => setBookingModal(true)}>+ Đặt phòng</button>
      </PageHeader>
      {msg && <div className="alert red">{msg}</div>}

      <Card title={`Lịch đặt phòng ngày`} actions={<input type="date" value={day} onChange={(e) => setDay(e.target.value)} style={{ width: "auto" }} />}>
        {bookings?.length ? (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Thời gian</th><th>Phòng</th><th>Nội dung</th><th>Người đặt</th><th></th></tr></thead>
              <tbody>
                {bookings.map((b) => (
                  <tr key={b.id}>
                    <td><strong>{fmtTime(b.start_time)} – {fmtTime(b.end_time)}</strong></td>
                    <td>{b.room_name}</td>
                    <td className="wrap">{b.title}</td>
                    <td>{b.employee_name}</td>
                    <td>{(b.employee_id === user.id || isAdmin) && <button className="btn sm danger" onClick={() => cancel(b)}>Hủy</button>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty>Chưa có lịch đặt phòng trong ngày này</Empty>
        )}
      </Card>

      <Card title="Danh sách phòng họp">
        <Loading loading={loading} error={error}>
          {rooms?.length ? (
            <div className="table-wrap">
              <table>
                <thead><tr><th>Tên phòng</th><th className="num">Sức chứa</th><th>Vị trí</th><th>Trang thiết bị</th>{isAdmin && <th></th>}</tr></thead>
                <tbody>
                  {rooms.map((r) => (
                    <tr key={r.id}>
                      <td><strong>{r.name}</strong></td>
                      <td className="num">{r.capacity}</td>
                      <td>{r.location || "—"}</td>
                      <td className="wrap">{r.equipment || "—"}</td>
                      {isAdmin && (
                        <td>
                          <div className="row-actions">
                            <button className="btn sm" onClick={() => setRoomModal(r)}>Sửa</button>
                            <button className="btn sm danger" onClick={() => removeRoom(r)}>Xóa</button>
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

      {bookingModal && (
        <FormModal
          title="Đặt phòng họp"
          fields={bookingFields}
          submitLabel="Đặt phòng"
          onClose={() => setBookingModal(false)}
          onSubmit={async (v) => {
            await api.post("/api/bookings", v);
            reloadBookings();
          }}
        />
      )}
      {roomModal && (
        <FormModal
          key={roomModal.id || "new"}
          title={roomModal.id ? "Sửa phòng họp" : "Thêm phòng họp"}
          fields={ROOM_FIELDS}
          initial={roomModal}
          onClose={() => setRoomModal(null)}
          onSubmit={async (v) => {
            if (roomModal.id) await api.put(`/api/rooms/${roomModal.id}`, v);
            else await api.post("/api/rooms", v);
            reloadRooms();
          }}
        />
      )}
    </>
  );
}
