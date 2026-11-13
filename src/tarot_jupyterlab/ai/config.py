"""AI configuration: resolution, validation, atomic persistence and key lifecycle.

Drop-in target: ``src/tarot_jupyterlab/ai/config.py``

Resolution order (high -> low):
  1. environment variables (``TAROT_AI_*``)
  2. saved user configuration (``<jupyter config dir>/tarot-jupyterlab/ai-config.json``)
  3. built-in defaults

Only non-sensitive fields are persisted. The API key lives in process memory
(bound to one normalized base URL) or comes from the environment; it is never
written to disk, never returned in a snapshot and never logged.
"""

from __future__ import annotations

import contextlib
import ipaddress
import json
import logging
import os
import tempfile
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from tarot_jupyterlab.errors import (
    ConfigConflictError,
    InvalidConfigError,
    StorageError,
)

LOGGER = logging.getLogger(__name__)

CONFIG_VERSION = 1
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_TIMEOUT_SECONDS = 30.0
MIN_TIMEOUT_SECONDS = 5.0
MAX_TIMEOUT_SECONDS = 120.0
MODES = ("real", "demo")
AUTH_MODES = ("bearer", "none")

ENV_MODE = "TAROT_DEMO_MODE"
ENV_API_KEY = "TAROT_AI_API_KEY"
ENV_FIELDS = {
    "base_url": "TAROT_AI_BASE_URL",
    "model": "TAROT_AI_MODEL",
    "auth_mode": "TAROT_AI_AUTH_MODE",
    "timeout_seconds": "TAROT_AI_TIMEOUT_SECONDS",
}

#: Hosts/IPs that must never be reachable through the configuration page.
_BLOCKED_HOSTS = frozenset(
    {
        "metadata.google.internal",
        "metadata.goog",
        "instance-data",
        "metadata",
    }
)
_BLOCKED_NETWORKS = (
    ipaddress.ip_network("169.254.0.0/16"),  # link-local + cloud metadata
    ipaddress.ip_network("100.100.100.200/32"),  # Alibaba Cloud metadata
    ipaddress.ip_network("fd00:ec2::254/128"),  # AWS IMDSv6
)

Resolver = Callable[[str], list[str]]


# --------------------------------------------------------------------------- #
# settings value object
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class AISettings:
    """Non-sensitive AI configuration. Never holds the API key."""

    mode: str = "real"
    base_url: str = DEFAULT_BASE_URL
    model: str = ""
    auth_mode: str = "bearer"
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS

    def to_dict(self) -> dict[str, Any]:
        timeout = self.timeout_seconds
        return {
            "mode": self.mode,
            "base_url": self.base_url,
            "model": self.model,
            "auth_mode": self.auth_mode,
            "timeout_seconds": int(timeout) if float(timeout).is_integer() else timeout,
        }


SETTINGS_FIELDS = ("mode", "base_url", "model", "auth_mode", "timeout_seconds")


# --------------------------------------------------------------------------- #
# URL boundary
# --------------------------------------------------------------------------- #
def _is_loopback(host: str) -> bool:
    if host == "localhost" or host.endswith(".localhost"):
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _check_literal_host(host: str, field: str, *, allow_loopback: bool = True) -> None:
    lowered = host.lower()
    if lowered in _BLOCKED_HOSTS:
        raise InvalidConfigError(field, "This host is not allowed as an AI server.")
    try:
        address = ipaddress.ip_address(lowered)
    except ValueError:
        return
    if address.is_loopback and allow_loopback:
        return
    for network in _BLOCKED_NETWORKS:
        if address.version == network.version and address in network:
            raise InvalidConfigError(field, "This address is not allowed as an AI server.")
    if (
        address.is_private
        or address.is_link_local
        or address.is_reserved
        or address.is_multicast
        or address.is_unspecified
    ):
        raise InvalidConfigError(field, "This address is not allowed as an AI server.")


