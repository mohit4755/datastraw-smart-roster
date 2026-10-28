# Vercel deployment runbook

## Confirmed state

- Repository: `mohit4755/datastraw-smart-roster`, branch `main`.
- Project created: `datastraw-smart-roster`, ID `prj_BYAVXUQbdPieQHAOziBKxuG7ESzR`.
- Account scope returned by Vercel: `team_tekpNRjkW1Rx4NZQ3pqitNSL`.
- Team-scoped operations returned HTTP 403 and require the candidate's Vercel consent. A short-lived authorization URL was provided in the conversation; regenerate it if expired.
- The GitHub update triggered deployment dpl_2RG4GXjZ1U2NNcfD2hZmkua5YEUX, which failed according to the Vercel GitHub status. Reading its build logs returned HTTP 403 pending team consent. The cause is not known yet. No working deployment URL has been verified. Never submit a guessed domain.

## Database

Provision a managed PostgreSQL database, for example Neon, without deploying the application to another host. The Neon connection has been requested but is not confirmed. Use a pooled URI with TLS. Set `DATABASE_URL` as a sensitive Vercel environment variable for Production and Preview; do not expose it in frontend variables.

Initialize the database once from a trusted local shell with DATABASE_URL exported:

```bash
python -m app.seed
```

For an empty configuration instead, run `python -c "from app.store import initialize; initialize()"`. Schema initialization is an explicit operation, not automatically run on each serverless request. The application must not fall back to ephemeral SQLite on Vercel.

## Build and publish

1. Complete Vercel team authorization and verify the exact project ID/account before mutation.
2. Confirm the existing Git connection points to this repository and `main`.
3. Set DATABASE_URL, and optionally ADMIN_TOKEN. If configured, the evaluator needs the write token via a private channel to exercise mutation workflows; never commit it.
4. Use Python 3.12, and Node 22/24. Dependencies are in requirements.txt; exact locally verified snapshots are in requirements-lock.txt and frontend/package-lock.json.
5. `vercel.json` builds Python and static React separately and routes API before the SPA.
6. Create a preview deployment from the verified commit and inspect build logs.
7. Confirm the Python function bundle fits the current Vercel limit, native OR-Tools imports, and memory/duration are within the account limits. Local install alone does not establish runtime compatibility.
8. Smoke-test preview through the authorized Vercel access route if protected. Fix every failure before promoting.
9. Publish production. The user explicitly requires public hiring-team access; configure production deployment protection accordingly, while retaining any appropriate preview protection.
10. Record the actual public URL and inspect it in a signed-out browser.

## Production acceptance — all pending

- GET `/` returns the React dashboard and correct assets.
- GET `/api/health` returns status ok, database connected, OR-Tools scheduler.
- GET `/docs` and `/openapi.json` respond correctly.
- Create an employee, configure pod/process eligibility, assign a brand demand and weekly off.
- Generate November 2026; inspect explicit shortages, holiday/leave handling and unique employee/day allocations.
- Preview an ineligible employee change and confirm conflict visibility; reject its save.
- Save a valid replacement; reload in another session and verify revision and assignment persist.
- Verify every management navigation item, filters and mobile layout.
- Inspect runtime/build logs and confirm no secrets appear.
- Record real measured duration and memory if available; do not invent benchmarks.

## Recovery

If runtime dependencies fail, inspect the specific import/build error. Do not silently replace CP-SAT with a greedy algorithm. A deterministic alternative requires maximum-coverage matching with cross-day capacity handling and regression tests. If database credentials are missing, configure them; never substitute ephemeral disk persistence in production.
