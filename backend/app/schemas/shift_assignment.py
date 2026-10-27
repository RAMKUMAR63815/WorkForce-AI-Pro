
from pydantic import BaseModel, ConfigDict, Field


class ShiftAssignmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shift_id: int | None = Field(default=None, gt=0)


class ShiftAssignmentResponse(BaseModel):
    employee_id: int
    employee_code: str
    shift_id: int | None
    shift_name: str | None
