import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MailboxResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    address: str
    token: str
    expires_at: datetime
    is_extended: bool


class MailboxExtendResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    expires_at: datetime
    is_extended: bool
