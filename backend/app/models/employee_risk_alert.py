
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class EmployeeRiskAlert(Base):
    __tablename__ = "employee_risk_alerts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id"),
        index=True,
        nullable=False,
    )

    previous_risk: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    current_risk: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    risk_increase: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        default="MEDIUM",
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="OPEN",
        index=True,
        nullable=False,
    )

    detected_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
    )
