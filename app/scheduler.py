"""Deterministic coverage-first scheduling with auditable constraint violations."""
from calendar import monthrange
from collections import Counter
from datetime import date
from typing import Iterable

from pydantic import BaseModel, Field


class Staff(BaseModel):
    id: int
    pod_id: int
    weekly_off: int = Field(ge=0, le=6)
    leave_dates: set[date] = Field(default_factory=set)
    max_work_days: int = Field(default=26, ge=0, le=31)


class Demand(BaseModel):
    brand: str
    process: str
    eligible_employee_ids: list[int]
    min_staff: int = Field(ge=1)
    operating_weekdays: set[int] = Field(default_factory=lambda: set(range(7)))
    holidays_closed: bool = True


class Slot(BaseModel):
    day: date
    employee_id: int
    brand: str
    process: str


class Shortage(BaseModel):
    day: date
    brand: str
    process: str
    required: int
    filled: int


class Plan(BaseModel):
    slots: list[Slot]
    shortages: list[Shortage]
    valid: bool
    workload: dict[int, int]


def plan_month(
    year: int,
    month: int,
    staff: Iterable[Staff],
    demands: Iterable[Demand],
    holidays: set[date] | None = None,
) -> Plan:
    if not (2000 <= year <= 2100 and 1 <= month <= 12):
        raise ValueError("Invalid year or month")
    staff_by_id = {person.id: person for person in staff}
    requirements = list(demands)
    if len({(r.brand, r.process) for r in requirements}) != len(requirements):
        raise ValueError("Duplicate brand/process demand")
    if any(any(day not in range(7) for day in r.operating_weekdays) for r in requirements):
        raise ValueError("Invalid operating weekday")
    holiday_set = holidays or set()
    workload: Counter[int] = Counter()
    slots: list[Slot] = []
    shortages: list[Shortage] = []
    for day_num in range(1, monthrange(year, month)[1] + 1):
        day = date(year, month, day_num)
        occupied: set[int] = set()
        # Most constrained requirements first; deterministic tie-breaking.
        daily = [
            r for r in requirements
            if day.weekday() in r.operating_weekdays
            and not (r.holidays_closed and day in holiday_set)
        ]
        daily.sort(key=lambda r: (len(set(r.eligible_employee_ids)) - r.min_staff, r.brand, r.process))
        for req in daily:
            eligible = [
                staff_by_id[employee_id]
                for employee_id in set(req.eligible_employee_ids)
                if employee_id in staff_by_id
            ]
            eligible = [
                person for person in eligible
                if person.id not in occupied
                and person.weekly_off != day.weekday()
                and day not in person.leave_dates
                and workload[person.id] < person.max_work_days
            ]
            eligible.sort(key=lambda person: (workload[person.id], person.id))
            chosen = eligible[:req.min_staff]
            for person in chosen:
                slots.append(Slot(day=day, employee_id=person.id, brand=req.brand, process=req.process))
                occupied.add(person.id)
                workload[person.id] += 1
            if len(chosen) < req.min_staff:
                shortages.append(Shortage(day=day, brand=req.brand, process=req.process,
                                          required=req.min_staff, filled=len(chosen)))
    return Plan(slots=slots, shortages=shortages, valid=not shortages,
                workload={person_id: workload[person_id] for person_id in staff_by_id})
