
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AttendanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    check_in: datetime
    check_out: datetime | None
    worked_minutes: int | None
