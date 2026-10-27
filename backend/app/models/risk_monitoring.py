
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class RiskMonitoringLog(Base):
    __tablename__ = "risk_monitoring_logs"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    prediction_id: Mapped[int] = mapped_column(
        ForeignKey("attrition_predictions.id"),
        nullable=False,
        index=True,
    )

    employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.id"),
        nullable=True,
        index=True,
    )

    previous_risk: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    current_risk: Mapped[float] = mapped_column(
        Float, nullable=False
    )

    risk_change: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    risk_level: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )

    alert_generated: Mapped[bool] = mapped_column(
        default=False, nullable=False
    )

    notes: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
