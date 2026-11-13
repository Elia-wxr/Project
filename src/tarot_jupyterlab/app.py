"""Jupyter Server registration and the JSON boundary for the Tarot sidebar."""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from uuid import UUID

from jupyter_core.paths import jupyter_data_dir
from jupyter_server.base.handlers import APIHandler
from jupyter_server.serverapp import ServerApp
from jupyter_server.utils import url_path_join
from tornado.web import authenticated

from tarot_jupyterlab.ai import AIProvider, FakeAIProvider, SocratesProvider
from tarot_jupyterlab.cards import load_card_set
from tarot_jupyterlab.errors import (
    AIProviderError,
    AITimeoutError,
    AIUnavailableError,
    InvalidSessionError,
    ReadingInProgressError,
    SessionConflictError,
    SessionNotFoundError,
    StorageError,
    TarotError,
)
from tarot_jupyterlab.history import record_to_dict
from tarot_jupyterlab.service import TarotService

_ERRORS = (
    (InvalidSessionError, 400, "INVALID_REQUEST"),
    (SessionNotFoundError, 404, "SESSION_NOT_FOUND"),
    (ReadingInProgressError, 409, "READING_IN_PROGRESS"),
    (SessionConflictError, 409, "SESSION_CONFLICT"),
    (AIUnavailableError, 503, "AI_UNAVAILABLE"),
    (AITimeoutError, 504, "AI_TIMEOUT"),
    (AIProviderError, 502, "AI_BAD_RESPONSE"),
    (StorageError, 500, "STORAGE_ERROR"),
)


class TarotHandler(APIHandler):
    def initialize(self, service: TarotService) -> None:
        self.service = service

    def read_object(
        self, required: set[str], *, optional: set[str] | None = None
    ) -> dict[str, Any]:
        content_type = self.request.headers.get("Content-Type", "").split(";", 1)[0].strip()
        if content_type.lower() != "application/json":
            raise InvalidSessionError("Send a JSON request.")
        try:
            body = json.loads(self.request.body)
        except ValueError as exc:
            raise InvalidSessionError("Send a valid JSON object.") from exc
        if not isinstance(body, dict):
            raise InvalidSessionError("Send a JSON object.")
        allowed = required | (optional or set())
        if not required.issubset(body) or not body.keys() <= allowed:
            raise InvalidSessionError("The request fields do not match this operation.")
        return body

    @contextmanager
    def report_errors(self) -> Iterator[None]:
        try:
            yield
        except TarotError as exc:
            for error_type, status, code in _ERRORS:
                if isinstance(exc, error_type):
                    self.set_status(status)
                    self.finish({"error": {"code": code, "message": str(exc)}})
                    return
            self.set_status(500)
            self.finish(
                {"error": {"code": "INTERNAL_ERROR", "message": "Tarot could not continue."}}
            )


class HealthHandler(TarotHandler):
    @authenticated
    def get(self) -> None:
        self.finish({"status": "ok"})


class DrawHandler(TarotHandler):
    @authenticated
    def post(self) -> None:
        with self.report_errors():
            question = self.read_object({"question"})["question"]
            if not isinstance(question, str):
                raise InvalidSessionError("The question must be text.")
            self.finish({"record": record_to_dict(self.service.draw(question))})


class ReadingHandler(TarotHandler):
    @authenticated
    async def post(self) -> None:
        with self.report_errors():
            body = self.read_object({"session_id"}, optional={"language"})
            if body.get("language", "en") != "en":
                raise InvalidSessionError("This version supports English readings.")
            record = await self.service.read(_session_id(body["session_id"]))
            self.finish({"record": record_to_dict(record)})


class LatestHistoryHandler(TarotHandler):
    @authenticated
    def get(self) -> None:
        with self.report_errors():
            self.finish({"record": self.service.latest()})

    @authenticated
    def post(self) -> None:
        with self.report_errors():
            body = self.read_object({"session_id"})
            record = self.service.save(_session_id(body["session_id"]))
            self.finish({"record": record_to_dict(record)})


def _session_id(value: object) -> str:
    if not isinstance(value, str):
        raise InvalidSessionError("Use the session ID returned when drawing a card.")
    try:
        return str(UUID(value))
    except ValueError as exc:
        raise InvalidSessionError("Use the session ID returned when drawing a card.") from exc


def _configured_provider() -> AIProvider | None:
    if os.environ.get("TAROT_DEMO_MODE") == "1":
        return FakeAIProvider()
    api_base = os.environ.get("SOCRATES_API_BASE", "").strip()
    api_key = os.environ.get("SOCRATES_API_KEY", "").strip()
    model = os.environ.get("SOCRATES_MODEL", "").strip()
    if api_base and api_key and model:
        return SocratesProvider(api_base=api_base, api_key=api_key, model=model)
    return None


def _load_jupyter_server_extension(serverapp: ServerApp) -> None:
    history_path = Path(jupyter_data_dir()) / "tarot-jupyterlab" / "latest.json"
    service = TarotService(load_card_set(), history_path, _configured_provider())
    base_url = serverapp.web_app.settings["base_url"]
    routes = (
        ("health", HealthHandler),
        ("draw", DrawHandler),
        ("reading", ReadingHandler),
        ("history/latest", LatestHistoryHandler),
    )
    serverapp.web_app.add_handlers(
        ".*$",
        [
            (url_path_join(base_url, "tarot/api", path), handler, {"service": service})
            for path, handler in routes
        ],
    )
