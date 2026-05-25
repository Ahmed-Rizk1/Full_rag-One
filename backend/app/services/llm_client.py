import os
from enum import Enum
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
    """Production-grade asynchronous client wrapper for the Groq and OpenAI APIs."""

    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or settings.GROQ_API_KEY
        # If API key is empty/placeholder, let's look at env or fallback
        if not key or key == "gsk_your_groq_api_key_here":
            key = os.getenv("GROQ_API_KEY", "")

        self.default_key = key
        self.default_client = groq.AsyncGroq(api_key=key)
        self.client = self.default_client

    @staticmethod
    async def validate_key(api_key: str, provider: str) -> bool:
        """Validate the API key by making a minimal test call to the provider."""
        if not api_key:
            return False
        try:
            if provider == "openai":
                import openai
                client = openai.AsyncOpenAI(api_key=api_key)
                await client.chat.completions.create(
                    messages=[{"role": "user", "content": "Ping"}],
                    model="gpt-4o-mini",
                    max_tokens=1,
                )
            elif provider == "groq":
                client = groq.AsyncGroq(api_key=api_key)
                await client.chat.completions.create(
                    messages=[{"role": "user", "content": "Ping"}],
                    model="llama-3.3-70b-versatile",
                    max_tokens=1,
                )
            else:
                return False
            return True
        except Exception as e:
            # Raise clear validation error
            raise ValidationError(
                detail=f"API key validation failed for {provider.upper()}: {str(e)}"
            ) from e

    def _get_client_and_model(
        self,
        model: Any,
        api_key: str | None = None,
        provider: str | None = None,
    ) -> tuple[Any, str, str]:
        """Resolve the client, provider, and model name to use based on inputs."""
        prov = provider or "groq"
        key = api_key

        if not key:
            if prov == "groq":
                key = self.default_key
            else:
                key = os.getenv("OPENAI_API_KEY", "")

        if not key or key == "gsk_your_groq_api_key_here":
            raise ValidationError(
                detail=f"API key for {prov.upper()} is not configured. Please set it in Settings."
            )

        model_str = model.value if hasattr(model, "value") else str(model)

        if prov == "openai":
            import openai
            # Map Groq models to OpenAI equivalents if needed
            if model_str == GroqModel.DEEPSEEK_R1.value:
                model_name = "gpt-4o"
            elif model_str == GroqModel.LLAMA_70B.value:
                model_name = "gpt-4o-mini"
            else:
                model_name = model_str
            client = openai.AsyncOpenAI(api_key=key)
        else:
            if model_str not in [GroqModel.LLAMA_70B.value, GroqModel.DEEPSEEK_R1.value]:
                # Fallback if an invalid groq model is passed
                model_name = GroqModel.LLAMA_70B.value
            else:
                model_name = model_str
            
            if key == self.default_key or key == "dummy_key":
                client = self.client
            else:
                client = groq.AsyncGroq(api_key=key)

        return client, prov, model_name

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
        api_key: str | None = None,
        provider: str | None = None,
    ) -> dict[str, Any]:
        """Perform a standard non-streaming chat completion."""
        self._validate_model(model)
        client, prov, model_name = self._get_client_and_model(model, api_key, provider)

        response = await client.chat.completions.create(
            messages=messages,  # type: ignore
            model=model_name,
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
        api_key: str | None = None,
        provider: str | None = None,
    ) -> AsyncIterator[str]:
        """Perform a streaming chat completion yielding string tokens."""
        self._validate_model(model)
        client, prov, model_name = self._get_client_and_model(model, api_key, provider)

        response_stream = await client.chat.completions.create(
            messages=messages,  # type: ignore
            model=model_name,
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
        api_key: str | None = None,
        provider: str | None = None,
    ) -> dict[str, Any]:
        """Perform a completion with tool support."""
        self._validate_model(model)
        client, prov, model_name = self._get_client_and_model(model, api_key, provider)

        response = await client.chat.completions.create(
            messages=messages,  # type: ignore
            tools=tools,  # type: ignore
            model=model_name,
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
