# Test and verification summary

Executed 28 October 2026 in the provided development environment.

| Check | Evidence | Result |
|---|---|---|
| Original prototype tests | tests/test_roster.py, tests/test_scheduler.py | 10 passed |
| Persistent API / CP-SAT tests | tests/test_persistent.py | 12 passed |
| Full backend run | python -m pytest -q | 22 passed; one upstream TestClient deprecation warning |
| Frontend component/integration tests | npm test in frontend | 5 passed |
| TypeScript and Vite | npm run build in frontend | Passed |
| Production npm dependencies | npm audit --omit=dev --audit-level=high | Zero vulnerabilities reported |
| Browser E2E | frontend/e2e/workflow.spec.ts, isolated SQLite, real Chromium | 1 passed |
| Hosted PostgreSQL | No connection provisioned | Not executed |
| Vercel build and public smoke test | GitHub Vercel status reports failed automatic deployment; build logs HTTP 403 pending team authorization | Failed deployment; public smoke not executed |
| Original PDF review | Seven-page AI Internship Assessment.pdf from assessment email | Reviewed; requirements mapped in ACCEPTANCE.md |

Backend assertions cover employee/pod/process CRUD, duplicate IDs, reference rejection and rollback, missing resources, invalid months, seed overwrite refusal, duplicate brand/process demands, employee eligibility, generation, persistence after reread, employee and brand filters, weekly offs, approved leave, company/brand holidays, workload limits, no double booking, stale revisions, manual preview and rejection, no coverage reduction, safe saves, availability impact, optional admin-token enforcement, and reproducible CP-SAT scenarios.

Frontend assertions cover overview/navigation, employee form JSON submission, calendar rendering/editor preview gating, and server error messages. Component tests mock the API; they are not a substitute for full browser-to-database verification.

The executed Playwright workflow creates an employee, updates eligibility, generates a month, previews an ineligible replacement, saves a valid replacement and reloads to inspect persistence. It also verifies pod/process filters, expands the conflict monitor and captures desktop/mobile screenshots. These screenshots were inspected. Initial standard-browser downloads failed; an alternative Chromium binary was extracted, font configuration was fixed, and the final real browser run passed. No narrated video was created. `python scripts/run_e2e.py` starts servers with an isolated temporary database; do not run the raw workflow against production.

An initial solver test exposed incomplete optimality proof under the original combined objective. The implementation was corrected to maximize coverage first and then optimize fairness with explicit workload bounds. The affected test and full backend suite passed after the fix.

Final successful tests: **22 backend + 5 frontend + 1 browser = 28**. Earlier browser launch and fixture failures were resolved and the final workflow was rerun successfully. No production verification is claimed.
