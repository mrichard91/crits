"""Conversation mutations for AI chat."""

import logging
from datetime import datetime

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_authenticated
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)


@strawberry.input
class ChatMessageInput:
    role: str
    content: str


@strawberry.type
class ConversationMutations:
    @strawberry.mutation(description="Create a new chat conversation")
    @require_authenticated
    def create_chat_conversation(
        self,
        info: Info,
        title: str | None = None,
    ) -> MutationResult:
        from crits_api.models.conversation import Conversation

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else ""

        try:
            conv = Conversation(
                title=title or "New Conversation",
                analyst=username,
            )
            conv.save()
            return MutationResult(
                success=True,
                message="Conversation created",
                id=str(conv.id),
            )
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Save messages to a chat conversation")
    @require_authenticated
    def save_chat_messages(
        self,
        info: Info,
        conversation_id: str,
        messages: list[ChatMessageInput],
    ) -> MutationResult:
        from bson import ObjectId

        from crits_api.models.conversation import ChatMessage, Conversation

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else ""

        try:
            conv = Conversation.objects(id=ObjectId(conversation_id), analyst=username).first()
            if not conv:
                return MutationResult(success=False, message="Conversation not found")

            conv.messages = [ChatMessage(role=m.role, content=m.content) for m in messages]
            conv.modified = datetime.utcnow()
            conv.save()
            return MutationResult(
                success=True,
                message="Messages saved",
                id=str(conv.id),
            )
        except Exception as e:
            logger.error(f"Error saving messages: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Rename a chat conversation")
    @require_authenticated
    def rename_chat_conversation(
        self,
        info: Info,
        id: str,
        title: str,
    ) -> MutationResult:
        from bson import ObjectId

        from crits_api.models.conversation import Conversation

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else ""

        try:
            conv = Conversation.objects(id=ObjectId(id), analyst=username).first()
            if not conv:
                return MutationResult(success=False, message="Conversation not found")

            conv.title = title
            conv.modified = datetime.utcnow()
            conv.save()
            return MutationResult(
                success=True,
                message="Conversation renamed",
                id=str(conv.id),
            )
        except Exception as e:
            logger.error(f"Error renaming conversation: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Delete a chat conversation")
    @require_authenticated
    def delete_chat_conversation(
        self,
        info: Info,
        id: str,
    ) -> MutationResult:
        from bson import ObjectId

        from crits_api.models.conversation import Conversation

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else ""

        try:
            conv = Conversation.objects(id=ObjectId(id), analyst=username).first()
            if not conv:
                return MutationResult(success=False, message="Conversation not found")

            conv.delete()
            return MutationResult(
                success=True,
                message="Conversation deleted",
                id=id,
            )
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            return MutationResult(success=False, message=str(e))
