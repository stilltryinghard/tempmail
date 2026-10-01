import asyncio
import logging

from app.database import async_session_maker

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from datetime import datetime, timezone

from app.emails.models import Mailbox


logger = logging.getLogger(__name__)

CLEANUP_INTERVAL_SECONDS = 60


async def delete_expired_mailboxes(session: AsyncSession) -> int:
    result = await session.execute(
        delete(Mailbox).where(Mailbox.expires_at < datetime.now(timezone.utc))
    )
    await session.commit()
    return result.rowcount


async def cleanup_loop() -> None:
    while True:
        try:
            async with async_session_maker() as session:
                deleted = await delete_expired_mailboxes(session)
                if deleted:
                    logger.info("Cleaned up %d expired mailboxes", deleted)
        except Exception:
            logger.exception("Cleanup failed")
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
