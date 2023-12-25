import json

import pytest
from fastapi.testclient import TestClient

from src import api


def test_chat_stream(client, mock_openai_chatcompletion, snapshot):
    response = client.post(
        "/chat",
        json={"messages": [{"content": "What is the capital of France?", "role": "user"}], "stream": True},
    )
    assert response.status_code == 200
    snapshot.assert_match(response.content, "result.jsonlines")


def test_chat_nostream(client, mock_openai_chatcompletion, snapshot):
    response = client.post(
        "/chat",
        json={"messages": [{"content": "What is the capital of France?", "role": "user"}], "stream": False},
    )
    assert response.status_code == 200
    snapshot.assert_match(json.dumps(response.json(), indent=4), "result.json")


@pytest.mark.asyncio
async def test_openai_azure_key(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_KEY", "test-key")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "test-openai-service.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT", "test-chatgpt")

    fastapi_app = api.create_app()

    with TestClient(fastapi_app):
        assert api.globals.clients["openai"].api_key is not None


@pytest.mark.asyncio
async def test_openai_azure_defaultcredential(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_KEY", "")
    monkeypatch.setenv("AZURE_OPENAI_CLIENT_ID", "")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "test-openai-service.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT", "test-chatgpt")

    fastapi_app = api.create_app()

    with TestClient(fastapi_app):
        assert api.globals.clients["openai"]._azure_ad_token_provider is not None


@pytest.mark.asyncio
async def test_openai_azure_managedidentity(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_KEY", "")
    monkeypatch.setenv("AZURE_OPENAI_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "test-openai-service.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT", "test-chatgpt")

    fastapi_app = api.create_app()

    with TestClient(fastapi_app):
        assert api.globals.clients["openai"]._azure_ad_token_provider is not None
