"""Browser E2E suite for the Tarot sidebar (optional, needs a live server).

Run it against a JupyterLab that has the extension installed:

    TAROT_E2E_BASE_URL=http://127.0.0.1:8888 TAROT_E2E_TOKEN=<token> \\
        python -m pytest tests/e2e -q

Add ``TAROT_E2E_DEMO=1`` for a server started with ``TAROT_DEMO_MODE=1`` and
``TAROT_E2E_NO_AI=1`` for a server without a configured AI connection.

Without ``TAROT_E2E_BASE_URL`` every test skips, so the default
``python -m pytest`` run stays offline and fast.  Playwright is an optional
dependency of this suite (``python -m pip install playwright`` and
``playwright install chromium``).
"""

from __future__ import annotations

import os

import pytest

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import Browser, Page, sync_playwright

BASE_URL = os.environ.get("TAROT_E2E_BASE_URL", "")
TOKEN = os.environ.get("TAROT_E2E_TOKEN", "")


@pytest.fixture(scope="session")
def browser() -> Browser:
    if not BASE_URL:
        pytest.skip("set TAROT_E2E_BASE_URL to run the browser E2E suite")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture
def page(browser: Browser) -> Page:
    context = browser.new_context(viewport={"width": 1600, "height": 900})
    page = context.new_page()
    page.goto(f"{BASE_URL}/lab?token={TOKEN}", wait_until="domcontentloaded")
    page.wait_for_selector("#jp-main-dock-panel", timeout=120_000)
    page.wait_for_timeout(2000)
    # The activity-bar tab has no text label; it must be reachable by name.
    page.get_by_role("tab", name="Tarot").first.click()
    page.wait_for_selector("#tarot-jupyterlab-sidebar", state="visible", timeout=30_000)
    yield page
    context.close()
