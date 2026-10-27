
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.api.rbac import DbSession, HRUser
from app.models.employee import Employee
from app.models.hr_intervention import HRIntervention
from app.schemas.hr_intervention import (
    HRInterventionCreate,
    HRInterventionResponse,
    HRInterventionUpdate,
)

router = APIRouter(
    prefix="/hr-interventions",
    tags=["HR Intervention & Decision Support"],
)


@router.post(
    "/",
    response_model=HRInterventionResponse,
    status_code=201,
)
def create_intervention(
    payload: HRInterventionCreate,
    db: DbSession,
    current_user: HRUser,
):
    employee = db.get(Employee, payload.employee_id)

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found.",
        )

    intervention = HRIntervention(
        employee_id=payload.employee_id,
        intervention_type=payload.intervention_type,
        action_plan=payload.action_plan,
        notes=payload.notes,
        follow_up_date=payload.follow_up_date,
        status="PLANNED",
        created_by=current_user.id,
    )

    db.add(intervention)
    db.commit()
    db.refresh(intervention)

    return intervention


@router.get(
    "/",
    response_model=list[HRInterventionResponse],
)
def list_interventions(
    db: DbSession,
    current_user: HRUser,
    employee_id: int | None = Query(default=None, gt=0),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
):
    query = select(HRIntervention)

    if employee_id is not None:
        query = query.where(
            HRIntervention.employee_id == employee_id
        )

    if status is not None:
        allowed_statuses = {
            "PLANNED",
            "IN_PROGRESS",
            "COMPLETED",
            "CANCELLED",
        }

        if status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail="Invalid status filter.",
            )

        query = query.where(HRIntervention.status == status)

    query = query.order_by(
        HRIntervention.created_at.desc()
    ).limit(limit)

    return db.scalars(query).all()


@router.get(
    "/{intervention_id}",
    response_model=HRInterventionResponse,
)
def get_intervention(
    intervention_id: int,
    db: DbSession,
    current_user: HRUser,
):
    intervention = db.get(HRIntervention, intervention_id)

    if intervention is None:
        raise HTTPException(
            status_code=404,
            detail="Intervention not found.",
        )

    return intervention


@router.patch(
    "/{intervention_id}",
    response_model=HRInterventionResponse,
)
def update_intervention(
    intervention_id: int,
    payload: HRInterventionUpdate,
    db: DbSession,
    current_user: HRUser,
):
    intervention = db.get(HRIntervention, intervention_id)

    if intervention is None:
        raise HTTPException(
            status_code=404,
            detail="Intervention not found.",
        )

    updates = payload.model_dump(exclude_unset=True)

    new_status = updates.get("status", intervention.status)
    new_outcome = updates.get("outcome", intervention.outcome)

    if new_status == "COMPLETED" and not (
        new_outcome and new_outcome.strip()
    ):
        raise HTTPException(
            status_code=400,
            detail="Provide an outcome before completing an intervention.",
        )

    if (
        "intervention_type" in updates
        and updates["intervention_type"] is None
    ):
        raise HTTPException(
            status_code=400,
            detail="Intervention type cannot be null.",
        )

    if (
        "action_plan" in updates
        and updates["action_plan"] is None
    ):
        raise HTTPException(
            status_code=400,
            detail="Action plan cannot be null.",
        )

    for field, value in updates.items():
        setattr(intervention, field, value)

    db.commit()
    db.refresh(intervention)

    return intervention
