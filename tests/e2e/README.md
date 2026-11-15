# Tarot sidebar browser tests (task A-04)

Playwright tests for the main sidebar flow. They drive the real JupyterLab UI —
nothing calls the HTTP API directly — and they are the place where task B-01
adds AI-settings scenarios (same fixtures, same server).

The suite is skipped by default so `python -m pytest` stays offline and fast.
It runs only when `TAROT_E2E_BASE_URL` points at a live JupyterLab with this
extension installed.

## Setup

```bash
python -m pip install playwright
playwright install chromium
```

## Run against a server without AI credentials

```bash
# terminal 1
jupyter lab --no-browser --IdentityProvider.token=devtoken --port=8899

# terminal 2
TAROT_E2E_BASE_URL=http://127.0.0.1:8899 \
TAROT_E2E_TOKEN=devtoken \
TAROT_E2E_NO_AI=1 \
python -m pytest tests/e2e -q
```

## Run against an explicit Demo-mode server

```bash
TAROT_DEMO_MODE=1 jupyter lab --no-browser --IdentityProvider.token=devtoken --port=8901

TAROT_E2E_BASE_URL=http://127.0.0.1:8901 \
TAROT_E2E_TOKEN=devtoken \
TAROT_E2E_DEMO=1 \
python -m pytest tests/e2e -q
```

## Coverage

| Test | What it proves |
| --- | --- |
| `test_empty_state_and_disabled_actions` | First-run state: empty card and history regions, read/save disabled, draw enabled. |
| `test_draw_shows_card_orientation_keywords_and_unsaved_state` | Draw renders name, orientation badge, keyword chips and the `Unsaved` state. |
| `test_keyboard_only_draw` | Tab from the question reaches the draw button and Enter draws. |
| `test_repeated_clicks_keep_one_card_and_recover` | Double click does not double-draw; `aria-busy` and disabled state recover. |
| `test_themes_and_narrow_widths_do_not_overflow` | Light/dark themes at 480 px and 320 px without horizontal overflow. |
| `test_save_then_view_latest` | Save confirmation, `Saved` state, and the read-only latest record. |
| `test_demo_reading_is_marked_and_keeps_the_card` | Demo mode shows the simulated marker and keeps the card. |
| `test_missing_ai_keeps_the_card_and_allows_retry` | Missing AI keeps the card and re-enables read/save. |
| `test_ai_settings_tab_round_trip` | The AI settings tab opens B's panel, shows no stored key, and returns to Reading. |
| `test_tab_keyboard_arrows` | Left/Right arrows move between the Reading and AI settings tabs. |

## For task B-01

Add a `tests/e2e/test_settings.py` that reuses the `page` fixture from
`conftest.py`: open the `AI settings` entry, exercise validation, save, test
connection and the unsaved-draft prompt. Failures should keep the current card
and must never expose an API key in the DOM.
