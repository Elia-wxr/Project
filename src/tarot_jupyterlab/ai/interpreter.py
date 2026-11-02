"""Reading generation and strict model-output parsing.

``generate_reading`` only consumes an isolated ``Session`` snapshot passed
in by the API facade.  It never touches the active-session table or the
history storage, and it fills ``session_id`` / ``session_revision`` from
the snapshot — model output can never supply association fields.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from tarot_jupyterlab.ai.prompts import build_reading_prompt
from tarot_jupyterlab.ai.provider import AIProvider
from tarot_jupyterlab.errors import AIProviderError
from tarot_jupyterlab.models import Reading, ReadingLanguage, Session

#: Hard limits enforced on model output and on each parsed section.
MAX_OUTPUT_CHARS = 20_000
MAX_SUMMARY_CHARS = 1_000
MAX_INTERPRETATION_CHARS = 1_000
MAX_ADVICE_CHARS = 1_500

_SUMMARY_RE = re.compile(r"<summary>\s*(.*?)\s*</summary>", re.DOTALL)
_CARD_RE = re.compile(r"<card>\s*(.*?)\s*</card>", re.DOTALL)
_ADVICE_RE = re.compile(r"<advice>\s*(.*?)\s*</advice>", re.DOTALL)


def generate_reading(
    session: Session,
    provider: AIProvider,
    *,
    language: ReadingLanguage = "zh-CN",
) -> Reading:
    """Return a validated reading bound to the supplied session snapshot.

    Flow: build the bounded prompt, call ``provider.generate`` once, parse
    the strict output format, then validate non-empty sections, one
    interpretation per drawn card in spread position order, and length
    caps.  Provider failures, empty responses and unparseable output raise
    :class:`tarot_jupyterlab.errors.AIProviderError` (or one of its
    subclasses, which are re-raised unchanged).
    """
    prompt = build_reading_prompt(session, language=language)
    try:
        output = provider.generate(prompt)
    except AIProviderError:
        raise
    except Exception as exc:
        raise AIProviderError(
            "The AI provider failed while generating the reading.",
        ) from exc
    if not isinstance(output, str) or not output.strip():
        raise AIProviderError("The AI provider returned an empty response.")
    if len(output) > MAX_OUTPUT_CHARS:
        raise AIProviderError(
            f"The AI provider output exceeds the {MAX_OUTPUT_CHARS} character limit.",
        )
    summary, interpretations, advice = _parse_reading_output(output)
    expected = len(session.cards)
    if len(interpretations) != expected:
        raise AIProviderError(
            "The reading must contain exactly one interpretation per drawn card",
            f" (expected {expected}, got {len(interpretations)}).",
        )
    _check_lengths(summary, interpretations, advice)
    provider_name = getattr(provider, "name", None) or type(provider).__name__
    return Reading(
        session_id=session.session_id,
        session_revision=session.revision,
        summary=summary,
        card_interpretations=tuple(interpretations),
        advice=advice,
        provider=provider_name,
        created_at=datetime.now(timezone.utc),
    )


def _parse_reading_output(output: str) -> tuple[str, list[str], str]:
    """Parse the strict output format into its three sections."""
    summary_match = _SUMMARY_RE.search(output)
    if summary_match is None or not summary_match.group(1).strip():
        raise AIProviderError(
            "The AI response is missing a non-empty <summary> section.",
        )
    advice_match = _ADVICE_RE.search(output)
    if advice_match is None or not advice_match.group(1).strip():
        raise AIProviderError(
            "The AI response is missing a non-empty <advice> section.",
        )
    interpretations = _CARD_RE.findall(output)
    if not interpretations:
        raise AIProviderError("The AI response contains no <card> sections.")
    cleaned = [text.strip() for text in interpretations]
    if any(not text for text in cleaned):
        raise AIProviderError("The AI response contains an empty <card> section.")
    return summary_match.group(1).strip(), cleaned, advice_match.group(1).strip()


def _check_lengths(summary: str, interpretations: list[str], advice: str) -> None:
    """Enforce per-section length caps on the parsed output."""
    if len(summary) > MAX_SUMMARY_CHARS:
        raise AIProviderError(
            f"The summary exceeds the {MAX_SUMMARY_CHARS} character limit.",
        )
    for text in interpretations:
        if len(text) > MAX_INTERPRETATION_CHARS:
            raise AIProviderError(
                f"A card interpretation exceeds the {MAX_INTERPRETATION_CHARS} character limit.",
            )
    if len(advice) > MAX_ADVICE_CHARS:
        raise AIProviderError(
            f"The advice exceeds the {MAX_ADVICE_CHARS} character limit.",
        )


__all__ = [
    "MAX_ADVICE_CHARS",
    "MAX_INTERPRETATION_CHARS",
    "MAX_OUTPUT_CHARS",
    "MAX_SUMMARY_CHARS",
    "generate_reading",
]
