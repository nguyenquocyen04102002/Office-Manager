import { useCallback, useEffect, useState } from "react";

export const ROLE_LABEL = { admin: "Quản trị viên", manager: "Quản lý", employee: "Nhân viên" };

export const LABELS = {
  attendance: {
    present: "Đúng giờ",
    late: "Đi muộn",
    early_leave: "Về sớm",
    late_early: "Muộn & về sớm",
    leave: "Nghỉ phép",
    absent: "Vắng",
  },
  leaveStatus: { pending: "Chờ duyệt", approved: "Đã duyệt", rejected: "Từ chối" },
  leaveType: { annual: "Phép năm", sick: "Nghỉ ốm", unpaid: "Không lương", maternity: "Thai sản", other: "Khác" },
  taskStatus: { todo: "Cần làm", in_progress: "Đang làm", done: "Hoàn thành" },
  priority: { low: "Thấp", medium: "Trung bình", high: "Cao" },
  assetStatus: { available: "Sẵn sàng", in_use: "Đang sử dụng", maintenance: "Bảo trì", retired: "Thanh lý" },
  empStatus: { active: "Đang làm việc", inactive: "Đã nghỉ" },
};

export const TONE = {
  present: "green", late: "amber", early_leave: "amber", late_early: "amber", leave: "blue", absent: "red",
  pending: "amber", approved: "green", rejected: "red",
  todo: "gray", in_progress: "blue", done: "green",
  low: "gray", medium: "blue", high: "red",
  available: "green", in_use: "blue", maintenance: "amber", retired: "gray",
  active: "green", inactive: "gray",
  admin: "red", manager: "blue", employee: "gray",
};

export const options = (map) => Object.entries(map).map(([value, label]) => ({ value, label }));

export const pad = (n) => String(n).padStart(2, "0");
export const todayStr = () => {
  const d = new Date();
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
};
export const fmtDate = (v) => {
  if (!v) return "—";
  const [y, m, d] = String(v).slice(0, 10).split("-");
  return `${d}/${m}/${y}`;
};
export const fmtTime = (v) => (v ? String(v).slice(11, 16) : "—");
export const fmtDateTime = (v) => (v ? `${fmtTime(v)} ${fmtDate(v)}` : "—");
export const toInputDateTime = (v) => (v ? String(v).slice(0, 16) : "");

// Hook tải dữ liệu: trả về { data, loading, error, reload }
export function useAsync(fn, deps = []) {
  const [state, setState] = useState({ data: null, loading: true, error: "" });
  const run = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: "" }));
    try {
      setState({ data: await fn(), loading: false, error: "" });
    } catch (e) {
      setState({ data: null, loading: false, error: e.message });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  useEffect(() => {
    run();
  }, [run]);
  return { ...state, reload: run };
}
