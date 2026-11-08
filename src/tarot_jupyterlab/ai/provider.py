"""AI provider abstractions and bundled provider implementations.

``AIProvider`` is the synchronous contract consumed by
:func:`tarot_jupyterlab.ai.interpreter.generate_reading`; the API facade
runs it inside a worker thread with an overall timeout.  ``FakeAIProvider``
is a deterministic, dependency-free stand-in for tests and demos, and
``SocratesProvider`` adapts the CS1302A course Socrates model through an
OpenAI-compatible chat completions endpoint using only the standard
library.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from collections import deque
from collections.abc import Sequence
from typing import Protocol

from tarot_jupyterlab.ai.prompts import CARD_FACTS_HEADER
from tarot_jupyterlab.errors import AIProviderError, AITimeoutError, AIUnavailableError

#: Marker emitted by prompts.build_reading_prompt once per drawn card;
#: FakeAIProvider counts it to shape its default structured response.
CARD_KEYWORD_MARKER = "Keywords:"


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
    """Deterministic provider used by unit tests and demos.

    Supports the features the API layer needs to exercise the two required
    races without a network:

    - **queued scripted responses** (``responses``): each ``generate`` call
      pops the next entry; an exhausted queue raises ``AIProviderError``;
    - **controlled delay** (``delay_seconds``): a slow call can still return
      successfully after the facade has timed out or redrawn, simulating a
      late result;
    - **controlled failures** (``fail_times`` / ``error``): the first N
      calls raise, so tests can cover failure, timeout and retry paths.

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


class SocratesProvider:
    """Adapter for the CS1302A course Socrates model.

    Talks to an OpenAI-compatible ``POST {base}/chat/completions`` endpoint
    using only the standard library.  Configuration is read from the
    environment with constructor overrides:

    - ``SOCRATES_API_BASE`` (default ``https://api.openai.com/v1``)
    - ``SOCRATES_API_KEY``
    - ``SOCRATES_MODEL`` (default ``socrates``)

    API keys are never embedded in prompts, history files, logs or raised
    error messages.
    """

    name = "Socrates"

    def __init__(
        self,
        *,
        api_base: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.api_base = (
            api_base or os.environ.get("SOCRATES_API_BASE") or "https://api.openai.com/v1"
        ).rstrip("/")
        self.api_key = api_key or os.environ.get("SOCRATES_API_KEY") or ""
        self.model = model or os.environ.get("SOCRATES_MODEL") or "socrates"
        self.timeout_seconds = timeout_seconds

    def generate(self, prompt: str) -> str:
        """Call the Socrates chat completions endpoint and return the text."""
        if not self.api_key:
            raise AIUnavailableError(
                "The Socrates provider is not configured: set SOCRATES_API_KEY.",
            )
        payload = json.dumps(
            {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
            },
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self.api_base}/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except TimeoutError as exc:
            raise AITimeoutError(
                f"The Socrates provider timed out after {self.timeout_seconds} seconds.",
            ) from exc
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                raise AIUnavailableError(
                    "The Socrates endpoint rejected the credentials; check SOCRATES_API_KEY.",
                ) from exc
            raise AIProviderError(
                f"The Socrates endpoint returned HTTP {exc.code}.",
            ) from exc
        except urllib.error.URLError as exc:
            raise AIUnavailableError(
                "The Socrates endpoint could not be reached; check SOCRATES_API_BASE.",
            ) from exc
        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIProviderError(
                "The Socrates endpoint returned an unexpected response body.",
            ) from exc
        if not isinstance(content, str) or not content.strip():
            raise AIProviderError("The Socrates endpoint returned an empty response.")
        return content


__all__ = ["AIProvider", "FakeAIProvider", "SocratesProvider"]
