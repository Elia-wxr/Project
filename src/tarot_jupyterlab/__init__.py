"""Tarot JupyterLab plugin.

A JupyterLab sidebar extension for browsing a 78-card tarot deck,
casting spreads, saving session history and generating AI readings.
"""

from __future__ import annotations

from tarot_jupyterlab._version import __version__

__all__ = ["__version__"]


def _jupyter_server_extension_points() -> list[dict[str, str]]:
    return [{"module": "tarot_jupyterlab.app"}]


def _jupyter_labextension_paths() -> list[dict[str, str]]:
    return [{"src": "labextension", "dest": "tarot-jupyterlab"}]
