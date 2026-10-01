import secrets
from fastapi import Header, HTTPException, status
from app.config import settings


async def verify_brevo_token(authorization: str | None = Header(default=None)) -> None:
    expected = f"Bearer {settings.brevo_webhook_secret.get_secret_value()}"
    if authorization is None or not secrets.compare_digest(authorization.encode(), expected.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid Brevo token',
        )