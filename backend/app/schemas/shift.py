
from datetime import time

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ShiftCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    start_time: time
    end_time: time
    break_minutes: int = Field(default=0, ge=0, le=480)

    @model_validator(mode="after")#Pydantic's model-level validation mechanism
    def validate_shift(self):
        if self.start_time == self.end_time:
            raise ValueError("Start and end times cannot be identical.")
        return self


class ShiftUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=2, max_length=100)
    start_time: time | None = None
    end_time: time | None = None
    break_minutes: int | None = Field(default=None, ge=0, le=480)
    is_active: bool | None = None


class ShiftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    start_time: time
    end_time: time
    break_minutes: int
    is_active: bool
