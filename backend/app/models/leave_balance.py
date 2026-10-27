
from sqlalchemy import ForeignKey, Integer, UniqueConstraint,String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "leave_type",
            "year",
            name="uq_employee_leave_type_year",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )

    leave_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    total_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    used_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
