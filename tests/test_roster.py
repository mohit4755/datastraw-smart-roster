from datetime import date

from fastapi.testclient import TestClient

from app.main import app, generate_roster, EMPLOYEES, REQUIREMENTS


client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_seed_size_and_brand_mix():
    assert len(EMPLOYEES) >= 30
    assert len({r.brand for r in REQUIREMENTS}) == 25
    assert sum(len(r.employee_ids) == 1 for r in REQUIREMENTS) == 20


def test_infeasible_single_resource_brand_is_flagged():
    result = generate_roster(2026, 11)
    assert not result.valid
    assert any(c.brand == "Brand 05" for c in result.conflicts)


def test_no_employee_double_booked_on_same_day():
    result = generate_roster(2026, 11)
    pairs = [(a.day, a.employee_id) for a in result.assignments]
    assert len(pairs) == len(set(pairs))


def test_invalid_month_rejected():
    assert client.post("/rosters/generate?year=2026&month=13").status_code == 422
