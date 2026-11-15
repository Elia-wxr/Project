"""Helpers shared by the Tarot sidebar browser tests."""

from __future__ import annotations

from playwright.sync_api import Page


def set_theme(page: Page, theme: str) -> None:
    """Switch the JupyterLab theme through the Settings menu."""
    page.get_by_role("menuitem", name="Settings").click()
    page.wait_for_timeout(300)
    page.locator(".lm-Menu-item", has_text="Theme").first.hover()
    page.wait_for_timeout(400)
    page.locator(".lm-Menu-item", has_text=theme).first.click()
    page.wait_for_timeout(800)


def set_sidebar_width(page: Page, target: int) -> None:
    """Resize the left area through its splitter so Lumino re-lays out."""
    box = page.locator("#jp-left-stack").bounding_box()
    assert box is not None
    delta = target - box["width"]
    if abs(delta) < 2:
        return
    handle_x = box["x"] + box["width"] + 1
    page.mouse.move(handle_x, 400)
    page.mouse.down()
    page.mouse.move(handle_x + delta, 400, steps=12)
    page.mouse.up()
    page.wait_for_timeout(500)


def overflow(page: Page) -> tuple[int, int]:
    """Return (scrollWidth, clientWidth) of the sidebar panel."""
    return page.eval_on_selector(
        "#tarot-jupyterlab-sidebar",
        "element => [element.scrollWidth, element.clientWidth]",
    )


def draw_card(page: Page, question: str = "What should I reflect on?") -> None:
    page.fill("#jp-tarot-question", question)
    page.click('[data-action="draw"]')
    page.wait_for_selector(".jp-TarotSidebar-cardName", timeout=30_000)
