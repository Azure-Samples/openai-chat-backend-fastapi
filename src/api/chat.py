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

    response = await clients["openai"].chat.completions.create(
        model=model,
        messages=messages,
        stream=False,
    )
    first_choice = response.model_dump()["choices"][0]
    return {"message": first_choice["message"]}


@router.post("/chat/stream")
async def chat_stream_handler(chat_request: ChatRequest) -> fastapi.responses.StreamingResponse:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + chat_request.messages
    # Azure Open AI takes the deployment name as the model name
    model = os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT", "chatgpt")

    async def response_stream():
        chat_coroutine = clients["openai"].chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        )
        async for event in await chat_coroutine:
            if event.choices:
                first_choice = event.model_dump()["choices"][0]
                yield json.dumps({"delta": first_choice["delta"]}, ensure_ascii=False) + "\n"

    return fastapi.responses.StreamingResponse(response_stream())
