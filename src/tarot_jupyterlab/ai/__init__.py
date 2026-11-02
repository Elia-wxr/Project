"""AI interpretation module for the Tarot JupyterLab plugin.

The module only interprets already-drawn cards: it never draws cards,
never generates random numbers and never writes history.  It consumes an
isolated ``Session`` snapshot and returns a validated :class:`Reading`.
"""

from __future__ import annotations

from tarot_jupyterlab.ai.interpreter import generate_reading
from tarot_jupyterlab.ai.prompts import build_reading_prompt
from tarot_jupyterlab.ai.provider import AIProvider, FakeAIProvider, SocratesProvider

__all__ = [
    "AIProvider",
    "FakeAIProvider",
    "SocratesProvider",
    "build_reading_prompt",
    "generate_reading",
]
