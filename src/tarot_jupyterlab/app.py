from __future__ import annotations

# 1. Standard Library
import asyncio
import json
import os
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from uuid import UUID

# 2. Third-party
import tornado.web
from jupyter_core.paths import jupyter_data_dir
from jupyter_server.base.handlers import APIHandler
from jupyter_server.serverapp import ServerApp
from jupyter_server.utils import url_path_join
from tornado import web
from tornado.web import authenticated

# 3.Local Application
from tarot_jupyterlab.ai import AIProvider, FakeAIProvider, OpenAICompatibleProvider
from tarot_jupyterlab.ai.config import (
    AIConfigStore,
    InvalidConfigError,
    default_config_path,
    system_resolver,
)
from tarot_jupyterlab.ai.provider import OpenAICompatibleProvider
from tarot_jupyterlab.cards import load_card_set
from tarot_jupyterlab.errors import (
    AIConfigBusyError,
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
TEST_PROMPT = "Reply with the single word: ok"

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

TEST_PROMPT = "Reply with the single word: ok"
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
    api_base = os.environ.get("TAROT_AI_API_BASE", "").strip()
    api_key = os.environ.get("TAROT_AI_API_KEY", "").strip()
    model = os.environ.get("TAROT_AI_MODEL", "").strip()
    if api_base and api_key and model:
        return OpenAICompatibleProvider(api_base=api_base, api_key=api_key, model=model)
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
class AIConfigHandler(APIHandler):
    """Shared error -> HTTP mapping. Merge this table into an existing write_error."""

    def write_error(self, status_code: int, **kwargs: object) -> None:
        exc = kwargs.get("exc_info", (None, None, None))[1]
        if isinstance(exc, TarotError):
            status_code = exc.status_code
            payload = exc.to_dict()
        else:
            payload = {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "The server could not handle the request.",
                }
            }
        self.set_status(status_code)
        self.set_header("Content-Type", "application/json")
        self.finish(json.dumps(payload))

    @property
    def store(self) -> AIConfigStore:
        return self.settings["tarot_ai_store"]

    def _require_idle(self) -> None:
        service = self.settings.get("tarot_service")
        if service is not None and getattr(service, "is_generating", False):
            raise AIConfigBusyError(
                "A reading is being generated. Wait for it to finish before changing AI settings."
            )


class AISettingsHandler(AIConfigHandler):
    """GET/PUT /tarot/api/ai/settings"""

    @web.authenticated
    def get(self) -> None:
        self.set_header("Cache-Control", "no-store")
        self.finish(json.dumps(self.store.snapshot()))

    @web.authenticated
    def put(self) -> None:
        body = self.get_json_body()
        if not isinstance(body, dict):
            raise InvalidConfigError("settings", "Request body must be a JSON object.")
        self._require_idle()
        snapshot = self.store.update(
            config_revision=body.get("config_revision"),
            settings=body.get("settings"),
            api_key=body.get("api_key"),
            clear_api_key=body.get("clear_api_key", False),
        )
        self.set_header("Cache-Control", "no-store")
        self.finish(json.dumps(snapshot))


class AITestHandler(AIConfigHandler):
    """POST /tarot/api/ai/test -- persists nothing, touches no card, sends no user question."""

    @web.authenticated
    async def post(self) -> None:
        body = self.get_json_body()
        if not isinstance(body, dict):
            raise InvalidConfigError("settings", "Request body must be a JSON object.")
        draft, key = self.store.draft(
            config_revision=body.get("config_revision"),
            settings=body.get("settings"),
            api_key=body.get("api_key"),
        )
        if draft.mode == "demo":
            raise InvalidConfigError(
                "mode", "Demo mode does not contact a server. Switch to Real API to test."
            )
        if not draft.model:
            raise InvalidConfigError("model", "A model ID is required to test the connection.")
        if draft.auth_mode == "bearer" and not key:
            raise InvalidConfigError(
                "api_key", "A runtime key is required for Bearer authentication."
            )

        provider = OpenAICompatibleProvider(
            base_url=draft.base_url,
            model=draft.model,
            api_key=key or "",
            auth_mode=draft.auth_mode,
            timeout_seconds=draft.timeout_seconds,
        )
        started = time.monotonic()
        # Same wait ceiling as a reading, so the test endpoint cannot hang a thread.
        await asyncio.wait_for(
            asyncio.to_thread(provider.generate, TEST_PROMPT),
            timeout=draft.timeout_seconds + 5,
        )
        latency_ms = int((time.monotonic() - started) * 1000)
        host = draft.base_url.split("://", 1)[-1].split("/", 1)[0]  # echo host only, no path, no key
        self.finish(
            json.dumps(
                {
                    "ok": True,
                    "latency_ms": latency_ms,
                    "message": f"Connected to {host} in {latency_ms} ms.",
                }
            )
        )


# --- registration (in setup_handlers / _load_jupyter_server_extension) ------
#
# from jupyter_server.utils import url_path_join
# from jupyter_core.paths import jupyter_config_dir
# from pathlib import Path
#
# store = AIConfigStore(default_config_path(), resolver=system_resolver)
# web_app.settings["tarot_ai_store"] = store
# Keep the five existing handlers as they are; just append these entries:
#
# handlers = [
#     (url_path_join(base_url, "tarot", "api", "ai", "settings"), AISettingsHandler),
#     (url_path_join(base_url, "tarot", "api", "ai", "test"), AITestHandler),
# ]
# web_app.add_handlers(".*$", handlers)


# ===========================================================================
# 3) src/tarot_jupyterlab/service.py  -- runtime wiring
# ===========================================================================
#
# Only four points matter:
#   (a) take one provider_kwargs() snapshot when a reading starts, so a config
#       change mid-flight cannot affect that reading;
#   (b) overall wait ceiling = timeout_seconds + 5 (do not hard-code 45 seconds);
#   (c) a late result is written back only if the request token and session_id
#       still match;
#   (d) on failure the active record, the old config and the old key stay intact.
#
# class TarotService:
#     def __init__(self, ..., ai_store: AIConfigStore) -> None:
#         self._ai_store = ai_store
#         self._generating = False          # used by the handler for the busy check
#
#     @property
#     def is_generating(self) -> bool:
#         return self._generating
#
#     def _provider(self, kwargs: dict):
#         if kwargs["mode"] == "demo":
#             from tarot_jupyterlab.ai.provider import FakeAIProvider
#             return FakeAIProvider()
#         return OpenAICompatibleProvider(
#             base_url=kwargs["base_url"],
#             model=kwargs["model"],
#             api_key=kwargs["api_key"],
#             auth_mode=kwargs["auth_mode"],
#             timeout_seconds=kwargs["timeout_seconds"],
#         )
#
#     def _generate(self, session, language: str):
#         snapshot = self._ai_store.provider_kwargs()   # snapshot; later edits do not affect this run
#         provider = self._provider(snapshot)
#         deadline = snapshot["timeout_seconds"] + 5
#         ...
