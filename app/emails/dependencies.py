import uuid
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from redis.asyncio import Redis

from app.database import get_db
from app.emails.models import Mailbox
from app.emails.service import _hash_token
from app.redis_client import get_redis
from app.config import settings


security = HTTPBearer()


async def get_authorized_mailbox(
    mailbox_id: uuid.UUID,  # FastAPI возьмет из path
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Mailbox:
    # 1. Найти ящик по id
    result = await db.execute(select(Mailbox).where(Mailbox.id == mailbox_id))
    mailbox = result.scalar_one_or_none()

    # 2. Нет ящика - 404
    if mailbox is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mailbox not found",
        )

    # 3. Ящик протух - 410
    if mailbox.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Mailbox expired",
        )

    # 4. Проверить токен: хэш присланного == token_hash в БД?
    token_hash = _hash_token(credentials.credentials)
    if token_hash != mailbox.token_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    # 5. вернуть ящик
    return mailbox


async def rate_limit_create(
    request: Request,
    redis: Redis = Depends(get_redis),
) -> None:
    ip = request.client.host
    key = f"ratelimit:create:{ip}"
    current = await redis.incr(key)

    if current == 1:
        await redis.expire(key, 60)

    if current > settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests, try again later",
        )
