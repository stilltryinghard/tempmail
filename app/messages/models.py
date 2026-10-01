import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.emails.models import Mailbox
from datetime import datetime

from sqlalchemy import String, DateTime, func, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from app.shared.utils import generate_uuidv7


class Message(Base):
    __tablename__ = "message"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuidv7
    )

    mailbox_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mailbox.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sender: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    subject: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    html_body: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    mailbox: Mapped["Mailbox"] = relationship(
        back_populates="messages",
    )
