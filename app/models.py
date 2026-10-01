"""Central model registry"""

from app.emails.models import Mailbox
from app.messages.models import Message


__all__ = ["Mailbox", "Message"]
