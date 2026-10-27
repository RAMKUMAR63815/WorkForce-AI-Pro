
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class EmployeeRiskAlertAction(Base):
    __tablename__ = "employee_risk_alert_actions"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    alert_id: Mapped[int] = mapped_column(
        ForeignKey("employee_risk_alerts.id"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    action: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
