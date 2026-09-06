import httpx
import pytest

from app import openrouter
from app.openrouter_check import main as check_main


def test_complete_builds_openrouter_request(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, object] = {}

    def fake_post(url: str, **kwargs: object) -> httpx.Response:
        calls["url"] = url
        calls.update(kwargs)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "  4  "}}]},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "test-model")
    monkeypatch.setattr(openrouter.httpx, "post", fake_post)

    assert openrouter.complete("2+2", timeout=12) == "4"
    assert calls == {
        "url": openrouter.OPENROUTER_URL,
        "headers": {"Authorization": "Bearer test-key"},
        "json": {
            "model": "test-model",
            "messages": [{"role": "user", "content": "2+2"}],
        },
        "timeout": 12,
    }


def test_complete_uses_default_model(monkeypatch: pytest.MonkeyPatch) -> None:
    request_payload: dict[str, object] = {}

    def fake_post(url: str, **kwargs: object) -> httpx.Response:
        request_payload.update(kwargs)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "4"}}]},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    monkeypatch.setattr(openrouter.httpx, "post", fake_post)

    assert openrouter.complete("2+2") == "4"
    assert request_payload["json"]["model"] == openrouter.DEFAULT_MODEL  # type: ignore[index]


def test_complete_rejects_missing_key_and_empty_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(openrouter.OpenRouterError, match="API_KEY"):
        openrouter.complete("2+2")

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    with pytest.raises(openrouter.OpenRouterError, match="Prompt"):
        openrouter.complete(" ")


@pytest.mark.parametrize(
    ("exception", "message"),
    [
        (httpx.ReadTimeout("timed out"), "timed out"),
        (httpx.ConnectError("offline"), "network request failed"),
    ],
)
def test_complete_handles_request_failures(
    monkeypatch: pytest.MonkeyPatch,
    exception: httpx.RequestError,
    message: str,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(openrouter.httpx, "post", lambda *args, **kwargs: (_ for _ in ()).throw(exception))

    with pytest.raises(openrouter.OpenRouterError, match=message):
        openrouter.complete("2+2")


def test_complete_handles_provider_and_payload_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    error_response = httpx.Response(
        503,
        request=httpx.Request("POST", openrouter.OPENROUTER_URL),
    )
    monkeypatch.setattr(openrouter.httpx, "post", lambda *args, **kwargs: error_response)

    with pytest.raises(openrouter.OpenRouterError, match="HTTP 503"):
        openrouter.complete("2+2")

    invalid_json_response = httpx.Response(
        200,
        content=b"not json",
        request=httpx.Request("POST", openrouter.OPENROUTER_URL),
    )
    monkeypatch.setattr(
        openrouter.httpx, "post", lambda *args, **kwargs: invalid_json_response
    )
    with pytest.raises(openrouter.OpenRouterError, match="invalid JSON"):
        openrouter.complete("2+2")

    malformed_response = httpx.Response(
        200,
        json={"choices": []},
        request=httpx.Request("POST", openrouter.OPENROUTER_URL),
    )
    monkeypatch.setattr(
        openrouter.httpx, "post", lambda *args, **kwargs: malformed_response
    )
    with pytest.raises(openrouter.OpenRouterError, match="invalid response"):
        openrouter.complete("2+2")


def test_connectivity_check_returns_success_and_failure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("app.openrouter_check.complete", lambda prompt: "4")

    assert check_main() == 0
    assert capsys.readouterr().out == "4\n"

    monkeypatch.setattr(
        "app.openrouter_check.complete",
        lambda prompt: (_ for _ in ()).throw(
            openrouter.OpenRouterError("OPENROUTER_API_KEY is not configured")
        ),
    )
    assert check_main() == 1
    assert "connectivity check failed" in capsys.readouterr().out