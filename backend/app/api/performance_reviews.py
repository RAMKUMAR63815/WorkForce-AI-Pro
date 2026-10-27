
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.rbac import AuthenticatedUser, HRUser, DbSession
from app.models.employee import Employee
from app.models.performance_review import PerformanceReview
from app.schemas.performance_review import (
    PerformanceReviewCreate,
    PerformanceReviewResponse,
    PerformanceReviewUpdate,
)
from sqlalchemy import select
from app.models.notification import Notification
router = APIRouter(
    prefix="/performance-reviews",
    tags=["Performance Reviews"],
)


@router.post(
    "/",
    response_model=PerformanceReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_performance_review(
    payload: PerformanceReviewCreate,
    db: DbSession,
    current_user: AuthenticatedUser,
):
    employee = db.get(Employee, payload.employee_id)

    if employee is None:
        raise HTTPException(404, "Employee not found.")

    if current_user.role in {"ADMIN", "HR"}:
        pass
    elif current_user.role == "MANAGER":
        manager_employee = db.scalar(
            select(Employee).where(
                Employee.user_id == current_user.id
            )
        )

        if (
            manager_employee is None
            or employee.manager_id != manager_employee.id
        ):
            raise HTTPException(
                status_code=403,
                detail="You can review only your assigned employees.",
            )
    else:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to create performance reviews.",
        )

    review = PerformanceReview(
        employee_id=employee.id,
        reviewer_id=current_user.id,
        review_period_start=payload.review_period_start,
        review_period_end=payload.review_period_end,
        rating=payload.rating,
        strengths=payload.strengths,
        areas_for_improvement=payload.areas_for_improvement,
        goals=payload.goals,
        comments=payload.comments,
        status="COMPLETED",
    )

    db.add(review)

    db.add(
        Notification(
            user_id=employee.user_id,
            title="Performance Review Published",
            message=(
                f"A performance review has been published for you. "
                f"Review period: {payload.review_period_start} "
                f"to {payload.review_period_end}. "
                f"Rating: {payload.rating}/5."
            ),
            notification_type="PERFORMANCE_REVIEW",
        )
    )

    db.commit()
    db.refresh(review)

    return review


@router.get("/my", response_model=list[PerformanceReviewResponse])
def get_my_performance_reviews(
    db: DbSession,
    current_user: AuthenticatedUser,
):
    employee = db.scalar(
        select(Employee).where(
            Employee.user_id == current_user.id
        )
    )

    if employee is None:
        return []

    return db.scalars(
        select(PerformanceReview)
        .where(PerformanceReview.employee_id == employee.id)
        .order_by(PerformanceReview.created_at.desc())
    ).all()


@router.get("/", response_model=list[PerformanceReviewResponse])
def get_all_performance_reviews(
    db: DbSession,
    current_user: HRUser,
    employee_id: int | None = Query(default=None, gt=0),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    query = select(PerformanceReview)

    if employee_id is not None:
        query = query.where(
            PerformanceReview.employee_id == employee_id
        )

    return db.scalars(
        query.order_by(PerformanceReview.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()


@router.get(
    "/{review_id}",
    response_model=PerformanceReviewResponse,
)
def get_performance_review(
    review_id: int,
    db: DbSession,
    current_user: AuthenticatedUser,
):
    review = db.get(PerformanceReview, review_id)

    if review is None:
        raise HTTPException(
            status_code=404,
            detail="Performance review not found.",
        )

    employee = db.get(Employee, review.employee_id)

    is_hr_or_admin = current_user.role in {"HR", "ADMIN"}
    is_employee_owner = (
        employee is not None
        and employee.user_id == current_user.id
    )
    is_reviewer = review.reviewer_id == current_user.id

    if not (is_hr_or_admin or is_employee_owner or is_reviewer):
        raise HTTPException(
            status_code=403,
            detail="You cannot access this performance review.",
        )

    return review

@router.patch("/{review_id}", response_model=PerformanceReviewResponse)
def update_performance_review(
    review_id: int,
    payload: PerformanceReviewUpdate,
    db: DbSession,
    current_user: HRUser,
):
    review = db.get(PerformanceReview, review_id)

    if review is None:
        raise HTTPException(404, "Performance review not found.")

    updates = payload.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(review, field, value)

    if not updates:
        raise HTTPException(400, "Provide at least one field to update.")

    db.commit()
    db.refresh(review)
    return review


@router.delete("/{review_id}")
def delete_performance_review(
    review_id: int,
    db: DbSession,
    current_user: HRUser,
):
    review = db.get(PerformanceReview, review_id)

    if review is None:
        raise HTTPException(404, "Performance review not found.")

    db.delete(review)
    db.commit()

    return {"message": "Performance review deleted successfully."}