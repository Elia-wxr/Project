"""Unit tests for the AI provider abstractions (Agent C scope).

Covers the OpenAI-compatible request contract: custom Base URLs and
subpaths, trailing slashes, bearer/none auth, model passthrough, the
minimal payload, timeouts, 401/403, 404, 429, 5xx, redirect refusal,
empty content, malformed JSON, no retries and no environment fallback.
"""

from __future__ import annotations

import io
import json
import socket
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any

import pytest

from tarot_jupyterlab.ai.interpreter import generate_reading
from tarot_jupyterlab.ai.prompts import build_reading_prompt
from tarot_jupyterlab.ai.provider import (
    CHAT_COMPLETIONS_PATH,
    AIProvider,
    FakeAIProvider,
    OpenAICompatibleProvider,
    _NoRedirectHandler,
)
from tarot_jupyterlab.errors import (
    AIProviderError,
    AIRateLimitedError,
    AITimeoutError,
    AIUnavailableError,
)
from tarot_jupyterlab.models import Session
from tests.unit.sample_data import make_card, make_drawn, make_session, structured_output


def _two_card_session() -> Session:
    return make_session(
        spread_name="three-card",
        drawn=[
            make_drawn(card=make_card(name="The Fool"), position="past"),
            make_drawn(
                card=make_card(name="The Magician", number=1),
                orientation="reversed",
                position="present",
            ),
        ],
    )


class _FakeResponse:
    """Minimal context-managed HTTP response double."""

    def __init__(self, body: str | bytes) -> None:
        self._body = body.encode("utf-8") if isinstance(body, str) else body

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._body


def _chat_body(content: str | None) -> bytes:
    payload: dict[str, object] = {
        "choices": [{"message": {"content": content}}],
    }
    return json.dumps(payload).encode("utf-8")


def _raising(exc: BaseException) -> Callable[[object, float], object]:
    """Build a handler that always raises the given exception."""

    def handler(request: object, timeout: float) -> object:
        raise exc

    return handler


def _patch_opener(
    monkeypatch: pytest.MonkeyPatch,
    handler: Callable[[object, float], object],
) -> list[tuple[Any, float]]:
    """Patch OpenerDirector.open and record every call (no retries allowed)."""
    calls: list[tuple[Any, float]] = []

    def fake_open(self: object, request: object, timeout: float = -1.0) -> object:
        calls.append((request, timeout))
        result = handler(request, timeout)
        if isinstance(result, BaseException):
            raise result
        return result

    monkeypatch.setattr(urllib.request.OpenerDirector, "open", fake_open)
    return calls


def _payload(request: Any) -> dict[str, Any]:
    """Decode the JSON payload of a captured request."""
    assert request.data is not None
    return json.loads(request.data.decode("utf-8"))


def _http_error(code: int, body: bytes = b"") -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        "http://example.com",
        code,
        f"HTTP {code}",
        {},
        io.BytesIO(body),
    )


def _make_provider(**kwargs: Any) -> OpenAICompatibleProvider:
    defaults: dict[str, Any] = {
        "base_url": "https://example.com/v1",
        "model": "test-model",
        "api_key": "secret",
    }
    defaults.update(kwargs)
    return OpenAICompatibleProvider(**defaults)


def _ok(content: str | None) -> Callable[[object, float], object]:
    return lambda request, timeout: _FakeResponse(_chat_body(content))


# --- FakeAIProvider (kept contract) -------------------------------------------


def test_protocol_shape() -> None:
    provider: AIProvider = FakeAIProvider()
    assert callable(provider.generate)
    assert provider.name == "FakeAIProvider"


def test_queued_responses_pop_in_order() -> None:
    provider = FakeAIProvider(responses=["one", "two"])
    assert provider.generate("p1") == "one"
    assert provider.generate("p2") == "two"
    assert provider.call_count == 2
    assert provider.calls == ["p1", "p2"]


def test_exhausted_queue_raises() -> None:
    provider = FakeAIProvider(responses=["only"])
    provider.generate("p1")
    with pytest.raises(AIProviderError):
        provider.generate("p2")


def test_default_response_matches_drawn_card_count() -> None:
    prompt = build_reading_prompt(_two_card_session(), language="en")
    output = FakeAIProvider().generate(prompt)
    assert output.count("<card>") == 2
    assert "<summary>" in output and "<advice>" in output


def test_controlled_delay() -> None:
    provider = FakeAIProvider(delay_seconds=0.15, responses=["ok"])
    start = time.monotonic()
    assert provider.generate("prompt") == "ok"
    assert time.monotonic() - start >= 0.1


