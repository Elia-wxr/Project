"""AI provider abstractions and bundled provider implementations.

``AIProvider`` is the synchronous contract consumed by
:func:`tarot_jupyterlab.ai.interpreter.generate_reading`; the service layer
runs it inside a worker thread with an overall timeout.

``FakeAIProvider`` is a deterministic, dependency-free stand-in for tests
and explicit Demo mode.  ``OpenAICompatibleProvider`` sends one non-streaming
Chat Completions request to a user-configured OpenAI-compatible server,
using only the standard library.

This module never reads environment variables: configuration (Base URL,
model, key, auth mode and timeout) is resolved by the configuration layer
and passed in as constructor arguments, mirroring the fields of the AI
settings contract shared with the frontend settings page.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from collections.abc import Sequence
from typing import Literal, Protocol

from tarot_jupyterlab.ai.prompts import CARD_FACTS_HEADER
from tarot_jupyterlab.errors import (
    AIProviderError,
    AIRateLimitedError,
    AITimeoutError,
    AIUnavailableError,
    TarotError,
)

#: Marker emitted by prompts.build_reading_prompt once per drawn card;
#: FakeAIProvider counts it to shape its default structured response.
CARD_KEYWORD_MARKER = "Keywords:"

#: Chat Completions path appended exactly once to a normalized Base URL.
CHAT_COMPLETIONS_PATH = "/chat/completions"

#: Default network timeout in seconds (configurable via timeout_seconds).
DEFAULT_TIMEOUT_SECONDS = 30.0

#: Supported authentication modes; "none" sends no Authorization header.
AuthMode = Literal["bearer", "none"]


class AIProvider(Protocol):
    """Synchronous provider interface consumed by ``generate_reading``.

    ``name`` is the human-visible provider label recorded in
    :attr:`tarot_jupyterlab.models.Reading.provider`; the adapter fills it,
    never the model output.
    """

    name: str

    def generate(self, prompt: str) -> str:
        """Return model output for one prompt."""
        ...


class FakeAIProvider:
    """Deterministic provider used by unit tests and explicit Demo mode.

    Supports the features the service layer needs to exercise race
    conditions without a network:

    - **queued scripted responses** (``responses``): each ``generate`` call
      pops the next entry; an exhausted queue raises ``AIProviderError``;
    - **controlled delay** (``delay_seconds``): a slow call can still return
      successfully after the service layer has timed out, simulating a
      late result;
    - **controlled failures** (``fail_times`` / ``error``): the first N
      calls raise, so tests can cover failure and retry paths.

    When no queued response is available, a valid structured response is
    built from the prompt itself, with one ``<card>`` block per drawn card.
    """

    def __init__(
        self,
        *,
        name: str = "FakeAIProvider",
        responses: Sequence[str] | None = None,
        delay_seconds: float = 0.0,
        error: type[BaseException] | BaseException | None = None,
        fail_times: int = 0,
    ) -> None:
        self.name = name
        self.delay_seconds = delay_seconds
        self._responses: deque[str] | None = deque(responses) if responses is not None else None
        self._error = error
        self._fail_remaining = max(0, fail_times)
        self.call_count = 0
        self.calls: list[str] = []

    def generate(self, prompt: str) -> str:
        """Return the next scripted response or a deterministic default."""
        self.call_count += 1
        self.calls.append(prompt)
        if self._fail_remaining > 0:
            self._fail_remaining -= 1
            error = self._error
            if isinstance(error, BaseException):
                raise error
            exception_type = error if error is not None else AIProviderError
            raise exception_type("FakeAIProvider simulated failure.")
        if self.delay_seconds > 0:
            time.sleep(self.delay_seconds)
        if self._responses is not None:
            if not self._responses:
                raise AIProviderError("FakeAIProvider has no queued responses left.")
            return self._responses.popleft()
        return self._default_response(prompt)

    def _default_response(self, prompt: str) -> str:
        card_facts = prompt.rsplit(CARD_FACTS_HEADER, maxsplit=1)[-1]
        card_count = card_facts.count(CARD_KEYWORD_MARKER)
        if card_count < 1:
            raise AIProviderError(
                "FakeAIProvider could not infer the drawn card count from the prompt.",
            )
        blocks = [
            f"<card>\nSimulated interpretation for drawn card {index}.\n</card>"
            for index in range(1, card_count + 1)
        ]
        parts = [
            "<summary>\nA simulated tarot reading produced by FakeAIProvider for testing and demos only.\n</summary>",
            *blocks,
            "<advice>\nSimulated advice: reflect on the question before acting.\n</advice>",
        ]
        return "\n".join(parts)


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Refuse every upstream redirect so credentials are never forwarded."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: object,
        code: int,
        msg: str,
        headers: object,
        newurl: str,
    ) -> None:
        return None


def _build_opener() -> urllib.request.OpenerDirector:
    """Build an opener that refuses to follow redirects."""
    return urllib.request.build_opener(_NoRedirectHandler)


def _normalize_base_url(base_url: str) -> str:
    """Validate and normalize a Chat Completions Base URL.

    Strips trailing slashes and keeps user-provided subpaths such as
    ``/v1``.  Rejects complete completions paths, queries, fragments,
    userinfo credentials and non-HTTP(S) schemes, and never appends a
    missing ``/v1``.
    """
    if not isinstance(base_url, str) or not base_url.strip():
        raise ValueError("base_url must be a non-empty string.")
    url = base_url.strip().rstrip("/")
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("base_url must use http:// or https://.")
    if not parsed.netloc:
        raise ValueError("base_url must include a host.")
    if "@" in parsed.netloc:
        raise ValueError("base_url must not contain userinfo credentials.")
    if parsed.query or parsed.fragment:
        raise ValueError("base_url must not contain a query or fragment.")
    if parsed.path.endswith(CHAT_COMPLETIONS_PATH):
        raise ValueError(
            "base_url must point at the API base, not the full /chat/completions path.",
        )
    return url


class OpenAICompatibleProvider:
    """Send one non-streaming Chat Completions request per reading.

    Constructor arguments mirror the AI settings contract shared with the
    frontend settings page (Demo mode is resolved by the service layer,
    which selects :class:`FakeAIProvider` instead of this class):

    - ``base_url``: API base such as ``https://api.openai.com/v1`` or a
      custom gateway; ``/chat/completions`` is appended exactly once and
      user-provided subpaths are preserved;
    - ``model``: model identifier, sent verbatim — no hard-coded defaults;
    - ``api_key``: bearer credential, required at request time when
      ``auth_mode="bearer"``; never read from the environment here;
    - ``auth_mode``: ``"bearer"`` sends ``Authorization: Bearer ...``,
      ``"none"`` sends no Authorization header at all;
    - ``timeout_seconds``: network timeout for the single request.

    Requests are never retried, upstream redirects are never followed, and
    failures never silently fall back to simulated output.  Raised error
    messages never include keys, headers, or upstream response bodies.
    """

    name = "OpenAI-compatible"

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str | None = None,
        auth_mode: AuthMode = "bearer",
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        if auth_mode not in ("bearer", "none"):
            raise ValueError(f"Unsupported auth_mode: {auth_mode!r}.")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("model must be a non-empty string.")
        if not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be a positive number.")
        self.base_url = _normalize_base_url(base_url)
        self.model = model
        self.api_key = api_key
        self.auth_mode: AuthMode = auth_mode
        self.timeout_seconds = float(timeout_seconds)
        self._opener = _build_opener()

    def generate(self, prompt: str) -> str:
        """Send one Chat Completions request and return the message content.

        Raises:
            AIUnavailableError: no key in bearer mode, credentials were
                rejected, or the server could not be reached;
            AITimeoutError: the single request exceeded ``timeout_seconds``;
            AIRateLimitedError: the server answered HTTP 429;
            AIProviderError: any other upstream or parsing failure.
        """
        if self.auth_mode == "bearer" and not (self.api_key or "").strip():
            raise AIUnavailableError(
                "No API key is configured for the AI server. Add one in AI settings.",
            )
        payload = json.dumps(
            {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.auth_mode == "bearer":
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(
            f"{self.base_url}{CHAT_COMPLETIONS_PATH}",
            data=payload,
            headers=headers,
            method="POST",
        )
        try:
            with self._opener.open(request, timeout=self.timeout_seconds) as response:
                raw = response.read()
        except TimeoutError as exc:
            raise AITimeoutError(
                f"The AI server timed out after {self.timeout_seconds:g} seconds.",
            ) from exc
        except urllib.error.HTTPError as exc:
            raise _http_error(exc) from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise AITimeoutError(
                    f"The AI server timed out after {self.timeout_seconds:g} seconds.",
                ) from exc
            raise AIUnavailableError(
                "The AI server could not be reached. Check the Base URL.",
            ) from exc
        return _parse_chat_response(raw)


def _http_error(exc: urllib.error.HTTPError) -> TarotError:
    """Map an upstream HTTP status to a sanitized project error."""
    code = exc.code
    if code in (401, 403):
        return AIUnavailableError(
            "The AI server rejected the credentials. Check the API key and auth mode.",
        )
    if code == 429:
        return AIRateLimitedError(
            "The AI server rate-limited the request. Wait a moment and try again.",
        )
    if code == 404:
        return AIProviderError(
            "The AI server returned 404. Check the Base URL and model name.",
        )
    if 300 <= code < 400:
        return AIProviderError(
            "The AI server redirected the request. Redirects are not followed; check the Base URL.",
        )
    return AIProviderError(f"The AI server returned HTTP {code}.")


def _parse_chat_response(raw: bytes) -> str:
    """Extract ``choices[0].message.content`` from a Chat Completions body."""
    try:
        body = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise AIProviderError("The AI server returned a non-JSON response.") from exc
    if not isinstance(body, dict):
        raise AIProviderError("The AI server returned an unexpected response body.")
    choices = body.get("choices")
    if not isinstance(choices, list) or not choices:
        raise AIProviderError("The AI server returned no completion choices.")
    first = choices[0]
    if not isinstance(first, dict):
        raise AIProviderError("The AI server returned an unexpected response body.")
    message = first.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise AIProviderError("The AI server returned empty content.")
    return content


__all__ = ["AIProvider", "AuthMode", "FakeAIProvider", "OpenAICompatibleProvider"]
