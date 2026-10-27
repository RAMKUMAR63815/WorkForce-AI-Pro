
from pydantic import BaseModel, ConfigDict, Field


class LeaveBalanceCreate(BaseModel):
    employee_id: int = Field(gt=0)

    leave_type: str = Field(
        min_length=2,
        max_length=50,
    )

    year: int = Field(
        ge=2020,
        le=2100,
    )

    total_days: int = Field(
        ge=0,
        le=365,
    )


class LeaveBalanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    leave_type: str
    year: int
    total_days: int
    used_days: int
