
from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.rbac import DbSession, HRUser
from app.models.attrition_prediction import AttritionPrediction
from app.models.employee import Employee
from app.models.user import User
from app.schemas.attrition_analytics import AttritionAnalyticsSummary

router = APIRouter(
    prefix="/attrition-analytics",
    tags=["Attrition Analytics Dashboard"],
)


def is_positive_prediction(label) -> bool:
    """Interpret common positive attrition labels."""
    return str(label).strip().lower() in {
        "yes",
        "1",
        "true",
        "leave",
        "attrition",
        "will leave",
    }


@router.get("/summary", response_model=AttritionAnalyticsSummary)
def get_attrition_analytics(
    db: DbSession,
    current_user: HRUser,
):
    # Total prediction records, including historical predictions.
    total_predictions = db.scalar(
        select(func.count(AttritionPrediction.id))
    ) or 0

    # Only include employees with active user accounts.
    active_employee_ids = set(
        db.scalars(
            select(Employee.id)
            .join(User, Employee.user_id == User.id)
            .where(User.is_active.is_(True))
        ).all()
    )

    # Newest prediction first.
    prediction_rows = db.scalars(
        select(AttritionPrediction)
        .where(AttritionPrediction.employee_id.is_not(None))
        .order_by(
            AttritionPrediction.created_at.desc(),
            AttritionPrediction.id.desc(),
        )
    ).all()

    # Keep one latest prediction for each active employee.
    latest_predictions = {}

    for prediction in prediction_rows:
        employee_id = prediction.employee_id

        if employee_id not in active_employee_ids:
            continue

        if employee_id not in latest_predictions:
            latest_predictions[employee_id] = prediction

    high_risk = 0
    medium_risk = 0
    low_risk = 0
    predicted_to_leave = 0
    total_risk = 0.0

    for prediction in latest_predictions.values():
        risk = max(
            0.0,
            min(100.0, float(prediction.risk_percentage)),
        )

        total_risk += risk

        if risk >= 70:
            high_risk += 1
        elif risk >= 40:
            medium_risk += 1
        else:
            low_risk += 1

        if is_positive_prediction(prediction.predicted_label):
            predicted_to_leave += 1

    employees_with_predictions = len(latest_predictions)

    average_risk = (
        total_risk / employees_with_predictions
        if employees_with_predictions
        else 0.0
    )

    active_headcount = len(active_employee_ids)

    coverage = (
        employees_with_predictions / active_headcount * 100
        if active_headcount
        else 0.0
    )

    return AttritionAnalyticsSummary(
        total_predictions=total_predictions,
        employees_with_predictions=employees_with_predictions,
        predicted_to_leave=predicted_to_leave,
        high_risk=high_risk,
        medium_risk=medium_risk,
        low_risk=low_risk,
        average_risk_percentage=round(average_risk, 2),
        risk_coverage_percentage=round(coverage, 2),
    )
