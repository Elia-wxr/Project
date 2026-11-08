"""Load the packaged deck and create one-card sessions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from importlib.resources import files
from pathlib import Path
from random import Random
from uuid import uuid4

from tarot_jupyterlab.errors import InvalidCardSetError, InvalidSessionError
from tarot_jupyterlab.models import Card, DrawnCard, Orientation, Session


def load_card_set(path: Path | None = None) -> tuple[Card, ...]:
    """Load all 78 cards; an explicit path makes the source data testable."""
    source = path if path is not None else files("tarot_jupyterlab") / "static" / "card_set.json"
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("Expected a list of cards.")
        cards = tuple(_parse_card(item) for item in data)
    except (OSError, TypeError, ValueError) as exc:
        raise InvalidCardSetError("The tarot deck could not be loaded.") from exc

    names = {card.name for card in cards}
    major_count = sum(card.arcana == "Major" for card in cards)
    if len(cards) != 78 or len(names) != 78 or major_count != 22:
        raise InvalidCardSetError("Expected 78 unique cards, including 22 Major Arcana cards.")
    return cards


def _parse_card(item: object) -> Card:
    if not isinstance(item, dict):
        raise ValueError("Expected a card object.")
    if not isinstance(item.get("name"), str) or not item["name"].strip():
        raise ValueError("A card must have a name.")
    if item.get("arcana") not in ("Major", "Minor"):
        raise ValueError("Unrecognized arcana.")
    keywords = {}
    for orientation in ("upright", "reversed"):
        values = item.get(orientation)
        if (
            not isinstance(values, list)
            or not values
            or not all(isinstance(value, str) and value.strip() for value in values)
        ):
            raise ValueError("A card must have keywords for both orientations.")
        keywords[orientation] = tuple(values)
    return Card(**{**item, **keywords})


def create_single_session(
    question: str,
    cards: tuple[Card, ...],
    *,
    rng: Random | None = None,
    now: datetime | None = None,
) -> Session:
    """Validate a question and draw one card with a stable position name."""
    question = question.strip()
    if not 1 <= len(question) <= 2000:
        raise InvalidSessionError("Enter a question between 1 and 2000 characters.")
    if not cards:
        raise InvalidCardSetError("The tarot deck is empty.")

    rng = rng if rng is not None else Random()
    card = rng.choice(cards)
    orientation: Orientation = rng.choice(("upright", "reversed"))
    now = now if now is not None else datetime.now(timezone.utc)
    return Session(
        session_id=str(uuid4()),
        question=question,
        spread_name="single",
        cards=[DrawnCard(card=card, orientation=orientation, position="focus")],
        revision=1,
        allow_repeats=False,
        created_at=now,
        updated_at=now,
    )
