"""Unit tests for the shared models (Owner scope)."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from tarot_jupyterlab.models import (
    SESSION_SCHEMA_VERSION,
    HistoryPage,
    SessionRecord,
    SessionState,
    SessionSummary,
    Spread,
)
from tests.unit.sample_data import NOW, make_card, make_drawn, make_reading, make_session


def test_card_is_frozen() -> None:
    card = make_card()
    with pytest.raises(FrozenInstanceError):
        card.name = "Tampered"  # type: ignore[misc]


def test_card_keyword_tuples_are_exposed() -> None:
    card = make_card()
    assert card.upright == ("beginnings", "freedom")
    assert card.reversed == ("recklessness", "hesitation")


def test_session_defaults_are_plain_fields() -> None:
    session = make_session()
    assert session.revision == 1
    assert session.allow_repeats is False
    assert session.spread_name == "single"
    assert session.cards == [make_drawn()]


def test_session_cards_list_is_mutable_but_drawn_card_is_frozen() -> None:
    session = make_session()
    session.cards.append(make_drawn(position="focus"))
    assert len(session.cards) == 2
    with pytest.raises(FrozenInstanceError):
        session.cards[0].orientation = "reversed"  # type: ignore[misc]


def test_reading_is_frozen() -> None:
    reading = make_reading(make_session())
    with pytest.raises(FrozenInstanceError):
        reading.summary = "Tampered"  # type: ignore[misc]
    assert isinstance(reading.card_interpretations, tuple)


def test_record_defaults() -> None:
    record = SessionRecord(session=make_session())
    assert record.schema_version == 1
    assert record.reading is None


def test_schema_version_constant_matches_record_default() -> None:
    assert SESSION_SCHEMA_VERSION == 1
    assert SessionRecord(session=make_session()).schema_version == SESSION_SCHEMA_VERSION


def test_session_state_is_frozen() -> None:
    record = SessionRecord(session=make_session())
    state = SessionState(record=record, dirty=True, reading_in_progress=False)
    assert state.dirty is True
    with pytest.raises(FrozenInstanceError):
        state.dirty = False  # type: ignore[misc]


def test_spread_summary_and_history_page() -> None:
    spread = Spread(name="three-card", positions=("past", "present", "future"))
    assert spread.positions == ("past", "present", "future")
    summary = SessionSummary(
        session_id="abc",
        question="Q?",
        spread_name="single",
        revision=1,
        has_reading=True,
        created_at=NOW,
        updated_at=NOW,
    )
    page = HistoryPage(items=(summary,), total=1, limit=20, offset=0)
    assert page.total == 1
    assert page.items[0].session_id == "abc"


def test_literal_alias_values_are_plain_strings() -> None:
    card = make_card()
    drawn = make_drawn(card=card)
    assert isinstance(card.arcana, str)
    assert isinstance(drawn.orientation, str)


def test_card_repr_contains_name() -> None:
    assert "The Fool" in repr(make_card())
