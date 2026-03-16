/**
 * ModuleCRUD
 *
 * Generic CRUD panel for a single template table.
 * - Fetches rows from  GET /api/records/table/{tableName}
 * - Inserts a new row via POST /api/records/table/{tableName}
 * - Infers form fields from FIELD_DEFS (known schemas) or from live column list
 */

import React, { useState, useEffect, useCallback } from "react";
import { dbTableFetch, dbTableInsert } from "../../services/supabase";

// ─── Per-table field definitions ─────────────────────────────────────────────
// Only the fields a user should fill in (auto columns like id/created_at excluded).

interface FieldDef {
  name: string;        // column name
  label: string;       // human label
  type: "text" | "number" | "date" | "select" | "textarea";
  required?: boolean;
  options?: string[];  // for select
  placeholder?: string;
}

const FIELD_DEFS: Record<string, FieldDef[]> = {
  // ── Payroll ──────────────────────────────────────────────────────────────
  employees: [
    { name: "first_name",  label: "First Name",  type: "text",   required: true },
    { name: "last_name",   label: "Last Name",   type: "text",   required: true },
    { name: "email",       label: "Email",       type: "text",   required: true, placeholder: "emp@company.com" },
    { name: "department",  label: "Department",  type: "text",   placeholder: "Engineering" },
    { name: "position",    label: "Position",    type: "text",   placeholder: "Software Engineer" },
    { name: "hire_date",   label: "Hire Date",   type: "date",   required: true },
    { name: "status",      label: "Status",      type: "select", options: ["active", "inactive", "on_leave"], required: true },
  ],
  attendance: [
    { name: "employee_id",  label: "Employee ID",   type: "number", required: true },
    { name: "date",          label: "Date",          type: "date",   required: true },
    { name: "check_in",      label: "Check In",      type: "text",   placeholder: "09:00" },
    { name: "check_out",     label: "Check Out",     type: "text",   placeholder: "18:00" },
    { name: "hours_worked",  label: "Hours Worked",  type: "number", placeholder: "8" },
    { name: "status",        label: "Status",        type: "select", options: ["present", "absent", "half_day", "leave"] },
    { name: "notes",         label: "Notes",         type: "textarea" },
  ],
  salary_components: [
    { name: "employee_id",    label: "Employee ID",    type: "number",  required: true },
    { name: "component",      label: "Component",      type: "text",    required: true, placeholder: "Basic Salary" },
    { name: "component_type", label: "Type",           type: "select",  options: ["earning", "deduction"], required: true },
    { name: "amount",         label: "Amount",         type: "number",  required: true },
    { name: "is_percentage",  label: "Is Percentage",  type: "select",  options: ["false", "true"] },
    { name: "effective_from", label: "Effective From", type: "date",    required: true },
    { name: "effective_to",   label: "Effective To",   type: "date" },
  ],
  payroll_runs: [
    { name: "period_start",   label: "Period Start",    type: "date",   required: true },
    { name: "period_end",     label: "Period End",      type: "date",   required: true },
    { name: "run_date",       label: "Run Date",        type: "date",   required: true },
    { name: "status",         label: "Status",          type: "select", options: ["draft", "processing", "completed", "cancelled"] },
    { name: "processed_by",   label: "Processed By",    type: "text",   placeholder: "admin@company.com" },
    { name: "notes",          label: "Notes",           type: "textarea" },
  ],
  payslips: [
    { name: "payroll_run_id",   label: "Payroll Run ID",    type: "number", required: true },
    { name: "employee_id",      label: "Employee ID",       type: "number", required: true },
    { name: "gross_salary",     label: "Gross Salary",      type: "number", required: true },
    { name: "total_deductions", label: "Total Deductions",  type: "number" },
    { name: "net_salary",       label: "Net Salary",        type: "number", required: true },
  ],
  // ── Invoice ──────────────────────────────────────────────────────────────
  customers: [
    { name: "name",    label: "Name",    type: "text",   required: true },
    { name: "email",   label: "Email",   type: "text" },
    { name: "phone",   label: "Phone",   type: "text" },
    { name: "address", label: "Address", type: "textarea" },
    { name: "city",    label: "City",    type: "text" },
    { name: "country", label: "Country", type: "text" },
    { name: "tax_id",  label: "Tax ID",  type: "text" },
    { name: "status",  label: "Status",  type: "select", options: ["active", "inactive"] },
  ],
  products: [
    { name: "name",        label: "Name",        type: "text",   required: true },
    { name: "sku",         label: "SKU",         type: "text" },
    { name: "description", label: "Description", type: "textarea" },
    { name: "unit_price",  label: "Unit Price",  type: "number", required: true },
    { name: "tax_rate",    label: "Tax Rate %",  type: "number",  placeholder: "18" },
    { name: "unit",        label: "Unit",        type: "text",   placeholder: "unit" },
    { name: "status",      label: "Status",      type: "select", options: ["active", "inactive"] },
  ],
  invoices: [
    { name: "invoice_number", label: "Invoice #",      type: "text",   required: true, placeholder: "INV-2026-001" },
    { name: "customer_id",    label: "Customer ID",    type: "number", required: true },
    { name: "issue_date",     label: "Issue Date",     type: "date",   required: true },
    { name: "due_date",       label: "Due Date",       type: "date" },
    { name: "status",         label: "Status",         type: "select", options: ["draft", "sent", "paid", "overdue", "cancelled"] },
    { name: "notes",          label: "Notes",          type: "textarea" },
  ],
  invoice_items: [
    { name: "invoice_id",   label: "Invoice ID",   type: "number", required: true },
    { name: "description",  label: "Description",  type: "text",   required: true },
    { name: "quantity",     label: "Quantity",     type: "number", required: true, placeholder: "1" },
    { name: "unit_price",   label: "Unit Price",   type: "number", required: true },
    { name: "tax_rate",     label: "Tax Rate %",   type: "number", placeholder: "18" },
  ],
  // ── CRM ──────────────────────────────────────────────────────────────────
  leads: [
    { name: "first_name",  label: "First Name",  type: "text" },
    { name: "last_name",   label: "Last Name",   type: "text" },
    { name: "email",       label: "Email",       type: "text" },
    { name: "phone",       label: "Phone",       type: "text" },
    { name: "company",     label: "Company",     type: "text" },
    { name: "source",      label: "Source",      type: "text",   placeholder: "Website" },
    { name: "status",      label: "Status",      type: "select", options: ["new", "contacted", "qualified", "converted", "lost"] },
    { name: "assigned_to", label: "Assigned To", type: "text" },
    { name: "notes",       label: "Notes",       type: "textarea" },
  ],
  deals: [
    { name: "title",          label: "Title",          type: "text",   required: true },
    { name: "stage",          label: "Stage",          type: "select", options: ["prospecting", "qualification", "proposal", "negotiation", "closed_won", "closed_lost"] },
    { name: "value",          label: "Value",          type: "number" },
    { name: "currency",       label: "Currency",       type: "text",   placeholder: "USD" },
    { name: "probability",    label: "Win Probability %", type: "number", placeholder: "50" },
    { name: "expected_close", label: "Expected Close", type: "date" },
    { name: "status",         label: "Status",         type: "select", options: ["open", "won", "lost"] },
    { name: "assigned_to",    label: "Assigned To",    type: "text" },
    { name: "notes",          label: "Notes",          type: "textarea" },
  ],
  activities: [
    { name: "activity_type", label: "Type",        type: "select",   required: true, options: ["call", "email", "meeting", "task", "note"] },
    { name: "subject",       label: "Subject",     type: "text",     required: true },
    { name: "description",   label: "Description", type: "textarea" },
    { name: "deal_id",       label: "Deal ID",     type: "number" },
    { name: "lead_id",       label: "Lead ID",     type: "number" },
    { name: "due_date",      label: "Due Date",    type: "date" },
    { name: "status",        label: "Status",      type: "select",   options: ["pending", "completed", "cancelled"] },
    { name: "assigned_to",   label: "Assigned To", type: "text" },
  ],
  contacts: [
    { name: "first_name", label: "First Name", type: "text",     required: true },
    { name: "last_name",  label: "Last Name",  type: "text" },
    { name: "email",      label: "Email",      type: "text" },
    { name: "phone",      label: "Phone",      type: "text" },
    { name: "company",    label: "Company",    type: "text" },
    { name: "job_title",  label: "Job Title",  type: "text" },
    { name: "lead_id",    label: "Lead ID",    type: "number" },
    { name: "notes",      label: "Notes",      type: "textarea" },
  ],
};

