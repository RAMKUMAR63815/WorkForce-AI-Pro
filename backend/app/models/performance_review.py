
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class PerformanceReview(Base):
    __tablename__ = "performance_reviews"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )

    reviewer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    review_period_start: Mapped[date] = mapped_column(
        Date, nullable=False
    )

    review_period_end: Mapped[date] = mapped_column(
        Date, nullable=False
    )

    rating: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    strengths: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    areas_for_improvement: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    goals: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    comments: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20), default="COMPLETED", nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
