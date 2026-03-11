"""Conversation GraphQL types for AI chat."""

from datetime import datetime
from typing import Any

import strawberry


@strawberry.type
class ChatMessageType:
    role: str
    content: str
    created: datetime | None = None

    @classmethod
    def from_model(cls, msg: Any) -> "ChatMessageType":
        return cls(
            role=msg.role,
            content=msg.content or "",
            created=getattr(msg, "created", None),
        )


@strawberry.type
class ConversationSummaryType:
    id: str
    title: str
    modified: datetime | None = None

    @classmethod
    def from_model(cls, conv: Any) -> "ConversationSummaryType":
        return cls(
            id=str(conv.id),
            title=conv.title or "New Conversation",
            modified=getattr(conv, "modified", None),
        )


@strawberry.type
class ConversationType:
    id: str
    title: str
    analyst: str
    provider: str = ""
    model: str = ""
    messages: list[ChatMessageType] = strawberry.field(default_factory=list)
    created: datetime | None = None
    modified: datetime | None = None

    @classmethod
    def from_model(cls, conv: Any) -> "ConversationType":
        messages = [ChatMessageType.from_model(m) for m in (conv.messages or [])]
        return cls(
            id=str(conv.id),
            title=conv.title or "New Conversation",
            analyst=conv.analyst or "",
            provider=conv.provider or "",
            model=conv.model or "",
            messages=messages,
            created=getattr(conv, "created", None),
            modified=getattr(conv, "modified", None),
        )
