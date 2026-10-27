
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    recipient_id: int = Field(gt=0)


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_one_id: int
    user_two_id: int
    created_at: datetime


class MessageCreate(BaseModel):
    message: str = Field(min_length=1, max_length=5000)


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    sender_id: int
    message: str
    sent_at: datetime
    read_at: datetime | None
