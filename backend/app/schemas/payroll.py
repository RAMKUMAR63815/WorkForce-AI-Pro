
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PayrollCreate(BaseModel):
    employee_id: int = Field(gt=0)
    year: int = Field(ge=2020, le=2100)
    month: int = Field(ge=1, le=12)

    basic_salary: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )

    allowance: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )

    deduction: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )


class PayrollResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    year: int
    month: int
    basic_salary: Decimal
    allowance: Decimal
    deduction: Decimal
    net_salary: Decimal
    status: str
    created_at: datetime
