import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MessagePreview(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sender: str
    subject: str | None
    received_at: datetime


class MessageDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sender: str
    subject: str | None
    body: str
    received_at: datetime


class MessageListResponse(BaseModel):
    messages: list[MessagePreview]
    count: int
