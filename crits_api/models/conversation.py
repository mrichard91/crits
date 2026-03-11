"""MongoDB model for AI chat conversations."""

from datetime import datetime

import mongoengine as me


class ChatMessage(me.EmbeddedDocument):
    role = me.StringField(required=True, choices=["user", "assistant"])
    content = me.StringField(default="")
    created = me.DateTimeField(default=datetime.utcnow)


class Conversation(me.Document):
    meta = {
        "collection": "chat_conversations",
        "ordering": ["-modified"],
        "indexes": ["analyst", "-modified"],
    }

    title = me.StringField(default="New Conversation")
    analyst = me.StringField(required=True)
    messages = me.EmbeddedDocumentListField(ChatMessage, default=list)
    provider = me.StringField(default="")
    model = me.StringField(default="")
    created = me.DateTimeField(default=datetime.utcnow)
    modified = me.DateTimeField(default=datetime.utcnow)
