
from fastapi import APIRouter
from sqlalchemy import func, select

from app.core.dependencies import DbSession, HRUser
from app.models.employee_risk_alert import EmployeeRiskAlert
from app.models.employee_risk_alert_action import (
    EmployeeRiskAlertAction,
)

router = APIRouter(
    prefix="/employee-risk-alert-dashboard",
    tags=["Employee Risk Alert Dashboard"],
)


@router.get("/summary")
def get_employee_risk_alert_summary(
    db: DbSession,
    current_user: HRUser,
):
    # Count alerts by their current status.
    status_rows = db.execute(
        select(
            EmployeeRiskAlert.status,
            func.count(EmployeeRiskAlert.id),
        ).group_by(EmployeeRiskAlert.status)
    ).all()

    status_counts = {
        str(alert_status): count
        for alert_status, count in status_rows
    }

    # Count alerts by severity.
    severity_rows = db.execute(
        select(
            EmployeeRiskAlert.severity,
            func.count(EmployeeRiskAlert.id),
        ).group_by(EmployeeRiskAlert.severity)
    ).all()

    severity_counts = {
        str(severity): count
        for severity, count in severity_rows
    }

    # An alert is acknowledged if it has an ACKNOWLEDGED action.
    acknowledged_ids = select(
        EmployeeRiskAlertAction.alert_id
    ).where(
        EmployeeRiskAlertAction.action == "ACKNOWLEDGED"
    ).distinct()

    acknowledged_count = db.scalar(
        select(func.count(EmployeeRiskAlert.id)).where(
            EmployeeRiskAlert.id.in_(acknowledged_ids)
        )
    ) or 0

    total_alerts = db.scalar(
        select(func.count(EmployeeRiskAlert.id))
    ) or 0

    open_count = status_counts.get("OPEN", 0)

    return {
        "total_alerts": total_alerts,
        "open_alerts": open_count,
        "resolved_alerts": status_counts.get("RESOLVED", 0),
        "high_severity_alerts": severity_counts.get("HIGH", 0),
        "medium_severity_alerts": severity_counts.get("MEDIUM", 0),
        "low_severity_alerts": severity_counts.get("LOW", 0),
        "acknowledged_alerts": acknowledged_count,
        "unacknowledged_alerts": max(
            total_alerts - acknowledged_count, 0
        ),
    }
