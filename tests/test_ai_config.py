"""Regression tests for Member D's configuration layer. Target location: tests/test_ai_config.py

Run: python -m pytest tests/test_ai_config.py -q
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from tarot_jupyterlab.ai.config import (
    AIConfigStore,
    AISettings,
    InvalidConfigError,
    normalize_base_url,
)
from tarot_jupyterlab.errors import ConfigConflictError, StorageError

BASE = "https://api.example.test/v1"


def make_store(tmp_path: Path, environ: dict[str, str] | None = None, **kwargs) -> AIConfigStore:
    return AIConfigStore(tmp_path / "ai-config.json", environ=environ or {}, **kwargs)


# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
def test_fresh_store_is_not_configured_and_leaks_nothing(tmp_path):
    store = make_store(tmp_path)
    snapshot = store.snapshot()

    assert snapshot["status"] == "not_configured"
    assert snapshot["key_present"] is False
    assert snapshot["key_source"] == "none"
    assert snapshot["locked_fields"] == []
    assert snapshot["settings"]["mode"] == "real"
    assert snapshot["settings"]["timeout_seconds"] == 30
    assert "api_key" not in json.dumps(snapshot)


def test_status_becomes_configured_with_model_and_key(tmp_path):
    store = make_store(tmp_path)
    snapshot = store.update(
        config_revision=1,
        settings={"base_url": BASE, "model": "gpt-4o-mini"},
        api_key="sk-test-value",
    )

    assert snapshot["status"] == "configured"
    assert snapshot["key_present"] is True
    assert snapshot["key_source"] == "runtime"
    assert snapshot["config_revision"] == 2


def test_demo_mode_status_and_no_key_needed(tmp_path):
    store = make_store(tmp_path)
    snapshot = store.update(config_revision=1, settings={"mode": "demo"})
    assert snapshot["status"] == "demo"


# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
def test_non_sensitive_settings_survive_restart_but_key_does_not(tmp_path):
    path = tmp_path / "ai-config.json"
    store = AIConfigStore(path, environ={})
    store.update(
        config_revision=1,
        settings={"base_url": BASE, "model": "m", "timeout_seconds": 45},
        api_key="sk-secret",
    )

    text = path.read_text(encoding="utf-8")
    assert "sk-secret" not in text
    assert "api_key" not in text

    reloaded = AIConfigStore(path, environ={})
    snapshot = reloaded.snapshot()
    assert snapshot["settings"]["model"] == "m"
    assert snapshot["settings"]["timeout_seconds"] == 45
    assert snapshot["key_present"] is False
    assert snapshot["config_revision"] == 2


def test_corrupt_file_raises_storage_error(tmp_path):
    path = tmp_path / "ai-config.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(StorageError):
        AIConfigStore(path, environ={})


def test_write_failure_keeps_old_config_and_key(tmp_path, monkeypatch):
    store = make_store(tmp_path)
    store.update(config_revision=1, settings={"model": "first"}, api_key="sk-keep")

    def boom(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(StorageError):
        store.update(config_revision=2, settings={"model": "second"}, api_key="sk-new")

    snapshot = store.snapshot()
    assert snapshot["config_revision"] == 2
    assert snapshot["settings"]["model"] == "first"
    assert store.api_key() == "sk-keep"


# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
def test_stale_revision_is_rejected_for_save_and_test(tmp_path):
    store = make_store(tmp_path)
    store.update(config_revision=1, settings={"model": "m"})

    with pytest.raises(ConfigConflictError):
        store.update(config_revision=1, settings={"model": "n"})
    with pytest.raises(ConfigConflictError):
        store.draft(config_revision=1, settings={"model": "n"})


def test_draft_does_not_persist(tmp_path):
    path = tmp_path / "ai-config.json"
    store = AIConfigStore(path, environ={})
    draft, key = store.draft(config_revision=1, settings={"model": "draft-model"}, api_key="sk-x")

    assert draft.model == "draft-model"
    assert key == "sk-x"
    assert not path.exists()
    assert store.revision == 1
    assert store.effective().model == ""


# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("timeout", [4, 121, "30", True, float("nan")])
def test_invalid_timeout_is_rejected(tmp_path, timeout):
    store = make_store(tmp_path)
    with pytest.raises(InvalidConfigError) as excinfo:
        store.update(config_revision=1, settings={"timeout_seconds": timeout})
    assert excinfo.value.field == "timeout_seconds"


def test_unknown_field_is_rejected(tmp_path):
    store = make_store(tmp_path)
    with pytest.raises(InvalidConfigError):
        store.update(config_revision=1, settings={"api_key": "oops"})


@pytest.mark.parametrize(
    "url",
    [
        "ftp://api.example.test/v1",
        "https://api.example.test/v1?x=1",
        "https://user:pw@api.example.test/v1",
        "https://api.example.test/v1#frag",
        "https://api.example.test/v1/chat/completions",
        "http://api.example.test/v1",
        "http://169.254.169.254/latest/meta-data",
    ],
)
def test_unsafe_base_urls_are_rejected(url):
    with pytest.raises(InvalidConfigError):
        normalize_base_url(url)


def test_base_url_is_canonicalized_and_subpath_kept():
    assert normalize_base_url("https://API.example.test/v1/") == "https://api.example.test/v1"
    assert (
        normalize_base_url("https://gw.example.test/openai/v1")
        == "https://gw.example.test/openai/v1"
    )
    assert normalize_base_url("http://127.0.0.1:8000/v1") == "http://127.0.0.1:8000/v1"


def test_resolved_target_is_checked(tmp_path):

    with pytest.raises(InvalidConfigError):
        normalize_base_url("https://evil.example.test/v1", resolver=lambda host: ["10.0.0.5"])


# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
def test_env_overrides_are_locked(tmp_path):
    store = make_store(
        tmp_path,
        environ={"TAROT_AI_BASE_URL": "https://env.example.test/v1", "TAROT_AI_MODEL": "env-model"},
    )
    snapshot = store.snapshot()
    assert snapshot["settings"]["base_url"] == "https://env.example.test/v1"
    assert set(snapshot["locked_fields"]) == {"base_url", "model"}

    with pytest.raises(InvalidConfigError):
        store.update(config_revision=1, settings={"model": "user-model"})

    store.update(config_revision=1, settings={"model": "env-model", "auth_mode": "bearer"})


def test_env_key_requires_env_base_url(tmp_path):
    store = make_store(tmp_path, environ={"TAROT_AI_API_KEY": "sk-env"})
    assert store.key_source() == "none"

    paired = make_store(
        tmp_path / "paired",
        environ={
            "TAROT_AI_API_KEY": "sk-env",
            "TAROT_AI_BASE_URL": "https://env.example.test/v1",
        },
    )
    assert paired.key_source() == "environment"
    assert paired.api_key() == "sk-env"


# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
def test_changing_base_url_drops_runtime_key(tmp_path):
    store = make_store(tmp_path)
    store.update(config_revision=1, settings={"base_url": BASE}, api_key="sk-bound")
    assert store.key_source() == "runtime"

    snapshot = store.update(
        config_revision=2, settings={"base_url": "https://other.example.test/v1"}
    )
    assert snapshot["key_present"] is False
    assert snapshot["key_source"] == "none"


def test_clear_key_and_illegal_key_combinations(tmp_path):
    store = make_store(tmp_path)
    store.update(config_revision=1, settings={"model": "m"}, api_key="sk-1")

    cleared = store.update(config_revision=2, clear_api_key=True)
    assert cleared["key_present"] is False

    with pytest.raises(InvalidConfigError):
        store.update(config_revision=3, api_key="sk-2", clear_api_key=True)
    with pytest.raises(InvalidConfigError):
        store.update(config_revision=3, api_key="   ")


def test_settings_object_serializes_timeout_as_number():
    assert AISettings(timeout_seconds=30.0).to_dict()["timeout_seconds"] == 30
