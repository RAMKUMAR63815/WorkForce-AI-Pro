
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EmployeeRiskAlertActionCreate(BaseModel):
    action: str = Field(
        default="ACKNOWLEDGED",
        pattern="^ACKNOWLEDGED$",
    )
    notes: str | None = Field(
        default=None,
        max_length=2000,
    )


class EmployeeRiskAlertActionResponse(BaseModel):
    id: int
    alert_id: int
    user_id: int
    action: str
    notes: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
