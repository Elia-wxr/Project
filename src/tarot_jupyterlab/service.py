"""Coordinate one active session across drawing, AI, and history."""

from __future__ import annotations

import asyncio
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any

from tarot_jupyterlab.ai import AIProvider, generate_reading
from tarot_jupyterlab.ai.config import AIConfigStore
from tarot_jupyterlab.ai.provider import FakeAIProvider, OpenAICompatibleProvider
from tarot_jupyterlab.cards import create_single_session
from tarot_jupyterlab.errors import (
    AITimeoutError,
    AIUnavailableError,
    ReadingInProgressError,
    SessionConflictError,
    SessionNotFoundError,
)
from tarot_jupyterlab.history import load_latest, save_latest
from tarot_jupyterlab.models import Card, SessionRecord


class TarotService:
    """One instance per Jupyter Server, used on its request event loop."""

    def __init__(
        self,
        cards: tuple[Card, ...],
        history_path: Path,
        provider: AIProvider | None = None,
        *,
        reading_timeout: float = 45,
        ai_store: AIConfigStore | None = None,
    ) -> None:
        self._cards = cards
        self._history_path = history_path
        self._provider = provider
        self._reading_timeout = reading_timeout
        self._ai_store = ai_store
        self._active: SessionRecord | None = None
        self._reading_in_progress = False

    def draw(self, question: str) -> SessionRecord:
        self._require_idle()
        self._active = SessionRecord(create_single_session(question, self._cards))
        return self._active

    async def read(self, session_id: str) -> SessionRecord:
        record = self._get_active(session_id)
        self._require_idle()
        if record.reading is not None:
            return record
        provider, timeout = self._provider_for_reading()
        if provider is None:
            raise AIUnavailableError(
                "No AI is configured. Open AI settings and choose a model or Demo mode. "
                "You can still save the card.",
            )

        snapshot = deepcopy(record.session)
        self._reading_in_progress = True
        try:
            # The worker only computes a Reading. Only this coroutine can publish it.
            reading = await asyncio.wait_for(
                asyncio.to_thread(generate_reading, snapshot, provider, language="en"),
                timeout=timeout,
            )
            self._get_active(session_id)
            session = replace(record.session, updated_at=reading.created_at)
            self._active = replace(record, session=session, reading=reading)
            return self._active
        except asyncio.TimeoutError as exc:
            raise AITimeoutError(
                "The reading took too long. You can retry or save the card."
            ) from exc
        finally:
            self._reading_in_progress = False

    def save(self, session_id: str) -> SessionRecord:
        record = self._get_active(session_id)
        self._require_idle()
        save_latest(record, self._history_path)
        return record

    def latest(self) -> dict[str, Any] | None:
        return load_latest(self._history_path)

    def _get_active(self, session_id: str) -> SessionRecord:
        if self._active is None:
            raise SessionNotFoundError("Draw a card before continuing.")
        if self._active.session.session_id != session_id:
            raise SessionConflictError("The active card has changed. Draw a new card to continue.")
        return self._active

    def _require_idle(self) -> None:
        if self._reading_in_progress:
            raise ReadingInProgressError("Wait for the current reading to finish.")

    @property
    def is_generating(self) -> bool:
        """True while a reading request is running (used by the AI config handlers)."""
        return self._reading_in_progress

    def _provider_for_reading(self) -> tuple[AIProvider | None, float]:
        """Build the provider for one reading from the effective AI config snapshot.

        The snapshot is taken once per request, so a mid-flight settings change
        can never swap the provider or timeout of the running reading.  With no
        config store the legacy injected provider is used instead.
        """
        if self._ai_store is not None:
            kwargs = self._ai_store.provider_kwargs()
            timeout = float(kwargs["timeout_seconds"]) + 5
            if kwargs["mode"] == "demo":
                return FakeAIProvider(), timeout
            if not kwargs["model"]:
                return None, timeout
            if kwargs["auth_mode"] == "bearer" and not kwargs["api_key"]:
                return None, timeout
            return (
                OpenAICompatibleProvider(
                    base_url=kwargs["base_url"],
                    model=kwargs["model"],
                    api_key=kwargs["api_key"],
                    auth_mode=kwargs["auth_mode"],
                    timeout_seconds=kwargs["timeout_seconds"],
                ),
                timeout,
            )
        return self._provider, self._reading_timeout
