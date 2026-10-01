import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.messages.models import Message
from app.messages.webhook_schemas import BrevoWebhookPayload

from app.emails.models import Mailbox


async def get_messages(session: AsyncSession, mailbox_id: uuid.UUID) -> list[Message]:
    """Достать все письма из ящика, новые сверху"""
    result = await session.execute(
        select(Message)
        .where(Message.mailbox_id == mailbox_id)
        .order_by(Message.received_at.desc())
    )
    return list(result.scalars().all())


async def get_message(
    session: AsyncSession, mailbox_id: uuid.UUID, message_id: uuid.UUID
) -> Message | None:
    """Прочитать письмо"""
    result = await session.execute(
        select(Message).where(
            Message.mailbox_id == mailbox_id, Message.id == message_id
        )
    )
    return result.scalar_one_or_none()


async def process_inbound(session: AsyncSession, payload: BrevoWebhookPayload) -> None:
    for item in payload.items:
        recipient_address = item.To[0].Address

        # найти ящик
        result = await session.execute(
            select(Mailbox).where(Mailbox.address == recipient_address)
        )
        mailbox = result.scalar_one_or_none()

        # Нет ящика - пропустить письмо
        if mailbox is None:
            continue
        # Ящик протух - пропустить письмо
        if mailbox.expires_at < datetime.now(timezone.utc):
            continue

        body = item.RawTextBody or ""
        html_body = item.RawHtmlBody
        message = Message(
            mailbox_id=mailbox.id,
            sender=item.From.Address,
            subject=item.Subject,
            body=body,
            html_body=html_body,
        )
        session.add(message)
    await session.commit()
