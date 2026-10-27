
from datetime import datetime

from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import DbSession, HRUser
from app.models.workforce_kpi_breach import WorkforceKPIBreach
from app.models.workforce_kpi_target import WorkforceKPITarget
from app.api.workforce_dashboard import get_workforce_kpis


router = APIRouter(
    prefix="/workforce-kpi-breaches",
    tags=["Automated KPI Breach Alerts"],
)


LOWER_IS_BETTER = {
    "high_risk_employees",
    "high_risk_percentage",
    "open_alerts",
}


def target_is_breached(metric_key: str, current: float, target: float) -> bool:
    """Return True when the current KPI misses its target."""
    if metric_key in LOWER_IS_BETTER:
        return current > target

    return current < target


def determine_severity(
    metric_key: str,
    current: float,
    target: float,
) -> str:
    """Assign HIGH severity for a substantial KPI deviation."""
    if metric_key in LOWER_IS_BETTER:
        deviation = current - target
    else:
        deviation = target - current

    if deviation >= 20:
        return "HIGH"

    return "MEDIUM"


@router.post("/evaluate")
def evaluate_kpi_breaches(
    db: DbSession,
    current_user: HRUser,
) -> dict:
    """
    Evaluate all configured KPI targets.
    Create alerts for missed targets and resolve alerts when targets recover.
    """
    kpis = get_workforce_kpis(db, current_user)
    targets = db.query(WorkforceKPITarget).all()

    created_alerts = 0
    updated_alerts = 0
    resolved_alerts = 0
    results = []

    try:
        for target in targets:
            metric_key = target.metric_key
            current_value = float(kpis[metric_key])
            target_value = float(target.target_value)

            breached = target_is_breached(
                metric_key,
                current_value,
                target_value,
            )

            open_breach = (
                db.query(WorkforceKPIBreach)
                .filter(
                    WorkforceKPIBreach.metric_key == metric_key,
                    WorkforceKPIBreach.status == "OPEN",
                )
                .order_by(WorkforceKPIBreach.detected_at.desc())
                .first()
            )

            if breached:
                message = (
                    f"{metric_key}: current value {current_value:g} "
                    f"misses target {target_value:g}."
                )

                if open_breach:
                    # Update the existing open alert instead of duplicating it.
                    open_breach.current_value = current_value
                    open_breach.target_value = target_value
                    open_breach.severity = determine_severity(
                        metric_key,
                        current_value,
                        target_value,
                    )
                    open_breach.message = message
                    updated_alerts += 1
                    breach = open_breach
                else:
                    breach = WorkforceKPIBreach(
                        metric_key=metric_key,
                        current_value=current_value,
                        target_value=target_value,
                        severity=determine_severity(
                            metric_key,
                            current_value,
                            target_value,
                        ),
                        status="OPEN",
                        message=message,
                    )
                    db.add(breach)
                    created_alerts += 1

                results.append(
                    {
                        "metric_key": metric_key,
                        "breached": True,
                        "status": "OPEN",
                        "current_value": current_value,
                        "target_value": target_value,
                    }
                )

            else:
                if open_breach:
                    open_breach.status = "RESOLVED"
                    open_breach.resolved_at = datetime.now()
                    resolved_alerts += 1

                results.append(
                    {
                        "metric_key": metric_key,
                        "breached": False,
                        "status": (
                            "RESOLVED" if open_breach else "OK"
                        ),
                        "current_value": current_value,
                        "target_value": target_value,
                    }
                )

        db.commit()

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="KPI breach evaluation failed.",
        ) from exc

    return {
        "evaluated_at": datetime.now(),
        "targets_checked": len(targets),
        "created_alerts": created_alerts,
        "updated_alerts": updated_alerts,
        "resolved_alerts": resolved_alerts,
        "results": results,
    }


@router.get("")
def list_kpi_breaches(
    db: DbSession,
    current_user: HRUser,
    status_filter: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """List KPI breach alerts, optionally filtered by status."""
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

    query = db.query(WorkforceKPIBreach)

    if status_filter:
        query = query.filter(
            WorkforceKPIBreach.status == status_filter
        )

    breaches = (
        query.order_by(WorkforceKPIBreach.detected_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": item.id,
            "metric_key": item.metric_key,
            "current_value": item.current_value,
            "target_value": item.target_value,
            "severity": item.severity,
            "status": item.status,
            "message": item.message,
            "detected_at": item.detected_at,
            "resolved_at": item.resolved_at,
        }
        for item in breaches
    ]


@router.patch("/{breach_id}/resolve")
def resolve_kpi_breach(
    breach_id: int,
    db: DbSession,
    current_user: HRUser,
) -> dict:
    """Allow HR to manually resolve an open breach."""
    breach = db.get(WorkforceKPIBreach, breach_id)

    if breach is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="KPI breach alert not found.",
        )

    if breach.status == "RESOLVED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This KPI breach alert is already resolved.",
        )

    breach.status = "RESOLVED"
    breach.resolved_at = datetime.now()

    try:
        db.commit()
        db.refresh(breach)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not resolve KPI breach alert.",
        ) from exc

    return {
        "message": "KPI breach alert resolved.",
        "id": breach.id,
        "metric_key": breach.metric_key,
        "status": breach.status,
        "resolved_at": breach.resolved_at,
    }

@router.get("/notifications")
def get_kpi_breach_notifications(
    db: DbSession,
    current_user: HRUser,
    unread_only: bool = False,
    limit: int = 20,
) -> dict:
    """Return KPI breach alerts in notification-feed format."""

    if not 1 <= limit <= 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Limit must be between 1 and 100.",
        )

    query = db.query(WorkforceKPIBreach)

    # Only show currently open breaches when requested.
    if unread_only:
        query = query.filter(
            WorkforceKPIBreach.status == "OPEN"
        )

    alerts = (
        query.order_by(WorkforceKPIBreach.detected_at.desc())
        .limit(limit)
        .all()
    )

    notifications = [
        {
            "id": alert.id,
            "type": "KPI_BREACH",
            "title": f"KPI target missed: {alert.metric_key}",
            "message": alert.message,
            "severity": alert.severity,
            "status": alert.status,
            "is_unresolved": alert.status == "OPEN",
            "created_at": alert.detected_at,
            "resolved_at": alert.resolved_at,
        }
        for alert in alerts
    ]

    return {
        "total_returned": len(notifications),
        "unresolved_count": sum(
            1 for item in notifications if item["is_unresolved"]
        ),
        "notifications": notifications,
    }
