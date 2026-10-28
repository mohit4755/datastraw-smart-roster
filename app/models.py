"""Validated API records. Weekdays use Monday=0 through Sunday=6."""
from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class Record(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=100)
class Pod(Record):
    lead_employee_id: int | None = Field(default=None, gt=0)
class Process(Record): pass
class Employee(Record):
    pod_id: int = Field(gt=0)
    process_ids: set[int] = Field(default_factory=set)
    weekly_off: int = Field(default=6, ge=0, le=6)
    max_work_days: int = Field(default=26, ge=0, le=31)
    active: bool = True
class Brand(Record):
    pod_id: int = Field(gt=0)
    operating_weekdays: set[int] = Field(default_factory=lambda:set(range(7)))
    holidays_closed: bool = True
    holiday_dates: set[date] = Field(default_factory=set)
    @model_validator(mode='after')
    def weekdays(self):
        if not self.operating_weekdays <= set(range(7)): raise ValueError('Weekdays must be 0..6')
        return self
class Demand(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: int = Field(gt=0)
    brand_id: int = Field(gt=0)
    process_id: int = Field(gt=0)
    employee_ids: set[int] = Field(default_factory=set)
    min_staff: int = Field(default=1, ge=1, le=100)
    operating_weekdays: set[int] = Field(default_factory=lambda:set(range(7)))
    holidays_closed: bool = False
    staffing_by_weekday: list[int] = Field(default_factory=list)
    @model_validator(mode='after')
    def rules(self):
        if not self.operating_weekdays <= set(range(7)): raise ValueError('Weekdays must be 0..6')
        if self.staffing_by_weekday and (len(self.staffing_by_weekday)!=7 or any(n<0 or n>100 for n in self.staffing_by_weekday)): raise ValueError('Daily staffing must have seven values in 0..100')
        return self
class Leave(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: int = Field(gt=0)
    employee_id: int = Field(gt=0)
    start: date
    end: date
    status: Literal['approved','pending','rejected'] = 'approved'
    kind: Literal['leave','comp_off','unavailable'] = 'leave'
    @model_validator(mode='after')
    def dates(self):
        if self.end < self.start: raise ValueError('End precedes start')
        return self
class Holiday(Record):
    day: date
class Slot(BaseModel):
    model_config = ConfigDict(extra='forbid')
    day: date
    employee_id: int = Field(gt=0)
    demand_id: int = Field(gt=0)
class Generate(BaseModel):
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
class Edit(BaseModel):
    revision: int = Field(ge=1)
    slots: list[Slot] = Field(max_length=5000)
    preview: bool = False
MODELS = {'employees':Employee,'pods':Pod,'processes':Process,'brands':Brand,'demands':Demand,'leaves':Leave,'holidays':Holiday}
