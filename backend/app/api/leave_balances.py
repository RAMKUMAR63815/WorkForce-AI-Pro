
from datetime import date

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.dependencies import DbSession, AuthenticatedUser, HRUser
from app.models.employee import Employee
from app.models.leave_balance import LeaveBalance
from app.schemas.leave_balance import (
    LeaveBalanceCreate,
    LeaveBalanceResponse,
)

router = APIRouter(
    prefix="/leave-balances",
    tags=["Leave Balance"],
)


@router.post(
    "/",
    response_model=LeaveBalanceResponse,
)
def create_leave_balance(
    payload: LeaveBalanceCreate,
    db: DbSession,
    current_user: HRUser,
):
    """HR/Admin creates an employee's leave allowance."""

    employee = db.get(Employee, payload.employee_id)

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found.",
        )

    existing = db.scalar(
        select(LeaveBalance).where(
            LeaveBalance.employee_id == payload.employee_id,
            LeaveBalance.leave_type == payload.leave_type,
            LeaveBalance.year == payload.year,
        )
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Leave balance already exists.",
        )

    balance = LeaveBalance(
        employee_id=payload.employee_id,
        leave_type=payload.leave_type,
        year=payload.year,
        total_days=payload.total_days,
        used_days=0,
    )

    db.add(balance)
    db.commit()
    db.refresh(balance)

    return balance


@router.get(
    "/my",
    response_model=list[LeaveBalanceResponse],
)
def get_my_leave_balances(
    db: DbSession,
    current_user: AuthenticatedUser,
):
    """Employee sees only their own leave balances."""

    employee = db.scalar(
        select(Employee).where(
            Employee.user_id == current_user.id
        )
    )

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee profile not found.",
        )

    return db.scalars(
        select(LeaveBalance).where(
            LeaveBalance.employee_id == employee.id,
            LeaveBalance.year == date.today().year,
        )
    ).all()


@router.get(
    "/employee/{employee_id}",
    response_model=list[LeaveBalanceResponse],
)
def get_employee_leave_balances(
    employee_id: int,
    db: DbSession,
    current_user: HRUser,
):
    """HR/Admin views a specific employee's balances."""

    employee = db.get(Employee, employee_id)

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found.",
        )

    return db.scalars(
        select(LeaveBalance).where(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.year == date.today().year,
        )
    ).all()
