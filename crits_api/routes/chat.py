"""REST endpoint for streaming LLM chat responses."""

import json
import logging
from collections.abc import AsyncGenerator

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from crits_api.auth.session import get_user_from_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    provider: str  # "openai" | "anthropic"
    apiKey: str
    model: str
    input: list[dict]  # Heterogeneous: conversation messages + function_call + function_call_output
    systemPrompt: str = ""
    tools: list[dict] = []  # Responses API format: {type, name, description, parameters}


# ---------------------------------------------------------------------------
# OpenAI — Responses API  (/v1/responses)
# ---------------------------------------------------------------------------


async def _stream_openai(req: ChatRequest) -> AsyncGenerator[str, None]:
    """Stream from OpenAI Responses API, emitting normalized SSE."""
    payload: dict = {
        "model": req.model,
        "input": req.input,
        "stream": True,
    }

    if req.systemPrompt:
        payload["instructions"] = req.systemPrompt

    if req.tools:
        payload["tools"] = req.tools

    try:
        async with (
            httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client,
            client.stream(
                "POST",
                "https://api.openai.com/v1/responses",
                headers={
                    "Authorization": f"Bearer {req.apiKey}",
                    "Content-Type": "application/json",
                },
                content=json.dumps(payload),
            ) as resp,
        ):
            if resp.status_code != 200:
                body = await resp.aread()
                yield f"data: {json.dumps({'type': 'error', 'message': f'OpenAI API error {resp.status_code}: {body.decode()}'})}\n\n"
                return

            # Parse two-line SSE: "event: <type>\ndata: <json>"
            current_event: str | None = None
            has_tool_calls = False

            async for line in resp.aiter_lines():
                if line.startswith("event: "):
                    current_event = line[7:]
                    continue

                if not line.startswith("data: "):
                    if not line:
                        current_event = None  # blank line resets
                    continue

                raw = line[6:]
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    current_event = None
                    continue

                if current_event == "response.output_text.delta":
                    delta = data.get("delta", "")
                    if delta:
                        yield f"data: {json.dumps({'type': 'text', 'content': delta})}\n\n"

                elif current_event == "response.function_call_arguments.done":
                    # Complete function call — no buffering needed
                    has_tool_calls = True
                    call_id = data.get("call_id", "")
                    name = data.get("name", "")
                    arguments = data.get("arguments", "{}")
                    try:
                        parsed = json.loads(arguments)
                    except json.JSONDecodeError:
                        parsed = {}
                    yield f"data: {json.dumps({'type': 'tool_use', 'call_id': call_id, 'name': name, 'input': parsed})}\n\n"

                elif current_event == "response.completed":
                    # Extract output items for the frontend to use in continuation
                    response_obj = data.get("response", {})
                    output_items = response_obj.get("output", [])
                    stop = "tool_use" if has_tool_calls else "end_turn"
                    yield f"data: {json.dumps({'type': 'done', 'stop_reason': stop, 'output_items': output_items})}\n\n"
                    return

                elif current_event == "error":
                    msg = data.get("message", "Unknown error")
                    yield f"data: {json.dumps({'type': 'error', 'message': msg})}\n\n"
                    return

                current_event = None

            # Fallback if stream ends without response.completed
            yield f"data: {json.dumps({'type': 'done', 'stop_reason': 'end_turn', 'output_items': []})}\n\n"

    except httpx.HTTPError as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


# ---------------------------------------------------------------------------
# Anthropic — Messages API  (/v1/messages)
# ---------------------------------------------------------------------------


def _convert_tools_for_anthropic(tools: list[dict]) -> list[dict]:
    """Convert Responses API tool defs to Anthropic format."""
    result = []
    for t in tools:
        result.append(
            {
                "name": t.get("name", ""),
                "description": t.get("description", ""),
                "input_schema": t.get("parameters", {}),
            }
        )
    return result


def _build_anthropic_messages(input_items: list[dict]) -> list[dict]:
    """Convert Responses API input array to Anthropic messages."""
    messages: list[dict] = []

    for item in input_items:
        role = item.get("role")
        item_type = item.get("type")

        if role == "user":
            messages.append({"role": "user", "content": item.get("content", "")})

        elif role == "assistant":
            messages.append({"role": "assistant", "content": item.get("content", "")})

        elif item_type == "function_call":
            # Becomes a tool_use block on the assistant message
            arguments = item.get("arguments", "{}")
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}
            tool_block = {
                "type": "tool_use",
                "id": item.get("call_id", ""),
                "name": item.get("name", ""),
                "input": arguments,
            }
            # Merge into preceding assistant message or create one
            if messages and messages[-1]["role"] == "assistant":
                content = messages[-1]["content"]
                if isinstance(content, str):
                    blocks: list[dict] = []
                    if content:
                        blocks.append({"type": "text", "text": content})
                    messages[-1]["content"] = blocks
                messages[-1]["content"].append(tool_block)
            else:
                messages.append({"role": "assistant", "content": [tool_block]})

        elif item_type == "function_call_output":
            tool_result = {
                "type": "tool_result",
                "tool_use_id": item.get("call_id", ""),
                "content": item.get("output", ""),
            }
            # Merge consecutive tool results into one user message
            if (
                messages
                and messages[-1]["role"] == "user"
                and isinstance(messages[-1]["content"], list)
                and messages[-1]["content"]
                and messages[-1]["content"][0].get("type") == "tool_result"
            ):
                messages[-1]["content"].append(tool_result)
            else:
                messages.append({"role": "user", "content": [tool_result]})

        elif item_type == "message":
            # Model output message item — extract text and add as assistant
            content_parts = item.get("content", [])
            text = ""
            for part in content_parts:
                if isinstance(part, dict) and part.get("type") == "output_text":
                    text += part.get("text", "")
            if text:
                messages.append({"role": "assistant", "content": text})

    return messages


