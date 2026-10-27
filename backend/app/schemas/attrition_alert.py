
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AttritionAlertResponse(BaseModel):
    id: int
    prediction_id: int
    employee_id: int
    risk_level: str
    risk_percentage: float
    message: str
    status: str
    created_at: datetime
    acknowledged_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class AlertEvaluationResponse(BaseModel):
    checked_employees: int
    created_alerts: int
    skipped_cooldown: int
    message: str
