# Future TODO

## AI Chat Interface

Add a chat interface to the UI that lets users ask natural-language questions about their CRITs data. The chat agent will:

- Support OpenAI and Anthropic APIs as configurable backends
- Run entirely in the frontend (API keys stored in browser/user settings)
- Have a system prompt with full context on the GraphQL schema and how to construct queries (mirroring the patterns the UI already uses)
- Be able to execute GraphQL queries against the CRITs API on behalf of the user to answer questions (e.g. "show me all samples uploaded this week", "what indicators are related to campaign X?")
- Present results in a conversational format with inline tables/badges where appropriate
- Support follow-up questions with conversation context
