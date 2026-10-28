# Datastraw Smart Roster

A constraint-aware monthly staffing roster prototype for multi-brand operations.

## Quick start

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs

## Initial API
- GET /health
- GET /sample-data
- POST /rosters/generate?year=2026&month=11

The initial scheduler is a deterministic baseline and **does not yet satisfy the full assessment**. It reports uncovered brand/process/day requirements instead of silently claiming complete coverage. Future phases: persistent CRUD, comprehensive shift/leave constraints, manual edits, React views, optimizer, deployment and tests.

## Design assumptions
- Brand operating days are independent of employee availability.
- An employee can be scheduled for at most one brand/process assignment per day in the initial baseline.
- Coverage shortages are hard conflicts; the generator never labels an incomplete roster valid.
- Seed data is fictional.
