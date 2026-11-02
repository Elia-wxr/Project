"""Shared sample builders for the Owner (models + AI) unit tests.

Owned by the Owner; agents A-E must not edit this file.  Card fixtures used
by the contract tests come from ``card_set.json`` (Agent A scope).
"""

from __future__ import annotations

from datetime import datetime, timezone

from tarot_jupyterlab.models import (
    Card,
    DrawnCard,
    Reading,
    Session,
    SessionRecord,
)

NOW = datetime(2026, 10, 28, 10, 0, 0, tzinfo=timezone.utc)
SESSION_ID = "5af02746-6e0b-4689-a61f-52d765d98831"


def make_card(
    name: str = "The Fool",
    *,
    arcana: str = "Major",
    suit: str | None = None,
    number: int | None = 0,
    rank: str | None = None,
    element: str = "Air",
    upright_keywords: tuple[str, ...] = ("beginnings", "freedom"),
    reversed_keywords: tuple[str, ...] = ("recklessness", "hesitation"),
) -> Card:
    """Build one immutable card with test-friendly defaults."""
    return Card(
        name=name,
        arcana=arcana,
        suit=suit,
        number=number,
        rank=rank,
        element=element,
        upright=upright_keywords,
        reversed=reversed_keywords,
    )


def make_drawn(
    *,
    card: Card | None = None,
    orientation: str = "upright",
    position: str = "focus",
) -> DrawnCard:
    """Build one drawn card bound to a spread position."""
    return DrawnCard(card=card or make_card(), orientation=orientation, position=position)


def make_session(
    *,
    session_id: str = SESSION_ID,
    question: str = "What should I focus on today?",
    spread_name: str = "single",
    drawn: list[DrawnCard] | None = None,
    revision: int = 1,
    allow_repeats: bool = False,
    created_at: datetime = NOW,
    updated_at: datetime = NOW,
) -> Session:
    """Build one in-memory session with a single drawn card by default."""
    if drawn is None:
        drawn = [make_drawn()]
    return Session(
        session_id=session_id,
        question=question,
        spread_name=spread_name,
        cards=list(drawn),
        revision=revision,
        allow_repeats=allow_repeats,
        created_at=created_at,
        updated_at=updated_at,
    )


def make_reading(
    session: Session | None = None,
    *,
    summary: str = "A test summary.",
    interpretations: tuple[str, ...] | None = None,
    advice: str = "Some test advice.",
    provider: str = "FakeAIProvider",
    created_at: datetime = NOW,
) -> Reading:
    """Build one reading linked to a session snapshot."""
    session = session or make_session()
    return Reading(
        session_id=session.session_id,
        session_revision=session.revision,
        summary=summary,
        card_interpretations=interpretations or ("One interpretation.",),
        advice=advice,
        provider=provider,
        created_at=created_at,
    )


_UNSET = object()


def make_record(
    session: Session | None = None,
    reading: Reading | object | None = _UNSET,
) -> SessionRecord:
    """Build one complete record.

    By default the record carries a linked reading; pass ``reading=None``
    explicitly for a record without a reading.
    """
    session = session or make_session()
    if reading is _UNSET:
        return SessionRecord(session=session, reading=make_reading(session))
    return SessionRecord(session=session, reading=reading)  # type: ignore[arg-type]


def structured_output(
    *,
    summary: str = "A structured summary.",
    interpretations: list[str] | None = None,
    advice: str = "A structured advice.",
) -> str:
    """Build a model response in the strict output format."""
    if interpretations is None:
        interpretations = ["First card interpretation."]
    blocks = ["<card>\n" + text + "\n</card>" for text in interpretations]
    return "\n".join(
        [
            "<summary>\n" + summary + "\n</summary>",
            *blocks,
            "<advice>\n" + advice + "\n</advice>",
        ]
    )
