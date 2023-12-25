import azure.core.credentials_async
import openai
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from src import api


@pytest.fixture
def mock_openai_chatcompletion(monkeypatch):
    class AsyncChatCompletionIterator:
        def __init__(self, answer: str):
            self.chunk_index = 0
            self.chunks = [
                # This is an Azure-specific chunk solely for prompt_filter_results
                openai.types.chat.ChatCompletionChunk(
                    object="chat.completion.chunk",
                    choices=[],
                    id="",
                    created=0,
                    model="",
                    prompt_filter_results=[
                        {
                            "prompt_index": 0,
                            "content_filter_results": {
                                "hate": {"filtered": False, "severity": "safe"},
                                "self_harm": {"filtered": False, "severity": "safe"},
                                "sexual": {"filtered": False, "severity": "safe"},
                                "violence": {"filtered": False, "severity": "safe"},
                            },
                        }
                    ],
                ),
                openai.types.chat.ChatCompletionChunk(
                    id="test-123",
                    object="chat.completion.chunk",
                    choices=[
                        openai.types.chat.chat_completion_chunk.Choice(
                            delta=openai.types.chat.chat_completion_chunk.ChoiceDelta(content=None, role="assistant"),
                            index=0,
                            finish_reason=None,
                            # Only Azure includes content_filter_results
                            content_filter_results={},
                        )
                    ],
                    created=1703462735,
                    model="gpt-35-turbo",
                ),
            ]
            answer_deltas = answer.split(" ")
            for answer_index, answer_delta in enumerate(answer_deltas):
                # Completion chunks include whitespace, so we need to add it back in
                if answer_index > 0:
                    answer_delta = " " + answer_delta
                self.chunks.append(
                    openai.types.chat.ChatCompletionChunk(
                        id="test-123",
                        object="chat.completion.chunk",
                        choices=[
                            openai.types.chat.chat_completion_chunk.Choice(
                                delta=openai.types.chat.chat_completion_chunk.ChoiceDelta(
                                    role=None, content=answer_delta
                                ),
                                finish_reason=None,
                                index=0,
                                logprobs=None,
                                # Only Azure includes content_filter_results
                                content_filter_results={
                                    "hate": {"filtered": False, "severity": "safe"},
                                    "self_harm": {"filtered": False, "severity": "safe"},
                                    "sexual": {"filtered": False, "severity": "safe"},
                                    "violence": {"filtered": False, "severity": "safe"},
                                },
                            )
                        ],
                        created=1703462735,
                        model="gpt-35-turbo",
                    )
                )
            self.chunks.append(
                openai.types.chat.ChatCompletionChunk(
                    id="test-123",
                    object="chat.completion.chunk",
                    choices=[
                        openai.types.chat.chat_completion_chunk.Choice(
                            delta=openai.types.chat.chat_completion_chunk.ChoiceDelta(content=None, role=None),
                            index=0,
                            finish_reason="stop",
                            # Only Azure includes content_filter_results
                            content_filter_results={},
                        )
                    ],
                    created=1703462735,
                    model="gpt-35-turbo",
                )
            )

        def __aiter__(self):
            return self

        async def __anext__(self):
            if self.chunk_index < len(self.chunks):
                next_chunk = self.chunks[self.chunk_index]
                self.chunk_index += 1
                return next_chunk
            else:
                raise StopAsyncIteration

    async def mock_acreate(*args, **kwargs):
        # Returned mocks do *not* include Azure-specific prompt_filter_results, content_filter_results
        if kwargs.get("stream"):
            return AsyncChatCompletionIterator("The capital of France is Paris.")
        else:
            return openai.types.chat.ChatCompletion(
                object="chat.completion",
                choices=[
                    openai.types.chat.chat_completion.Choice(
                        message=openai.types.chat.chat_completion.ChatCompletionMessage(
                            role="assistant", content="The capital of France is Paris."
                        ),
                        finish_reason="stop",
                        index=0,
                        logprobs=None,
                    )
                ],
                id="test-123",
                created=0,
                model="test-model",
                usage=openai.types.completion_usage.CompletionUsage(
                    completion_tokens=7,
                    prompt_tokens=24,
                    total_tokens=31,
                ),
            )

    monkeypatch.setattr("openai.resources.chat.AsyncCompletions.create", mock_acreate)


@pytest.fixture
def mock_azure_credentials(monkeypatch):
    class MockAzureCredential(azure.core.credentials_async.AsyncTokenCredential):
        pass

    monkeypatch.setattr("azure.identity.aio.DefaultAzureCredential", MockAzureCredential)
    monkeypatch.setattr("azure.identity.aio.ManagedIdentityCredential", MockAzureCredential)


@pytest_asyncio.fixture
async def client(monkeypatch, mock_openai_chatcompletion, mock_azure_credentials):
    monkeypatch.setenv("AZURE_OPENAI_KEY", "")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "test-openai-service.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT", "test-chatgpt")

    fastapi_app = api.create_app()

    with TestClient(fastapi_app) as test_client:
        yield test_client
