
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func

from app.core.dependencies import DbSession, HRUser
from app.models.user import User
from app.models.employee import Employee
from app.models.attrition_prediction import AttritionPrediction
from app.models.attrition_alert import AttritionAlert
from app.models.workforce_monitoring import WorkforceMonitoring
from app.schemas.workforce_monitoring import WorkforceMonitoringResponse


router = APIRouter(
    prefix="/workforce-monitoring",
    tags=["Real-Time Workforce Monitoring"],
)


def calculate_metrics(db: DbSession) -> dict:
    """Calculate current workforce monitoring metrics."""

    # Count employees whose user accounts are active.
    active_headcount = (
        db.query(func.count(Employee.id))
        .join(User, Employee.user_id == User.id)
        .filter(User.is_active.is_(True))
        .scalar()
        or 0
    )

    # Find the latest prediction for each employee.
    latest_predictions = (
        db.query(
            AttritionPrediction.employee_id.label("employee_id"),
            func.max(AttritionPrediction.id).label("latest_id"),
        )
        .filter(AttritionPrediction.employee_id.isnot(None))
        .group_by(AttritionPrediction.employee_id)
        .subquery()
    )

    # Retrieve the latest prediction for each active employee.
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
        .join(
            User,
            Employee.user_id == User.id,
        )
        .filter(User.is_active.is_(True))
        .all()
    )

    employees_with_predictions = len(predictions)

    high_risk_employees = sum(
        1
        for prediction in predictions
        if (prediction.risk_percentage or 0) >= 70
    )

    # Count alerts that are still open.
    open_alerts = (
        db.query(func.count(AttritionAlert.id))
        .filter(AttritionAlert.status == "OPEN")
        .scalar()
        or 0
    )

    return {
        "active_headcount": active_headcount,
        "employees_with_predictions": employees_with_predictions,
        "high_risk_employees": high_risk_employees,
        "open_alerts": open_alerts,
    }


@router.get("/overview")
def get_workforce_overview(
    db: DbSession,
    current_user: HRUser,
) -> dict:
    """Return current workforce metrics."""

    return {
        **calculate_metrics(db),
        "checked_at": datetime.now(),
    }


@router.post(
    "/snapshot",
    response_model=WorkforceMonitoringResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_workforce_snapshot(
    db: DbSession,
    current_user: HRUser,
) -> WorkforceMonitoringResponse:
    """Calculate and save a workforce monitoring snapshot."""

    metrics = calculate_metrics(db)

    snapshot = WorkforceMonitoring(**metrics)
    db.add(snapshot)

    try:
        db.commit()
        db.refresh(snapshot)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save workforce monitoring snapshot.",
        ) from exc

    return snapshot


@router.get(
    "/history",
    response_model=list[WorkforceMonitoringResponse],
)
def get_workforce_snapshot_history(
    db: DbSession,
    current_user: HRUser,
    limit: int = 20,
) -> list[WorkforceMonitoring]:
    """Return recent monitoring snapshots."""

    if not 1 <= limit <= 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Limit must be between 1 and 100.",
        )

    return (
        db.query(WorkforceMonitoring)
        .order_by(WorkforceMonitoring.snapshot_at.desc())
        .limit(limit)
        .all()
    )

@router.get("/trends")
def get_workforce_monitoring_trends(
    db: DbSession,
    current_user: HRUser,
    limit: int = 20,
) -> dict:
    """
    Compare recent workforce snapshots and calculate metric changes.
    """

    # Validate the requested number of snapshots.
    if not 2 <= limit <= 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Limit must be between 2 and 100.",
        )

    # Fetch the newest snapshots first.
    recent_snapshots = (
        db.query(WorkforceMonitoring)
        .order_by(WorkforceMonitoring.snapshot_at.desc())
        .limit(limit)
        .all()
    )

    # Return a useful response if there is insufficient history.
    if len(recent_snapshots) < 2:
        return {
            "message": "At least two monitoring snapshots are required.",
            "snapshots_available": len(recent_snapshots),
            "data_points": [],
            "changes": {},
        }

    # Reverse the results so charts and comparisons run oldest to newest.
    snapshots = list(reversed(recent_snapshots))

    metric_names = [
        "active_headcount",
        "employees_with_predictions",
        "high_risk_employees",
        "open_alerts",
    ]

    # Compare the oldest and newest snapshots.
    oldest = snapshots[0]
    latest = snapshots[-1]

    changes = {}

    for metric in metric_names:
        start_value = getattr(oldest, metric)
        end_value = getattr(latest, metric)
        difference = end_value - start_value

        if difference > 0:
            direction = "increased"
        elif difference < 0:
            direction = "decreased"
        else:
            direction = "unchanged"

        changes[metric] = {
            "start_value": start_value,
            "latest_value": end_value,
            "difference": difference,
            "direction": direction,
        }

    # Prepare chronological data for dashboard charts.
    data_points = [
        {
            "snapshot_id": snapshot.id,
            "snapshot_at": snapshot.snapshot_at,
            "active_headcount": snapshot.active_headcount,
            "employees_with_predictions": (
                snapshot.employees_with_predictions
            ),
            "high_risk_employees": snapshot.high_risk_employees,
            "open_alerts": snapshot.open_alerts,
        }
        for snapshot in snapshots
    ]

    return {
        "snapshots_available": len(snapshots),
        "period_start": oldest.snapshot_at,
        "period_end": latest.snapshot_at,
        "data_points": data_points,
        "changes": changes,
    }
