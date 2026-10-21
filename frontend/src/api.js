// Lớp gọi API dùng chung. Mặc định gọi cùng origin (/api) - Nginx/Vite proxy sang backend.
const BASE = import.meta.env.VITE_API_URL || "";
const TOKEN_KEY = "office_token";

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (t) => (t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY));

function errorMessage(data, status) {
  const detail = data && data.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => `${(d.loc || []).slice(1).join(".")}: ${d.msg}`).join("; ");
  }
  return `Lỗi ${status}`;
}

async function request(path, { method = "GET", body, form, blob } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  let payload;
  if (form) {
    payload = new URLSearchParams(form);
    headers["Content-Type"] = "application/x-www-form-urlencoded";
  } else if (body !== undefined) {
    payload = JSON.stringify(body);
    headers["Content-Type"] = "application/json";
  }

  let res;
  try {
    res = await fetch(`${BASE}${path}`, { method, headers, body: payload });
  } catch {
    throw new Error("Không kết nối được máy chủ. Hãy kiểm tra backend đã chạy chưa.");
  }

  if (res.status === 401 && !path.includes("/auth/login")) {
    setToken(null);
    window.dispatchEvent(new Event("auth-expired"));
  }
  if (!res.ok) {
    let data = null;
    try {
      data = await res.json();
    } catch {
      /* không có JSON */
    }
    throw new Error(errorMessage(data, res.status));
  }
  if (blob) return res.blob();
  return res.json();
}

export const qs = (params = {}) => {
  const s = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") s.append(k, v);
  });
  const text = s.toString();
  return text ? `?${text}` : "";
};

export const api = {
  get: (path, params) => request(path + qs(params)),
  post: (path, body) => request(path, { method: "POST", body: body ?? {} }),
  put: (path, body) => request(path, { method: "PUT", body }),
  del: (path) => request(path, { method: "DELETE" }),
  login: (email, password) => request("/api/auth/login", { method: "POST", form: { username: email, password } }),
  download: async (path, params, filename) => {
    const blob = await request(path + qs(params), { blob: true });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  },
};
