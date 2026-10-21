import { useState } from "react";
import { Alert } from "./ui.jsx";

/**
 * Modal biểu mẫu dùng chung.
 * fields: [{ name, label, type, options, required, numeric, omitEmpty, placeholder, span }]
 *   type: text | email | password | number | date | datetime-local | select | textarea | checkbox
 *   options (select): [{ value, label }]  — giá trị rỗng sẽ được gửi là null
 */
export default function FormModal({ title, fields, initial = {}, onSubmit, onClose, submitLabel = "Lưu" }) {
  const [values, setValues] = useState(() => {
    const v = {};
    fields.forEach((f) => {
      v[f.name] = initial[f.name] ?? (f.type === "checkbox" ? false : f.defaultValue ?? "");
    });
    return v;
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const set = (name, value) => setValues((s) => ({ ...s, [name]: value }));

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    const out = {};
    fields.forEach((f) => {
      const v = values[f.name];
      if (f.type === "checkbox") out[f.name] = !!v;
      else if (v === "" || v === undefined || v === null) {
        if (!f.omitEmpty) out[f.name] = null;
      } else out[f.name] = f.numeric ? Number(v) : v;
    });
    try {
      await onSubmit(out);
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <form className="modal" onSubmit={submit}>
        <div className="modal-head">
          <h3>{title}</h3>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Đóng">
            ×
          </button>
        </div>
        <div className="form-grid">
          {fields.map((f) => (
            <label key={f.name} className={`field ${f.span === 2 || f.type === "textarea" ? "span-2" : ""}`}>
              <span>
                {f.label}
                {f.required && <em> *</em>}
              </span>
              {f.type === "select" ? (
                <select value={values[f.name]} required={f.required} onChange={(e) => set(f.name, e.target.value)}>
                  {!f.required && <option value="">— Không chọn —</option>}
                  {f.required && values[f.name] === "" && <option value="">— Chọn —</option>}
                  {f.options.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              ) : f.type === "textarea" ? (
                <textarea rows={3} value={values[f.name]} required={f.required} onChange={(e) => set(f.name, e.target.value)} />
              ) : f.type === "checkbox" ? (
                <input type="checkbox" checked={values[f.name]} onChange={(e) => set(f.name, e.target.checked)} />
              ) : (
                <input
                  type={f.type || "text"}
                  value={values[f.name]}
                  required={f.required}
                  placeholder={f.placeholder}
                  min={f.min}
                  onChange={(e) => set(f.name, e.target.value)}
                />
              )}
            </label>
          ))}
        </div>
        <Alert>{error}</Alert>
        <div className="modal-foot">
          <button type="button" className="btn ghost" onClick={onClose}>
            Hủy
          </button>
          <button type="submit" className="btn primary" disabled={busy}>
            {busy ? "Đang lưu..." : submitLabel}
          </button>
        </div>
      </form>
    </div>
  );
}
