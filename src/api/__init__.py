import contextlib
import logging
import os

import azure.identity.aio
import fastapi
import openai
from environs import Env
from fastapi.middleware.cors import CORSMiddleware

from .globals import clients


@contextlib.asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    client_args = {}
    if os.getenv("LOCAL_OPENAI_ENDPOINT"):
        # Use a local endpoint like llamafile server
        client_args["api_key"] = "no-key-required"
        client_args["base_url"] = os.getenv("LOCAL_OPENAI_ENDPOINT")
        clients["openai"] = openai.AsyncOpenAI(
            **client_args,
        )
    else:
        # Use an Azure OpenAI endpoint instead,
        # either with a key or with keyless authentication
        if os.getenv("AZURE_OPENAI_KEY"):
            # Authenticate using an Azure OpenAI API key
            # This is generally discouraged, but is provided for developers
            # that want to develop locally inside the Docker container.
            client_args["api_key"] = os.getenv("AZURE_OPENAI_KEY")
        else:
            if client_id := os.getenv("AZURE_OPENAI_CLIENT_ID"):
                # Authenticate using a user-assigned managed identity on Azure
                # See aca.bicep for value of AZURE_OPENAI_CLIENT_ID
                default_credential = azure.identity.aio.ManagedIdentityCredential(client_id=client_id)
            else:
                # Authenticate using the default Azure credential chain
                # See https://docs.microsoft.com/azure/developer/python/azure-sdk-authenticate#defaultazurecredential
                # This will *not* work inside a Docker container.
                default_credential = azure.identity.aio.DefaultAzureCredential(
                    exclude_shared_token_cache_credential=True
                )
            client_args["azure_ad_token_provider"] = azure.identity.aio.get_bearer_token_provider(
                default_credential, "https://api.openai.com/.default"
            )
        clients["openai"] = openai.AsyncAzureOpenAI(
            api_version="2023-07-01-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            **client_args,
        )

    yield

    await clients["openai"].close()


def create_app():
    env = Env()

    if not os.getenv("RUNNING_IN_PRODUCTION"):
        env.read_env(".env")
        logging.basicConfig(level=logging.DEBUG)

    app = fastapi.FastAPI(docs_url="/", lifespan=lifespan)

    origins = env.list("ALLOWED_ORIGINS", ["http://localhost", "http://localhost:8080"])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from . import chat  # noqa

    app.include_router(chat.router)

    return app
