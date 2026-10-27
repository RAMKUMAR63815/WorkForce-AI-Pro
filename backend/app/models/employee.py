
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    employee_code: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )

    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id"),
        nullable=True,
        index=True,
    )

    designation: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    joining_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    salary: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    shift_id: Mapped[int | None] = mapped_column(
        ForeignKey("shifts.id"),
        nullable=True,
        index=True,
    )
    manager_id: Mapped[int | None] = mapped_column(
    ForeignKey("employees.id"),
    nullable=True,
    index=True,
)
    user = relationship("User", back_populates="employee")
    department = relationship("Department")
    shift = relationship("Shift")
