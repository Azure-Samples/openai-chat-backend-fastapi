import json
import os

import azure.identity.aio
import openai
import fastapi
import pydantic

router = fastapi.APIRouter()

@router.on_event("startup")
async def configure_openai():
    openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
    openai.api_version = "2023-03-15-preview"
    if os.getenv("AZURE_OPENAI_KEY"):
        openai.api_type = "azure"
        openai.api_key = os.getenv("AZURE_OPENAI_KEY")
    else:
        openai.api_type = "azure_ad"
        if client_id := os.getenv("AZURE_OPENAI_CLIENT_ID"):
            default_credential = azure.identity.aio.ManagedIdentityCredential(client_id=client_id)
        else:
            default_credential = azure.identity.aio.DefaultAzureCredential(exclude_shared_token_cache_credential=True)
        token = await default_credential.get_token("https://cognitiveservices.azure.com/.default")
        openai.api_key = token.token


class Message(pydantic.BaseModel):
    content: str


@router.post("/chat")
async def chat_handler(message: Message):

    async def response_stream():
        chat_coroutine = openai.ChatCompletion.acreate(
            deployment_id=os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT", "chatgpt"),
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": message.content},
            ],
            stream=True,
        )
        async for event in await chat_coroutine:
            yield json.dumps(event, ensure_ascii=False) + "\n"

    return fastapi.responses.StreamingResponse(response_stream())
