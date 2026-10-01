from pydantic import BaseModel


class BrevoMailBox(BaseModel):
    Name: str | None = None
    Address: str


class BrevoItem(BaseModel):
    From: BrevoMailBox
    To: list[BrevoMailBox]
    Subject: str | None = None
    RawTextBody: str | None = None
    RawHtmlBody: str | None = None


class BrevoWebhookPayload(BaseModel):
    items: list[BrevoItem]
