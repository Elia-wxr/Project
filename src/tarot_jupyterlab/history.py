"""Serialize records and store the most recent saved reading."""

from __future__ import annotations

import json
from contextlib import suppress
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from tarot_jupyterlab.errors import StorageError
from tarot_jupyterlab.models import SESSION_SCHEMA_VERSION, SessionRecord


def record_to_dict(record: SessionRecord) -> dict[str, Any]:
    """Convert one record to the JSON shape shared by the API and disk."""
    session = asdict(record.session)
    session["created_at"] = record.session.created_at.isoformat()
    session["updated_at"] = record.session.updated_at.isoformat()
    for drawn in session["cards"]:
        card = drawn["card"]
        card["upright"] = list(card["upright"])
        card["reversed"] = list(card["reversed"])

    reading = None
    if record.reading is not None:
        reading = asdict(record.reading)
        reading["created_at"] = record.reading.created_at.isoformat()
        reading["card_interpretations"] = list(record.reading.card_interpretations)
    return {"schema_version": record.schema_version, "session": session, "reading": reading}


def save_latest(record: SessionRecord, path: Path) -> None:
    """Replace the previous file only after the complete new JSON is written."""
    payload = record_to_dict(record)
    _validate_snapshot(payload)
    temporary_path = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=".latest-", delete=False
        ) as file:
            temporary_path = Path(file.name)
            json.dump(payload, file, ensure_ascii=False, indent=2)
        temporary_path.replace(path)
    except OSError as exc:
        raise StorageError("Could not save the reading. The previous file was preserved.") from exc
    finally:
        if temporary_path is not None:
            with suppress(OSError):
                temporary_path.unlink(missing_ok=True)


def load_latest(path: Path) -> dict[str, Any] | None:
    """Load the snapshot for display, or return None when no file exists."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as exc:
        raise StorageError("The saved reading could not be opened.") from exc
    _validate_snapshot(payload)
    return payload


def _validate_snapshot(payload: dict[str, Any]) -> None:
    """Check the fields the sidebar needs and the reading-to-session link."""
    try:
        if type(payload["schema_version"]) is not int or (
            payload["schema_version"] != SESSION_SCHEMA_VERSION
        ):
            raise ValueError("Unsupported record version.")
        session = payload["session"]
        if (
            not isinstance(session["session_id"], str)
            or not isinstance(session["question"], str)
            or session["spread_name"] != "single"
            or type(session["revision"]) is not int
            or session["revision"] != 1
            or session["allow_repeats"] is not False
            or not isinstance(session["cards"], list)
            or len(session["cards"]) != 1
        ):
            raise ValueError("Expected a single-card session.")
        _check_timestamp(session["created_at"])
        _check_timestamp(session["updated_at"])
        drawn = session["cards"][0]
        card = drawn["card"]
        if (
            drawn["position"] != "focus"
            or drawn["orientation"] not in ("upright", "reversed")
            or not isinstance(card["name"], str)
            or not _is_text_list(card["upright"])
            or not _is_text_list(card["reversed"])
        ):
            raise ValueError("Invalid card snapshot.")
        reading = payload["reading"]
        if reading is not None:
            if (
                reading["session_id"] != session["session_id"]
                or type(reading["session_revision"]) is not int
                or reading["session_revision"] != session["revision"]
                or not _is_text_list(reading["card_interpretations"])
                or len(reading["card_interpretations"]) != 1
                or not all(
                    isinstance(reading[field], str) for field in ("summary", "advice", "provider")
                )
            ):
                raise ValueError("The reading does not match the session.")
            _check_timestamp(reading["created_at"])
    except (KeyError, TypeError, ValueError) as exc:
        raise StorageError("The saved reading has an invalid format.") from exc


def _check_timestamp(value: str) -> None:
    if datetime.fromisoformat(value).utcoffset() is None:
        raise ValueError("Expected a timestamp with a time zone.")


def _is_text_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)
