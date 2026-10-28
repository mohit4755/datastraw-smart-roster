from __future__ import annotations

from calendar import monthrange
from datetime import date
from typing import Literal

from fastapi import FastAPI, HTTPException
from app.scheduler import Staff, Demand, Plan, plan_month
from pydantic import BaseModel, Field

app = FastAPI(title="Datastraw Smart Roster", version="0.1.0")


class Employee(BaseModel):
    id: int
    name: str
    pod_id: int
    weekly_off: int = Field(ge=0, le=6)
    leave_dates: set[date] = Field(default_factory=set)


class Requirement(BaseModel):
    brand: str
    process: str
    employee_ids: list[int]
    min_staff: int = Field(default=1, ge=1)
    calendar: Literal["all_days", "no_holidays", "weekdays_no_holidays"]


class Assignment(BaseModel):
    day: date
    employee_id: int
    brand: str
    process: str


class Conflict(BaseModel):
    day: date
    brand: str
    process: str
    required: int
    assigned: int
    reason: str


class RosterResult(BaseModel):
    year: int
    month: int
    valid: bool
    assignments: list[Assignment]
    conflicts: list[Conflict]


EMPLOYEES = [
    Employee(id=i, name=f"Employee {i:02d}", pod_id=(i - 1) // 10 + 1, weekly_off=(i - 1) % 7)
    for i in range(1, 34)
]
# 20 single-resource brands and 5 multi-resource brands: 80% single-resource.
REQUIREMENTS = [
    Requirement(brand=f"Brand {i:02d}", process="Customer Support",
                employee_ids=[i], calendar="all_days" if i % 5 == 0 else "weekdays_no_holidays")
    for i in range(1, 21)
] + [
    Requirement(brand=f"Brand {i:02d}", process="Customer Support",
                employee_ids=[21 + (i - 21) * 2, 22 + (i - 21) * 2],
                calendar="all_days")
    for i in range(21, 26)
]
HOLIDAYS: set[date] = set()


def operates(req: Requirement, day: date) -> bool:
    if req.calendar == "all_days":
        return True
    if day in HOLIDAYS:
        return False
    return req.calendar == "no_holidays" or day.weekday() != 6


def generate_roster(year: int, month: int) -> RosterResult:
    if not (2000 <= year <= 2100 and 1 <= month <= 12):
        raise ValueError("Invalid year or month")
    by_id = {employee.id: employee for employee in EMPLOYEES}
    assignments: list[Assignment] = []
    conflicts: list[Conflict] = []
    for day_num in range(1, monthrange(year, month)[1] + 1):
        day = date(year, month, day_num)
        used: set[int] = set()
        for req in REQUIREMENTS:
            if not operates(req, day):
                continue
            assigned = 0
            for employee_id in req.employee_ids:
                employee = by_id.get(employee_id)
                if employee is None or employee.weekly_off == day.weekday() or day in employee.leave_dates or employee_id in used:
                    continue
                assignments.append(Assignment(day=day, employee_id=employee_id, brand=req.brand, process=req.process))
                used.add(employee_id)
                assigned += 1
                if assigned >= req.min_staff:
                    break
            if assigned < req.min_staff:
                conflicts.append(Conflict(
                    day=day, brand=req.brand, process=req.process,
                    required=req.min_staff, assigned=assigned,
                    reason="Insufficient eligible staff (weekly off, leave, missing assignment, or allocation conflict)",
                ))
    return RosterResult(year=year, month=month, valid=not conflicts,
                        assignments=assignments, conflicts=conflicts)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/sample-data")
def sample_data() -> dict:
    return {"employees": [e.model_dump(mode="json") for e in EMPLOYEES],
            "requirements": [r.model_dump() for r in REQUIREMENTS]}


@app.post("/rosters/generate", response_model=RosterResult)
def generate(year: int, month: int) -> RosterResult:
    try:
        return generate_roster(year, month)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.post("/rosters/generate-v2", response_model=Plan)
def generate_v2(year: int, month: int) -> Plan:
    """Constraint-aware coverage planning with explicit shortages."""
    staff = [
        Staff(id=e.id, pod_id=e.pod_id, weekly_off=e.weekly_off, leave_dates=e.leave_dates)
        for e in EMPLOYEES
    ]
    demands = [
        Demand(
            brand=r.brand,
            process=r.process,
            eligible_employee_ids=r.employee_ids,
            min_staff=r.min_staff,
            operating_weekdays=set(range(7)) if r.calendar != "weekdays_no_holidays" else set(range(6)),
            holidays_closed=r.calendar != "all_days",
        )
        for r in REQUIREMENTS
    ]
    try:
        return plan_month(year, month, staff, demands, HOLIDAYS)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