def normalize_base_url(raw: Any, *, resolver: Resolver | None = None) -> str:
    """Validate and canonicalize a base URL. Raises ``InvalidConfigError``."""
    field = "base_url"
    if not isinstance(raw, str):
        raise InvalidConfigError(field, "Base URL must be a string.")
    value = raw.strip()
    if not value:
        raise InvalidConfigError(field, "Base URL is required.")

    parts = urlsplit(value)
    if parts.scheme not in ("http", "https"):
        raise InvalidConfigError(field, "Base URL must start with http:// or https://.")
    if not parts.hostname:
        raise InvalidConfigError(field, "Base URL must include a host name.")
    if parts.username is not None or parts.password is not None:
        raise InvalidConfigError(field, "Base URL must not contain a user name or password.")
    if parts.query or parts.fragment:
        raise InvalidConfigError(field, "Base URL must not contain a query string or fragment.")
    try:
        port = parts.port
    except ValueError as exc:
        raise InvalidConfigError(field, "Base URL contains an invalid port.") from exc

    path = parts.path.rstrip("/")
    if path.endswith("/chat/completions"):
        raise InvalidConfigError(
            field,
            "Enter the API base URL (for example https://api.openai.com/v1), "
            "not the full /chat/completions endpoint.",
        )

    host = parts.hostname
    _check_literal_host(host, field)
    if parts.scheme == "http" and not _is_loopback(host):
        raise InvalidConfigError(
            field,
            "Plain http:// is only allowed for a loopback address; use https:// for remote servers.",
        )

    if resolver is not None and parts.scheme == "https":
        try:
            addresses = resolver(host) or []
        except OSError as exc:
            raise InvalidConfigError(field, "Base URL host could not be resolved.") from exc
        for address in addresses:
            _check_literal_host(address, field)

    netloc_host = f"[{host}]" if ":" in host else host
    default_port = 443 if parts.scheme == "https" else 80
    netloc = netloc_host if port in (None, default_port) else f"{netloc_host}:{port}"
    return urlunsplit((parts.scheme, netloc.lower(), path, "", ""))


# --------------------------------------------------------------------------- #
# field validation
# --------------------------------------------------------------------------- #
def _validate_mode(value: Any) -> str:
    if not isinstance(value, str) or value not in MODES:
        raise InvalidConfigError("mode", "Mode must be 'real' or 'demo'.")
    return value


