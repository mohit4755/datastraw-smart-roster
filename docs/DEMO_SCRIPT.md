# 4–5 minute demonstration — Mohit Vijay Wankhede

## Recording readiness

This is a recording plan and complete English script, not an existing video. Record only after public deployment and browser acceptance pass. Do not call the application deployed until that is verified. Use November 2026 and a freshly seeded demo workspace; keep secrets out of every screen.

Record at 1920×1080, 100% browser zoom and approximately 120 spoken words per minute. Use OBS Studio or the operating system's screen recorder, with microphone on and notifications off. Make one rehearsal, record, review the complete file, then upload it with viewer access enabled. Open the video link signed out before adding it to the email.

## Screen-by-screen sequence and speaking script

### 0:00–0:25 — Overview

Screen: public application → Overview, with the URL visible briefly.

“Hello, I am Mohit Vijay Wankhede, an MCA student at ASM's IBMR in Pune. This is my Smart Roster Management System for the Datastraw AI and Tech Intern assessment. It helps an operations manager organize employees, generate monthly schedules and identify staffing gaps before the roster is used.”

### 0:25–0:55 — Problem and data model

Screen: Employees → Pods → Brands; point to a pod lead and weekly-off field.

“The main challenge is that different brands follow different operating rules. An employee's leave or weekly off can affect more than one process. The sample workspace contains 33 fictional employees, three pods and 25 brands. Twenty brands have one dedicated employee. The other five have two or three employees, including shared and separate process responsibilities. Pod leads and employee skills are configurable.”

Expected: records, IDs, pod leads and process eligibility are visible. Do not claim those are real employees.

### 0:55–1:35 — Calendars, leave and generation

Screen: Assignments → Brand 01 and a multi-resource brand; Leave & holidays; select November 2026; Generate roster.

“Working calendars are separate from employee availability. I can configure a brand to operate every day, to close on company holidays, or to close on Sundays. A process can add its own working-day restrictions. Minimum staffing can also vary across the week. Approved leave and comp-offs are stored separately. Now I select November 2026 and generate the roster. The solver first maximizes required coverage and then tries to balance working days.”

Expected: generation finishes, a revision appears and shortages remain explicitly visible. Do not promise a particular count; read the actual result.

### 1:35–2:15 — Views and constraints

Screen: Roster calendar → filter Brand 01; then employee 1, pod 1 and process 2; clear filters.

“Here is the monthly calendar. These filters show the company, pod, brand, process and employee views. The employee view also labels weekly offs, approved absences and unassigned days. One daily brand shift can cover several eligible processes for that same brand. The employee cannot work for two different brands on the same day. Monthly workload counts working days, rather than counting each process as another full day.”

Expected: filters change visible assignments; no incompatible brand overlap is accepted. A same-brand multi-process day is an explicitly documented assumption, not two independent shifts.

### 2:15–2:55 — Explain a shortage

Screen: Conflicts → expand a Brand 01 shortage or another shortage actually shown.

“The application does not call an incomplete schedule valid. This panel shows the required and filled staff count for each affected day and process. Expanding an issue explains whether assigned employees are on leave, on a weekly off, at their monthly limit, or allocated elsewhere. A dedicated single-resource brand can be impossible to cover on the employee's approved leave. The manager must add a suitable backup or change an operational requirement explicitly.”

Expected: a shortage is shown with reasons. If generation is only feasible, state that maximum coverage was not proven.

### 2:55–3:45 — Change after generation and resolve it

Screen: select an employee with a visible saved assignment. Add approved one-day leave on that assignment date. Return to Conflicts. Then add a qualified backup to the demand and use calendar `+ Assignment` to fill the missing coverage, or regenerate the month.

“Next I add approved leave after generation. The saved roster is revalidated against the new availability. The assignment becomes a conflict and coverage falls, so the change is visible immediately. I can add an eligible backup to the brand and process. A manual edit has an impact preview. An employee from the wrong pod, or someone already on another brand, is rejected. After selecting a suitable available employee, I preview again and save. I reload the page to verify persistence.”

Expected: invalid preview → disabled save; valid replacement → revision increments; reload retains it. Select a backup from the same pod with the process skill, no absence and a free day. If a different date remains conflicted, resolve all hard conflicts or regenerate rather than claim one edit repaired everything.

### 3:45–4:30 — Architecture, tests and limits

Screen: Analytics, then repository README and test summary.

“The frontend uses React and TypeScript. FastAPI validates requests, and SQLAlchemy stores the workspace transactionally. The scheduling engine uses Google OR-Tools CP-SAT, with an independent validator for generated and edited schedules. I used AI-assisted development and reviewed the models, constraints and tests. The README records the exact executed test results and remaining verification. This assessment version stores one workspace document, so normalized tables and audit history are future improvements. Gemini is optional and is not enabled in this version.”

Expected: state only the current test counts from TEST_SUMMARY.md and the real deployment status.

### 4:30–4:45 — Close

Screen: Overview.

“The priority of this project is reliable scheduling with clear limitations. It keeps hard-rule violations visible, reports missing coverage and leaves operational decisions under human control. Thank you for reviewing my assessment.”

## Rehearsal scenarios

| Scenario | Setup | Expected result |
|---|---|---|
| Single-resource absence | Employee 1 approved leave 3–4 November | Brand 01 shortages, no generated leave-day allocation |
| Sunday/holiday difference | Compare brand calendars and demand weekday rules | Calendar operates only on configured days |
| Comp-off | Employee 12 approved comp-off 9–11 November | No generated assignment on those days |
| Multi-resource need | Brand 24, two required support resources | Filled count evaluated against two, not just one |
| Invalid edit | Choose wrong-pod employee | Preview conflict and rejected save |
| Cross-brand overlap | Choose employee working a different brand that day | Double-booking conflict |
| Safe same-brand processes | Employee qualified for both Brand 01 processes | One compatible brand shift; one workload day |
| Changed availability | Add approved leave to a saved work day | Conflict and coverage gap reported without deleting history |

## Recording steps

1. Complete deployment, browser workflow and link checks.
2. Seed a disposable demo workspace and rehearse the exact dates and candidates.
3. Start recorder, select only browser window, choose microphone and make a 10-second sound check.
4. Follow the sequence; pause naturally while the solver runs.
5. Stop, watch all footage and confirm audio, date selection, URLs and claimed results.
6. Trim only setup/ending dead time; keep the actual error rejection and persistence reload visible.
7. Upload the 3–5 minute file, enable link viewing, test signed out and update the submission draft.
