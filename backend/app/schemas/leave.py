
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LeaveCreate(BaseModel):
    leave_type: Literal[
        "CASUAL",
        "SICK",
        "ANNUAL",
        "UNPAID",
    ]
    start_date: date
    end_date: date
    reason: str = Field(min_length=5, max_length=1000)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("End date cannot be before start date.")
        return self


class LeaveReview(BaseModel):
    status: Literal["APPROVED", "REJECTED"]
    review_remarks: str | None = Field(
        default=None,
        max_length=1000,
    )


class LeaveResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    leave_type: str
    start_date: date
    end_date: date
    reason: str
    status: str
    reviewed_by: int | None
    review_remarks: str | None
    created_at: datetime
