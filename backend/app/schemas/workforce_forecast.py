
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WorkforceForecastResponse(BaseModel):
    id: int
    forecast_months: int
    current_headcount: int
    employees_with_predictions: int
    expected_attrition_12_months: float
    projected_attrition: float
    projected_headcount: float
    projected_retention_rate: float
    assumptions: str
    generated_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
