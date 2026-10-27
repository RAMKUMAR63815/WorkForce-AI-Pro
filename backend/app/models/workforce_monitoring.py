
from datetime import datetime

from sqlalchemy import DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class WorkforceMonitoring(Base):
    """Stores a snapshot of workforce monitoring metrics."""

    __tablename__ = "workforce_monitoring"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    active_headcount: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    employees_with_predictions: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    high_risk_employees: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    open_alerts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    snapshot_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
    )
