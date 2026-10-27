
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class WorkforceForecast(Base):
    __tablename__ = "workforce_forecasts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    forecast_months: Mapped[int] = mapped_column(Integer, nullable=False)
    current_headcount: Mapped[int] = mapped_column(Integer, nullable=False)
    employees_with_predictions: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    expected_attrition_12_months: Mapped[float] = mapped_column(
        Float, nullable=False
    )
    projected_attrition: Mapped[float] = mapped_column(
        Float, nullable=False
    )
    projected_headcount: Mapped[float] = mapped_column(
        Float, nullable=False
    )
    projected_retention_rate: Mapped[float] = mapped_column(
        Float, nullable=False
    )

    assumptions: Mapped[str] = mapped_column(Text, nullable=False)

    generated_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )
