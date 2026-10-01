import secrets
import hashlib
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.emails.models import Mailbox


def _generate_address() -> str:
    """Сгенерить случайный email-адрес на домене сервиса"""
    local_part = secrets.token_hex(6)
    return f"{local_part}@{settings.mail_domain}"


def _hash_token(raw_token: str) -> str:
    """Хэш токена для хранения в БД (sha256, hex)"""
    return hashlib.sha256(raw_token.encode()).hexdigest()


async def create_mailbox(session: AsyncSession) -> tuple[Mailbox, str]:
    """
    Создать ящик. Возвращает (ORM-обьект, оригинальный токен).
    Токен возвращается отдельно - в БД хранится только хэш.
    """
    # 1. Адрес
    address = _generate_address()

    # 2. Токен: генерим оригинал, хэшируем
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)

    # 3. expires_at: Сейчас(UTC) + TTL из конфига
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.mailbox_ttl_minutes
    )

    # 4. ORM-обьект
    mailbox = Mailbox(
        address=address,
        token_hash=token_hash,
        expires_at=expires_at,
        # id, created_at, is_extended - дефолт, не указываю.
    )

    # 5. Сохранить в БД
    session.add(mailbox)
    await session.commit()
    await session.refresh(mailbox)

    # 6. вернуть обьект + оригинальный токен
    return mailbox, raw_token


async def extend_mailbox(session: AsyncSession, mailbox: Mailbox) -> Mailbox:
    if mailbox.is_extended:
        raise ValueError("Mailbox already extended")

    mailbox.expires_at = mailbox.expires_at + timedelta(
        minutes=settings.mailbox_ttl_minutes
    )
    mailbox.is_extended = True
    await session.commit()
    await session.refresh(mailbox)
    return mailbox
