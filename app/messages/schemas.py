import uuid
import nh3

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


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
    html_body: str | None

    @field_validator("html_body")
    @classmethod
    def sanitize_body(cls, v: str | None) -> str | None:
        return nh3.clean(v) if v else v


class MessageListResponse(BaseModel):
    messages: list[MessagePreview]
    count: int
