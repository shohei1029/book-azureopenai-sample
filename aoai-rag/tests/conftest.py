from collections import namedtuple
from unittest import mock

import pytest
import pytest_asyncio
from azure.search.documents.aio import SearchClient
from openai.resources.chat.completions import AsyncCompletions
from openai.resources.embeddings import AsyncEmbeddings
from openai.types import CreateEmbeddingResponse, Embedding
from openai.types.chat import ChatCompletion, ChatCompletionChunk, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice
from openai.types.chat.chat_completion_chunk import ChoiceDelta
from openai.types.create_embedding_response import Usage

import app

MockToken = namedtuple("MockToken", ["token", "expires_on"])


class MockAzureCredential:
    async def get_token(self, *scopes, **kwargs):
        return MockToken("mock_token", 9999999999)

    async def close(self):
        pass


@pytest.fixture
def mock_openai_embedding(monkeypatch):
    async def mock_create(*args, **kwargs):
        return CreateEmbeddingResponse(
            object="list",
            data=[Embedding(object="embedding", index=0, embedding=[0.1, 0.2, 0.3])],
            model="text-embedding-3-small",
            usage=Usage(prompt_tokens=8, total_tokens=8),
        )

    monkeypatch.setattr(AsyncEmbeddings, "create", mock_create)


@pytest.fixture
def mock_openai_chatcompletion(monkeypatch):
    class AsyncChatCompletionIterator:
        def __init__(self, answer):
            self.num = 1
            self.answer = answer

        def __aiter__(self):
            return self

        async def __anext__(self):
            if self.num == 1:
                self.num = 0
                return ChatCompletionChunk(
                    id="test-123",
                    object="chat.completion.chunk",
                    created=1700000000,
                    model="gpt-35-turbo",
                    choices=[ChunkChoice(index=0, delta=ChoiceDelta(content=self.answer), finish_reason=None)],
                )
            else:
                raise StopAsyncIteration

    async def mock_create(*args, **kwargs):
        messages = kwargs["messages"]
        if messages[-1]["content"] == "Generate search query for: What is the capital of France?":
            answer = "capital of France"
        else:
            answer = "The capital of France is Paris."
        if kwargs.get("stream") is True:
            return AsyncChatCompletionIterator(answer)
        else:
            return ChatCompletion(
                id="test-123",
                object="chat.completion",
                created=1700000000,
                model="gpt-35-turbo",
                choices=[Choice(index=0, message=ChatCompletionMessage(role="assistant", content=answer), finish_reason="stop")],
            )

    monkeypatch.setattr(AsyncCompletions, "create", mock_create)


@pytest.fixture
def mock_acs_search(monkeypatch):
    class Caption:
        def __init__(self, text):
            self.text = text

    class AsyncSearchResultsIterator:
        def __init__(self):
            self.num = 1

        def __aiter__(self):
            return self

        async def __anext__(self):
            if self.num == 1:
                self.num = 0
                return {
                    "sourcepage": "Benefit_Options-2.pdf",
                    "sourcefile": "Benefit_Options.pdf",
                    "content": "There is a whistleblower policy.",
                    "embeddings": [],
                    "category": None,
                    "id": "file-Benefit_Options_pdf-42656E656669745F4F7074696F6E732E706466-page-2",
                    "@search.score": 0.03279569745063782,
                    "@search.reranker_score": 3.4577205181121826,
                    "@search.highlights": None,
                    "@search.captions": [Caption("Caption: A whistleblower policy.")],
                }
            else:
                raise StopAsyncIteration

    async def mock_search(*args, **kwargs):
        return AsyncSearchResultsIterator()

    monkeypatch.setattr(SearchClient, "search", mock_search)


@pytest_asyncio.fixture
async def client(monkeypatch, mock_openai_chatcompletion, mock_openai_embedding, mock_acs_search):
    monkeypatch.setenv("AZURE_STORAGE_ACCOUNT", "test-storage-account")
    monkeypatch.setenv("AZURE_STORAGE_CONTAINER", "test-storage-container")
    monkeypatch.setenv("AZURE_SEARCH_INDEX", "test-search-index")
    monkeypatch.setenv("AZURE_SEARCH_SERVICE", "test-search-service")
    monkeypatch.setenv("AZURE_OPENAI_SERVICE", "test-openai-service")
    monkeypatch.setenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT", "test-chatgpt")
    monkeypatch.setenv("AZURE_OPENAI_CHATGPT_MODEL", "gpt-35-turbo")
    monkeypatch.setenv("AZURE_OPENAI_EMB_DEPLOYMENT", "test-ada")

    with mock.patch("app.DefaultAzureCredential") as mock_default_azure_credential:
        mock_default_azure_credential.return_value = MockAzureCredential()
        quart_app = app.create_app()

        async with quart_app.test_app() as test_app:
            quart_app.config.update({"TESTING": True})

            yield test_app.test_client()
