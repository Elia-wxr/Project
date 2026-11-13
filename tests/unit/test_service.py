from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from tarot_jupyterlab.ai import FakeAIProvider
from tarot_jupyterlab.cards import load_card_set
from tarot_jupyterlab.errors import (
    AITimeoutError,
    AIUnavailableError,
    SessionConflictError,
    StorageError,
)
from tarot_jupyterlab.history import record_to_dict
from tarot_jupyterlab.service import TarotService

DECK_PATH = Path(__file__).resolve().parents[2] / "card_set.json"


async def test_draw_read_save_and_reopen(tmp_path: Path) -> None:
    cards = load_card_set(DECK_PATH)
    path = tmp_path / "latest.json"
    service = TarotService(cards, path, FakeAIProvider())
    assert service.latest() is None

    drawn = service.draw(" Keywords: What should I reflect on? ")
    assert drawn.session.question == "Keywords: What should I reflect on?"
    assert len(drawn.session.cards) == 1
    assert drawn.session.cards[0].card in cards
    assert service.latest() is None

    session_id = drawn.session.session_id
    result = await service.read(session_id)
    assert result.reading is not None
    assert result.reading.session_id == session_id
    assert result.reading.session_revision == 1
    service.save(session_id)

    reopened = TarotService(cards, path)
    assert reopened.latest() == record_to_dict(result)


async def test_timeout_cannot_publish_an_old_reading(tmp_path: Path) -> None:
    service = TarotService(
        load_card_set(DECK_PATH),
        tmp_path / "latest.json",
        FakeAIProvider(delay_seconds=0.12),
        reading_timeout=0.02,
    )
    old_id = service.draw("The first question").session.session_id
    with pytest.raises(AITimeoutError):
        await service.read(old_id)

    new_id = service.draw("The next question").session.session_id
    await asyncio.sleep(0.14)
    with pytest.raises(SessionConflictError):
        service.save(old_id)
    assert service.save(new_id).reading is None


async def test_missing_ai_does_not_block_saving(tmp_path: Path) -> None:
    service = TarotService(load_card_set(DECK_PATH), tmp_path / "latest.json")
    session_id = service.draw("A question without AI").session.session_id
    with pytest.raises(AIUnavailableError):
        await service.read(session_id)
    assert service.save(session_id).reading is None


def test_failed_replacement_preserves_the_saved_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = TarotService(load_card_set(DECK_PATH), tmp_path / "latest.json")
    first = service.draw("The saved question")
    service.save(first.session.session_id)

    def fail_replace(_self: Path, _target: Path) -> None:
        raise PermissionError("Simulated write failure")

    monkeypatch.setattr(Path, "replace", fail_replace)
    second = service.draw("The unsaved question")
    with pytest.raises(StorageError):
        service.save(second.session.session_id)
    assert service.latest() == record_to_dict(first)
