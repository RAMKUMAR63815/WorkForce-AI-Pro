
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class AttritionDataset(Base):
    __tablename__ = "attrition_datasets"
    __table_args__ = (
        UniqueConstraint(
            "dataset_name",
            "version",
            name="uq_attrition_dataset_version",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    dataset_name: Mapped[str] = mapped_column(
        String(150), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    original_filename: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    stored_filename: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    uploaded_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    total_rows: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    valid_rows: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    invalid_rows: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(30), default="VALIDATED", nullable=False
    )
    validation_report: Mapped[str] = mapped_column(
        Text, nullable=False, default="[]"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
