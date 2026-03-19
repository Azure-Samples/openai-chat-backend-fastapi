import azure.core.credentials_async
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from src import api


@pytest.fixture
def mock_openai_responses(monkeypatch):
    class MockResponseEvent:
        def __init__(self, event_type, delta=None):
            self.type = event_type
            self.delta = delta

    class AsyncResponseIterator:
        def __init__(self, answer):
            self.event_index = 0
            self.events = []
            for i, word in enumerate(answer.split(" ")):
                if i > 0:
                    word = " " + word
                self.events.append(MockResponseEvent("response.output_text.delta", delta=word))
            self.events.append(MockResponseEvent("response.completed"))

        def __aiter__(self):
            return self

        async def __anext__(self):
            if self.event_index < len(self.events):
                event = self.events[self.event_index]
                self.event_index += 1
                return event
            raise StopAsyncIteration

    class MockResponse:
        def __init__(self, output_text):
            self.output_text = output_text

    async def mock_acreate(*args, **kwargs):
        if kwargs.get("stream"):
            return AsyncResponseIterator("The capital of France is Paris.")
        else:
            return MockResponse("The capital of France is Paris.")

    monkeypatch.setattr("openai.resources.responses.AsyncResponses.create", mock_acreate)


@pytest.fixture
def mock_azure_credentials(monkeypatch):
    class MockAzureCredential(azure.core.credentials_async.AsyncTokenCredential):
        pass

    monkeypatch.setattr("azure.identity.aio.DefaultAzureCredential", MockAzureCredential)
    monkeypatch.setattr("azure.identity.aio.ManagedIdentityCredential", MockAzureCredential)


@pytest_asyncio.fixture
async def client(monkeypatch, mock_openai_responses, mock_azure_credentials):
    monkeypatch.setenv("AZURE_OPENAI_KEY", "")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "test-openai-service.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT", "test-chatgpt")

    fastapi_app = api.create_app()

    with TestClient(fastapi_app) as test_client:
        yield test_client