// ─── Auto-infer field defs from raw column names ──────────────────────────────
function inferFieldDefs(columns: string[]): FieldDef[] {
  const skip = new Set(["id", "created_at", "updated_at"]);
  return columns
    .filter((c) => !skip.has(c))
    .map((c) => ({
      name: c,
      label: c.replace(/_/g, " ").replace(/\b\w/g, (ch) => ch.toUpperCase()),
      type: c.includes("date") || c.includes("_at")
        ? "date"
        : c.includes("_id") || c === "amount" || c.includes("salary") || c.includes("price")
        ? "number"
        : "text",
    }));
}

// ─── Component ────────────────────────────────────────────────────────────────

interface ModuleCRUDProps {
  tableName: string;           // e.g. "employees"
  moduleLabel: string;         // e.g. "Employee Management"
}

export const ModuleCRUD: React.FC<ModuleCRUDProps> = ({ tableName, moduleLabel }) => {
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  const [columns, setColumns] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [showForm, setShowForm] = useState(false);
  const [formValues, setFormValues] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const fields: FieldDef[] = FIELD_DEFS[tableName] ?? inferFieldDefs(columns);

  // ── Fetch ──
  const fetchRows = useCallback(async () => {
    setLoading(true);
    setError(null);
    const result = await dbTableFetch(tableName);
    if (result.rows.length === 0 && result.columns.length === 0) {
      setError("Could not load data — is the backend running?");
    }
    setColumns(result.columns);
    setRows(result.rows);
    setLoading(false);
  }, [tableName]);

  useEffect(() => { fetchRows(); }, [fetchRows]);

  // ── Save ──
  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSaveError(null);
    const row: Record<string, unknown> = {};
    for (const f of fields) {
      const v = formValues[f.name] ?? "";
      if (v !== "") {
        row[f.name] = f.type === "number" ? Number(v) : v;
      }
    }
    const res = await dbTableInsert(tableName, row);
    if (res.ok) {
      setSaveSuccess(true);
      setFormValues({});
      setTimeout(() => { setSaveSuccess(false); setShowForm(false); }, 1500);
      await fetchRows();
    } else {
      setSaveError(res.error ?? "Insert failed");
    }
    setSaving(false);
  };

  // ── Display columns (skip verbose ones for the table) ──
  const displayCols = columns.filter(
    (c) => !["id", "updated_at"].includes(c)
  ).slice(0, 7); // cap at 7 columns to avoid overflow

  // ─── Render ───────────────────────────────────────────────────────────────
  return (
    <div className="space-y-3">
      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-400">
          {loading ? "Loading…" : `${rows.length} record${rows.length !== 1 ? "s" : ""}`}
        </span>
        <div className="flex gap-2">
          <button
            onClick={fetchRows}
            disabled={loading}
            className="px-3 py-1.5 text-xs rounded bg-gray-700 hover:bg-gray-600 text-gray-300 transition-colors disabled:opacity-50"
          >
            ↺ Refresh
          </button>
          <button
            onClick={() => { setShowForm(!showForm); setSaveError(null); }}
            className="px-3 py-1.5 text-xs rounded bg-blue-700 hover:bg-blue-600 text-white font-medium transition-colors"
          >
            {showForm ? "✕ Cancel" : "+ Add Record"}
          </button>
        </div>
      </div>

      {/* Add Record Form */}
      {showForm && (
        <div className="bg-gray-800 border border-gray-600 rounded-lg p-4">
          <h4 className="text-sm font-medium text-white mb-3">New {moduleLabel} Record</h4>
          <form onSubmit={handleSave}>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {fields.map((f) => (
                <div key={f.name}>
                  <label className="block text-xs text-gray-400 mb-1">
                    {f.label}{f.required && <span className="text-red-400 ml-0.5">*</span>}
                  </label>
                  {f.type === "select" ? (
                    <select
                      className="w-full px-2 py-1.5 text-sm bg-gray-900 border border-gray-600 rounded text-white focus:outline-none focus:border-blue-500"
                      value={formValues[f.name] ?? ""}
                      onChange={(e) => setFormValues({ ...formValues, [f.name]: e.target.value })}
                      required={f.required}
                    >
                      <option value="">— select —</option>
                      {(f.options ?? []).map((o) => (
                        <option key={o} value={o}>{o}</option>
                      ))}
                    </select>
                  ) : f.type === "textarea" ? (
                    <textarea
                      className="w-full px-2 py-1.5 text-sm bg-gray-900 border border-gray-600 rounded text-white focus:outline-none focus:border-blue-500 resize-none"
                      rows={2}
                      placeholder={f.placeholder}
                      value={formValues[f.name] ?? ""}
                      onChange={(e) => setFormValues({ ...formValues, [f.name]: e.target.value })}
                      required={f.required}
                    />
                  ) : (
                    <input
                      type={f.type === "number" ? "number" : f.type === "date" ? "date" : "text"}
                      className="w-full px-2 py-1.5 text-sm bg-gray-900 border border-gray-600 rounded text-white focus:outline-none focus:border-blue-500"
                      placeholder={f.placeholder}
                      value={formValues[f.name] ?? ""}
                      onChange={(e) => setFormValues({ ...formValues, [f.name]: e.target.value })}
                      required={f.required}
                    />
                  )}
                </div>
              ))}
            </div>
            {saveError && (
              <p className="mt-2 text-xs text-red-400">⚠ {saveError}</p>
            )}
            <div className="flex items-center gap-3 mt-4">
              <button
                type="submit"
                disabled={saving}
                className="px-4 py-1.5 text-sm rounded bg-blue-600 hover:bg-blue-500 text-white font-medium disabled:opacity-60 transition-colors"
              >
                {saving ? "Saving…" : "Save Record"}
              </button>
              {saveSuccess && <span className="text-xs text-green-400">✓ Saved!</span>}
            </div>
          </form>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="text-xs text-red-400 bg-red-900/20 border border-red-800 rounded px-3 py-2">{error}</div>
      )}

      {/* Data Table */}
      {!loading && rows.length === 0 && !error && (
        <div className="text-center py-10 text-gray-500 text-sm border border-gray-700 rounded-lg">
          No records yet — click <strong className="text-gray-300">+ Add Record</strong> to insert the first one.
        </div>
      )}

      {rows.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-gray-700">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-800 border-b border-gray-700">
                {displayCols.map((col) => (
                  <th
                    key={col}
                    className="px-3 py-2 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider whitespace-nowrap"
                  >
                    {col.replace(/_/g, " ")}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700/50">
              {rows.map((row, ri) => (
                <tr key={ri} className="hover:bg-gray-800/50 transition-colors">
                  {displayCols.map((col) => {
                    const val = row[col];
                    const display = val === null || val === undefined ? (
                      <span className="text-gray-600">—</span>
                    ) : typeof val === "boolean" ? (
                      <span className={val ? "text-green-400" : "text-gray-500"}>{val ? "Yes" : "No"}</span>
                    ) : (
                      String(val)
                    );
                    return (
                      <td key={col} className="px-3 py-2 text-gray-300 max-w-[180px] truncate" title={String(val ?? "")}>
                        {display}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