def test_fail_times_then_success() -> None:
    provider = FakeAIProvider(fail_times=2, responses=["ok"])
    with pytest.raises(AIProviderError):
        provider.generate("p1")
    with pytest.raises(AIProviderError):
        provider.generate("p2")
    assert provider.generate("p3") == "ok"


def test_custom_error_instance_is_raised() -> None:
    error = AIUnavailableError("simulated outage")
    provider = FakeAIProvider(error=error, fail_times=1, responses=["ok"])
    with pytest.raises(AIUnavailableError) as excinfo:
        provider.generate("p1")
    assert excinfo.value is error
    assert provider.generate("p2") == "ok"


def test_custom_error_class_is_instantiated() -> None:
    provider = FakeAIProvider(error=AITimeoutError, fail_times=1, responses=["ok"])
    with pytest.raises(AITimeoutError):
        provider.generate("p1")


# --- OpenAICompatibleProvider construction -------------------------------------


def test_provider_name_is_neutral() -> None:
    assert _make_provider().name == "OpenAI-compatible"


def test_base_url_strips_trailing_slashes_and_keeps_subpath() -> None:
    provider = _make_provider(base_url="https://example.com/openai/v1///")
    assert provider.base_url == "https://example.com/openai/v1"


@pytest.mark.parametrize(
    "base_url",
    [
        "https://example.com/v1/chat/completions",
        "https://example.com/v1/chat/completions/",
        "https://example.com/v1?token=x",
        "https://example.com/v1#frag",
        "https://user:secret@example.com/v1",
        "ftp://example.com/v1",
        "http://",
        "not a url",
        "   ",
    ],
)
def test_invalid_base_urls_are_rejected(base_url: str) -> None:
    with pytest.raises(ValueError):
        _make_provider(base_url=base_url)


def test_full_completions_path_rejection_hints_at_base_url() -> None:
    with pytest.raises(ValueError, match="base"):
        _make_provider(base_url="https://example.com/v1/chat/completions")


def test_invalid_auth_mode_is_rejected() -> None:
    with pytest.raises(ValueError):
        _make_provider(auth_mode="basic")


def test_empty_model_is_rejected() -> None:
    with pytest.raises(ValueError):
        _make_provider(model="   ")


@pytest.mark.parametrize("timeout_seconds", [0, -5, "30"])
def test_invalid_timeouts_are_rejected(timeout_seconds: Any) -> None:
    with pytest.raises(ValueError):
        _make_provider(timeout_seconds=timeout_seconds)


# --- OpenAICompatibleProvider request contract ---------------------------------


