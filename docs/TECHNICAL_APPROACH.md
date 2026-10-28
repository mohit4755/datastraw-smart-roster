# Technical approach — Smart Roster Management System

**Candidate:** Mohit Vijay Wankhede · **Position:** AI + Tech Intern · **Date:** 28 October 2026

## Understanding the problem

A monthly roster must connect operational demand with eligible employee availability. A visually complete calendar is insufficient if it double-books someone or hides a staffing shortage. The application therefore treats hard-rule validity and staffing coverage as explicit, separately inspectable results.

## Architecture and technology choices

React and TypeScript provide management forms, a responsive calendar and filtering. FastAPI exposes a JSON API with strict Pydantic record validation. SQLAlchemy persists a transactional workspace in PostgreSQL; local tests use isolated SQLite files. Google OR-Tools CP-SAT solves the staffing allocation problem. Vercel is the only planned application host, with a Python function and a static Vite frontend.

Existing prototype APIs were preserved for compatibility. New management functionality is isolated under `/api`, and the dashboard uses those persistent endpoints exclusively.

## Allocation and optimization

Each eligible employee/day/demand combination has a Boolean decision variable. A demand is a brand/process pair with a minimum staffing count and assigned employee set. Calendar closure, brand/company holidays, approved leave, weekly offs, inactive status, pod mismatch and missing process skills exclude variables.

Employee/day allocations are limited to one. Monthly work limits constrain total assignments. Demand staffing is capped at its configured requirement. Stage one maximizes covered slots; if proven optimal, stage two fixes that coverage and minimizes maximum-minus-minimum employee workload. This order prevents fairness improvements from reducing coverage.

Single-worker CP-SAT uses seed zero, deterministic search budgets and wall-clock limits. The API records proof status rather than assuming that a feasible result is optimal. Coverage shortages remain visible and make the roster invalid for operational acceptance. Time-limited results can be feasible without a proof of maximum coverage.

## Conflict detection and safe editing

An independent validator checks generated and manually edited schedules. It checks IDs, dates, eligibility, operating calendars, double booking, monthly workload and daily coverage. Manual edits are previewed before saving. Hard-rule violations and new/worsened coverage shortages return HTTP 409. Revision numbers reject stale edits.

Configuration and availability changes return a schedule-impact report. Saved rosters are revalidated on retrieval, so a newly approved leave becomes visible as a conflict instead of being ignored.

## Persistence and consistency

One PostgreSQL row stores the workspace document. Row-level locking makes related record edits and impact calculation atomic. Application validation rejects missing references and duplicate brand/process demands. The implementation intentionally favors a compact assessment-scale transaction model. It does not claim normalized database design, multi-tenant scale or immutable historical snapshots. Normalized tables, foreign keys, migrations and audit records are the next architectural improvements.

## Testing and runtime

Executed locally: 22 Pytest tests and 5 Vitest tests passed. These cover CRUD, transaction rollback on invalid references, generation, holidays, leave, weekly offs, no double booking, limits, deterministic examples, manual edit rejection, stale revisions, availability impact, frontend rendering/form/API behavior and API errors. The TypeScript/Vite production build passed. A production npm dependency audit reported zero vulnerabilities.

One real Chromium Playwright workflow passed against isolated local data, including invalid-edit rejection and persistence after reload. Desktop/mobile screenshots were captured and inspected. Initial standard-browser download failures were resolved using an alternative browser runtime. Hosted PostgreSQL and production verification are also pending. OR-Tools installed and executed on Python 3.12; its installed package footprint measured approximately 79.5 MiB locally, excluding transitive dependencies. This is not a Vercel bundle measurement. Each optimization stage has a ten-second wall-clock safety bound; actual production memory and duration require deployment evidence.

## AI, limitations and disclosure

Gemini was deliberately deferred. No unvalidated AI output can modify a roster. Optional future explanations would consume already verified scheduling facts and require deterministic validation before any change.

The demo permits one full-day brand shift per employee; compatible same-brand processes can share it, but shift intervals are not modeled. Admin access is a shared optional token, rather than account-based authorization. All sample people are fictional. Hosted database provisioning, Vercel team authorization/deployment and a narrated public video are pending. This note describes implemented behavior and verified local results; it does not claim the assessment is ready to submit.
