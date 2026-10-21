import { TONE } from "../utils";

export function Badge({ value, label }) {
  return <span className={`badge ${TONE[value] || "gray"}`}>{label ?? value}</span>;
}

export function PageHeader({ title, subtitle, children }) {
  return (
    <div className="page-header">
      <div>
        <h1>{title}</h1>
        {subtitle && <p className="muted">{subtitle}</p>}
      </div>
      <div className="actions">{children}</div>
    </div>
  );
}

export function Card({ title, children, actions }) {
  return (
    <section className="card">
      {(title || actions) && (
        <div className="card-head">
          <h2>{title}</h2>
          <div className="actions">{actions}</div>
        </div>
      )}
      {children}
    </section>
  );
}

export function Alert({ children, tone = "red" }) {
  if (!children) return null;
  return <div className={`alert ${tone}`}>{children}</div>;
}

export function Empty({ children = "Chưa có dữ liệu" }) {
  return <p className="empty">{children}</p>;
}

export function Loading({ loading, error, children }) {
  if (loading) return <p className="muted">Đang tải...</p>;
  if (error) return <Alert>{error}</Alert>;
  return children;
}

export function StatCard({ label, value, tone = "blue", hint }) {
  return (
    <div className={`stat ${tone}`}>
      <span className="stat-label">{label}</span>
      <strong>{value}</strong>
      {hint && <small>{hint}</small>}
    </div>
  );
}
