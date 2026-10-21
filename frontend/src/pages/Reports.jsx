import { useState } from "react";
import { api } from "../api";
import { Alert, Card, Empty, Loading, PageHeader } from "../components/ui.jsx";
import { LABELS, useAsync } from "../utils";

function Bars({ rows, labelKey = "label" }) {
  const max = Math.max(1, ...rows.map((r) => r.value));
  return rows.map((r) => (
    <div className="bar-row" key={r[labelKey]}>
      <span>{r[labelKey]}</span>
      <div className="bar"><span style={{ width: `${(r.value / max) * 100}%` }} /></div>
      <strong>{r.value}</strong>
    </div>
  ));
}

const toRows = (obj, labels = {}) => Object.entries(obj || {}).map(([k, v]) => ({ label: labels[k] || k, value: v }));

export default function Reports() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [dep, setDep] = useState("");
  const [err, setErr] = useState("");

  const { data: deps } = useAsync(() => api.get("/api/departments"), []);
  const { data: overview } = useAsync(() => api.get("/api/reports/overview"), []);
  const { data, loading, error } = useAsync(
    () => api.get("/api/reports/attendance-monthly", { year, month, department_id: dep }),
    [year, month, dep]
  );

  const exportCsv = async () => {
    setErr("");
    try {
      await api.download("/api/reports/attendance-monthly/export", { year, month, department_id: dep }, `bao-cao-cham-cong-${year}-${String(month).padStart(2, "0")}.csv`);
    } catch (e) {
      setErr(e.message);
    }
  };

  return (
    <>
      <PageHeader title="Báo cáo" subtitle="Thống kê chấm công và tổng quan tổ chức">
        <button className="btn primary" onClick={exportCsv}>⬇ Xuất CSV (Excel)</button>
      </PageHeader>
      <Alert>{err}</Alert>

      <Card title="Báo cáo chấm công theo tháng">
        <div className="filters">
          <select value={month} onChange={(e) => setMonth(Number(e.target.value))}>
            {Array.from({ length: 12 }, (_, i) => <option key={i + 1} value={i + 1}>Tháng {i + 1}</option>)}
          </select>
          <input type="number" value={year} min={2020} max={2100} onChange={(e) => setYear(Number(e.target.value))} style={{ width: 100 }} />
          <select value={dep} onChange={(e) => setDep(e.target.value)}>
            <option value="">Tất cả phòng ban</option>
            {(deps || []).map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
        </div>
        <Loading loading={loading} error={error}>
          {data?.rows?.length ? (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Mã</th><th>Họ tên</th><th>Phòng ban</th>
                    <th className="num">Ngày công chuẩn</th><th className="num">Đi làm</th><th className="num">Đi muộn</th>
                    <th className="num">Về sớm</th><th className="num">Nghỉ phép</th><th className="num">Vắng</th><th className="num">Tổng giờ</th>
                  </tr>
                </thead>
                <tbody>
                  {data.rows.map((r) => (
                    <tr key={r.employee_id}>
                      <td>{r.code}</td>
                      <td><strong>{r.full_name}</strong></td>
                      <td>{r.department || "—"}</td>
                      <td className="num">{r.workdays}</td>
                      <td className="num">{r.days_worked}</td>
                      <td className="num">{r.late}</td>
                      <td className="num">{r.early_leave}</td>
                      <td className="num">{r.leave}</td>
                      <td className="num">{r.absent}</td>
                      <td className="num">{r.total_hours}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <Empty>Không có dữ liệu</Empty>
          )}
        </Loading>
      </Card>

      {overview && (
        <div className="grid cols-2">
          <Card title="Nhân viên theo phòng ban">
            <Bars rows={overview.employees_by_department.map((d) => ({ label: d.department, value: d.count }))} />
          </Card>
          <Card title="Công việc theo trạng thái">
            <Bars rows={toRows(overview.tasks_by_status, LABELS.taskStatus)} />
          </Card>
          <Card title="Đơn nghỉ phép theo trạng thái">
            <Bars rows={toRows(overview.leaves_by_status, LABELS.leaveStatus)} />
          </Card>
          <Card title="Tài sản theo trạng thái">
            <Bars rows={toRows(overview.assets_by_status, LABELS.assetStatus)} />
          </Card>
        </div>
      )}
    </>
  );
}
