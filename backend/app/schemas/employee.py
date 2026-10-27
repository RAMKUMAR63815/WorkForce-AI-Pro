from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EmployeeCreate(BaseModel):
    """Validate data required to create an employee."""

    # Login account details
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)

    # Employee details
    employee_code: str = Field(min_length=1, max_length=30)
    department_id: int | None = Field(default=None, gt=0)
    designation: str = Field(min_length=1, max_length=100)
    joining_date: date
    salary: Decimal = Field(gt=0, max_digits=12, decimal_places=2)

    phone: str | None = Field(default=None, max_length=20)
    address: str | None = None


class EmployeeUpdate(BaseModel):
    """Validate fields that may be updated."""

    model_config = ConfigDict(extra="forbid")

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    department_id: int | None = Field(default=None, gt=0)
    designation: str | None = Field(default=None, min_length=1, max_length=100)
    joining_date: date | None = None
    salary: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=12,
        decimal_places=2,
    )
    phone: str | None = Field(default=None, max_length=20)
    address: str | None = None


class EmployeeUserSummary(BaseModel):
    """Safe account information returned with an employee."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool


class EmployeeDepartmentSummary(BaseModel):
    """Department information returned with an employee."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class EmployeeResponse(BaseModel):
    """Employee information returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_code: str
    department_id: int | None
    designation: str
    joining_date: date
    salary: Decimal
    phone: str | None
    address: str | None

    user: EmployeeUserSummary
    department: EmployeeDepartmentSummary | None
