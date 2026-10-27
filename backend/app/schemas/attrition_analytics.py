
from pydantic import BaseModel


class AttritionAnalyticsSummary(BaseModel):
    total_predictions: int
    employees_with_predictions: int
    predicted_to_leave: int
    high_risk: int
    medium_risk: int
    low_risk: int
    average_risk_percentage: float
    risk_coverage_percentage: float
