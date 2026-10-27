
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.dependencies import DbSession, HRUser, AuthenticatedUser
from app.models import Shift
from app.schemas.shift import ShiftCreate, ShiftUpdate, ShiftResponse

from app.models import Employee, Shift
from app.schemas.shift_assignment import (
    ShiftAssignmentRequest,
    ShiftAssignmentResponse,
)

router = APIRouter(prefix="/shifts", tags=["Shifts"])


@router.post(
    "/",
    response_model=ShiftResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_shift(
    payload: ShiftCreate,
    db: DbSession,
    current_user: HRUser,
):
    name = payload.name.strip()

    if not name:
        raise HTTPException(
            status_code=422,
            detail="Shift name cannot be blank.",
        )

    existing = db.scalar(
        select(Shift).where(Shift.name == name)
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="A shift with this name already exists.",
        )

    shift = Shift(
        name=name,
        start_time=payload.start_time,
        end_time=payload.end_time,
        break_minutes=payload.break_minutes,
    )

    db.add(shift)

    try:
        db.commit()
        db.refresh(shift)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Unable to create shift due to a data conflict.",
        ) from None

    return shift


@router.get("/", response_model=list[ShiftResponse])
def list_shifts(
    db: DbSession,
    current_user: AuthenticatedUser,
):
    return db.scalars(
        select(Shift)
        .where(Shift.is_active.is_(True))
        .order_by(Shift.start_time)
    ).all()


@router.put("/{shift_id}", response_model=ShiftResponse)
def update_shift(
    shift_id: int,
    payload: ShiftUpdate,
    db: DbSession,
    current_user: HRUser,
):
    shift = db.get(Shift, shift_id)

    if shift is None:
        raise HTTPException(
            status_code=404,
            detail="Shift not found.",
        )

    changes = payload.model_dump(exclude_unset=True)

    if not changes:
        raise HTTPException(
            status_code=422,
            detail="Provide at least one field to update.",
        )

    if "name" in changes:
        name = changes["name"]

        if name is None or not name.strip():
            raise HTTPException(
                status_code=422,
                detail="Shift name cannot be blank.",
            )

        name = name.strip()

        duplicate = db.scalar(
            select(Shift).where(
                Shift.name == name,
                Shift.id != shift_id,
            )
        )

        if duplicate:
            raise HTTPException(
                status_code=409,
                detail="A shift with this name already exists.",
            )

        changes["name"] = name

    start_time = changes.get("start_time", shift.start_time)
    end_time = changes.get("end_time", shift.end_time)

    if start_time is None or end_time is None:
        raise HTTPException(
            status_code=422,
            detail="Start time and end time cannot be null.",
        )

    if start_time == end_time:
        raise HTTPException(
            status_code=422,
            detail="Start and end times cannot be identical.",
        )

    for field, value in changes.items():
        setattr(shift, field, value)

    try:
        db.commit()
        db.refresh(shift)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Unable to update shift due to a data conflict.",
        ) from None

    return shift


@router.delete("/{shift_id}")
def deactivate_shift(
    shift_id: int,
    db: DbSession,
    current_user: HRUser,
):
    shift = db.get(Shift, shift_id)

    if shift is None:
        raise HTTPException(
            status_code=404,
            detail="Shift not found.",
        )

    if not shift.is_active:
        raise HTTPException(
            status_code=409,
            detail="Shift is already inactive.",
        )

    shift.is_active = False
    db.commit()

    return {
        "message": "Shift deactivated successfully.",
        "shift_id": shift.id,
    }

@router.patch(
    "/assignments/{employee_id}",
    response_model=ShiftAssignmentResponse,
)
def assign_employee_shift(
    employee_id: int,
    payload: ShiftAssignmentRequest,
    db: DbSession,
    current_user: HRUser,
):
    """Assign or remove an employee's shift."""

    employee = db.get(Employee, employee_id)

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found.",
        )

    selected_shift = None

    if payload.shift_id is not None:
        selected_shift = db.get(Shift, payload.shift_id)

        if selected_shift is None or not selected_shift.is_active:
            raise HTTPException(
                status_code=400,
                detail="Active shift not found.",
            )

    employee.shift_id = (
        selected_shift.id if selected_shift else None
    )

    db.commit()
    db.refresh(employee)

    return {
        "employee_id": employee.id,
        "employee_code": employee.employee_code,
        "shift_id": employee.shift_id,
        "shift_name": (
            selected_shift.name if selected_shift else None
        ),
    }
