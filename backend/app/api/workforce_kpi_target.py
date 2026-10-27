
from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import DbSession, HRUser
from app.models.workforce_kpi_target import WorkforceKPITarget
from app.schemas.workforce_kpi_target import (
    WorkforceKPITargetCreate,
    WorkforceKPITargetUpdate,
    WorkforceKPITargetResponse,
)
from app.api.workforce_dashboard import get_workforce_kpis


router = APIRouter(
    prefix="/workforce-kpi-targets",
    tags=["Workforce KPI Targets"],
)


@router.post(
    "",
    response_model=WorkforceKPITargetResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_kpi_target(
    payload: WorkforceKPITargetCreate,
    db: DbSession,
    current_user: HRUser,
) -> WorkforceKPITarget:
    # One target per metric. Reject duplicate target definitions.
    existing = (
        db.query(WorkforceKPITarget)
        .filter(WorkforceKPITarget.metric_key == payload.metric_key)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A target already exists for this metric. Update it instead.",
        )

    target = WorkforceKPITarget(
        metric_key=payload.metric_key,
        target_value=payload.target_value,
    )

    db.add(target)

    try:
        db.commit()
        db.refresh(target)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create KPI target.",
        ) from exc

    return target


@router.get(
    "",
    response_model=list[WorkforceKPITargetResponse],
)
def list_kpi_targets(
    db: DbSession,
    current_user: HRUser,
) -> list[WorkforceKPITarget]:
    return (
        db.query(WorkforceKPITarget)
        .order_by(WorkforceKPITarget.metric_key.asc())
        .all()
    )


@router.patch(
    "/{target_id}",
    response_model=WorkforceKPITargetResponse,
)
def update_kpi_target(
    target_id: int,
    payload: WorkforceKPITargetUpdate,
    db: DbSession,
    current_user: HRUser,
) -> WorkforceKPITarget:
    target = db.get(WorkforceKPITarget, target_id)

    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="KPI target not found.",
        )

    target.target_value = payload.target_value

    try:
        db.commit()
        db.refresh(target)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update KPI target.",
        ) from exc

    return target


@router.get("/achievement")
def get_kpi_target_achievements(
    db: DbSession,
    current_user: HRUser,
) -> dict:
    # Get the current metrics from the existing KPI dashboard function.
    current_kpis = get_workforce_kpis(db, current_user)

    targets = db.query(WorkforceKPITarget).all()
    achievements = []

    for target in targets:
        current_value = current_kpis[target.metric_key]
        target_value = target.target_value

        # For high-risk counts and open alerts, lower is better.
        lower_is_better = target.metric_key in {
            "high_risk_employees",
            "high_risk_percentage",
            "open_alerts",
        }

        if lower_is_better:
            achieved = current_value <= target_value
        else:
            achieved = current_value >= target_value

        if target_value == 0:
            achievement_percentage = (
                100.0 if current_value == 0 else None
            )
        else:
            achievement_percentage = round(
                current_value / target_value * 100,
                2,
            )

        achievements.append(
            {
                "metric_key": target.metric_key,
                "current_value": current_value,
                "target_value": target_value,
                "achieved": achieved,
                "achievement_percentage": achievement_percentage,
                "comparison": (
                    "lower_is_better"
                    if lower_is_better
                    else "higher_is_better"
                ),
            }
        )

    return {
        "generated_at": current_kpis["generated_at"],
        "total_targets": len(targets),
        "achieved_targets": sum(
            1 for item in achievements if item["achieved"]
        ),
        "results": achievements,
    }
