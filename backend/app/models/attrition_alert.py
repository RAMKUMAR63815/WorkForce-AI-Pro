
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class AttritionAlert(Base):
    __tablename__ = "attrition_alerts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    prediction_id: Mapped[int] = mapped_column(
        ForeignKey("attrition_predictions.id"),
        nullable=False,
    )

    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )

    risk_level: Mapped[str] = mapped_column(
        String(20), nullable=False
    )

    risk_percentage: Mapped[float] = mapped_column(
        Float, nullable=False
    )

    message: Mapped[str] = mapped_column(
        String(500), nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30), default="OPEN", nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )

    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
