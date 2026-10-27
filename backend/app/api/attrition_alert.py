
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.api.rbac import DbSession, HRUser
from app.models.attrition_alert import AttritionAlert
from app.models.attrition_prediction import AttritionPrediction
from app.models.employee import Employee
from app.models.user import User
from app.schemas.attrition_alert import (
    AlertEvaluationResponse,
    AttritionAlertResponse,
)

router = APIRouter(
    prefix="/attrition-alerts",
    tags=["Smart Notification & Alert Engine"],
)


def get_risk_level(risk: float) -> str:
    if risk >= 70:
        return "HIGH"
    if risk >= 40:
        return "MEDIUM"
    return "LOW"


@router.post(
    "/evaluate",
    response_model=AlertEvaluationResponse,
)
def evaluate_alerts(
    db: DbSession,
    current_user: HRUser,
    cooldown_hours: int = Query(default=24, ge=1, le=720),
):
    # Only consider employees with active user accounts.
    active_employee_ids = set(
        db.scalars(
            select(Employee.id)
            .join(User, Employee.user_id == User.id)
            .where(User.is_active.is_(True))
        ).all()
    )

    # Find the latest prediction for each active employee.
    predictions = db.scalars(
        select(AttritionPrediction)
        .where(AttritionPrediction.employee_id.is_not(None))
        .order_by(
            AttritionPrediction.created_at.desc(),
            AttritionPrediction.id.desc(),
        )
    ).all()

    latest_predictions = {}

    for prediction in predictions:
        employee_id = prediction.employee_id

        if employee_id not in active_employee_ids:
            continue

        if employee_id not in latest_predictions:
            latest_predictions[employee_id] = prediction

    created_alerts = 0
    skipped_cooldown = 0
    cutoff = datetime.now() - timedelta(hours=cooldown_hours)

    for employee_id, prediction in latest_predictions.items():
        risk = max(
            0.0,
            min(100.0, float(prediction.risk_percentage)),
        )

        risk_level = get_risk_level(risk)

        # Generate alerts only for medium or high risk.
        if risk_level == "LOW":
            continue

        # Avoid repeating the same employee/risk-level alert
        # within the cooldown period.
        recent_alert = db.scalar(
            select(AttritionAlert.id)
            .where(
                AttritionAlert.employee_id == employee_id,
                AttritionAlert.risk_level == risk_level,
                AttritionAlert.created_at >= cutoff,
            )
            .limit(1)
        )

        if recent_alert is not None:
            skipped_cooldown += 1
            continue

        alert = AttritionAlert(
            prediction_id=prediction.id,
            employee_id=employee_id,
            risk_level=risk_level,
            risk_percentage=round(risk, 2),
            message=(
                f"{risk_level} attrition risk detected "
                f"({risk:.2f}%). HR review recommended."
            ),
            status="OPEN",
        )

        db.add(alert)
        created_alerts += 1

    db.commit()

    return AlertEvaluationResponse(
        checked_employees=len(latest_predictions),
        created_alerts=created_alerts,
        skipped_cooldown=skipped_cooldown,
        message="Alert evaluation completed.",
    )


@router.get(
    "/",
    response_model=list[AttritionAlertResponse],
)
def list_alerts(
    db: DbSession,
    current_user: HRUser,
    status: str | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
):
    query = select(AttritionAlert)

    if status is not None:
        status = status.upper()

        if status not in {"OPEN", "ACKNOWLEDGED", "RESOLVED"}:
            raise HTTPException(
                status_code=400,
                detail="Invalid alert status.",
            )

        query = query.where(AttritionAlert.status == status)

    if risk_level is not None:
        risk_level = risk_level.upper()

        if risk_level not in {"HIGH", "MEDIUM", "LOW"}:
            raise HTTPException(
                status_code=400,
                detail="Invalid risk level.",
            )

        query = query.where(
            AttritionAlert.risk_level == risk_level
        )

    query = query.order_by(
        AttritionAlert.created_at.desc()
    ).limit(limit)

    return db.scalars(query).all()


@router.patch(
    "/{alert_id}/acknowledge",
    response_model=AttritionAlertResponse,
)
def acknowledge_alert(
    alert_id: int,
    db: DbSession,
    current_user: HRUser,
):
    alert = db.get(AttritionAlert, alert_id)

    if alert is None:
        raise HTTPException(
            status_code=404,
            detail="Alert not found.",
        )

    if alert.status == "OPEN":
        alert.status = "ACKNOWLEDGED"
        alert.acknowledged_at = datetime.now()

        db.commit()
        db.refresh(alert)

    return alert


@router.patch(
    "/{alert_id}/resolve",
    response_model=AttritionAlertResponse,
)
def resolve_alert(
    alert_id: int,
    db: DbSession,
    current_user: HRUser,
):
    alert = db.get(AttritionAlert, alert_id)

    if alert is None:
        raise HTTPException(
            status_code=404,
            detail="Alert not found.",
        )

    alert.status = "RESOLVED"

    if alert.acknowledged_at is None:
        alert.acknowledged_at = datetime.now()

    db.commit()
    db.refresh(alert)

    return alert
