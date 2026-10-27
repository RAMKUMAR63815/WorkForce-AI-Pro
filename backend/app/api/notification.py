
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select , func
from fastapi import Query

from app.core.dependencies import DbSession, AuthenticatedUser, HRUser
from app.models.employee import Employee
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
)

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.get("/my", response_model=list[NotificationResponse])
def get_my_notifications(
    db: DbSession,
    current_user: AuthenticatedUser,
    unread_only: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """Employee views their own notifications."""

    query = select(Notification).where(
        Notification.user_id == current_user.id
    )

    if unread_only:
        query = query.where(Notification.is_read.is_(False))

    return db.scalars(
        query.order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()


@router.patch("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    db: DbSession,
    current_user: AuthenticatedUser,
):
    """Mark only the current user's notification as read."""

    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )

    if notification is None:
        raise HTTPException(
            status_code=404,
            detail="Notification not found.",
        )

    notification.is_read = True
    db.commit()

    return {"message": "Notification marked as read."}


@router.post(
    "/employee/{employee_id}",
    response_model=NotificationResponse,
)
def send_employee_notification(
    employee_id: int,
    payload: NotificationCreate,
    db: DbSession,
    current_user: HRUser,
):
    """HR/Admin sends a notification to an employee."""

    employee = db.get(Employee, employee_id)

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found.",
        )

    user = db.get(User, employee.user_id)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=400,
            detail="Employee account is unavailable.",
        )

    notification = Notification(
        user_id=user.id,
        title=payload.title,
        message=payload.message,
        notification_type=payload.notification_type,
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification


@router.get("/", response_model=list[NotificationResponse])
def get_all_notifications(
    db: DbSession,
    current_user: HRUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """HR/Admin views notifications across the organization."""

    return db.scalars(
        select(Notification)
        .order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()


@router.get("/my/unread-count")
def get_my_unread_count(
    db: DbSession,
    current_user: AuthenticatedUser,
):
    count = db.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
    )

    return {"unread_count": count or 0}