
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Attendance(Base):
    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )

    check_in: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    check_out: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    worked_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
