
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AttritionPredictRequest(BaseModel):
    dataset_id: int = Field(gt=0)
    features: dict[str, str | int | float | bool | None]
    employee_id: int | None = Field(default=None, gt=0)


class AttritionPredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    model_id: int
    dataset_id: int
    employee_id: int | None
    predicted_label: str
    risk_percentage: float
    confidence_score: float
    created_at: datetime
