import logging
import os

from environs import Env
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_app():
    env = Env()

    if not os.getenv("RUNNING_IN_PRODUCTION"):
        logging.basicConfig(level=logging.DEBUG)

    app = FastAPI(docs_url="/")

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