async def _stream_anthropic(req: ChatRequest) -> AsyncGenerator[str, None]:
    """Stream from Anthropic Messages API, emitting normalized SSE."""
    anthropic_messages = _build_anthropic_messages(req.input)
    anthropic_tools = _convert_tools_for_anthropic(req.tools) if req.tools else []

    payload: dict = {
        "model": req.model,
        "messages": anthropic_messages,
        "max_tokens": 8192,
        "stream": True,
    }

    if req.systemPrompt:
        payload["system"] = req.systemPrompt

    if anthropic_tools:
        payload["tools"] = anthropic_tools

    try:
        async with (
            httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client,
            client.stream(
                "POST",
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": req.apiKey,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                content=json.dumps(payload),
            ) as resp,
        ):
            if resp.status_code != 200:
                body = await resp.aread()
                yield f"data: {json.dumps({'type': 'error', 'message': f'Anthropic API error {resp.status_code}: {body.decode()}'})}\n\n"
                return

            current_tool: dict | None = None
            tool_json_buf = ""
            assistant_text = ""
            tool_calls: list[dict] = []

            async for line in resp.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                raw = line[6:]

                try:
                    event = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                event_type = event.get("type")

                if event_type == "content_block_start":
                    block = event.get("content_block", {})
                    if block.get("type") == "text":
                        if block.get("text"):
                            assistant_text += block["text"]
                            yield f"data: {json.dumps({'type': 'text', 'content': block['text']})}\n\n"
                    elif block.get("type") == "tool_use":
                        current_tool = {
                            "id": block.get("id", ""),
                            "name": block.get("name", ""),
                        }
                        tool_json_buf = ""

                elif event_type == "content_block_delta":
                    delta = event.get("delta", {})
                    if delta.get("type") == "text_delta":
                        text = delta.get("text", "")
                        assistant_text += text
                        yield f"data: {json.dumps({'type': 'text', 'content': text})}\n\n"
                    elif delta.get("type") == "input_json_delta":
                        tool_json_buf += delta.get("partial_json", "")

                elif event_type == "content_block_stop":
                    if current_tool:
                        try:
                            parsed_input = json.loads(tool_json_buf) if tool_json_buf else {}
                        except json.JSONDecodeError:
                            parsed_input = {}
                        tool_calls.append(
                            {
                                "call_id": current_tool["id"],
                                "name": current_tool["name"],
                                "input": parsed_input,
                                "arguments": tool_json_buf or "{}",
                            }
                        )
                        yield f"data: {json.dumps({'type': 'tool_use', 'call_id': current_tool['id'], 'name': current_tool['name'], 'input': parsed_input})}\n\n"
                        current_tool = None
                        tool_json_buf = ""

                elif event_type == "message_delta":
                    stop = event.get("delta", {}).get("stop_reason", "end_turn")
                    reason = "tool_use" if stop == "tool_use" else "end_turn"

                    # Build output_items in Responses API format for the frontend
                    output_items: list[dict] = []
                    if assistant_text or tool_calls:
                        # Build a message output item
                        content = []
                        if assistant_text:
                            content.append({"type": "output_text", "text": assistant_text})
                        if content:
                            output_items.append(
                                {
                                    "type": "message",
                                    "role": "assistant",
                                    "content": content,
                                }
                            )
                        # Build function_call output items
                        for tc in tool_calls:
                            output_items.append(
                                {
                                    "type": "function_call",
                                    "call_id": tc["call_id"],
                                    "name": tc["name"],
                                    "arguments": tc["arguments"],
                                }
                            )

                    yield f"data: {json.dumps({'type': 'done', 'stop_reason': reason, 'output_items': output_items})}\n\n"
                    return

                elif event_type == "message_stop":
                    yield f"data: {json.dumps({'type': 'done', 'stop_reason': 'end_turn', 'output_items': []})}\n\n"
                    return

            yield f"data: {json.dumps({'type': 'done', 'stop_reason': 'end_turn', 'output_items': []})}\n\n"

    except httpx.HTTPError as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------


@router.post("/chat/stream", response_model=None)
async def chat_stream(request: Request) -> StreamingResponse | JSONResponse:
    """Stream LLM responses, proxying to OpenAI or Anthropic."""
    user = await get_user_from_session(request)
    if not user:
        return JSONResponse(status_code=401, content={"detail": "Authentication required"})

    body = await request.json()
    try:
        req = ChatRequest(**body)
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})

    if req.provider == "openai":
        gen = _stream_openai(req)
    elif req.provider == "anthropic":
        gen = _stream_anthropic(req)
    else:
        return JSONResponse(
            status_code=400, content={"detail": f"Unknown provider: {req.provider}"}
        )

    return StreamingResponse(
        gen,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
