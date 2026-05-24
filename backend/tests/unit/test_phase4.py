from unittest.mock import AsyncMock, MagicMock
import httpx
import pytest
import groq
from tenacity import wait_exponential

from app.core.exceptions import ValidationError
from app.core.schemas.enums import GroqModel
from app.services.llm_client import LLMClient


@pytest.mark.asyncio
async def test_validate_model_rejection():
    """Verify that models outside of the GroqModel Enum are aggressively rejected."""
    client = LLMClient(api_key="dummy_key")

    with pytest.raises(ValidationError) as exc_info:
        await client.complete(messages=[{"role": "user", "content": "hi"}], model="gpt-4")  # type: ignore

    assert "Invalid model" in str(exc_info.value)


@pytest.mark.asyncio
async def test_llm_client_complete_success():
    """Verify that complete() returns text content and usage data successfully."""
    llm_client = LLMClient(api_key="dummy_key")

    # Mock completions create call
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Test response content"
    mock_response.choices = [mock_choice]
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 20
    mock_response.usage.total_tokens = 30

    llm_client.client.chat.completions.create = AsyncMock(return_value=mock_response)  # type: ignore

    result = await llm_client.complete(
        messages=[{"role": "user", "content": "hello"}],
        model=GroqModel.LLAMA_70B,
    )

    assert result["content"] == "Test response content"
    assert result["usage"]["prompt_tokens"] == 10
    assert result["usage"]["completion_tokens"] == 20
    assert result["usage"]["total_tokens"] == 30


@pytest.mark.asyncio
async def test_llm_client_retries_on_rate_limit():
    """Verify that rate limit errors (429) trigger retries and fail after 3 attempts."""
    llm_client = LLMClient(api_key="dummy_key")

    # Create mock 429 response
    response_429 = httpx.Response(
        status_code=429,
        request=httpx.Request("POST", "https://api.groq.com"),
    )
    rate_limit_error = groq.RateLimitError(
        message="Rate Limit Exceeded",
        response=response_429,
        body=None,
    )

    # Configure mock to raise RateLimitError every time
    mock_create = AsyncMock(side_effect=rate_limit_error)
    llm_client.client.chat.completions.create = mock_create  # type: ignore

    # Reduce tenacity wait times dynamically for test speed
    llm_client.complete.retry.wait = wait_exponential(multiplier=0.01, min=0.01, max=0.05)

    with pytest.raises(groq.RateLimitError):
        await llm_client.complete(
            messages=[{"role": "user", "content": "retry test"}],
            model=GroqModel.LLAMA_70B,
        )

    # Verify completions create was called exactly 3 times before raising
    assert mock_create.call_count == 3


@pytest.mark.asyncio
async def test_llm_client_retries_on_server_error():
    """Verify that server errors (500) trigger retries and fail after 3 attempts."""
    llm_client = LLMClient(api_key="dummy_key")

    response_500 = httpx.Response(
        status_code=500,
        request=httpx.Request("POST", "https://api.groq.com"),
    )
    server_error = groq.APIStatusError(
        message="Internal Server Error",
        response=response_500,
        body=None,
    )

    mock_create = AsyncMock(side_effect=server_error)
    llm_client.client.chat.completions.create = mock_create  # type: ignore

    # Speed up retries
    llm_client.complete.retry.wait = wait_exponential(multiplier=0.01, min=0.01, max=0.05)

    with pytest.raises(groq.APIStatusError):
        await llm_client.complete(
            messages=[{"role": "user", "content": "server error test"}],
            model=GroqModel.DEEPSEEK_R1,
        )

    assert mock_create.call_count == 3


@pytest.mark.asyncio
async def test_llm_client_non_transient_no_retry():
    """Verify that non-transient errors (like 400 Bad Request) raise immediately without retry."""
    llm_client = LLMClient(api_key="dummy_key")

    response_400 = httpx.Response(
        status_code=400,
        request=httpx.Request("POST", "https://api.groq.com"),
    )
    bad_request_error = groq.BadRequestError(
        message="Bad Request Parameter",
        response=response_400,
        body=None,
    )

    mock_create = AsyncMock(side_effect=bad_request_error)
    llm_client.client.chat.completions.create = mock_create  # type: ignore

    with pytest.raises(groq.BadRequestError):
        await llm_client.complete(
            messages=[{"role": "user", "content": "no retry test"}],
            model=GroqModel.LLAMA_70B,
        )

    # Should only try once
    assert mock_create.call_count == 1


@pytest.mark.asyncio
async def test_llm_client_stream():
    """Verify that stream() yields string chunks sequentially."""
    llm_client = LLMClient(api_key="dummy_key")

    # Mock async generator response
    async def mock_stream_generator(*args, **kwargs):
        chunks = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content="Streaming "))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content="token "))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content="chunks."))]),
        ]
        for chunk in chunks:
            yield chunk

    llm_client.client.chat.completions.create = AsyncMock(side_effect=mock_stream_generator)  # type: ignore

    tokens = []
    # Do not 'await' the generator itself, iterate directly
    async for token in llm_client.stream(
        messages=[{"role": "user", "content": "stream this"}],
        model=GroqModel.DEEPSEEK_R1,
    ):
        tokens.append(token)

    assert tokens == ["Streaming ", "token ", "chunks."]
