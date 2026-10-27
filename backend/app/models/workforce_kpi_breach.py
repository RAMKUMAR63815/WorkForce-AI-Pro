
from datetime import datetime

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class WorkforceKPIBreach(Base):
    __tablename__ = "workforce_kpi_breaches"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    metric_key: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )

    current_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    target_value: Mapped[float] = mapped_column(
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

    message: Mapped[str] = mapped_column(
        String(255),
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
