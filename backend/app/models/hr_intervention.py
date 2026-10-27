
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class HRIntervention(Base):
    __tablename__ = "hr_interventions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )

    intervention_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    action_plan: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    notes: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30), default="PLANNED", nullable=False
    )

    follow_up_date: Mapped[date | None] = mapped_column(
        Date, nullable=True
    )

    outcome: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False,
    )
