
from datetime import date

from fastapi import APIRouter, HTTPException
from sqlalchemy import select, func

from app.core.dependencies import DbSession, AuthenticatedUser, HRUser
from app.models.employee import Employee
from app.models.attendance import Attendance
from app.models.leave import Leave
from app.models.department import Department

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get("/employee")
def employee_dashboard(
    db: DbSession,
    current_user: AuthenticatedUser,
):
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

    attendance_count = db.scalar(
        select(func.count(Attendance.id)).where(
            Attendance.employee_id == employee.id
        )
    )

    pending_leaves = db.scalar(
        select(func.count(Leave.id)).where(
            Leave.employee_id == employee.id,
            Leave.status == "PENDING",
        )
    )

    approved_leaves = db.scalar(
        select(func.count(Leave.id)).where(
            Leave.employee_id == employee.id,
            Leave.status == "APPROVED",
        )
    )

    return {
        "employee_id": employee.id,
        "employee_code": employee.employee_code,
        "designation": employee.designation,
        "attendance_records": attendance_count or 0,
        "pending_leave_requests": pending_leaves or 0,
        "approved_leave_requests": approved_leaves or 0,
    }


@router.get("/hr")
def hr_dashboard(
    db: DbSession,
    current_user: HRUser,
):
    total_employees = db.scalar(
        select(func.count(Employee.id))
    )

    total_departments = db.scalar(
        select(func.count(Department.id))
    )

    pending_leaves = db.scalar(
        select(func.count(Leave.id)).where(
            Leave.status == "PENDING"
        )
    )

    approved_leaves = db.scalar(
        select(func.count(Leave.id)).where(
            Leave.status == "APPROVED"
        )
    )

    return {
        "total_employees": total_employees or 0,
        "total_departments": total_departments or 0,
        "pending_leave_requests": pending_leaves or 0,
        "approved_leave_requests": approved_leaves or 0,
    }
