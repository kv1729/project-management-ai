import os
from typing import Any

import httpx


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-120b"
DEFAULT_TIMEOUT_SECONDS = 30.0


class OpenRouterError(RuntimeError):
    """Raised when an OpenRouter request cannot produce a valid response."""


def _configured_api_key() -> str:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise OpenRouterError("OPENROUTER_API_KEY is not configured")
    return api_key


def _response_content(payload: Any) -> str:
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise OpenRouterError("OpenRouter returned an invalid response") from error

    if not isinstance(content, str) or not content.strip():
        raise OpenRouterError("OpenRouter returned an empty response")
    return content.strip()


def complete_messages(
    messages: list[dict[str, str]], *, timeout: float = DEFAULT_TIMEOUT_SECONDS
) -> str:
    """Send a conversation to OpenRouter and return the assistant's text."""
    if not messages or any(not message.get("content", "").strip() for message in messages):
        raise OpenRouterError("Messages must not be empty")

    api_key = _configured_api_key()
    model = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    payload = {
        "model": model,
        "messages": messages,
    }

    try:
        response = httpx.post(
            OPENROUTER_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        return _response_content(response.json())
    except httpx.TimeoutException as error:
        raise OpenRouterError("OpenRouter request timed out") from error
    except httpx.RequestError as error:
        raise OpenRouterError("OpenRouter network request failed") from error
    except httpx.HTTPStatusError as error:
        raise OpenRouterError(
            f"OpenRouter returned HTTP {error.response.status_code}"
        ) from error
    except ValueError as error:
        raise OpenRouterError("OpenRouter returned invalid JSON") from error


def complete(prompt: str, *, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> str:
    """Send one prompt to OpenRouter and return the assistant's text."""
    if not prompt.strip():
        raise OpenRouterError("Prompt must not be empty")
    return complete_messages(
        [{"role": "user", "content": prompt}], timeout=timeout
    )