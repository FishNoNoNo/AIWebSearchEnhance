from __future__ import annotations

import json
import time
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from src.api.models.request import ChatCompletionRequest

router = APIRouter(prefix="/v1/chat", tags=["chat"])


@router.post("/completions")
async def chat_completions(payload: ChatCompletionRequest, request: Request):
    if payload.stream:
        return StreamingResponse(
            _stream_completion(payload, request),
            media_type="text/event-stream",
        )
    result = await request.app.state.pipeline.execute(payload)
    completion_id = "chatcmpl-" + uuid.uuid4().hex
    return {
        "id": completion_id,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": result.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": result.content,
                    "search_metadata": result.search_metadata.model_dump(),
                },
                "finish_reason": "stop",
            }
        ],
        "usage": result.usage or {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


async def _stream_completion(payload: ChatCompletionRequest, request: Request):
    result = await request.app.state.pipeline.execute(payload)
    completion_id = "chatcmpl-" + uuid.uuid4().hex
    created = int(time.time())
    first = {
        "id": completion_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": result.model,
        "choices": [
            {
                "index": 0,
                "delta": {
                    "role": "assistant",
                    "search_metadata": result.search_metadata.model_dump(),
                },
                "finish_reason": None,
            }
        ],
    }
    yield "data: " + json.dumps(first, ensure_ascii=False) + "\n\n"
    chunk = {
        "id": completion_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": result.model,
        "choices": [
            {"index": 0, "delta": {"content": result.content}, "finish_reason": None}
        ],
    }
    yield "data: " + json.dumps(chunk, ensure_ascii=False) + "\n\n"
    final = {
        "id": completion_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": result.model,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
    }
    yield "data: " + json.dumps(final, ensure_ascii=False) + "\n\n"
    yield "data: [DONE]\n\n"
