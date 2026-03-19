import json
import os

import fastapi
import pydantic

from .globals import clients

router = fastapi.APIRouter()


class Message(pydantic.BaseModel):
    content: str
    role: str = "user"


class ChatRequest(pydantic.BaseModel):
    messages: list[Message]


SYSTEM_PROMPT = """You are a helpful assistant."""


@router.post("/chat")
async def chat_handler(chat_request: ChatRequest) -> dict:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + chat_request.messages
    # Azure Open AI takes the deployment name as the model name
    model = os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT", "chatgpt")

    response = await clients["openai"].responses.create(
        model=model,
        input=messages,
        store=False,
    )
    return {"message": {"content": response.output_text, "role": "assistant"}}


@router.post("/chat/stream")
async def chat_stream_handler(chat_request: ChatRequest) -> fastapi.responses.StreamingResponse:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + chat_request.messages
    # Azure Open AI takes the deployment name as the model name
    model = os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT", "chatgpt")

    async def response_stream():
        chat_coroutine = clients["openai"].responses.create(
            model=model,
            input=messages,
            stream=True,
            store=False,
        )
        try:
            async for event in await chat_coroutine:
                if event.type == "response.output_text.delta":
                    yield json.dumps({"delta": {"content": event.delta}}, ensure_ascii=False) + "\n"
                elif event.type == "response.completed":
                    yield json.dumps({"delta": {"content": None}, "finish_reason": "stop"}, ensure_ascii=False) + "\n"
        except Exception as e:
            yield json.dumps({"error": str(e)}) + "\n"

    return fastapi.responses.StreamingResponse(response_stream())
