import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  CalendarDays,
  LayoutDashboard,
  Users,
  Layers,
  Building2,
  Workflow,
  CalendarOff,
  ShieldAlert,
  ChartNoAxesCombined,
  ChevronLeft,
  ChevronRight,
  Plus,
  X,
  ArrowUpRight,
  Settings,
  Check,
  RefreshCw,
} from "lucide-react";
import { api } from "./api";
import "./style.css";
type Value = string | number | boolean | number[] | string[];
type Row = { id: number; [key: string]: Value };
type Data = Record<string, Row[]>;
type Slot = { day: string; employee_id: number; demand_id: number };
type Issue = {
  day?: string;
  demand_id?: number;
  employee_id?: number;
  type: string;
  required?: number;
  filled?: number;
  missing?: number;
  reasons?: string[];
  slot?: Slot;
  candidates?: { employee_id: number; reasons: string[] }[];
};
type Report = {
  valid: boolean;
  conflicts: Issue[];
  shortages: Issue[];
  workload: Record<string, number>;
  coverage_required: number;
  coverage_filled: number;
};
type Roster = Report & {
  year: number;
  month: number;
  revision: number;
  slots: Slot[];
  solver_status: string;
  optimal: boolean;
};
type Field = {
  key: string;
  label: string;
  type?: "number" | "boolean" | "date" | "list" | "dates" | "select";
  options?: string[];
  help?: string;
};
const schemas: Record<string, Field[]> = {
  employees: [
    { key: "name", label: "Full name" },
    { key: "pod_id", label: "Pod ID", type: "number" },
    { key: "process_ids", label: "Eligible process IDs", type: "list" },
    { key: "weekly_off", label: "Weekly off (Mon 0 – Sun 6)", type: "number" },
    { key: "max_work_days", label: "Maximum work days", type: "number" },
    { key: "active", label: "Active", type: "boolean" },
  ],
  brands: [
    { key: "name", label: "Brand name" },
    { key: "pod_id", label: "Pod ID", type: "number" },
    {
      key: "operating_weekdays",
      label: "Operating days (Mon 0 – Sun 6)",
      type: "list",
    },
    {
      key: "holidays_closed",
      label: "Closed on company holidays",
      type: "boolean",
    },
    {
      key: "holiday_dates",
      label: "Brand holidays",
      type: "dates",
      help: "Comma-separated YYYY-MM-DD dates",
    },
  ],
  pods: [
    { key: "name", label: "Pod name" },
    {
      key: "lead_employee_id",
      label: "Pod lead employee ID (0 means unset)",
      type: "number",
    },
  ],
  processes: [{ key: "name", label: "Process name" }],
  demands: [
    { key: "brand_id", label: "Brand ID", type: "number" },
    { key: "process_id", label: "Process ID", type: "number" },
    { key: "employee_ids", label: "Assigned employee IDs", type: "list" },
    { key: "min_staff", label: "Minimum daily staffing", type: "number" },
    {
      key: "operating_weekdays",
      label: "Process operating weekdays",
      type: "list",
    },
    {
      key: "holidays_closed",
      label: "Process closed on company holidays",
      type: "boolean",
    },
    {
      key: "staffing_by_weekday",
      label: "Staffing Mon–Sun (7 values or empty)",
      type: "list",
    },
  ],
  leaves: [
    { key: "employee_id", label: "Employee ID", type: "number" },
    { key: "start", label: "Start date", type: "date" },
    { key: "end", label: "End date", type: "date" },
    {
      key: "kind",
      label: "Absence type",
      type: "select",
      options: ["leave", "comp_off", "unavailable"],
    },
    {
      key: "status",
      label: "Approval status",
      type: "select",
      options: ["approved", "pending", "rejected"],
    },
  ],
  holidays: [
    { key: "name", label: "Holiday name" },
    { key: "day", label: "Date", type: "date" },
  ],
};
const menu = [
  ["Overview", LayoutDashboard],
  ["Roster calendar", CalendarDays],
  ["Employees", Users],
  ["Brands", Building2],
  ["Pods", Layers],
  ["Processes", Workflow],
  ["Assignments", Workflow],
  ["Leave & holidays", CalendarOff],
  ["Conflicts", ShieldAlert],
  ["Analytics", ChartNoAxesCombined],
] as const;
const initial: Data = {
  employees: [],
  brands: [],
  pods: [],
  processes: [],
  demands: [],
  leaves: [],
  holidays: [],
};
export function App() {
  const [page, setPage] = useState("Overview"),
    [data, setData] = useState<Data>(initial),
    [roster, setRoster] = useState<Roster | null>(null),
    [month, setMonth] = useState("2026-11"),
    [loading, setLoading] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [tab, setTab] = useState("leaves");
  const [filter, setFilter] = useState({
      employee_id: "",
      brand_id: "",
      process_id: "",
      pod_id: "",
    }),
    [search, setSearch] = useState("");
  const [form, setForm] = useState<{
      kind: string;
      row: Row;
      exists: boolean;
    } | null>(null),
    [editing, setEditing] = useState<Slot | null>(null),
    [candidate, setCandidate] = useState(""),
    [preview, setPreview] = useState<Report | null>(null),
    [settings, setSettings] = useState(false);
  const [year, mo] = month.split("-").map(Number);
  function offReasons(day: string, e: Row) {
    const reasons: string[] = [];
    if (!e.active) reasons.push("Inactive");
    if (new Date(day + "T12:00:00").getDay() === (Number(e.weekly_off) + 1) % 7)
      reasons.push("Weekly off");
    for (const l of data.leaves)
      if (
        l.employee_id === e.id &&
        l.status === "approved" &&
        String(l.start) <= day &&
        day <= String(l.end)
      )
        reasons.push(
          l.kind === "comp_off" ? "Comp-off" : "Leave / unavailable",
        );
    if (data.holidays.some((h) => h.day === day))
      reasons.push("Company holiday");
    return reasons.length ? reasons.join(" · ") : "Unassigned / available";
  }
  async function run(task: () => Promise<void>) {
    setLoading(true);
    setError("");
    setNotice("");
    try {
      await task();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }
  async function refresh() {
    setData(await api<Data>("/data"));
  }
  async function load() {
    try {
      setRoster(await api<Roster>(`/rosters/${year}/${mo}`));
    } catch (e) {
      setRoster(null);
      if (!(e instanceof Error && e.message === "Generate this month first"))
        throw e;
    }
  }
  useEffect(() => {
    void run(refresh);
  }, []);
  useEffect(() => {
    void run(load);
  }, [month]);
  function label(kind: string, id: Value | undefined) {
    return data[kind]?.find((r) => r.id === Number(id))?.name ?? `#${id}`;
  }
  const demand = (id: number) => data.demands.find((d) => d.id === id);
  const filtered = (roster?.slots ?? []).filter((s) => {
    const d = demand(s.demand_id),
      e = data.employees.find((e) => e.id === s.employee_id);
    return (
      (!filter.employee_id || s.employee_id === +filter.employee_id) &&
      (!filter.brand_id || d?.brand_id === +filter.brand_id) &&
      (!filter.process_id || d?.process_id === +filter.process_id) &&
      (!filter.pod_id || e?.pod_id === +filter.pod_id)
    );
  });
  const coverage = roster?.coverage_required
    ? Math.round((roster.coverage_filled / roster.coverage_required) * 100)
    : 0;
  const issues = [...(roster?.conflicts ?? []), ...(roster?.shortages ?? [])];
  function newRecord(kind: string) {
    const defaults: Row = {
      id: Math.max(0, ...data[kind].map((r) => r.id)) + 1,
    };
    for (const f of schemas[kind])
      defaults[f.key] =
        f.type === "boolean"
          ? true
          : f.type === "number"
            ? f.key === "max_work_days"
              ? 26
              : f.key === "weekly_off"
                ? 6
                : f.key === "lead_employee_id"
                  ? 0
                  : 1
            : f.type === "list"
              ? []
              : f.type === "dates"
                ? []
                : (f.options?.[0] ?? "");
    if (kind === "brands" || kind === "demands")
      defaults.operating_weekdays = [0, 1, 2, 3, 4, 5, 6];
    setForm({ kind, row: defaults, exists: false });
  }
  async function saveForm() {
    if (!form) return;
    await run(async () => {
      const row = { ...form.row };
      if (form.kind === "pods" && !row.lead_employee_id)
        delete row.lead_employee_id;
      await api(
        `/${form.kind}${form.exists ? `/${form.row.id}` : ""}`,
        form.exists ? "PUT" : "POST",
        row,
      );
      setForm(null);
      await refresh();
      await load();
      setNotice(
        "Saved. Existing rosters were revalidated against current availability.",
      );
    });
  }
  async function edit(previewOnly: boolean) {
    if (!editing || !roster) return;
    const replacement = { ...editing, employee_id: +candidate };
    const slots = roster.slots.includes(editing)
      ? roster.slots.map((s) => (s === editing ? replacement : s))
      : [...roster.slots, replacement];
    await run(async () => {
      const result = await api<Roster>(`/rosters/${year}/${mo}`, "PUT", {
        revision: roster.revision,
        slots,
        preview: previewOnly,
      });
      if (previewOnly) setPreview(result);
      else {
        setRoster(result);
        setEditing(null);
        setNotice("Assignment saved and constraints verified.");
      }
    });
  }
  const kind =
    page === "Employees"
      ? "employees"
      : page === "Brands"
        ? "brands"
        : page === "Pods"
          ? "pods"
          : page === "Processes"
            ? "processes"
            : page === "Assignments"
              ? "demands"
              : page === "Leave & holidays"
                ? tab
                : "";
  function monthShift(offset: number) {
    const d = new Date(year, mo - 1 + offset, 1);
    setMonth(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`);
  }
  return (
    <div className="app">
      <aside>
        <a className="logo" href="#" onClick={() => setPage("Overview")}>
          <span className="logo-mark">
            d<span>✳</span>
          </span>
          datastraw<span className="ai">AI</span>
        </a>
        <div className="workspace">
          <span className="avatar">DS</span>
          <div>
            Demo workspace<small>SMART ROSTER MANAGEMENT</small>
          </div>
          <span className="live-dot" />
        </div>
        <div className="nav-caption">WORKSPACE</div>
        <nav>
          {menu.map(([name, Icon]) => (
            <button
              key={name}
              aria-current={page === name ? "page" : undefined}
              className={page === name ? "selected" : ""}
              onClick={() => {
                setPage(name);
                setSearch("");
              }}
            >
              <Icon size={18} />
              {name}
              {name === "Conflicts" && issues.length > 0 && (
                <span className="count">{issues.length}</span>
              )}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="engine">
            <span className="live-dot" />
            Constraint-aware scheduling<small>Powered by OR-Tools CP-SAT</small>
          </div>
          <button onClick={() => setSettings(true)}>
            <Settings size={17} /> Workspace settings
          </button>
          <div className="candidate">
            <span className="avatar light">MW</span>
            <div>
              Mohit Wankhede<small>AI + Tech Intern assessment</small>
            </div>
          </div>
        </div>
      </aside>
      <main>
        <header>
          <span>
            Workspace <span className="slash">/</span> <strong>{page}</strong>
          </span>
          <div className="header-actions">
            <span className="demo-tag">FICTIONAL DEMO DATA</span>
            <button
              aria-label="Open workspace settings"
              onClick={() => setSettings(true)}
            >
              <Settings size={15} />
            </button>
          </div>
        </header>
        <div className="content">
          <div className="page-heading">
            <div>
              <div className="eyebrow">OPERATIONS, IN SYNC</div>
              <h1>
                {page === "Overview" ? "A clearer view of your team." : page}
              </h1>
              <p>
                {page === "Overview"
                  ? "Plan with confidence. Keep every brand covered and every schedule clear."
                  : "Manage your operation with verified scheduling rules."}
              </p>
            </div>
            <button
              className="button secondary"
              disabled={loading}
              onClick={() =>
                void run(async () => {
                  await refresh();
                  await load();
                })
              }
            >
              <RefreshCw size={15} />
              Refresh
            </button>
          </div>
          {error && (
            <div role="alert" className="alert error">
              {error}
            </div>
          )}
          {notice && (
            <div role="status" className="alert success">
              <Check size={16} />
              {notice}
            </div>
          )}
          {loading && (
            <div role="status" className="loading">
              Updating workspace…
            </div>
          )}
          <div className="toolbar">
            <div className="month">
              <button
                aria-label="Previous month"
                onClick={() => monthShift(-1)}
              >
                <ChevronLeft size={16} />
              </button>
              <label>
                <CalendarDays size={16} />
                <input
                  aria-label="Roster month"
                  type="month"
                  min="2000-01"
                  max="2100-12"
                  value={month}
                  onChange={(e) => setMonth(e.target.value)}
                />
              </label>
              <button aria-label="Next month" onClick={() => monthShift(1)}>
                <ChevronRight size={16} />
              </button>
            </div>
            <div className="toolbar-right">
              <span className="pill">
                {roster ? `Revision ${roster.revision}` : "No saved roster"}
              </span>
              <button
                className="button primary"
                disabled={loading}
                onClick={() => {
                  if (
                    roster &&
                    !window.confirm(
                      "Regenerate this month? This replaces saved manual changes.",
                    )
                  )
                    return;
                  void run(async () => {
                    setRoster(
                      await api<Roster>("/rosters/generate", "POST", {
                        year,
                        month: mo,
                      }),
                    );
                    setNotice(
                      "Roster generated. Review any reported shortages before operational use.",
                    );
                  });
                }}
              >
                <Plus size={16} />
                Generate roster
              </button>
            </div>
          </div>
          {data.employees.length === 0 && (
            <div className="empty">
              <h2>Start with a demonstration workspace</h2>
              <p>
                33 fictional employees, 25 brands (80% single-resource), 3 pods,
                calendars and deliberate shortages.
              </p>
              <button
                className="button primary"
                disabled={loading}
                onClick={() =>
                  void run(async () => {
                    await api("/seed", "POST");
                    await refresh();
                    setNotice(
                      "Demo data initialized. Generate November 2026 to explore.",
                    );
                  })
                }
              >
                Initialize demo data
              </button>
            </div>
          )}
          {page === "Overview" && (
            <>
              <div className="stats">
                {[
                  [
                    "Total employees",
                    data.employees.length,
                    "Across " + data.pods.length + " operational pods",
                  ],
                  [
                    "Active brands",
                    data.brands.length,
                    "Single & multi-resource teams",
                  ],
                  [
                    "Coverage",
                    `${coverage}%`,
                    roster
                      ? `${roster.coverage_filled} of ${roster.coverage_required} required assignments`
                      : "Generate a month to calculate",
                  ],
                  [
                    "Issues to review",
                    issues.length,
                    "Shortages and hard-constraint conflicts",
                  ],
                ].map(([title, value, sub], i) => (
                  <article className="stat" key={title}>
                    <div>
                      {title}
                      <span className={"stat-icon s" + i}>
                        {i === 0 ? (
                          <Users size={18} />
                        ) : i === 1 ? (
                          <Building2 size={18} />
                        ) : i === 2 ? (
                          <ChartNoAxesCombined size={18} />
                        ) : (
                          <ShieldAlert size={18} />
                        )}
                      </span>
                    </div>
                    <strong>{value}</strong>
                    <small>{sub}</small>
                  </article>
                ))}
              </div>
              <div className="overview-grid">
                <section className="panel">
                  <div className="panel-title">
                    <div>
                      <h2>Monthly coverage</h2>
                      <p>Required staffing across your brands</p>
                    </div>
                    <button
                      className="text-button"
                      onClick={() => setPage("Analytics")}
                    >
                      View analytics <ArrowUpRight size={14} />
                    </button>
                  </div>
                  <div className="coverage-hero">
                    <div
                      className="ring"
                      style={{
                        background: `conic-gradient(#3e806b ${coverage}%,#eaf0ed 0)`,
                      }}
                    >
                      <div>
                        <strong>{coverage}%</strong>
                        <small>coverage</small>
                      </div>
                    </div>
                    <div>
                      <span className="eyebrow">SCHEDULE HEALTH</span>
                      <h2>
                        {!roster
                          ? "Ready when you are"
                          : roster.valid
                            ? "Coverage verified"
                            : "Review staffing gaps"}
                      </h2>
                      <p>
                        {!roster
                          ? "Generate your first monthly roster to see coverage and workload."
                          : `${roster.shortages.length} brand / process / day shortages need your attention.`}
                      </p>
                      <span
                        className={
                          "status-badge " + (roster?.valid ? "good" : "warn")
                        }
                      >
                        {roster?.valid
                          ? "Verified feasible"
                          : roster
                            ? "Action required"
                            : "Awaiting generation"}
                      </span>
                    </div>
                  </div>
                  <div className="panel-footer">
                    <span className="live-dot" />
                    Hard constraints are checked before every save.
                  </div>
                </section>
                <section className="panel">
                  <div className="panel-title">
                    <div>
                      <h2>Your workspace</h2>
                      <p>The building blocks of a reliable roster</p>
                    </div>
                  </div>
                  {[
                    ["Pods", data.pods.length, "Operational teams"],
                    [
                      "Processes",
                      data.processes.length,
                      "Employee skill eligibility",
                    ],
                    [
                      "Assignments",
                      data.demands.length,
                      "Brand & process staffing rules",
                    ],
                    [
                      "Leave & holidays",
                      data.leaves.length + data.holidays.length,
                      "Availability exceptions",
                    ],
                  ].map(([title, value, sub]) => (
                    <button
                      className="workspace-row"
                      key={title}
                      onClick={() => setPage(String(title))}
                    >
                      <span>
                        <strong>{title}</strong>
                        <small>{sub}</small>
                      </span>
                      <b>{value}</b>
                      <ChevronRight size={16} />
                    </button>
                  ))}
                </section>
              </div>
              <section className="panel bottom-panel">
                <div>
                  <span className="eyebrow">NEXT STEP</span>
                  <h2>A month of work. One shared view.</h2>
                  <p>
                    Explore employee, brand, process and pod schedules in the
                    roster calendar.
                  </p>
                </div>
                <button
                  className="button secondary"
                  onClick={() => setPage("Roster calendar")}
                >
                  Open roster <ArrowUpRight size={15} />
                </button>
              </section>
            </>
          )}
          {kind && (
            <section className="panel">
              <div className="panel-title">
                <div>
                  <h2>
                    {page === "Leave & holidays"
                      ? tab === "leaves"
                        ? "Employee leave"
                        : "Company holidays"
                      : page}
                  </h2>
                  <p>
                    {data[kind].length} records · IDs are shown for
                    cross-reference
                  </p>
                </div>
                <button
                  className="button primary"
                  onClick={() => newRecord(kind)}
                >
                  <Plus size={16} />
                  Add {kind === "employees" ? "employee" : "record"}
                </button>
              </div>
              {page === "Leave & holidays" && (
                <div className="tabs">
                  <button
                    className={tab === "leaves" ? "active" : ""}
                    onClick={() => setTab("leaves")}
                  >
                    Leave
                  </button>
                  <button
                    className={tab === "holidays" ? "active" : ""}
                    onClick={() => setTab("holidays")}
                  >
                    Holidays
                  </button>
                </div>
              )}
              <div className="table-tools">
                <input
                  aria-label="Search records"
                  placeholder="Search records…"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                <span>
                  Tip: employee IDs connect skills, assignments, absences and
                  pod leads.
                </span>
              </div>
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>ID</th>
                      {schemas[kind].map((f) => (
                        <th key={f.key}>{f.label}</th>
                      ))}
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data[kind]
                      .filter((r) =>
                        JSON.stringify(r)
                          .toLowerCase()
                          .includes(search.toLowerCase()),
                      )
                      .map((r) => (
                        <tr key={r.id}>
                          <td className="muted">#{r.id}</td>
                          {schemas[kind].map((f) => (
                            <td key={f.key}>
                              {Array.isArray(r[f.key])
                                ? (r[f.key] as (number | string)[]).join(
                                    ", ",
                                  ) || "—"
                                : typeof r[f.key] === "boolean"
                                  ? r[f.key]
                                    ? "Yes"
                                    : "No"
                                  : String(r[f.key] ?? "—")}
                            </td>
                          ))}
                          <td>
                            <div className="row-actions">
                              <button
                                onClick={() =>
                                  setForm({ kind, row: { ...r }, exists: true })
                                }
                              >
                                Edit
                              </button>
                              <button
                                className="danger"
                                onClick={() => {
                                  if (
                                    window.confirm(
                                      "Delete this record? Referenced records cannot be deleted.",
                                    )
                                  )
                                    void run(async () => {
                                      await api(`/${kind}/${r.id}`, "DELETE");
                                      await refresh();
                                      await load();
                                    });
                                }}
                              >
                                Delete
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
              {data[kind].length === 0 && (
                <p className="empty">
                  No records yet. Add a record to get started.
                </p>
              )}
            </section>
          )}
          {page === "Roster calendar" && (
            <section className="panel">
              <div className="panel-title">
                <div>
                  <h2>Monthly roster</h2>
                  <p>Select any assignment to preview and edit its employee.</p>
                </div>
                <span className="pill">{filtered.length} assignments</span>
              </div>
              <div className="filters">
                {(
                  ["employee_id", "brand_id", "process_id", "pod_id"] as const
                ).map((key) => (
                  <label key={key}>
                    {key.replace("_id", "")}
                    <select
                      aria-label={`Filter ${key}`}
                      value={filter[key]}
                      onChange={(e) =>
                        setFilter({ ...filter, [key]: e.target.value })
                      }
                    >
                      <option value="">All {key.replace("_id", "")}s</option>
                      {data[
                        key === "employee_id"
                          ? "employees"
                          : key === "brand_id"
                            ? "brands"
                            : key === "process_id"
                              ? "processes"
                              : "pods"
                      ].map((r) => (
                        <option key={r.id} value={r.id}>
                          {r.name}
                        </option>
                      ))}
                    </select>
                  </label>
                ))}
              </div>
              {!roster ? (
                <p className="empty">
                  Generate this month to view assignments.
                </p>
              ) : (
                <div className="calendar">
                  {filter.pod_id && (
                    <p className="panel-footer">
                      Pod lead:{" "}
                      {label(
                        "employees",
                        data.pods.find((p) => p.id === +filter.pod_id)
                          ?.lead_employee_id,
                      )}
                    </p>
                  )}
                  <div className="weekdays">
                    {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map(
                      (d) => (
                        <span key={d}>{d}</span>
                      ),
                    )}
                  </div>
                  <div className="days">
                    {Array.from(
                      { length: (new Date(year, mo - 1, 1).getDay() + 6) % 7 },
                      (_, i) => (
                        <div className="day blank" key={"b" + i} />
                      ),
                    )}
                    {Array.from(
                      { length: new Date(year, mo, 0).getDate() },
                      (_, i) => {
                        const day = `${month}-${String(i + 1).padStart(2, "0")}`,
                          slots = filtered.filter((s) => s.day === day),
                          gaps = roster.shortages.filter(
                            (s) => s.day === day,
                          ).length;
                        return (
                          <div className="day" key={day}>
                            <div className="day-number">
                              {i + 1}
                              {gaps > 0 && (
                                <span
                                  title="Coverage shortages"
                                  className="gap-dot"
                                />
                              )}
                            </div>
                            {slots.map((s) => (
                              <button
                                className="slot"
                                key={s.employee_id + "-" + s.demand_id}
                                onClick={() => {
                                  setEditing(s);
                                  setCandidate(String(s.employee_id));
                                  setPreview(null);
                                }}
                              >
                                <strong>
                                  {label("employees", s.employee_id)}
                                </strong>
                                <span>
                                  {label(
                                    "brands",
                                    demand(s.demand_id)?.brand_id,
                                  )}{" "}
                                  ·{" "}
                                  {label(
                                    "processes",
                                    demand(s.demand_id)?.process_id,
                                  )}
                                </span>
                              </button>
                            ))}
                            <button
                              className="add-slot"
                              aria-label={`Add assignment ${day}`}
                              onClick={() => {
                                setEditing({
                                  day,
                                  employee_id: 0,
                                  demand_id: data.demands[0]?.id ?? 0,
                                });
                                setCandidate(
                                  String(data.employees[0]?.id ?? 0),
                                );
                                setPreview(null);
                              }}
                            >
                              + Assignment
                            </button>
                            {slots.length === 0 && (
                              <small className="muted">
                                {filter.employee_id
                                  ? offReasons(
                                      day,
                                      data.employees.find(
                                        (e) => e.id === +filter.employee_id,
                                      )!,
                                    )
                                  : "No assignments"}
                              </small>
                            )}
                          </div>
                        );
                      },
                    )}
                  </div>
                </div>
              )}
            </section>
          )}
          {page === "Conflicts" && (
            <section className="panel">
              <div className="panel-title">
                <div>
                  <h2>Schedule validation</h2>
                  <p>
                    Results from deterministic rules. Shortages never count as a
                    valid roster.
                  </p>
                </div>
                <span className="status-badge warn">
                  {issues.length} issues
                </span>
              </div>
              {!roster ? (
                <p className="empty">Generate a roster to inspect conflicts.</p>
              ) : issues.length === 0 ? (
                <p className="empty">
                  No shortages or hard-constraint conflicts detected.
                </p>
              ) : (
                <div className="issue-list">
                  {issues.map((issue, i) => (
                    <article key={i} className="issue">
                      <ShieldAlert size={18} />
                      <div>
                        <strong>
                          {issue.type === "shortage"
                            ? `${label("brands", demand(issue.demand_id!)?.brand_id)} · ${label("processes", demand(issue.demand_id!)?.process_id)}`
                            : issue.type.replace("_", " ")}
                        </strong>
                        <p>
                          {issue.day ?? issue.slot?.day}{" "}
                          {issue.required !== undefined
                            ? `· ${issue.filled} / ${issue.required} required staff`
                            : ""}{" "}
                          {issue.reasons?.join(", ")}
                        </p>
                        {issue.candidates && (
                          <details>
                            <summary>
                              Why coverage is short · {issue.candidates.length}{" "}
                              assigned candidates
                            </summary>
                            {issue.candidates.length === 0 ? (
                              <p>No employees are assigned to this demand.</p>
                            ) : (
                              issue.candidates.map((c) => (
                                <p key={c.employee_id}>
                                  {label("employees", c.employee_id)}:{" "}
                                  {c.reasons.join(", ") ||
                                    "available; competing demand or workload objective"}
                                </p>
                              ))
                            )}
                            <p>
                              Review eligibility and availability, then add a
                              suitable employee in Assignments and regenerate.
                            </p>
                          </details>
                        )}
                      </div>
                      <span className="status-badge warn">
                        {issue.type === "shortage"
                          ? `${issue.missing} missing`
                          : "Conflict"}
                      </span>
                    </article>
                  ))}
                </div>
              )}
            </section>
          )}
          {page === "Analytics" && (
            <section className="panel">
              <div className="panel-title">
                <div>
                  <h2>Coverage & workload</h2>
                  <p>
                    {roster
                      ? `${roster.coverage_filled} / ${roster.coverage_required} required slots filled · ${roster.solver_status}`
                      : "Generate a roster to calculate workload."}
                  </p>
                </div>
                <span className="pill">
                  {roster?.optimal
                    ? "Optimal objective proven"
                    : "No optimality claim"}
                </span>
              </div>
              <div className="workloads">
                {data.employees.map((e) => {
                  const value = roster?.workload[e.id] ?? 0;
                  return (
                    <div className="workload" key={e.id}>
                      <span>{e.name}</span>
                      <div className="bar">
                        <div style={{ width: `${(value / 31) * 100}%` }} />
                      </div>
                      <strong>{value} days</strong>
                      <small>limit {e.max_work_days}</small>
                    </div>
                  );
                })}
              </div>
            </section>
          )}
          <footer>
            Datastraw Smart Roster{" "}
            <span>
              Built for clear decisions. Verified by scheduling rules.
            </span>
          </footer>
        </div>
      </main>
      {form && (
        <div className="modal-backdrop">
          <form
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-label={`Edit ${form.kind}`}
            onSubmit={(e) => {
              e.preventDefault();
              void saveForm();
            }}
          >
            <div className="panel-title">
              <h2>
                {form.exists ? "Edit" : "Add"} {form.kind}
              </h2>
              <button
                type="button"
                aria-label="Close form"
                onClick={() => setForm(null)}
              >
                <X size={20} />
              </button>
            </div>
            <div className="form-fields">
              <label>
                Record ID
                <input
                  type="number"
                  min="1"
                  required
                  disabled={form.exists}
                  value={form.row.id}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      row: { ...form.row, id: +e.target.value },
                    })
                  }
                />
              </label>
              {schemas[form.kind].map((f) => (
                <label key={f.key}>
                  {f.label}
                  {f.type === "boolean" ? (
                    <input
                      type="checkbox"
                      checked={Boolean(form.row[f.key])}
                      onChange={(e) =>
                        setForm({
                          ...form,
                          row: { ...form.row, [f.key]: e.target.checked },
                        })
                      }
                    />
                  ) : f.type === "select" ? (
                    <select
                      value={String(form.row[f.key] ?? "")}
                      onChange={(e) =>
                        setForm({
                          ...form,
                          row: { ...form.row, [f.key]: e.target.value },
                        })
                      }
                    >
                      {f.options!.map((o) => (
                        <option key={o}>{o}</option>
                      ))}
                    </select>
                  ) : (
                    <input
                      required={f.type !== "list" && f.type !== "dates"}
                      type={
                        f.type === "number"
                          ? "number"
                          : f.type === "date"
                            ? "date"
                            : "text"
                      }
                      defaultValue={
                        Array.isArray(form.row[f.key])
                          ? (form.row[f.key] as (number | string)[]).join(", ")
                          : String(form.row[f.key] ?? "")
                      }
                      onChange={(e) =>
                        setForm({
                          ...form,
                          row: {
                            ...form.row,
                            [f.key]:
                              f.type === "number"
                                ? Number(e.target.value)
                                : f.type === "list"
                                  ? e.target.value
                                      .split(",")
                                      .map((s) => s.trim())
                                      .filter(Boolean)
                                      .map(Number)
                                  : f.type === "dates"
                                    ? e.target.value
                                        .split(",")
                                        .map((s) => s.trim())
                                        .filter(Boolean)
                                    : e.target.value,
                          },
                        })
                      }
                    />
                  )}
                  <small>
                    {f.help ??
                      (f.type === "list"
                        ? "Comma-separated IDs / weekday numbers"
                        : "")}
                  </small>
                </label>
              ))}
            </div>
            {error && (
              <p role="alert" className="alert error">
                {error}
              </p>
            )}
            <div className="modal-actions">
              <button
                type="button"
                className="button secondary"
                onClick={() => setForm(null)}
              >
                Cancel
              </button>
              <button className="button primary" disabled={loading}>
                Save record
              </button>
            </div>
          </form>
        </div>
      )}
      {editing && (
        <div className="modal-backdrop">
          <section
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-label="Edit assignment"
          >
            <div className="panel-title">
              <h2>Edit assignment</h2>
              <button
                aria-label="Close editor"
                onClick={() => setEditing(null)}
              >
                <X size={20} />
              </button>
            </div>
            <p>
              {editing.day} ·{" "}
              {label("brands", demand(editing.demand_id)?.brand_id)}
            </p>
            {editing.employee_id === 0 && (
              <label>
                Brand / process demand
                <select
                  aria-label="Assignment demand"
                  value={editing.demand_id}
                  onChange={(e) => {
                    setEditing({ ...editing, demand_id: +e.target.value });
                    setPreview(null);
                  }}
                >
                  {data.demands.map((d) => (
                    <option key={d.id} value={d.id}>
                      {label("brands", d.brand_id)} ·{" "}
                      {label("processes", d.process_id)}
                    </option>
                  ))}
                </select>
              </label>
            )}
            <label>
              Assigned employee
              <select
                aria-label="Assigned employee"
                value={candidate}
                onChange={(e) => {
                  setCandidate(e.target.value);
                  setPreview(null);
                }}
              >
                {data.employees.map((e) => (
                  <option key={e.id} value={e.id}>
                    {e.name}
                  </option>
                ))}
              </select>
            </label>
            <p className="muted">
              Preview checks availability, weekly offs, skills, conflicting
              brand shifts and coverage before saving.
            </p>
            {preview && (
              <div
                role="status"
                className={
                  "alert " + (preview.conflicts.length ? "error" : "success")
                }
              >
                {preview.conflicts.length} hard conflicts ·{" "}
                {preview.shortages.length} shortages
                {preview.conflicts.map((c, i) => (
                  <p key={i}>
                    {c.type}: {c.reasons?.join(", ") ?? c.employee_id}
                  </p>
                ))}
              </div>
            )}
            {error && (
              <p role="alert" className="alert error">
                {error}
              </p>
            )}
            <div className="modal-actions">
              {editing.employee_id !== 0 && (
                <button
                  className="button secondary"
                  disabled={loading}
                  onClick={() => {
                    if (
                      !window.confirm(
                        "Remove this assignment? Saving will be rejected if it reduces required coverage.",
                      )
                    )
                      return;
                    void run(async () => {
                      const result = await api<Roster>(
                        `/rosters/${year}/${mo}`,
                        "PUT",
                        {
                          revision: roster!.revision,
                          slots: roster!.slots.filter((s) => s !== editing),
                          preview: false,
                        },
                      );
                      setRoster(result);
                      setEditing(null);
                      setNotice("Assignment removed after validation.");
                    });
                  }}
                >
                  Remove
                </button>
              )}
              <button
                className="button secondary"
                disabled={loading}
                onClick={() => void edit(true)}
              >
                Preview impact
              </button>
              <button
                className="button primary"
                disabled={loading || !preview || preview.conflicts.length > 0}
                onClick={() => void edit(false)}
              >
                Save assignment
              </button>
            </div>
          </section>
        </div>
      )}
      {settings && (
        <div className="modal-backdrop">
          <form
            className="modal"
            onSubmit={(e) => {
              e.preventDefault();
              setSettings(false);
            }}
          >
            <div className="panel-title">
              <h2>Workspace settings</h2>
              <button
                type="button"
                aria-label="Close settings"
                onClick={() => setSettings(false)}
              >
                <X size={20} />
              </button>
            </div>
            <label>
              Admin token
              <input
                type="password"
                autoComplete="off"
                defaultValue={sessionStorage.getItem("adminToken") ?? ""}
                onChange={(e) =>
                  sessionStorage.setItem("adminToken", e.target.value)
                }
              />
            </label>
            <p className="muted">
              Required only when ADMIN_TOKEN is configured on the server. Stored
              for this browser session. Gemini recommendations are not enabled.
            </p>
            <button className="button primary">Done</button>
          </form>
        </div>
      )}
    </div>
  );
}
const root = document.getElementById("root");
if (root)
  createRoot(root).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  );
