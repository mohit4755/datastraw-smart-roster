from datetime import date
from app.scheduler import Staff, Demand, plan_month


def test_no_double_booking_and_weekly_off():
    people = [Staff(id=1, pod_id=1, weekly_off=6), Staff(id=2, pod_id=1, weekly_off=5)]
    demands = [Demand(brand="A", process="P", eligible_employee_ids=[1, 2], min_staff=1)]
    plan = plan_month(2026, 11, people, demands)
    assert len({(s.day, s.employee_id) for s in plan.slots}) == len(plan.slots)
    assert all(not (s.employee_id == 1 and s.day.weekday() == 6) for s in plan.slots)
    assert all(not (s.employee_id == 2 and s.day.weekday() == 5) for s in plan.slots)


def test_holidays_and_leave():
    people = [Staff(id=1, pod_id=1, weekly_off=6, leave_dates={date(2026, 11, 2)})]
    demand = [Demand(brand="A", process="P", eligible_employee_ids=[1], min_staff=1,
                     operating_weekdays={0, 1, 2, 3, 4})]
    plan = plan_month(2026, 11, people, demand, {date(2026, 11, 3)})
    assert any(s.day == date(2026, 11, 2) for s in plan.shortages)
    assert not any(s.day == date(2026, 11, 3) for s in plan.slots + plan.shortages)


def test_max_work_days():
    people = [Staff(id=1, pod_id=1, weekly_off=6, max_work_days=2)]
    demands = [Demand(brand="A", process="P", eligible_employee_ids=[1], min_staff=1)]
    plan = plan_month(2026, 11, people, demands)
    assert plan.workload[1] == 2
    assert not plan.valid


def test_deterministic():
    people = [Staff(id=i, pod_id=1, weekly_off=6) for i in (1, 2, 3)]
    demands = [Demand(brand="A", process="P", eligible_employee_ids=[1, 2, 3], min_staff=2)]
    first = plan_month(2026, 11, people, demands)
    second = plan_month(2026, 11, people, demands)
    assert first == second
    assert abs(first.workload[1] - first.workload[2]) <= 1


def test_invalid_month():
    try:
        plan_month(2026, 13, [], [])
        assert False
    except ValueError:
        pass
