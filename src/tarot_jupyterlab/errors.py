"""Shared exception hierarchy for the Tarot JupyterLab plugin.

Public functions succeed with their declared return values and raise one of
the exceptions below on failure.  The HTTP layer maps these exceptions onto
stable error codes; modules must not invent ad-hoc exceptions or mixed
return values.
"""

from __future__ import annotations

__all__ = [
    "AIProviderError",
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


class AITimeoutError(AIProviderError):
    """Raised when an AI request exceeds its time budget."""
