
from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from fastapi import Query
from app.core.dependencies import (
    DbSession,
    AuthenticatedUser,
    HRUser,
)
from app.models.employee import Employee
from app.models.leave import Leave
from app.models.leave_balance import LeaveBalance
from app.schemas.leave import (
    LeaveCreate,
    LeaveReview,
    LeaveResponse,
)
from app.models.notification import Notification

router = APIRouter(
    prefix="/leaves",
    tags=["Leave Management"],
)


def calculate_yearly_working_days(
    start_date: date,
    end_date: date,
) -> dict[int, int]:
    """Count weekdays separately for each calendar year."""

    yearly_days = {}
    current_date = start_date

    while current_date <= end_date:
        # Monday = 0, Friday = 4; skip weekends.
        if current_date.weekday() < 5:
            year = current_date.year
            yearly_days[year] = yearly_days.get(year, 0) + 1

        current_date += timedelta(days=1)

    return yearly_days


@router.post(
    "/",
    response_model=LeaveResponse,
    status_code=status.HTTP_201_CREATED,
)
def apply_leave(
    payload: LeaveCreate,
    db: DbSession,
    current_user: AuthenticatedUser,
):
    """An employee submits their own leave request."""

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

    if payload.start_date < date.today():
        raise HTTPException(
            status_code=400,
            detail="Leave cannot start in the past.",
        )

    if payload.end_date < payload.start_date:
        raise HTTPException(
            status_code=400,
            detail="End date cannot be before start date.",
        )

    # Find requests for the same employee that overlap the dates.
    overlapping_leave = db.scalar(
        select(Leave.id)
        .where(
            Leave.employee_id == employee.id,
            Leave.status.in_(["PENDING", "APPROVED"]),
            Leave.start_date <= payload.end_date,
            Leave.end_date >= payload.start_date,
        )
        .limit(1)
    )

    if overlapping_leave is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "These dates overlap an existing pending "
                "or approved leave request."
            ),
        )

    leave = Leave(
        employee_id=employee.id,
        leave_type=payload.leave_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        reason=payload.reason,
        status="PENDING",
    )

    db.add(leave)
    db.add(
    Notification(
        user_id=current_user.id,
        title="Leave Request Submitted",
        message=(
            f"Your {leave.leave_type} leave request "
            f"from {leave.start_date} to {leave.end_date} "
            "has been submitted for review."
        ),
        notification_type="LEAVE",
    )
)
    db.commit()
    db.refresh(leave)

    return leave


@router.get(
    "/my",
    response_model=list[LeaveResponse],
)
def get_my_leaves(
    db: DbSession,
    current_user: AuthenticatedUser,
):
    """Return only the current employee's leave requests."""

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
        select(Leave)
        .where(Leave.employee_id == employee.id)
        .order_by(Leave.created_at.desc())
    ).all()



@router.get("/", response_model=list[LeaveResponse])
def get_all_leaves(
    db: DbSession,
    current_user: HRUser,
    leave_status: str | None = Query(default=None),
    employee_id: int | None = Query(default=None, gt=0),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
):
    """HR/Admin leave history with filters and pagination."""

    query = select(Leave)

    if leave_status:
        if leave_status not in ["PENDING", "APPROVED", "REJECTED"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid leave status.",
            )

        query = query.where(Leave.status == leave_status)

    if employee_id is not None:
        query = query.where(
            Leave.employee_id == employee_id
        )

    query = (
        query
        .order_by(Leave.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    return db.scalars(query).all()



@router.patch(
    "/{leave_id}/review",
    response_model=LeaveResponse,
)
def review_leave(
    leave_id: int,
    payload: LeaveReview,
    db: DbSession,
    current_user: HRUser,
):
    """HR/Admin approves or rejects a pending leave request."""

    try:
        # Lock the leave request to prevent concurrent reviews.
        leave = db.scalar(
            select(Leave)
            .where(Leave.id == leave_id)
            .with_for_update()
        )

        if leave is None:
            raise HTTPException(
                status_code=404,
                detail="Leave request not found.",
            )

        if leave.status != "PENDING":
            raise HTTPException(
                status_code=400,
                detail="This leave request has already been reviewed.",
            )

        # Only APPROVED or REJECTED are valid review decisions.
        if payload.status not in ("APPROVED", "REJECTED"):
            raise HTTPException(
                status_code=400,
                detail="Review status must be APPROVED or REJECTED.",
            )

        # Rejection does not consume leave balance.
        if payload.status == "REJECTED":
            leave.status = "REJECTED"
            leave.reviewed_by = current_user.id
            leave.review_remarks = payload.review_remarks

            employee = db.get(Employee, leave.employee_id)
            if employee is not None:
                db.add(
                    Notification(
                        user_id=employee.user_id,
                        title="Leave Request Rejected",
                        message=(
                            f"Your leave request #{leave.id} was rejected."
                            + (
                                f" Reason: {payload.review_remarks}"
                                if payload.review_remarks
                                else ""
                            )
                        ),
                        notification_type="LEAVE",
                    )
            )
            db.commit()
            db.refresh(leave)
            return leave

        # UNPAID leave does not consume allocated leave balance.
        if leave.leave_type != "UNPAID":
            yearly_days = calculate_yearly_working_days(
                leave.start_date,
                leave.end_date,
            )

            balances = {}

            # First, validate every year's balance.
            for year, days in yearly_days.items():
                balance = db.scalar(
                    select(LeaveBalance)
                    .where(
                        LeaveBalance.employee_id == leave.employee_id,
                        LeaveBalance.leave_type == leave.leave_type,
                        LeaveBalance.year == year,
                    )
                    .with_for_update()
                )

                if balance is None:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"No {leave.leave_type} leave balance "
                            f"exists for {year}."
                        ),
                    )

                remaining_days = (
                    balance.total_days - balance.used_days
                )

                if remaining_days < days:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"Insufficient {leave.leave_type} leave "
                            f"balance for {year}. "
                            f"Required: {days}, "
                            f"available: {remaining_days}."
                        ),
                    )

                balances[year] = (balance, days)

            # Deduct only after all yearly balances pass validation.
            for balance, days in balances.values():
                balance.used_days += days

        # Update review details.
        leave.status = "APPROVED"
        leave.reviewed_by = current_user.id
        leave.review_remarks = payload.review_remarks
        employee = db.get(Employee, leave.employee_id)

        if employee is not None:
            db.add(
                Notification(
                    user_id=employee.user_id,
                    title="Leave Request Approved",
                    message=(
                        f"Your {leave.leave_type} leave request "
                        f"from {leave.start_date} to {leave.end_date} "
                        "has been approved."
                    ),
                    notification_type="LEAVE",
                )
        )
        db.commit()
        db.refresh(leave)

        return leave

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise
