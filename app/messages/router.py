import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.messages import service
from app.emails.models import Mailbox
from app.emails.dependencies import get_authorized_mailbox
from app.messages.schemas import MessageListResponse, MessagePreview, MessageDetail
from app.messages.webhook_schemas import BrevoWebhookPayload
from app.messages.dependencies import verify_brevo_token

router = APIRouter(prefix="/mailboxes/{mailbox_id}/messages", tags=["messages"])
webhook_router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.get("", response_model=MessageListResponse)
async def list_messages(
    mailbox: Mailbox = Depends(get_authorized_mailbox),
    db: AsyncSession = Depends(get_db),
) -> MessageListResponse:
    messages = await service.get_messages(db, mailbox.id)
    
    return MessageListResponse(
        messages=[MessagePreview.model_validate(m) for m in messages],
        count=len(messages),
    )
    
@router.get("/{message_id}", response_model=MessageDetail)
async def read_message(
    message_id: uuid.UUID,
    mailbox: Mailbox = Depends(get_authorized_mailbox),
    db: AsyncSession = Depends(get_db),
) -> MessageDetail:
    message = await service.get_message(db, mailbox.id, message_id)
    
    if message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )
    
    return MessageDetail.model_validate(message)

@webhook_router.post("/brevo/inbound", dependencies=[Depends(verify_brevo_token)])
async def handle_inbound(
    payload: BrevoWebhookPayload,
    db: AsyncSession = Depends(get_db),
):
    await service.process_inbound(db, payload)
    return {"status": "ok"}