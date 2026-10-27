
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


MetricKey = Literal[
    "active_headcount",
    "employees_with_predictions",
    "prediction_coverage_percentage",
    "high_risk_employees",
    "high_risk_percentage",
    "open_alerts",
]


class WorkforceKPITargetCreate(BaseModel):
    metric_key: MetricKey
    target_value: float = Field(ge=0)


class WorkforceKPITargetUpdate(BaseModel):
    target_value: float = Field(ge=0)


class WorkforceKPITargetResponse(BaseModel):
    id: int
    metric_key: str
    target_value: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
