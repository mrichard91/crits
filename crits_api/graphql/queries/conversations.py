"""Conversation queries for AI chat."""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_authenticated
from crits_api.graphql.types.conversation import ConversationSummaryType, ConversationType

logger = logging.getLogger(__name__)


@strawberry.type
class ConversationQueries:
    @strawberry.field(description="List chat conversations for the current user")
    @require_authenticated
    def chat_conversations(
        self,
        info: Info,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ConversationSummaryType]:
        from crits_api.models.conversation import Conversation

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else ""

        try:
            convos = (
                Conversation.objects(analyst=username)
                .only("id", "title", "modified")
                .skip(offset)
                .limit(min(limit, 100))
            )
            return [ConversationSummaryType.from_model(c) for c in convos]
        except Exception as e:
            logger.error(f"Error listing conversations: {e}")
            return []

    @strawberry.field(description="Get a single chat conversation by ID")
    @require_authenticated
    def chat_conversation(self, info: Info, id: str) -> ConversationType | None:
        from bson import ObjectId

        from crits_api.models.conversation import Conversation

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else ""

        try:
            conv = Conversation.objects(id=ObjectId(id), analyst=username).first()
            if conv:
                return ConversationType.from_model(conv)
            return None
        except Exception as e:
            logger.error(f"Error fetching conversation {id}: {e}")
            return None
