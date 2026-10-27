
from datetime import datetime
from datetime import datetime
from sqlalchemy import func
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.dependencies import (
    DbSession,
    AuthenticatedUser,
    HRUser,
)
from app.models import Attendance, Employee
from app.schemas.attendance import AttendanceResponse


router = APIRouter(
    prefix="/attendance",
    tags=["Attendance"],
)


@router.post(
    "/check-in",
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED,
)
def check_in(
    db: DbSession,
    current_user: AuthenticatedUser,
):
    # Find the employee profile for the logged-in user.
    employee = db.scalar(
        select(Employee).where(
            Employee.user_id == current_user.id
        )
    )

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee profile not found.",
        )

    # Check whether this employee already has an open session.
    open_attendance = db.scalar(
        select(Attendance).where(
            Attendance.employee_id == employee.id,
            Attendance.check_out.is_(None),
        )
    )

    if open_attendance is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an active check-in.",
        )

    # Create a new attendance record.
    attendance = Attendance(
        employee_id=employee.id,
        check_in=datetime.now(),
    )

    db.add(attendance)
    db.commit()
    db.refresh(attendance)

    return attendance


@router.post(
    "/check-out",
    response_model=AttendanceResponse,
)
def check_out(
    db: DbSession,
    current_user: AuthenticatedUser,
):
    # Find the logged-in user's employee profile.
    employee = db.scalar(
        select(Employee).where(
            Employee.user_id == current_user.id
        )
    )

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee profile not found.",
        )

    # Find the employee's current open attendance.
    attendance = db.scalar(
        select(Attendance).where(
            Attendance.employee_id == employee.id,
            Attendance.check_out.is_(None),
        )
    )

    if attendance is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must check in before checking out.",
        )

    # Record the check-out time.
    checkout_time = datetime.now()

    # Calculate total working time in minutes.
    worked_minutes = int(
        (checkout_time - attendance.check_in).total_seconds()
        // 60
    )

    attendance.check_out = checkout_time
    attendance.worked_minutes = worked_minutes

    db.commit()
    db.refresh(attendance)

    return attendance


@router.get(
    "/my",
    response_model=list[AttendanceResponse],
)
def my_attendance(
    db: DbSession,
    current_user: AuthenticatedUser,
):
    """Return attendance history for the logged-in employee."""

    employee = db.scalar(
        select(Employee).where(
            Employee.user_id == current_user.id
        )
    )

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee profile not found.",
        )

    records = db.scalars(
        select(Attendance)
        .where(Attendance.employee_id == employee.id)
        .order_by(Attendance.check_in.desc())
    ).all()

    return records


@router.get(
    "/employee/{employee_id}",
    response_model=list[AttendanceResponse],
)
def employee_attendance_history(
    employee_id: int,
    db: DbSession,
    current_user: HRUser,
):
    """Allow ADMIN and HR to view one employee's history."""

    employee = db.get(Employee, employee_id)

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found.",
        )

    records = db.scalars(
        select(Attendance)
        .where(Attendance.employee_id == employee_id)
        .order_by(Attendance.check_in.desc())
    ).all()

    return records


@router.get(
    "/",
    response_model=list[AttendanceResponse],
)
def list_attendance(
    db: DbSession,
    current_user: HRUser,
):
    # ADMIN and HR can review attendance records.
    records = db.scalars(
        select(Attendance).order_by(
            Attendance.check_in.desc()
        )
    ).all()

    return records

@router.get("/my/summary")
def my_attendance_summary(
    db: DbSession,
    current_user: AuthenticatedUser,
    year: int = 2026,
    month: int = 10,
):
    """Current employee's monthly attendance summary."""

    if month < 1 or month > 12:
        raise HTTPException(
            status_code=400,
            detail="Month must be between 1 and 12.",
        )

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

    start_date = datetime(year, month, 1)

    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    records = db.scalars(
        select(Attendance).where(
            Attendance.employee_id == employee.id,
            Attendance.check_in >= start_date,
            Attendance.check_in < end_date,
        )
    ).all()

    total_days = len(records)

    completed_records = [
        record for record in records
        if record.worked_minutes is not None
    ]

    total_minutes = sum(
        record.worked_minutes
        for record in completed_records
    )

    return {
        "employee_id": employee.id,
        "year": year,
        "month": month,
        "attendance_days": total_days,
        "completed_days": len(completed_records),
        "total_worked_minutes": total_minutes,
        "total_worked_hours": round(total_minutes / 60, 2),
        "open_sessions": total_days - len(completed_records),
    }
