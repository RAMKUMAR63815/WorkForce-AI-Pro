
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


class AttritionModel(Base):
    __tablename__ = "attrition_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("attrition_datasets.id"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    artifact_filename: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    feature_columns: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    target_column: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    trained_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    training_rows: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    accuracy: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class AttritionPrediction(Base):
    __tablename__ = "attrition_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_id: Mapped[int] = mapped_column(
        ForeignKey("attrition_models.id"),
        nullable=False,
        index=True,
    )
    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("attrition_datasets.id"),
        nullable=False,
        index=True,
    )
    employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.id"), nullable=True, index=True
    )
    predicted_label: Mapped[str] = mapped_column(
        String(10), nullable=False
    )
    risk_percentage: Mapped[float] = mapped_column(
        Float, nullable=False
    )
    confidence_score: Mapped[float] = mapped_column(
        Float, nullable=False
    )
    input_features: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
