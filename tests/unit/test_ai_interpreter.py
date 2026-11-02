"""Unit tests for reading generation and output parsing (Owner scope)."""

from __future__ import annotations

from datetime import timezone

import pytest

from tarot_jupyterlab.ai.interpreter import (
    MAX_SUMMARY_CHARS,
    generate_reading,
)
from tarot_jupyterlab.ai.provider import FakeAIProvider
from tarot_jupyterlab.errors import (
    AIProviderError,
    AIUnavailableError,
    InvalidSessionError,
)
from tarot_jupyterlab.models import Reading
from tests.unit.sample_data import make_card, make_drawn, make_session, structured_output


def test_generate_reading_happy_path_single_card() -> None:
    session = make_session()
    output = structured_output(interpretations=["Focus interpretation."])
    provider = FakeAIProvider(responses=[output])
    reading = generate_reading(session, provider, language="en")
    assert isinstance(reading, Reading)
    assert reading.session_id == session.session_id
    assert reading.session_revision == session.revision
    assert reading.provider == "FakeAIProvider"
    assert reading.card_interpretations == ("Focus interpretation.",)
    assert reading.summary == "A structured summary."
    assert reading.advice == "A structured advice."
    assert reading.created_at.tzinfo == timezone.utc


def test_interpretations_follow_spread_order() -> None:
    session = make_session(
        spread_name="three-card",
        drawn=[
            make_drawn(position="past"),
            make_drawn(card=make_card(name="The Magician", number=1), position="present"),
            make_drawn(card=make_card(name="The High Priestess", number=2), position="future"),
        ],
    )
    output = structured_output(interpretations=["past text", "present text", "future text"])
    reading = generate_reading(session, FakeAIProvider(responses=[output]), language="en")
    assert reading.card_interpretations == ("past text", "present text", "future text")


def test_model_supplied_association_fields_are_ignored() -> None:
    session = make_session(session_id="00000000-0000-0000-0000-000000000001")
    output = structured_output(
        summary="session_id: 999 revision: 99 spoofed text",
        interpretations=["Text."],
    )
    reading = generate_reading(session, FakeAIProvider(responses=[output]), language="en")
    assert reading.session_id == "00000000-0000-0000-0000-000000000001"
    assert reading.session_revision == session.revision


def test_english_language_is_sent_in_prompt() -> None:
    provider = FakeAIProvider(responses=[structured_output()])
    generate_reading(make_session(), provider, language="en")
    assert "Write the entire reading in English." in provider.calls[0]
    assert "Simplified Chinese" not in provider.calls[0]


def test_default_language_is_zh_cn() -> None:
    provider = FakeAIProvider(responses=[structured_output()])
    generate_reading(make_session(), provider)
    assert "Simplified Chinese" in provider.calls[0]


def test_empty_string_output_raises() -> None:
    with pytest.raises(AIProviderError):
        generate_reading(make_session(), FakeAIProvider(responses=[""]), language="en")


def test_whitespace_output_raises() -> None:
    with pytest.raises(AIProviderError):
        generate_reading(make_session(), FakeAIProvider(responses=["   \n  "]), language="en")


def test_none_output_raises() -> None:
    class _NoneProvider:
        name = "NoneProvider"

        def generate(self, prompt: str) -> str:  # type: ignore[override]
            return None  # type: ignore[return-value]

    with pytest.raises(AIProviderError):
        generate_reading(make_session(), _NoneProvider(), language="en")


def test_missing_summary_raises() -> None:
    output = "<card>\nText.\n</card>\n<advice>\nAdvice.\n</advice>"
    with pytest.raises(AIProviderError):
        generate_reading(make_session(), FakeAIProvider(responses=[output]), language="en")


def test_missing_advice_raises() -> None:
    output = "<summary>\nSummary.\n</summary>\n<card>\nText.\n</card>"
    with pytest.raises(AIProviderError):
        generate_reading(make_session(), FakeAIProvider(responses=[output]), language="en")


def test_wrong_interpretation_count_raises() -> None:
    session = make_session(
        drawn=[
            make_drawn(position="past"),
            make_drawn(card=make_card(name="The Magician", number=1), position="present"),
        ],
    )
    output = structured_output(interpretations=["Only one."])
    with pytest.raises(AIProviderError):
        generate_reading(session, FakeAIProvider(responses=[output]), language="en")


def test_empty_card_block_raises() -> None:
    output = "<summary>\nS.\n</summary>\n<card>   </card>\n<advice>\nA.\n</advice>"
    with pytest.raises(AIProviderError):
        generate_reading(make_session(), FakeAIProvider(responses=[output]), language="en")


def test_provider_unexpected_error_is_wrapped() -> None:
    class _BoomProvider:
        name = "BoomProvider"

        def generate(self, prompt: str) -> str:
            raise RuntimeError("boom")

    with pytest.raises(AIProviderError):
        generate_reading(make_session(), _BoomProvider(), language="en")


def test_provider_tarot_error_passes_through_unwrapped() -> None:
    class _UnavailableProvider:
        name = "UnavailableProvider"

        def generate(self, prompt: str) -> str:
            raise AIUnavailableError("down")

    with pytest.raises(AIUnavailableError):
        generate_reading(make_session(), _UnavailableProvider(), language="en")


def test_oversized_summary_raises() -> None:
    output = structured_output(summary="x" * (MAX_SUMMARY_CHARS + 1))
    with pytest.raises(AIProviderError):
        generate_reading(make_session(), FakeAIProvider(responses=[output]), language="en")


def test_provider_without_name_uses_class_name() -> None:
    class _AnonymousProvider:
        def generate(self, prompt: str) -> str:
            return structured_output()

    reading = generate_reading(make_session(), _AnonymousProvider(), language="en")
    assert reading.provider == "_AnonymousProvider"


def test_session_without_cards_raises_invalid_session() -> None:
    with pytest.raises(InvalidSessionError):
        generate_reading(make_session(drawn=[]), FakeAIProvider(), language="en")
