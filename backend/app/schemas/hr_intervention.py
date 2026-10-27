
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


InterventionStatus = Literal[
    "PLANNED",
    "IN_PROGRESS",
    "COMPLETED",
    "CANCELLED",
]


class HRInterventionCreate(BaseModel):
    employee_id: int = Field(gt=0)
    intervention_type: str = Field(min_length=2, max_length=100)
    action_plan: str = Field(min_length=3, max_length=10000)
    notes: str | None = Field(default=None, max_length=10000)
    follow_up_date: date | None = None


class HRInterventionUpdate(BaseModel):
    intervention_type: str | None = Field(
        default=None, min_length=2, max_length=100
    )
    action_plan: str | None = Field(
        default=None, min_length=3, max_length=10000
    )
    notes: str | None = Field(default=None, max_length=10000)
    status: InterventionStatus | None = None
    follow_up_date: date | None = None
    outcome: str | None = Field(default=None, max_length=10000)


class HRInterventionResponse(BaseModel):
    id: int
    employee_id: int
    intervention_type: str
    action_plan: str
    notes: str | None
    status: str
    follow_up_date: date | None
    outcome: str | None
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
