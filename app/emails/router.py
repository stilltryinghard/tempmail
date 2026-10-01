from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.emails import service
from app.emails.dependencies import get_authorized_mailbox, rate_limit_create
from app.emails.schemas import MailboxResponse, MailboxExtendResponse
from app.emails.models import Mailbox


# Роутер для эндпойнтов, связанных с ящиками
router = APIRouter(prefix="/mailboxes", tags=["mailboxes"])


@router.post(
    "",  # путь относительно prefix - POST /mailboxes
    response_model=MailboxResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_create)],
)
async def create_mailbox(
    db: AsyncSession = Depends(get_db),
) -> MailboxResponse:
    # 1. Зову сервис - он создает ящик, возвращает (обьект, токен)
    mailbox, raw_token = await service.create_mailbox(db)

    # 2. Собираю ответ ВРУЧНУЮ - токен подставляется из памяти
    return MailboxResponse(
        id=mailbox.id,
        address=mailbox.address,
        token=raw_token,
        expires_at=mailbox.expires_at,
        is_extended=mailbox.is_extended,
    )


@router.post("/{mailbox_id}/extend", response_model=MailboxExtendResponse)
async def renew_mailbox(
    db: AsyncSession = Depends(get_db),
    mailbox: Mailbox = Depends(get_authorized_mailbox),
) -> MailboxExtendResponse:
    try:
        mailbox = await service.extend_mailbox(db, mailbox)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Mailbox already extended!"
        )
    return MailboxExtendResponse.model_validate(mailbox)
