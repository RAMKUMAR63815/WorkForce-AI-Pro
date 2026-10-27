
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.dependencies import DbSession, HRUser
from app.models.employee_risk_alert import EmployeeRiskAlert
from app.models.employee_risk_alert_action import (
    EmployeeRiskAlertAction,
)
from app.schemas.employee_risk_alert_action import (
    EmployeeRiskAlertActionCreate,
    EmployeeRiskAlertActionResponse,
)

router = APIRouter(
    prefix="/employee-risk-alerts",
    tags=["Employee Risk Alert Actions"],
)


@router.post(
    "/{alert_id}/acknowledge",
    response_model=EmployeeRiskAlertActionResponse,
    status_code=status.HTTP_201_CREATED,
)
def acknowledge_alert(
    alert_id: int,
    payload: EmployeeRiskAlertActionCreate,
    db: DbSession,
    current_user: HRUser,
):
    alert = db.scalar(
        select(EmployeeRiskAlert).where(
            EmployeeRiskAlert.id == alert_id
        )
    )

    if alert is None:
        raise HTTPException(
            status_code=404,
            detail="Employee risk alert not found",
        )

    action = EmployeeRiskAlertAction(
        alert_id=alert_id,
        user_id=current_user.id,
        action=payload.action,
        notes=payload.notes,
    )

    db.add(action)
    db.commit()
    db.refresh(action)

    return action


@router.get(
    "/{alert_id}/actions",
    response_model=list[EmployeeRiskAlertActionResponse],
)
def get_alert_actions(
    alert_id: int,
    db: DbSession,
    current_user: HRUser,
):
    alert = db.scalar(
        select(EmployeeRiskAlert).where(
            EmployeeRiskAlert.id == alert_id
        )
    )

    if alert is None:
        raise HTTPException(
            status_code=404,
            detail="Employee risk alert not found",
        )

    actions = db.scalars(
        select(EmployeeRiskAlertAction)
        .where(EmployeeRiskAlertAction.alert_id == alert_id)
        .order_by(EmployeeRiskAlertAction.created_at.desc())
    ).all()

    return actions
