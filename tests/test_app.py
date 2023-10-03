import openai
import pytest
from fastapi.testclient import TestClient

from . import mock_cred
from src import api


def test_chat_stream_text(client):
    response = client.post(
        "/chat",
        json={"content": "What is the capital of France?"},
    )
    assert response.status_code == 200
    assert (
        response.content
        == b'{"choices": [{"delta": {"content": "The"}}]}\n{"choices": [{"delta": {"content": "capital"}}]}\n{"choices": [{"delta": {"content": "of"}}]}\n{"choices": [{"delta": {"content": "France"}}]}\n{"choices": [{"delta": {"content": "is"}}]}\n{"choices": [{"delta": {"content": "Paris."}}]}\n'  # noqa
    )


@pytest.mark.asyncio
async def test_openai_key(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_KEY", "test-key")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "test-openai-service.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT", "test-chatgpt")

    fastapi_app = api.create_app()

    with TestClient(fastapi_app):
        assert openai.api_type == "azure"


@pytest.mark.asyncio
async def test_openai_managedidentity(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "test-openai-service.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT", "test-chatgpt")

    monkeypatch.setattr("azure.identity.aio.ManagedIdentityCredential", mock_cred.MockAzureCredential)

    fastapi_app = api.create_app()

    with TestClient(fastapi_app):
        assert openai.api_type == "azure_ad"
