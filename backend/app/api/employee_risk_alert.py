
from datetime import datetime

from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import DbSession, HRUser
from app.models.employee import Employee
from app.models.user import User
from app.models.attrition_prediction import AttritionPrediction
from app.models.employee_risk_alert import EmployeeRiskAlert


router = APIRouter(
    prefix="/employee-risk-alerts",
    tags=["Employee Risk Change Alerts"],
)

# Create an alert for an increase of at least 10 percentage points,
# provided the latest risk is at least 40%.
MIN_RISK_INCREASE = 10.0
MIN_CURRENT_RISK = 40.0


@router.post("/evaluate")
def evaluate_employee_risk_changes(
    db: DbSession,
    current_user: HRUser,
) -> dict:
    """Detect significant increases in employees' latest risk scores."""

    # Load predictions for active employees, newest prediction first.
    records = (
        db.query(AttritionPrediction, Employee.id.label("employee_record_id"))
        .join(
            Employee,
            AttritionPrediction.employee_id == Employee.id,
        )
        .join(User, Employee.user_id == User.id)
        .filter(User.is_active.is_(True))
        .filter(AttritionPrediction.employee_id.isnot(None))
        .order_by(
            AttritionPrediction.employee_id.asc(),
            AttritionPrediction.id.desc(),
        )
        .all()
    )

    # Keep the latest two prediction records per employee.
    latest_two = {}

    for row in records:
        prediction = row[0]
        employee_id = row.employee_record_id

        if employee_id not in latest_two:
            latest_two[employee_id] = []

        if len(latest_two[employee_id]) < 2:
            latest_two[employee_id].append(prediction)

    checked = 0
    created = 0
    updated = 0
    resolved = 0
    results = []

    try:
        for employee_id, predictions in latest_two.items():
            if len(predictions) < 2:
                continue

            checked += 1

            latest = predictions[0]
            previous = predictions[1]

            current_risk = float(latest.risk_percentage or 0)
            previous_risk = float(previous.risk_percentage or 0)
            increase = round(current_risk - previous_risk, 2)

            qualifies = (
                increase >= MIN_RISK_INCREASE
                and current_risk >= MIN_CURRENT_RISK
            )

            open_alert = (
                db.query(EmployeeRiskAlert)
                .filter(
                    EmployeeRiskAlert.employee_id == employee_id,
                    EmployeeRiskAlert.status == "OPEN",
                )
                .order_by(EmployeeRiskAlert.detected_at.desc())
                .first()
            )

            if qualifies:
                severity = (
                    "HIGH"
                    if current_risk >= 70 or increase >= 20
                    else "MEDIUM"
                )

                if open_alert:
                    # Refresh the existing alert rather than duplicating it.
                    open_alert.previous_risk = previous_risk
                    open_alert.current_risk = current_risk
                    open_alert.risk_increase = increase
                    open_alert.severity = severity
                    updated += 1
                    alert_id = open_alert.id
                else:
                    alert = EmployeeRiskAlert(
                        employee_id=employee_id,
                        previous_risk=previous_risk,
                        current_risk=current_risk,
                        risk_increase=increase,
                        severity=severity,
                        status="OPEN",
                    )
                    db.add(alert)
                    db.flush()
                    created += 1
                    alert_id = alert.id

                results.append({
                    "employee_id": employee_id,
                    "alert_id": alert_id,
                    "previous_risk": previous_risk,
                    "current_risk": current_risk,
                    "risk_increase": increase,
                    "severity": severity,
                    "status": "OPEN",
                })

            elif open_alert:
                open_alert.status = "RESOLVED"
                open_alert.resolved_at = datetime.now()
                resolved += 1

        db.commit()

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Employee risk alert evaluation failed.",
        ) from exc

    return {
        "employees_checked": checked,
        "alerts_created": created,
        "alerts_updated": updated,
        "alerts_resolved": resolved,
        "alerts": results,
    }


@router.get("/")
def list_employee_risk_alerts(
    db: DbSession,
    current_user: HRUser,
    status_filter: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """List risk-change alerts, optionally filtered by status."""

    if not 1 <= limit <= 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Limit must be between 1 and 100.",
        )

    if status_filter and status_filter not in {"OPEN", "RESOLVED"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="status_filter must be OPEN or RESOLVED.",
        )

    query = db.query(EmployeeRiskAlert)

    if status_filter:
        query = query.filter(
            EmployeeRiskAlert.status == status_filter
        )

    alerts = (
        query.order_by(EmployeeRiskAlert.detected_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": alert.id,
            "employee_id": alert.employee_id,
            "previous_risk": alert.previous_risk,
            "current_risk": alert.current_risk,
            "risk_increase": alert.risk_increase,
            "severity": alert.severity,
            "status": alert.status,
            "detected_at": alert.detected_at,
            "resolved_at": alert.resolved_at,
        }
        for alert in alerts
    ]


@router.patch("/{alert_id}/resolve")
def resolve_employee_risk_alert(
    alert_id: int,
    db: DbSession,
    current_user: HRUser,
) -> dict:
    """Allow HR to resolve a risk-change alert manually."""

    alert = db.get(EmployeeRiskAlert, alert_id)

    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee risk alert not found.",
        )

    if alert.status == "RESOLVED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This alert is already resolved.",
        )

    alert.status = "RESOLVED"
    alert.resolved_at = datetime.now()

    try:
        db.commit()
        db.refresh(alert)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not resolve employee risk alert.",
        ) from exc

    return {
        "message": "Employee risk alert resolved.",
        "id": alert.id,
        "employee_id": alert.employee_id,
        "status": alert.status,
        "resolved_at": alert.resolved_at,
    }
