"""Unit tests for the AI provider abstractions (Owner scope)."""

from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.request
from unittest.mock import patch

import pytest

from tarot_jupyterlab.ai.prompts import build_reading_prompt
from tarot_jupyterlab.ai.provider import AIProvider, FakeAIProvider, SocratesProvider
from tarot_jupyterlab.errors import (
    AIProviderError,
    AITimeoutError,
    AIUnavailableError,
)
from tarot_jupyterlab.models import Session
from tests.unit.sample_data import make_card, make_drawn, make_session


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
    session = _two_card_session()
    prompt = build_reading_prompt(session, language="en")
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


class _FakeResponse:
    """Minimal context-managed urlopen replacement."""

    def __init__(self, body: bytes, status: int = 200) -> None:
        self._body = body
        self.status = status

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._body


def _chat_body(content: str) -> bytes:
    return json.dumps({"choices": [{"message": {"content": content}}]}).encode("utf-8")


def test_socrates_provider_missing_key_raises_without_network() -> None:
    provider = SocratesProvider(api_key="", api_base="http://localhost:9")
    with pytest.raises(AIUnavailableError):
        provider.generate("prompt")


def test_socrates_provider_success_and_payload() -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request: urllib.request.Request, timeout: float) -> _FakeResponse:
        captured["full_url"] = request.full_url
        captured["data"] = json.loads(request.data.decode("utf-8"))
        captured["auth"] = request.headers.get("Authorization")
        captured["timeout"] = timeout
        return _FakeResponse(_chat_body("the answer"))

    provider = SocratesProvider(api_base="http://socrates.test/v1", api_key="secret", model="s-1")
    with patch("urllib.request.urlopen", fake_urlopen):
        assert provider.generate("prompt") == "the answer"
    assert captured["full_url"] == "http://socrates.test/v1/chat/completions"
    assert captured["data"]["model"] == "s-1"
    assert captured["data"]["messages"] == [{"role": "user", "content": "prompt"}]
    assert captured["auth"] == "Bearer secret"
    assert captured["timeout"] == 30.0


def test_socrates_provider_http_401_maps_to_unavailable() -> None:
    def fake_urlopen(request: urllib.request.Request, timeout: float) -> _FakeResponse:
        raise urllib.error.HTTPError("http://x", 401, "Unauthorized", {}, None)

    provider = SocratesProvider(api_base="http://x", api_key="k")
    with patch("urllib.request.urlopen", fake_urlopen), pytest.raises(AIUnavailableError):
        provider.generate("prompt")


def test_socrates_provider_http_500_maps_to_provider_error() -> None:
    def fake_urlopen(request: urllib.request.Request, timeout: float) -> _FakeResponse:
        raise urllib.error.HTTPError("http://x", 500, "Boom", {}, None)

    provider = SocratesProvider(api_base="http://x", api_key="k")
    with patch("urllib.request.urlopen", fake_urlopen), pytest.raises(AIProviderError):
        provider.generate("prompt")


def test_socrates_provider_timeout_maps_to_timeout_error() -> None:
    def fake_urlopen(request: urllib.request.Request, timeout: float) -> _FakeResponse:
        raise TimeoutError("socket timed out")

    provider = SocratesProvider(api_base="http://x", api_key="k")
    with patch("urllib.request.urlopen", fake_urlopen), pytest.raises(AITimeoutError):
        provider.generate("prompt")


def test_socrates_provider_urlerror_maps_to_unavailable() -> None:
    def fake_urlopen(request: urllib.request.Request, timeout: float) -> _FakeResponse:
        raise urllib.error.URLError(socket.gaierror("no route"))

    provider = SocratesProvider(api_base="http://x", api_key="k")
    with patch("urllib.request.urlopen", fake_urlopen), pytest.raises(AIUnavailableError):
        provider.generate("prompt")


def test_socrates_provider_malformed_body_maps_to_provider_error() -> None:
    def fake_urlopen(request: urllib.request.Request, timeout: float) -> _FakeResponse:
        return _FakeResponse(b'{"unexpected": true}')

    provider = SocratesProvider(api_base="http://x", api_key="k")
    with patch("urllib.request.urlopen", fake_urlopen), pytest.raises(AIProviderError):
        provider.generate("prompt")


def test_socrates_provider_empty_content_maps_to_provider_error() -> None:
    def fake_urlopen(request: urllib.request.Request, timeout: float) -> _FakeResponse:
        return _FakeResponse(_chat_body("   "))

    provider = SocratesProvider(api_base="http://x", api_key="k")
    with patch("urllib.request.urlopen", fake_urlopen), pytest.raises(AIProviderError):
        provider.generate("prompt")
