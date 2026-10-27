
from datetime import datetime

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class WorkforceKPITarget(Base):
    __tablename__ = "workforce_kpi_targets"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    # Example: prediction_coverage_percentage
    metric_key: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    # Example: 80.0 means an 80% target.
    target_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
