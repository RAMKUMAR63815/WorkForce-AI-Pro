
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.api.rbac import DbSession, HRUser
from app.models.attrition_prediction import AttritionPrediction
from app.models.notification import Notification
from app.models.risk_monitoring import RiskMonitoringLog

router = APIRouter(
    prefix="/risk-monitoring",
    tags=["Employee Risk Monitoring"],
)


def classify_risk(risk: float) -> str:
    if risk >= 70:
        return "HIGH"
    if risk >= 40:
        return "MEDIUM"
    return "LOW"


def record_risk(
    db: DbSession,
    prediction: AttritionPrediction,
) -> RiskMonitoringLog:
    previous = None

    if prediction.employee_id is not None:
        previous = db.scalar(
            select(RiskMonitoringLog)
            .where(
                RiskMonitoringLog.employee_id == prediction.employee_id
            )
            .order_by(RiskMonitoringLog.created_at.desc())
            .limit(1)
        )

    previous_risk = previous.current_risk if previous else None
    current_risk = prediction.risk_percentage
    risk_change = (
        round(current_risk - previous_risk, 2)
        if previous_risk is not None
        else None
    )

    level = classify_risk(current_risk)
    alert_generated = level == "HIGH"

    log = RiskMonitoringLog(
        prediction_id=prediction.id,
        employee_id=prediction.employee_id,
        previous_risk=previous_risk,
        current_risk=current_risk,
        risk_change=risk_change,
        risk_level=level,
        alert_generated=alert_generated,
        notes=(
            "High attrition risk detected."
            if alert_generated
            else None
        ),
    )
    db.add(log)

    # Notify HR/Admin users if this prediction belongs to an employee
    # and crosses the high-risk threshold.
    if alert_generated and prediction.employee_id is not None:
        from app.models.user import User

        recipients = db.scalars(
            select(User).where(
                User.role.in_(["HR", "ADMIN"]),
                User.is_active.is_(True),
            )
        ).all()

        change_text = (
            f" Risk changed by {risk_change:+.2f} percentage points."
            if risk_change is not None
            else ""
        )

        for recipient in recipients:
            db.add(
                Notification(
                    user_id=recipient.id,
                    title="High Attrition Risk Alert",
                    message=(
                        f"Employee ID {prediction.employee_id} has an "
                        f"estimated attrition risk of {current_risk:.2f}%."
                        f"{change_text}"
                    ),
                    notification_type="ATTRITION_RISK",
                )
            )

    return log


@router.get("/summary")
def get_risk_summary(
    db: DbSession,
    current_user: HRUser,
):
    logs = db.scalars(
        select(RiskMonitoringLog)
        .order_by(RiskMonitoringLog.created_at.desc())
        .limit(1000)
    ).all()

    latest_by_employee = {}

    for log in logs:
        key = log.employee_id if log.employee_id is not None else (
            f"prediction-{log.prediction_id}"
        )
        if key not in latest_by_employee:
            latest_by_employee[key] = log

    latest_logs = list(latest_by_employee.values())

    return {
        "employees_monitored": sum(
            1 for log in latest_logs if log.employee_id is not None
        ),
        "high_risk": sum(
            1 for log in latest_logs if log.risk_level == "HIGH"
        ),
        "medium_risk": sum(
            1 for log in latest_logs if log.risk_level == "MEDIUM"
        ),
        "low_risk": sum(
            1 for log in latest_logs if log.risk_level == "LOW"
        ),
        "high_risk_threshold": 70,
        "note": "Summary covers the latest 1000 monitoring logs.",
    }


@router.get("/logs")
def get_risk_logs(
    db: DbSession,
    current_user: HRUser,
    employee_id: int | None = Query(default=None, gt=0),
    risk_level: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    query = select(RiskMonitoringLog)

    if employee_id is not None:
        query = query.where(
            RiskMonitoringLog.employee_id == employee_id
        )

    if risk_level is not None:
        risk_level = risk_level.upper()
        if risk_level not in {"LOW", "MEDIUM", "HIGH"}:
            raise HTTPException(
                400, "risk_level must be LOW, MEDIUM, or HIGH."
            )
        query = query.where(
            RiskMonitoringLog.risk_level == risk_level
        )

    return db.scalars(
        query.order_by(RiskMonitoringLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()


@router.get("/employees/{employee_id}/history")
def get_employee_risk_history(
    employee_id: int,
    db: DbSession,
    current_user: HRUser,
):
    return db.scalars(
        select(RiskMonitoringLog)
        .where(RiskMonitoringLog.employee_id == employee_id)
        .order_by(RiskMonitoringLog.created_at.asc())
    ).all()
