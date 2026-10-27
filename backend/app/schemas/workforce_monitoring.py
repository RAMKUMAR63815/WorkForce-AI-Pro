
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WorkforceMonitoringResponse(BaseModel):
    id: int
    active_headcount: int
    employees_with_predictions: int
    high_risk_employees: int
    open_alerts: int
    snapshot_at: datetime

    model_config = ConfigDict(from_attributes=True)
