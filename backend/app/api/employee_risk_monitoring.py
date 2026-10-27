
from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import DbSession, HRUser
from app.models.employee import Employee
from app.models.user import User
from app.models.attrition_prediction import AttritionPrediction


router = APIRouter(
    prefix="/employee-risk-monitoring",
    tags=["Employee Attrition Risk Monitoring"],
)


def classify_risk(risk_percentage: float) -> str:
    """Classify an employee's latest risk percentage."""
    if risk_percentage >= 70:
        return "HIGH"
    if risk_percentage >= 40:
        return "MEDIUM"
    return "LOW"


@router.get("/")
def get_employee_risk_monitoring(
    db: DbSession,
    current_user: HRUser,
    risk_level: str | None = None,
    limit: int = 50,
) -> dict:
    """
    Return each active employee's latest attrition prediction,
    previous risk score, and risk movement.
    """

    if not 1 <= limit <= 200:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Limit must be between 1 and 200.",
        )

    if risk_level and risk_level.upper() not in {
        "LOW", "MEDIUM", "HIGH"
    }:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="risk_level must be LOW, MEDIUM, or HIGH.",
        )

    # Load predictions for active employees, newest record first.
    records = (
        db.query(
            AttritionPrediction,
            Employee.id.label("employee_record_id"),
            Employee.employee_code,
            User.email,
            User.first_name,
            User.last_name,
        )
        .join(
            Employee,
            AttritionPrediction.employee_id == Employee.id,
        )
        .join(
            User,
            Employee.user_id == User.id,
        )
        .filter(User.is_active.is_(True))
        .filter(AttritionPrediction.employee_id.isnot(None))
        .order_by(
            AttritionPrediction.employee_id.asc(),
            AttritionPrediction.id.desc(),
        )
        .all()
    )

    # Group the newest two predictions for each employee.
    employee_predictions = {}

    for row in records:
        prediction = row[0]
        employee_id = row.employee_record_id

        if employee_id not in employee_predictions:
            employee_predictions[employee_id] = {
                "employee_id": employee_id,
                "employee_code": row.employee_code,
                "email": row.email,
                "first_name": row.first_name,
                "last_name": row.last_name,
                "predictions": [],
            }

        prediction_list = employee_predictions[employee_id]["predictions"]

        if len(prediction_list) < 2:
            prediction_list.append(prediction)

    results = []

    for employee_id, employee_data in employee_predictions.items():
        predictions = employee_data["predictions"]
        latest = predictions[0]

        latest_risk = float(latest.risk_percentage or 0)
        latest_level = classify_risk(latest_risk)

        previous_risk = None
        risk_difference = None
        risk_movement = "INSUFFICIENT_HISTORY"

        if len(predictions) >= 2:
            previous_risk = float(
                predictions[1].risk_percentage or 0
            )
            risk_difference = round(latest_risk - previous_risk, 2)

            if risk_difference > 0:
                risk_movement = "INCREASED"
            elif risk_difference < 0:
                risk_movement = "DECREASED"
            else:
                risk_movement = "UNCHANGED"

        if risk_level and latest_level != risk_level.upper():
            continue

        results.append(
            {
                "employee_id": employee_id,
                "employee_code": employee_data["employee_code"],
                "email": employee_data["email"],
                "first_name": employee_data["first_name"],
                "last_name": employee_data["last_name"],
                "prediction_id": latest.id,
                "predicted_label": latest.predicted_label,
                "risk_percentage": latest_risk,
                "risk_level": latest_level,
                "previous_risk_percentage": previous_risk,
                "risk_difference": risk_difference,
                "risk_movement": risk_movement,
                "prediction_created_at": latest.created_at,
            }
        )

    # Show highest-risk employees first.
    results.sort(
        key=lambda item: item["risk_percentage"],
        reverse=True,
    )

    results = results[:limit]

    return {
        "total_employees": len(results),
        "risk_level_filter": (
            risk_level.upper() if risk_level else None
        ),
        "employees": results,
    }
