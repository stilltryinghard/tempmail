import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.messages.models import Message

from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from app.shared.utils import generate_uuidv7


class Mailbox(Base):
    __tablename__ = "mailbox"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuidv7
    )

    address: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    is_extended: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="mailbox",
        cascade="all, delete-orphan",
    )
