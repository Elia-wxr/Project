"""Shared exception hierarchy for the Tarot JupyterLab plugin.

Public functions succeed with their declared return values and raise one of
the exceptions below on failure.  The HTTP layer maps these exceptions onto
stable error codes; modules must not invent ad-hoc exceptions or mixed
return values.
"""

from __future__ import annotations

__all__ = [
    "AIProviderError",
    "AIRateLimitedError",
    "AITimeoutError",
    "AIUnavailableError",
    "CardNotFoundError",
    "DuplicateSessionError",
    "HistoryNotFoundError",
    "InvalidCardSetError",
    "InvalidSessionError",
    "ReadingInProgressError",
    "RecordValidationError",
    "SessionConflictError",
    "SessionNotFoundError",
    "SessionRevisionConflictError",
    "StaleReadingError",
    "StorageError",
    "ConfigConflictError",
    "InvalidConfigError",
    "TarotError",
]


class TarotError(Exception):
    """Base exception for expected application errors."""


class CardNotFoundError(TarotError):
    """Raised when a card name is not present in the loaded card library."""


class InvalidCardSetError(TarotError):
    """Raised when the card library fails count, name or field validation."""


class InvalidSessionError(TarotError):
    """Raised when a session violates business rules (question, spread, etc.)."""


class RecordValidationError(TarotError):
    """Raised when a session record fails structure or linkage validation."""


class SessionNotFoundError(TarotError):
    """Raised when an active session ID is not registered in the facade."""


class HistoryNotFoundError(TarotError):
    """Raised when a saved history record does not exist on disk."""


class SessionConflictError(TarotError):
    """Base class for concurrent or conflicting session state changes."""


class SessionRevisionConflictError(SessionConflictError):
    """Raised when an operation expects a different session revision."""


class ReadingInProgressError(SessionConflictError):
    """Raised when a second reading request or save hits a generating session."""


class StaleReadingError(SessionConflictError):
    """Raised when a late AI result arrives for a superseded revision."""


class DuplicateSessionError(SessionConflictError):
    """Raised when importing a record whose ID already exists."""


class StorageError(TarotError):
    """Raised when history persistence fails or a saved file is corrupt."""


class AIProviderError(TarotError):
    """Raised for expected AI provider failures."""


class AIUnavailableError(AIProviderError):
    """Raised when no AI provider is configured or it cannot be reached."""


class AIRateLimitedError(AIProviderError):
    """Raised when the configured AI server rate-limits a request.

    The HTTP layer maps this to ``503 AI_RATE_LIMITED``.
    """


class AITimeoutError(AIProviderError):
    """Raised when an AI request exceeds its time budget."""
class ConfigConflictError(TarotError):
    """Raised when config revision conflicts."""
    pass


class InvalidConfigError(TarotError):
    """Raised when config data is invalid."""
    def __init__(self, message: str, field: str = ""):
        super().__init__(message)
        self.field = field
# PASTE TARGET: src/tarot_jupyterlab/errors.py  (append to the end of the file)
#
# Do NOT paste the `from __future__ import annotations` line: errors.py almost
# certainly already has it at the top, and a second one mid-file is a SyntaxError.
# If your errors.py already defines TarotError, delete that class here and let the
# new classes inherit from the existing base instead.


class InvalidConfigError(TarotError):
    """400 INVALID_REQUEST: an invalid field; the user must be told which one."""

    code = "INVALID_REQUEST"
    status_code = 400

    def __init__(self, field: str, message: str) -> None:
        super().__init__(message)
        self.field = field

    def to_dict(self) -> dict:
        return {"error": {"code": self.code, "message": self.message, "field": self.field}}


class ConfigConflictError(TarotError):
    """409 CONFIG_CONFLICT: the config_revision is stale."""

    code = "CONFIG_CONFLICT"
    status_code = 409


class AIConfigBusyError(TarotError):
    """409 READING_IN_PROGRESS: a reading or test is running; the effective config is locked."""

    code = "READING_IN_PROGRESS"
    status_code = 409


# If errors.py has no TarotError yet, append this base class as well and put the
# three classes above *after* it:
#
# class TarotError(Exception):
#     code = "INTERNAL_ERROR"
#     status_code = 500
#
#     def __init__(self, message: str) -> None:
#         super().__init__(message)
#         self.message = message
#
#     def to_dict(self) -> dict:
#         return {"error": {"code": self.code, "message": self.message}}
