/**
 * Form components — styled inputs, selects, textareas, checkboxes.
 * Provides consistent form UX with label, error display, and styling.
 */

import { type InputHTMLAttributes, type SelectHTMLAttributes, type TextareaHTMLAttributes, forwardRef } from "react";

type SharedProps = {
  label: string;
  error?: string;
  hint?: string;
};

// ── Input ──────────────────────────────────────────────────────────

type InputProps = SharedProps & InputHTMLAttributes<HTMLInputElement> & { as?: "input" };

export const FormInput = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, className = "", ...props }, ref) => (
    <label className="form-field block">
      <span className="form-label">{label}</span>
      <input
        ref={ref}
        className={`form-input ${error ? "form-input-error" : ""} ${className}`}
        {...props}
      />
      {error && <span className="form-error">{error}</span>}
      {hint && !error && <span className="form-hint">{hint}</span>}
    </label>
  ),
);
FormInput.displayName = "FormInput";

// ── Select ─────────────────────────────────────────────────────────

type SelectProps = SharedProps & SelectHTMLAttributes<HTMLSelectElement> & {
  options: { value: string; label: string }[];
};

export const FormSelect = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, hint, options, className = "", ...props }, ref) => (
    <label className="form-field block">
      <span className="form-label">{label}</span>
      <select
        ref={ref}
        className={`form-input appearance-none ${error ? "form-input-error" : ""} ${className}`}
        {...props}
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
      {error && <span className="form-error">{error}</span>}
      {hint && !error && <span className="form-hint">{hint}</span>}
    </label>
  ),
);
FormSelect.displayName = "FormSelect";

// ── Textarea ───────────────────────────────────────────────────────

type TextareaProps = SharedProps & TextareaHTMLAttributes<HTMLTextAreaElement>;

export const FormTextarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, hint, className = "", ...props }, ref) => (
    <label className="form-field block">
      <span className="form-label">{label}</span>
      <textarea
        ref={ref}
        className={`form-input ${error ? "form-input-error" : ""} ${className}`}
        rows={4}
        {...props}
      />
      {error && <span className="form-error">{error}</span>}
      {hint && !error && <span className="form-hint">{hint}</span>}
    </label>
  ),
);
FormTextarea.displayName = "FormTextarea";

// ── Checkbox ───────────────────────────────────────────────────────

type CheckboxProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & {
  label: string;
};

export const FormCheckbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ label, className = "", ...props }, ref) => (
    <label className={`flex items-center gap-2 cursor-pointer ${className}`}>
      <input
        ref={ref}
        type="checkbox"
        className="w-4 h-4 rounded border-[var(--border)] text-[var(--accent)] focus:ring-[var(--accent)]"
        {...props}
      />
      <span className="text-sm text-[var(--text)]">{label}</span>
    </label>
  ),
);
FormCheckbox.displayName = "FormCheckbox";