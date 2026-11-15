"""Main-flow browser tests for the Tarot sidebar (task A-04 skeleton).

These tests only use the public UI: they never call the HTTP API directly, so
they break when the panel loses functionality a user depends on.
"""

from __future__ import annotations

import os
import re

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.helpers import draw_card, overflow, set_sidebar_width, set_theme

SIDEBAR = "#tarot-jupyterlab-sidebar"
STATUS = '[data-region="status"]'
CURRENT = '[data-region="current"]'
HISTORY = '[data-region="history"]'


def test_empty_state_and_disabled_actions(page: Page) -> None:
    expect(page.locator(CURRENT)).to_contain_text("No card drawn yet")
    expect(page.locator(HISTORY)).to_contain_text("View latest")
    expect(page.locator('[data-action="read"]')).to_be_disabled()
    expect(page.locator('[data-action="save"]')).to_be_disabled()
    expect(page.locator('[data-action="draw"]')).to_be_enabled()


def test_draw_shows_card_orientation_keywords_and_unsaved_state(page: Page) -> None:
    draw_card(page)

    card = page.locator(f"{CURRENT} .jp-TarotSidebar-cardName")
    expect(card).to_be_visible()
    expect(page.locator(f"{CURRENT} .jp-TarotSidebar-badge").first).to_have_text(
        re.compile("Upright|Reversed")
    )
    expect(page.locator(f"{CURRENT} .jp-TarotSidebar-keywords > li").first).to_be_visible()
    expect(page.locator(f"{CURRENT} .jp-TarotSidebar-state")).to_have_text("Unsaved")
    expect(page.locator(STATUS)).to_contain_text("Card drawn")
    expect(page.locator('[data-action="read"]')).to_be_enabled()
    expect(page.locator('[data-action="save"]')).to_be_enabled()


def test_keyboard_only_draw(page: Page) -> None:
    page.focus("#jp-tarot-question")
    page.keyboard.type("Keyboard question")
    page.keyboard.press("Tab")
    assert page.evaluate(
        "() => document.activeElement?.getAttribute('data-action')"
    ) == "draw"
    assert page.evaluate(
        "() => document.activeElement?.matches(':focus-visible')"
    )
    page.keyboard.press("Enter")

    expect(page.locator(f"{CURRENT} .jp-TarotSidebar-cardName")).to_be_visible()
    expect(page.locator(f"{CURRENT} .jp-TarotSidebar-state")).to_have_text("Unsaved")


def test_repeated_clicks_keep_one_card_and_recover(page: Page) -> None:
    page.fill("#jp-tarot-question", "What should I reflect on?")
    # Fire two clicks in the same task: the busy guard must ignore the second.
    page.eval_on_selector(
        '[data-action="draw"]',
        "button => { button.click(); button.click(); }",
    )
    page.wait_for_selector(f"{CURRENT} .jp-TarotSidebar-cardName", timeout=30_000)
    page.wait_for_timeout(500)

    expect(page.locator(f"{CURRENT} .jp-TarotSidebar-cardName")).to_have_count(1)
    expect(page.locator(STATUS)).not_to_contain_text("Error")
    expect(page.locator(SIDEBAR)).to_have_attribute("aria-busy", "false")
    expect(page.locator('[data-action="draw"]')).to_be_enabled()


def test_themes_and_narrow_widths_do_not_overflow(page: Page) -> None:
    draw_card(page)
    panel = page.locator(SIDEBAR)

    for theme, is_light in (("JupyterLab Light", "true"), ("JupyterLab Dark", "false")):
        set_theme(page, theme)
        assert page.eval_on_selector(
            "body", "body => body.getAttribute('data-jp-theme-light')"
        ) == is_light
        # 240px is the effective content width of 480px at 200% zoom.
        for width in (480, 320, 240):
            set_sidebar_width(page, width)
            scroll, client = overflow(page)
            assert scroll <= client, f"{theme} at {width}px overflows: {scroll} > {client}"
            expect(panel.locator(".jp-TarotSidebar-title")).to_be_visible()
            expect(panel.locator(".jp-TarotSidebar-actions")).to_be_visible()


def test_save_then_view_latest(page: Page) -> None:
    page.on("dialog", lambda dialog: dialog.accept())
    draw_card(page, "Save this record")

    page.click('[data-action="save"]')
    expect(page.locator(STATUS)).to_have_text("Saved.")
    expect(page.locator(f"{CURRENT} .jp-TarotSidebar-state")).to_have_text("Saved")

    page.click('[data-action="latest"]')
    expect(page.locator(f"{HISTORY} .jp-TarotSidebar-cardName")).to_be_visible()
    expect(page.locator(f"{HISTORY} .jp-TarotSidebar-state")).to_have_text("Saved")


@pytest.mark.skipif(
    os.environ.get("TAROT_E2E_DEMO") != "1",
    reason="needs a server started with TAROT_DEMO_MODE=1",
)
def test_demo_reading_is_marked_and_keeps_the_card(page: Page) -> None:
    draw_card(page)
    page.click('[data-action="read"]')
    page.wait_for_selector(".jp-TarotSidebar-reading", timeout=60_000)

    expect(page.locator(f"{CURRENT} .jp-TarotSidebar-badge", has_text="Demo reading")).to_be_visible()
    expect(page.locator(".jp-TarotSidebar-readingLabel").first).to_have_text("Summary")
    expect(page.locator('[data-action="read"]')).to_be_disabled()
    expect(page.locator(f"{CURRENT} .jp-TarotSidebar-cardName")).to_be_visible()


@pytest.mark.skipif(
    os.environ.get("TAROT_E2E_NO_AI") != "1",
    reason="needs a server without a configured AI connection",
)
def test_missing_ai_keeps_the_card_and_allows_retry(page: Page) -> None:
    draw_card(page)
    page.click('[data-action="read"]')

    status = page.locator(STATUS)
    expect(status).to_contain_text("No AI server is configured", timeout=30_000)
    expect(status).to_have_attribute("data-tone", "error")
    expect(page.locator(f"{CURRENT} .jp-TarotSidebar-cardName")).to_be_visible()
    expect(page.locator('[data-action="read"]')).to_be_enabled()
    expect(page.locator('[data-action="save"]')).to_be_enabled()


def test_ai_settings_tab_round_trip(page: Page) -> None:
    page.click('[data-tab="settings"]')
    panel = page.locator(".jp-TarotSettingsPanel")
    expect(panel).to_be_visible()
    expect(panel.locator("h2").first).to_have_text("AI connection")
    # The key input never shows a stored value.
    expect(panel.locator('input[name="api_key"]')).to_have_value("")

    page.click('[data-tab="reading"]')
    expect(page.locator('[data-view="reading"]')).to_be_visible()
    expect(page.locator("#jp-tarot-question")).to_be_visible()


def test_tab_keyboard_arrows(page: Page) -> None:
    page.focus('[data-tab="reading"]')
    page.keyboard.press("ArrowRight")
    expect(page.locator('[data-tab="settings"]')).to_have_attribute("aria-selected", "true")
    page.keyboard.press("ArrowLeft")
    expect(page.locator('[data-tab="reading"]')).to_have_attribute("aria-selected", "true")
