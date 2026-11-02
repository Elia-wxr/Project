"""Shared data models and types for the Tarot JupyterLab plugin.

Every module must build on the definitions in this file instead of
re-declaring equivalent fields.  Conversion between these models and JSON
happens at serialization boundaries (the ``session_history`` package owns
that conversion); the models themselves carry no JSON or HTTP knowledge.

Public functions succeed with their declared return values and raise
``TarotError`` subclasses on failure.  ``None`` is used only for explicitly
optional fields.  ``SessionState`` runtime flags are computed by the API
facade and are never persisted or accepted from clients.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

Arcana = Literal["Major", "Minor"]
Suit = Literal["Wands", "Cups", "Swords", "Pentacles"]
Orientation = Literal["upright", "reversed"]
ReadingLanguage = Literal["zh-CN", "en", "bilingual"]
ExportFormat = Literal["json", "markdown"]

#: Schema version recorded in every saved or imported :class:`SessionRecord`.
SESSION_SCHEMA_VERSION: Literal[1] = 1


@dataclass(frozen=True)
class Card:
    """One immutable card from the loaded card library.

    ``upright`` and ``reversed`` hold display-ready keyword tuples for the
    two orientations; the attribute names shadow the builtin ``reversed``
    only inside this dataclass.
    """

    name: str
    arcana: Arcana
    suit: Suit | None
    number: int | None
    rank: str | None
    element: str
    upright: tuple[str, ...]
    reversed: tuple[str, ...]


@dataclass(frozen=True)
class DrawnCard:
    """A card bound to one spread position with a recorded orientation."""

    card: Card
    orientation: Orientation
    position: str


@dataclass
class Session:
    """In-memory business state of one reading session.

    Revision rules: a new session starts at ``revision=0``; every successful
    draw or redraw increases it by one.  Generating or saving a reading does
    not change it.  ``allow_repeats`` is fixed at creation time and is
    carried in the record so that loads, imports and redraws reuse the same
    rule.
    """

    session_id: str
    question: str
    spread_name: str
    cards: list[DrawnCard]
    revision: int
    allow_repeats: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class Reading:
    """One accepted AI reading bound to an exact session revision."""

    session_id: str
    session_revision: int
    summary: str
    card_interpretations: tuple[str, ...]
    advice: str
    provider: str
    created_at: datetime


@dataclass
class SessionRecord:
    """The complete unit of save, load, JSON import and export.

    Always carries a :class:`Session` and an optional :class:`Reading`.
    A record with a non-null ``reading`` must satisfy the linkage
    invariants: matching ``session_id``, matching ``session_revision``, a
    fully drawn spread, and one interpretation per drawn card in spread
    position order.
    """

    session: Session
    reading: Reading | None = None
    schema_version: Literal[1] = 1


@dataclass(frozen=True)
class SessionState:
    """Active-session runtime state returned to HTTP and frontend callers.

    ``dirty`` and ``reading_in_progress`` are computed by the API facade;
    they are never written to history files and never accepted from clients.
    """

    record: SessionRecord
    dirty: bool
    reading_in_progress: bool


@dataclass(frozen=True)
class Spread:
    """A named spread with its ordered position names."""

    name: str
    positions: tuple[str, ...]


@dataclass(frozen=True)
class SessionSummary:
    """One row of the saved-history listing."""

    session_id: str
    question: str
    spread_name: str
    revision: int
    has_reading: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class HistoryPage:
    """A page of saved-history summaries."""

    items: tuple[SessionSummary, ...]
    total: int
    limit: int
    offset: int


__all__ = [
    "SESSION_SCHEMA_VERSION",
    "Arcana",
    "Card",
    "DrawnCard",
    "ExportFormat",
    "HistoryPage",
    "Orientation",
    "Reading",
    "ReadingLanguage",
    "Session",
    "SessionRecord",
    "SessionState",
    "SessionSummary",
    "Spread",
    "Suit",
]
