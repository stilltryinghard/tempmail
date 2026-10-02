import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.config import settings

brevo_scheme = HTTPBearer(scheme_name="BrevoWebhook", auto_error=False)

async def verify_brevo_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(brevo_scheme),
) -> None:
    expected = settings.brevo_webhook_secret.get_secret_value()
    if credentials is None or not secrets.compare_digest(
        credentials.credentials.encode(), expected.encode()
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)