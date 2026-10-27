
from datetime import datetime

from fastapi import APIRouter
from sqlalchemy import func

from app.core.dependencies import DbSession, HRUser
from app.models.user import User
from app.models.employee import Employee
from app.models.attrition_prediction import AttritionPrediction
from app.models.attrition_alert import AttritionAlert


router = APIRouter(
    prefix="/workforce-dashboard",
    tags=["Workforce KPI Dashboard"],
)


@router.get("/kpis")
def get_workforce_kpis(
    db: DbSession,
    current_user: HRUser,
) -> dict:
    """Return key workforce indicators for the HR dashboard."""

    # 1. Count employees whose linked user accounts are active.
    active_headcount = (
        db.query(func.count(Employee.id))
        .join(User, Employee.user_id == User.id)
        .filter(User.is_active.is_(True))
        .scalar()
        or 0
    )

    # 2. Find the latest prediction record for each employee.
    latest_predictions = (
        db.query(
            AttritionPrediction.employee_id.label("employee_id"),
            func.max(AttritionPrediction.id).label("latest_id"),
        )
        .filter(AttritionPrediction.employee_id.isnot(None))
        .group_by(AttritionPrediction.employee_id)
        .subquery()
    )

    # Only count predictions belonging to active employees.
    predictions = (
        db.query(AttritionPrediction)
        .join(
            latest_predictions,
            AttritionPrediction.id == latest_predictions.c.latest_id,
        )
        .join(
            Employee,
            AttritionPrediction.employee_id == Employee.id,
        )
        .join(User, Employee.user_id == User.id)
        .filter(User.is_active.is_(True))
        .all()
    )

    employees_with_predictions = len(predictions)

    # 3. Count employees whose latest risk score is at least 70%.
    high_risk_employees = sum(
        1
        for prediction in predictions
        if (prediction.risk_percentage or 0) >= 70
    )

    # 4. Count alerts that are still open.
    open_alerts = (
        db.query(func.count(AttritionAlert.id))
        .filter(AttritionAlert.status == "OPEN")
        .scalar()
        or 0
    )

    # 5. Calculate prediction coverage percentage.
    prediction_coverage = (
        round(employees_with_predictions / active_headcount * 100, 2)
        if active_headcount
        else 0.0
    )

    # 6. Calculate high-risk percentage among predicted employees.
    high_risk_percentage = (
        round(high_risk_employees / employees_with_predictions * 100, 2)
        if employees_with_predictions
        else 0.0
    )

    return {
        "generated_at": datetime.now(),
        "active_headcount": active_headcount,
        "employees_with_predictions": employees_with_predictions,
        "prediction_coverage_percentage": prediction_coverage,
        "high_risk_employees": high_risk_employees,
        "high_risk_percentage": high_risk_percentage,
        "open_alerts": open_alerts,
    }