def _validate_model(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise InvalidConfigError("model", "Model must be a string.")
    return value.strip()


def _validate_auth_mode(value: Any) -> str:
    if not isinstance(value, str) or value not in AUTH_MODES:
        raise InvalidConfigError("auth_mode", "Authentication must be 'bearer' or 'none'.")
    return value


def _validate_timeout(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidConfigError("timeout_seconds", "Timeout must be a number of seconds.")
    timeout = float(value)
    if not timeout == timeout or timeout in (float("inf"), float("-inf")):
        raise InvalidConfigError("timeout_seconds", "Timeout must be finite.")
    if timeout < MIN_TIMEOUT_SECONDS or timeout > MAX_TIMEOUT_SECONDS:
        raise InvalidConfigError(
            "timeout_seconds",
            f"Timeout must be between {MIN_TIMEOUT_SECONDS:g} and {MAX_TIMEOUT_SECONDS:g} seconds.",
        )
    return timeout


def settings_from_mapping(
    data: Mapping[str, Any] | None,
    *,
    base: AISettings | None = None,
    resolver: Resolver | None = None,
) -> AISettings:
    """Merge ``data`` onto ``base`` and validate every field."""
    if data is None:
        data = {}
    if not isinstance(data, Mapping):
        raise InvalidConfigError("settings", "Settings must be an object.")
    unknown = sorted(set(data) - set(SETTINGS_FIELDS))
    if unknown:
        raise InvalidConfigError("settings", f"Unknown settings field(s): {', '.join(unknown)}.")

    current = base or AISettings()
    values: dict[str, Any] = {
        "mode": _validate_mode(data.get("mode", current.mode)),
        "base_url": normalize_base_url(data.get("base_url", current.base_url), resolver=resolver),
        "model": _validate_model(data.get("model", current.model)),
        "auth_mode": _validate_auth_mode(data.get("auth_mode", current.auth_mode)),
        "timeout_seconds": _validate_timeout(data.get("timeout_seconds", current.timeout_seconds)),
    }
    return AISettings(**values)


def _same_value(field: str, value: Any, current: AISettings) -> bool:
    try:
        if field == "timeout_seconds":
            return _validate_timeout(value) == current.timeout_seconds
        if field == "base_url":
            return normalize_base_url(value) == current.base_url
        if field == "model":
            return _validate_model(value) == current.model
        if field == "mode":
            return _validate_mode(value) == current.mode
        if field == "auth_mode":
            return _validate_auth_mode(value) == current.auth_mode
    except InvalidConfigError:
        return False
    return False


# --------------------------------------------------------------------------- #
# store
# --------------------------------------------------------------------------- #
class AIConfigStore:
    """Owns the effective AI configuration, its revision and the runtime key."""

    def __init__(
        self,
        config_path: Path,
        *,
        environ: Mapping[str, str] | None = None,
        resolver: Resolver | None = None,
    ) -> None:
        self._path = Path(config_path)
        self._environ = dict(os.environ if environ is None else environ)
        self._resolver = resolver
        self._lock = threading.RLock()
        self._revision = 1
        self._saved = AISettings()
        self._runtime_key: str | None = None
        self._runtime_key_base_url: str | None = None
        self._env_overrides = self._compute_env_overrides()
        self._load()

    # -- ids ---------------------------------------------------------------
    @property
    def path(self) -> Path:
        return self._path

    @property
    def revision(self) -> int:
        with self._lock:
            return self._revision

    # -- persisted config --------------------------------------------------
    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise StorageError(
                "The saved AI configuration could not be read. Fix or remove the file to continue."
            ) from exc
        if not isinstance(payload, dict):
            raise StorageError("The saved AI configuration is not a valid object.")
        try:
            self._saved = settings_from_mapping(
                payload.get("settings", {}), resolver=self._resolver
            )
            revision = payload.get("config_revision", 1)
            self._revision = int(revision) if isinstance(revision, int) else 1
        except InvalidConfigError as exc:
            raise StorageError("The saved AI configuration is invalid.") from exc

    def _write(self, payload: Mapping[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            prefix=".ai-config-", suffix=".json", dir=str(self._path.parent)
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, self._path)
        except OSError as exc:
            with contextlib.suppress(OSError):
                os.unlink(tmp_name)
            raise StorageError("The AI configuration could not be saved.") from exc

    # -- environment -------------------------------------------------------
    def _compute_env_overrides(self) -> dict[str, Any]:
        env = self._environ
        overrides: dict[str, Any] = {}

        mode = env.get(ENV_MODE, "").strip()
        if mode:
            overrides["mode"] = "demo" if mode.lower() in ("1", "true", "yes", "on") else "real"

        base = env.get(ENV_FIELDS["base_url"], "").strip()
        if base:
            try:
                overrides["base_url"] = normalize_base_url(base, resolver=self._resolver)
            except InvalidConfigError:
                LOGGER.warning(
                    "%s is not a valid base URL and was ignored.", ENV_FIELDS["base_url"]
                )

        model = env.get(ENV_FIELDS["model"], "").strip()
        if model:
            overrides["model"] = model

        auth_mode = env.get(ENV_FIELDS["auth_mode"], "").strip().lower()
        if auth_mode in AUTH_MODES:
            overrides["auth_mode"] = auth_mode

        timeout = env.get(ENV_FIELDS["timeout_seconds"], "").strip()
        if timeout:
            try:
                overrides["timeout_seconds"] = _validate_timeout(float(timeout))
            except (ValueError, InvalidConfigError):
                LOGGER.warning(
                    "%s is not a valid timeout and was ignored.", ENV_FIELDS["timeout_seconds"]
                )
        return overrides

    def locked_fields(self) -> list[str]:
        """Fields the server environment controls; the UI must render them read-only."""
        locked: list[str] = []
        if "mode" in self._env_overrides:
            locked.append("mode")
        for field in ENV_FIELDS:
            if field in self._env_overrides:
                locked.append(field)
        return locked

    def effective(self) -> AISettings:
        with self._lock:
            return replace(self._saved, **self._env_overrides)

    # -- key lifecycle -----------------------------------------------------
    def _env_api_key(self) -> str | None:
        # An environment key is only trusted together with an environment base URL,
        # so the credential can never be sent to a user-entered server.
        raw = self._environ.get(ENV_API_KEY, "").strip()
        if not raw or "base_url" not in self._env_overrides:
            return None
        return raw

    def key_source(self) -> str:
        if self._env_api_key():
            return "environment"
        with self._lock:
            if self._runtime_key and self._runtime_key_base_url == self.effective().base_url:
                return "runtime"
        return "none"

    def api_key(self) -> str | None:
        source = self.key_source()
        if source == "environment":
            return self._env_api_key()
        if source == "runtime":
            with self._lock:
                return self._runtime_key
        return None

    def status(self) -> str:
        settings = self.effective()
        if settings.mode == "demo":
            return "demo"
        if not settings.model:
            return "not_configured"
        if settings.auth_mode == "bearer" and not self.api_key():
            return "not_configured"
        return "configured"

    # -- snapshots ---------------------------------------------------------
    def snapshot(self) -> dict[str, Any]:
        """Public, secret-free view for GET/PUT responses."""
        settings = self.effective()
        return {
            "config_revision": self.revision,
            "settings": settings.to_dict(),
            "key_present": self.api_key() is not None,
            "key_source": self.key_source(),
            "locked_fields": self.locked_fields(),
            "status": self.status(),
        }

    def provider_kwargs(self) -> dict[str, Any]:
        """Internal snapshot used to build a provider. Contains the key."""
        settings = self.effective()
        return {
            "mode": settings.mode,
            "base_url": settings.base_url,
            "model": settings.model,
            "auth_mode": settings.auth_mode,
            "timeout_seconds": settings.timeout_seconds,
            "api_key": self.api_key() or "",
        }

    # -- writes ------------------------------------------------------------
    def _check_revision(self, config_revision: Any) -> None:
        if isinstance(config_revision, bool) or not isinstance(config_revision, int):
            raise InvalidConfigError("config_revision", "config_revision must be an integer.")
        if config_revision != self._revision:
            raise ConfigConflictError(
                "The AI configuration changed on the server. Reload it and try again."
            )

    def _drop_locked(self, patch: Mapping[str, Any], current: AISettings) -> dict[str, Any]:
        allowed: dict[str, Any] = {}
        locked = set(self.locked_fields())
        for name, value in patch.items():
            if name in locked:
                if not _same_value(name, value, current):
                    raise InvalidConfigError(
                        name,
                        f"{name} is controlled by the server environment and cannot be changed.",
                    )
                continue
            allowed[name] = value
        return allowed

    def update(
        self,
        *,
        config_revision: Any,
        settings: Mapping[str, Any] | None = None,
        api_key: Any = None,
        clear_api_key: Any = False,
    ) -> dict[str, Any]:
        with self._lock:
            self._check_revision(config_revision)
            if not isinstance(clear_api_key, bool):
                raise InvalidConfigError("clear_api_key", "clear_api_key must be a boolean.")
            if api_key is not None and clear_api_key:
                raise InvalidConfigError("api_key", "Provide api_key or clear_api_key, not both.")
            if api_key is not None and (not isinstance(api_key, str) or not api_key.strip()):
                raise InvalidConfigError(
                    "api_key", "API key must be a non-empty string; use clear_api_key to remove it."
                )

            current = self.effective()
            patch = self._drop_locked(settings or {}, current)
            # Merge onto the *persisted* values: environment overrides must never be
            # written into the user's file as if the user had chosen them.
            candidate = settings_from_mapping(patch, base=self._saved, resolver=self._resolver)

            # Disk first: a failed write must leave the old config and key intact.
            self._write(
                {
                    "config_version": CONFIG_VERSION,
                    "config_revision": self._revision + 1,
                    "settings": candidate.to_dict(),
                }
            )

            self._saved = candidate
            self._revision += 1
            effective_base = self.effective().base_url
            if clear_api_key:
                self._runtime_key = None
                self._runtime_key_base_url = None
            elif api_key is not None:
                self._runtime_key = api_key.strip()
                self._runtime_key_base_url = effective_base
            elif self._runtime_key and self._runtime_key_base_url != effective_base:
                # A key is bound to one server; changing the base URL drops it.
                self._runtime_key = None
                self._runtime_key_base_url = None
            return self.snapshot()

    def draft(
        self,
        *,
        config_revision: Any,
        settings: Mapping[str, Any] | None = None,
        api_key: Any = None,
    ) -> tuple[AISettings, str | None]:
        """Validate an unsaved draft for a connection test. Nothing is persisted."""
        with self._lock:
            self._check_revision(config_revision)
            if api_key is not None and (not isinstance(api_key, str) or not api_key.strip()):
                raise InvalidConfigError("api_key", "API key must be a non-empty string.")
            current = self.effective()
            patch = self._drop_locked(settings or {}, current)
            candidate = settings_from_mapping(patch, base=current, resolver=self._resolver)
            if api_key is not None:
                key: str | None = api_key
            elif candidate.base_url == current.base_url:
                key = self.api_key()
            else:
                key = None
            return candidate, key


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def default_config_path() -> Path:
    """``<jupyter config dir>/tarot-jupyterlab/ai-config.json``."""
    from jupyter_core.paths import jupyter_config_dir

    return Path(jupyter_config_dir()) / "tarot-jupyterlab" / "ai-config.json"


def system_resolver(host: str) -> list[str]:
    """Resolve a host to its addresses so the boundary check sees the real target."""
    import socket

    infos = socket.getaddrinfo(host, None)
    return sorted({info[4][0] for info in infos})
