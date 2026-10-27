
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str
    # This field is populated only in explicit development mode.
    reset_token: str | None = None


class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=20, max_length=200)
    new_password: str = Field(min_length=12, max_length=128)


class ResetPasswordResponse(BaseModel):
    message: str