def test_bearer_request_payload_headers_and_url(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _patch_opener(monkeypatch, _ok("answer"))
    provider = _make_provider(base_url="https://gateway.example.com/openai/v1///")
    assert provider.generate("the prompt") == "answer"
    assert len(calls) == 1
    request, timeout = calls[0]
    assert request.full_url == "https://gateway.example.com/openai/v1" + CHAT_COMPLETIONS_PATH
    payload = _payload(request)
    assert payload["model"] == "test-model"
    assert payload["messages"] == [{"role": "user", "content": "the prompt"}]
    assert payload["stream"] is False
    assert "temperature" not in payload
    assert request.headers["Content-type"] == "application/json"
    assert request.headers["Authorization"] == "Bearer secret"
    assert timeout == 30.0


def test_auth_none_sends_no_authorization_header(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _patch_opener(monkeypatch, _ok("answer"))
    provider = _make_provider(api_key="", auth_mode="none")
    assert provider.generate("prompt") == "answer"
    request, _ = calls[0]
    assert "Authorization" not in request.headers
    assert "Content-type" in request.headers


def test_bearer_without_key_raises_before_any_request(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _patch_opener(monkeypatch, _ok("x"))
    provider = _make_provider(api_key="")
    with pytest.raises(AIUnavailableError):
        provider.generate("prompt")
    assert calls == []


def test_custom_timeout_is_forwarded(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _patch_opener(monkeypatch, _ok("answer"))
    provider = _make_provider(timeout_seconds=7)
    provider.generate("prompt")
    assert calls[0][1] == 7.0


def test_model_is_sent_verbatim(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _patch_opener(monkeypatch, _ok("answer"))
    provider = _make_provider(model="my-org/custom-model-42")
    provider.generate("prompt")
    assert _payload(calls[0][0])["model"] == "my-org/custom-model-42"


# --- OpenAICompatibleProvider error mapping ------------------------------------


def test_timeout_maps_to_timeout_error(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_opener(monkeypatch, _raising(TimeoutError("socket timed out")))
    with pytest.raises(AITimeoutError):
        _make_provider().generate("prompt")


def test_urlerror_with_timeout_reason_maps_to_timeout_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_opener(monkeypatch, _raising(urllib.error.URLError(TimeoutError("socket timed out"))))
    with pytest.raises(AITimeoutError):
        _make_provider().generate("prompt")


def test_urlerror_maps_to_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_opener(monkeypatch, _raising(urllib.error.URLError(socket.gaierror("no route"))))
    with pytest.raises(AIUnavailableError):
        _make_provider().generate("prompt")


@pytest.mark.parametrize("code", [401, 403])
def test_credential_errors_map_to_unavailable(code: int, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_opener(monkeypatch, _raising(_http_error(code)))
    with pytest.raises(AIUnavailableError):
        _make_provider().generate("prompt")


def test_429_maps_to_rate_limited(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_opener(monkeypatch, _raising(_http_error(429)))
    with pytest.raises(AIRateLimitedError):
        _make_provider().generate("prompt")


def test_404_maps_to_provider_error_with_base_url_hint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_opener(monkeypatch, _raising(_http_error(404)))
    with pytest.raises(AIProviderError, match="404"):
        _make_provider().generate("prompt")


@pytest.mark.parametrize("code", [500, 502, 503])
def test_5xx_maps_to_provider_error_without_body_leak(
    code: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    error = _http_error(code, body=b"secret upstream body")
    _patch_opener(monkeypatch, _raising(error))
    with pytest.raises(AIProviderError, match=f"HTTP {code}") as excinfo:
        _make_provider().generate("prompt")
    assert "secret upstream body" not in str(excinfo.value)


@pytest.mark.parametrize("code", [301, 302, 307, 308])
def test_redirects_map_to_provider_error_and_are_not_followed(
    code: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _patch_opener(monkeypatch, _raising(_http_error(code)))
    with pytest.raises(AIProviderError, match=r"[Rr]edirect"):
        _make_provider().generate("prompt")
    assert len(calls) == 1


def test_opener_installs_only_the_no_redirect_handler() -> None:
    provider = _make_provider()
    redirect_handlers = [
        handler
        for handler in provider._opener.handlers
        if isinstance(handler, urllib.request.HTTPRedirectHandler)
    ]
    assert len(redirect_handlers) == 1
    handler = redirect_handlers[0]
    assert isinstance(handler, _NoRedirectHandler)
    assert handler.redirect_request(None, None, 302, "", {}, "https://elsewhere") is None


def test_non_json_body_maps_to_provider_error(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_opener(monkeypatch, lambda request, timeout: _FakeResponse(b"<html>oops</html>"))
    with pytest.raises(AIProviderError, match="non-JSON"):
        _make_provider().generate("prompt")


@pytest.mark.parametrize(
    "body",
    [
        b"{}",
        b"[]",
        _chat_body(None),
        _chat_body(""),
        _chat_body("   "),
        b'{"choices": []}',
        b'{"choices": [{}]}',
        b'{"choices": [{"message": {}}]}',
        b'{"choices": [{"message": {"content": 7}}]}',
    ],
)
def test_malformed_bodies_map_to_provider_error(
    body: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_opener(monkeypatch, lambda request, timeout: _FakeResponse(body))
    with pytest.raises(AIProviderError):
        _make_provider().generate("prompt")


def test_failure_is_never_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _patch_opener(monkeypatch, _raising(_http_error(500)))
    with pytest.raises(AIProviderError):
        _make_provider().generate("prompt")
    assert len(calls) == 1


# --- OpenAICompatibleProvider decoupling ---------------------------------------


def test_no_environment_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TAROT_AI_API_KEY", "env-key")
    monkeypatch.setenv("TAROT_AI_MODEL", "env-model")
    monkeypatch.setenv("TAROT_AI_BASE_URL", "https://env.example.com/v1")
    calls = _patch_opener(monkeypatch, _ok("answer"))

    # No key passed in: the provider must not fall back to any environment key.
    provider = _make_provider(api_key="")
    with pytest.raises(AIUnavailableError):
        provider.generate("prompt")
    assert calls == []

    # An explicit key wins; environment values are never injected into headers.
    explicit = _make_provider(api_key="explicit-key")
    explicit.generate("prompt")
    assert calls[0][0].headers["Authorization"] == "Bearer explicit-key"


def test_reading_flow_records_neutral_provider_name(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_opener(
        monkeypatch,
        lambda request, timeout: _FakeResponse(
            _chat_body(structured_output(interpretations=["Focus interpretation."]))
        ),
    )
    reading = generate_reading(make_session(), _make_provider(), language="en")
    assert reading.provider == "OpenAI-compatible"
    assert reading.card_interpretations == ("Focus interpretation.",)
