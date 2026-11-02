"""Unit tests for reading prompt construction (Owner scope)."""

from __future__ import annotations

import pytest

from tarot_jupyterlab.ai.prompts import LANGUAGE_INSTRUCTION, build_reading_prompt
from tarot_jupyterlab.errors import InvalidSessionError
from tests.unit.sample_data import make_card, make_drawn, make_session


def test_prompt_contains_question_stripped() -> None:
    prompt = build_reading_prompt(make_session(question="  My question?  "), language="en")
    assert "My question?" in prompt
    assert "  My question?  " not in prompt


def test_prompt_contains_card_facts_in_order() -> None:
    session = make_session(
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
    prompt = build_reading_prompt(session, language="en")
    facts = prompt.split("Card facts", 1)[1].split("Write the entire reading", 1)[0]
    assert 'Position "past" — The Fool (Major, upright)' in facts
    assert 'Position "present" — The Magician (Major, reversed)' in facts
    assert facts.index("The Fool") < facts.index("The Magician")


def test_prompt_uses_orientation_keywords() -> None:
    upright = make_drawn(card=make_card(), orientation="upright", position="focus")
    prompt = build_reading_prompt(make_session(drawn=[upright]), language="en")
    assert "Keywords: beginnings, freedom" in prompt
    assert "recklessness" not in prompt
    reversed_card = make_drawn(card=make_card(), orientation="reversed", position="focus")
    reversed_prompt = build_reading_prompt(make_session(drawn=[reversed_card]), language="en")
    assert "Keywords: recklessness, hesitation" in reversed_prompt


def test_prompt_distinguishes_question_cards_format() -> None:
    prompt = build_reading_prompt(make_session(), language="en")
    assert "Question:" in prompt
    assert "Card facts" in prompt
    assert "Output format" in prompt
    assert "<summary>" in prompt and "<card>" in prompt and "<advice>" in prompt
    assert "entertainment and self-reflection" in prompt


def test_default_language_is_zh_cn() -> None:
    prompt = build_reading_prompt(make_session())
    assert "Simplified Chinese" in prompt


def test_language_en() -> None:
    prompt = build_reading_prompt(make_session(), language="en")
    assert "Write the entire reading in English." in prompt
    assert "Simplified Chinese" not in prompt


def test_language_bilingual() -> None:
    prompt = build_reading_prompt(make_session(), language="bilingual")
    assert "both English and Simplified Chinese" in prompt


def test_unknown_language_raises() -> None:
    with pytest.raises(InvalidSessionError):
        build_reading_prompt(make_session(), language="fr")  # type: ignore[arg-type]


def test_empty_question_raises() -> None:
    with pytest.raises(InvalidSessionError):
        build_reading_prompt(make_session(question="   "), language="en")


def test_session_without_cards_raises() -> None:
    with pytest.raises(InvalidSessionError):
        build_reading_prompt(make_session(drawn=[]), language="en")


def test_keyword_marker_appears_once_per_card() -> None:
    session = make_session(
        spread_name="three-card",
        drawn=[
            make_drawn(position="past"),
            make_drawn(card=make_card(name="The Magician", number=1), position="present"),
            make_drawn(card=make_card(name="The High Priestess", number=2), position="future"),
        ],
    )
    prompt = build_reading_prompt(session, language="en")
    assert prompt.count("Keywords:") == 3


def test_language_instruction_dict_covers_all_languages() -> None:
    assert set(LANGUAGE_INSTRUCTION) == {"zh-CN", "en", "bilingual"}
