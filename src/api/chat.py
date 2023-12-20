import json
import os

import contextlib
import azure.identity.aio
import fastapi
import openai
import pydantic

router = fastapi.APIRouter()
clients = {}

@contextlib.asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    client_args = {}
    if os.getenv("AZURE_OPENAI_KEY"):
        client_args["api_key"] = os.getenv("AZURE_OPENAI_KEY")
    else:
        if client_id := os.getenv("AZURE_OPENAI_CLIENT_ID"):
            default_credential = azure.identity.aio.ManagedIdentityCredential(client_id=client_id)
        else:
            default_credential = azure.identity.aio.DefaultAzureCredential(exclude_shared_token_cache_credential=True)
        client_args["azure_ad_token_provider"] = azure.identity.aio.get_bearer_token_provider(default_credential, "https://api.openai.com/.default")

    clients["openai"] = openai.AsyncAzureOpenAI(
        api_version="2023-07-01-preview",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        **client_args,
    )

    yield

    await clients["openai"].close()


class Message(pydantic.BaseModel):
    content: str


@router.post("/chat")
async def chat_handler(message: Message):
    async def response_stream():
        chat_coroutine = clients["openai"].chat.completions.create(
            # Azure Open AI takes the deployment name as the model name
            model=os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT", "chatgpt"),
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": message.content},
            ],
            stream=True,
        )
        async for event in await chat_coroutine:
            yield json.dumps(event.model_dump(), ensure_ascii=False) + "\n"

    return fastapi.responses.StreamingResponse(response_stream())
