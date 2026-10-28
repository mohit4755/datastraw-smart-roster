# Original assessment requirement-to-implementation acceptance

Source: **AI Internship Assessment.pdf**, seven pages, attached to the Datastraw assessment email dated 28 October 2026. Full extracted text was read. The PDF specifies a four-day submission window; the recruiter did not provide a precise cutoff timestamp in the inspected email. User instructions additionally restrict app hosting to Vercel.

Status means local evidence only unless stated. **Pass** = executed automated checks support implementation; **Partial** = implemented but browser/production evidence is missing or an assumption limits scope; **Blocked** = required external deliverable is not available. No overall acceptance pass is claimed.

| Requirement (PDF section/page) | Implementation | Test evidence | Status |
|---|---|---|---|
| Central employee/brand/process/pod/allocation database (2, p2) | models.py, store.py, api.py; transactional workspace | CRUD/reference/rollback integration tests | Pass locally; hosted DB blocked |
| At least 30 employees (3A, p2) | seed.py: 33 fictional employees | test_original_pdf_seed_patterns | Pass |
| Multiple brands and pods (3A) | 25 brands, 3 pods | Seed and reference tests | Pass |
| Multiple processes/different employee skills (3A) | 3 processes and process_ids | Eligibility checks and seed tests | Pass |
| One or more assigned employees per brand (3A) | demand employee pools | Seed pattern/reference tests | Pass |
| Pod leads (3A) | Pod.lead_employee_id, same-pod validation, pod-view lead label | Seed lead assertion and invalid-lead API test | Pass locally; browser lead label verified |
| Multi-brand/process assignments (3A) | Editable demand pools, process skills, brand-shift variables | Overlap rejection and compatible-process tests | Pass |
| Approximately 80% single-resource sample (3A) | 20/25 brands, one dedicated employee per single-resource brand | test_original_pdf_seed_patterns asserts .8 | Pass |
| Remaining brands generally 2–3 employees (3A) | Five multi-resource brand pools | Seed pool-size assertions | Pass |
| Separate and overlapping process assignments (3A) | Multi-resource CS/ACC demands | Seed and process tests | Pass locally |
| More than one staff for a process (3A) | min_staff and weekday staffing | Required=2 scenario | Pass |
| Add/edit/remove assignments without code changes (3A) | Demand CRUD and UI form | CRUD/reference tests | Pass API; UI partial |
| 365-day operations including holidays (3B, p3) | Brand full weekdays, holidays_closed=false | Operating/holiday integration scenarios | Pass locally |
| Daily operations except public holidays (3B) | Brand full weekdays, holidays_closed=true | Holiday exclusion assertions | Pass |
| Sundays/public holidays off (3B) | Weekdays 0..5, holiday closure | Calendar and holiday tests | Pass |
| Different process calendars within brand (3B) | Demand operating_weekdays and holiday closure | test_process_calendar_daily_staffing_and_bundled_brand_shift | Pass |
| Minimum staffing on particular days (3B) | Seven-value weekday staffing vector | Monday=2 fixture and malformed-vector rejection | Pass; date-specific overrides not modeled |
| Different employee weekly offs within brand (3B) | Per-employee weekly_off | Weekly-off constraints and seed | Pass |
| Brand calendar separate from employee schedule (3B) | operates() versus eligible() | Closed-calendar/absence tests | Pass |
| Month selection and entire-team generation (3C) | Generate model, CP-SAT, dashboard month input | API generation, invalid-month tests | Pass locally; production blocked |
| Leave, approved comp-offs, availability (3C) | Leave.kind/status/range, active flag | Comp-off validation, absence/availability tests | Pass |
| Employee preferences where applicable (3C/D) | Hard weekly offs explicitly distinguished from optional preferences | README assumption and fairness test | Partial; optional preferred-off model absent |
| Show work, off and coverage by day (3C) | Calendar slots, employee off labels, conflict daily counts | Component calendar tests; rule tests | Partial; screenshot inspection passed, exhaustive view audit pending |
| Never silently create invalid schedule (3C/D) | Independent validate(), valid flag and shortages | Generation/constraint/shortage assertions | Pass |
| No assigned employee available (3D, p3) | Candidate shortage reasons | Leave/weekly-off/work-limit cases | Pass |
| Overlapping/incompatible responsibilities (3D) | At most one brand shift/day, no duplicate slots | Cross-brand/duplicate-edit rejection | Pass under documented full-day model |
| Weekly offs/leave versus coverage (3D) | Excluded allocations with explicit shortage | Weekly-off/leave tests | Pass |
| Insufficient staff for process/day (3D) | Exact required, filled and missing | Staffing-vector and shortage assertions | Pass |
| Changes causing gaps across accounts (3D/F, p4) | Current configuration revalidation and impact | Availability preview/save impact tests | Pass locally |
| Mandatory constraints versus preferences (3D) | Hard-rule checks, coverage-first objective, fairness secondary | Invalid-edit rejection and optimization scenarios | Pass for implemented model |
| Company-wide monthly view (3E) | Unfiltered calendar | Component render and real browser workflow | Pass locally |
| Pod view under pod lead (3E) | Pod filter and lead label | API + browser pod filter and lead label | Pass locally |
| Brand assigned staff/process/daily coverage (3E) | Brand filter, assignments, conflict details | API brand filter; component calendar | Partial; combined UI coverage view needs browser review |
| Process staffing/work schedules (3E) | Process filter, demand rules, daily issue panel | Model/rule/API and browser process filter | Pass locally |
| Employee work/off/holiday/leave view (3E) | Employee filter and day absence labels | API filters, rules, component and browser checks | Pass locally; all absence-label combinations not visually audited |
| Manual assignment/schedule editing and impact (3E) | CRUD, calendar add/replace, preview, safe PUT | Manual preview/reject/save/revision tests | Pass locally; production blocked |
| Demonstrate change after generation (3F) | Availability update, impact and fresh validation | test_availability_impact_preview_and_save; demo script | Pass integration; recorded demo blocked |
| Dedicated employee unavailable resolution (3F) | Flag shortage; add eligible backup; regenerate/edit | Leave and shortage tests | Pass locally |
| Evaluate remaining multi-resource team (3F) | Revalidate exact coverage against requirement | Staffing and eligibility tests | Pass locally |
| Fictional realistic sample and assumptions (4, p4–5) | seed.py, README explicit assumptions | Seed mix and reference validation | Pass |
| Configurable additional rules/entities (4) | CRUD, weekday and staffing configuration | API CRUD and model tests | Pass locally |
| Explain approach/tool use and decisions (5, p5) | README and TECHNICAL_APPROACH.md; AI-assisted disclosure | Documentation reviewed | Pass documentation |
| Public app with realistic data (7, p6) | Vercel project and deployment configuration | No completed build/runtime deployment | Blocked: team consent + hosted DB |
| GitHub, README, setup, .env.example (7) | Existing repository and committed files | Git synchronization verification recorded in HANDOFF | Pending final push verification |
| 3–5 minute video incl. generation/calendars/conflicts/change (7) | DEMO_SCRIPT.md recording sequence | Narrated recording not created | Blocked |
| Short technical approach (7) | TECHNICAL_APPROACH.md | Implementation-grounded note | Pass documentation |
| Accessible LinkedIn profile (7) | Known candidate URL in submission draft | Identity corroborated by prior candidate materials; signed-out access not verified | Partial |
| Eight README reasoning answers (8, p6) | README “Tell us how you think” | All eight prompts answered | Pass documentation |
| Correct submission addresses/subject and five items (9, p6–7) | SUBMISSION_EMAIL.md; unsent draft | Exact recipients from user and PDF; missing live/video links labeled | Partial; do not send |

## Optional PDF features (6, p5)

| Optional feature | Status |
|---|---|
| Fair weekly-off distribution | Not implemented; fixed weekly offs respected |
| Preference-based scheduling | Not implemented |
| Automatic regeneration after leave | Not implemented; impact automatic, regeneration explicit |
| Backup recommendations | Basic candidate blockers/resolution guidance; no ranked recommendation engine |
| Alternative plan comparison | Not implemented |
| Pod/operations approval workflows | Not implemented |
| Change notifications | Not implemented |
| CSV/Excel/Sheets export | Not implemented |
| AI explanations | Deferred; deterministic explanations implemented |
| Add brands/pods/processes dynamically | Implemented via CRUD |

Final acceptance requires production evidence and remaining browser coverage, not just successful unit tests. Full-day same-brand process compatibility, mandatory weekly offs and the workspace document design are disclosed assumptions and trade-offs.
