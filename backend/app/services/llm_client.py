import os
from typing import Any, AsyncIterator
import groq
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.config import settings
from app.core.exceptions import ValidationError
from app.core.schemas.enums import GroqModel


def is_transient_error(exception: Exception) -> bool:
    """Helper function to classify transient errors for retry logic."""
    if isinstance(exception, (groq.APIConnectionError, groq.RateLimitError)):
        return True
    if isinstance(exception, groq.APIStatusError):
        # Retry on standard transient status codes (Rate limits and internal server overloads)
        return exception.status_code in (429, 500, 502, 503, 504)
    return False


class LLMClient:
    """Production-grade asynchronous client wrapper for the Groq API."""

    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or settings.GROQ_API_KEY
        # If API key is empty/placeholder, let's look at env or fallback
        if not key or key == "gsk_your_groq_api_key_here":
            key = os.getenv("GROQ_API_KEY", "")

        self.client = groq.AsyncGroq(api_key=key)

    def _validate_model(self, model: Any) -> None:
        """Reject any model parameters outside of the strict GroqModel enum."""
        if not isinstance(model, GroqModel):
            raise ValidationError(
                detail=f"Invalid model: {model}. Supported models are {list(GroqModel)}."
            )

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception(is_transient_error),
    )
    async def complete(
        self,
        messages: list[dict[str, Any]],
        model: GroqModel,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """Perform a standard non-streaming chat completion."""
        self._validate_model(model)

        response = await self.client.chat.completions.create(
            messages=messages,  # type: ignore
            model=model.value,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )

        choice = response.choices[0]
        usage_data = {}
        if response.usage:
            usage_data = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return {
            "content": choice.message.content or "",
            "usage": usage_data,
        }

    async def stream(
        self,
        messages: list[dict[str, Any]],
        model: GroqModel,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """Perform a streaming chat completion yielding string tokens."""
        self._validate_model(model)

        # Retry logic inside stream setup is handled by the initial create call
        response_stream = await self.client.chat.completions.create(
            messages=messages,  # type: ignore
            model=model.value,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        async for chunk in response_stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception(is_transient_error),
    )
    async def complete_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        model: GroqModel,
    ) -> dict[str, Any]:
        """Perform a completion with tool support."""
        self._validate_model(model)

        response = await self.client.chat.completions.create(
            messages=messages,  # type: ignore
            tools=tools,  # type: ignore
            model=model.value,
            stream=False,
        )

        choice = response.choices[0]
        message = choice.message

        tool_calls_list = []
        if message.tool_calls:
            for tc in message.tool_calls:
                tool_calls_list.append(
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                )

        usage_data = {}
        if response.usage:
            usage_data = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return {
            "content": message.content or "",
            "tool_calls": tool_calls_list,
            "usage": usage_data,
        }
