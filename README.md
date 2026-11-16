# Tarot JupyterLab

[![JupyterLab 4](https://img.shields.io/badge/JupyterLab-4-orange)](https://jupyter.org/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Tarot JupyterLab is an English-language JupyterLab sidebar extension for drawing a tarot card, optionally generating an AI interpretation, and saving the latest reading. Readings are intended for entertainment and self-reflection only.

## Introduction / Feature Overview

- **Single-card draw:** Submit a reflection question and draw one card from the bundled 78-card deck. The sidebar displays the card, upright or reversed orientation, and corresponding keywords.
- **AI readings:** Request a reading from an OpenAI-compatible Chat Completions service. The result includes a summary, card interpretation, and advice. AI is optional; drawing and saving cards remain available without it.
- **Latest-reading history:** Save the current card and any generated reading as the latest record, then view it later. Saving replaces the previous latest record.
- **Dedicated AI settings panel:** Configure the server, model, authentication, API key, and timeout in the sidebar. Test a connection before saving settings.
- **JupyterLab-native interface:** Use the Reading and AI settings tabs, with keyboard-accessible controls and light/dark theme support.

## Installation

The extension requires Python 3.10 or later and JupyterLab 4. Install from a local checkout in a virtual environment:

```bash
git clone https://github.com/Elia-wxr/jupyterlab-tarot-card.git
cd jupyterlab-tarot-card
python -m venv .venv
```

Activate the virtual environment, then install JupyterLab and the extension:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
# .venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install "jupyterlab>=4,<5" .
```

Start JupyterLab:

```bash
jupyter lab
```

To install a built wheel instead, install JupyterLab 4 in the target environment and run `python -m pip install <path-to-wheel.whl>`.

## Usage

1. Start JupyterLab and select the **Tarot** icon in the left activity bar.
2. In **Reading**, enter a question (1–2,000 characters) and select **Draw a card**.
3. Review the card, orientation, and keywords. Select **Generate reading** if AI is enabled and configured.
4. Select **Save as latest** to save the current card and reading. Confirming the action replaces the previous saved record.
5. Select **View latest** to load the most recently saved record.
6. To configure AI, open **AI settings** in the sidebar. See [AI Configuration](#ai-configuration).

The latest saved record is stored by the Jupyter Server under its data directory at `tarot-jupyterlab/latest.json`. AI configuration is stored separately in the Jupyter configuration directory; API keys are not written to that file.

## Screenshots

Screenshots are maintained under `docs/screenshot/`.

<!-- Add current screenshots here, for example: ![Tarot sidebar](docs/screenshot/tarot-sidebar.png) -->

> **Screenshot update required:** The AI settings UI has been updated. Reinstall the project to load the latest extension, then recapture and add new screenshots of the current AI settings panel under `docs/screenshot/`.

## Configuration

The extension works without AI configuration: users can draw cards and save or view the latest record. The **Configuration** section covers server-level options; AI-specific setup and security details are in the dedicated [AI Configuration](#ai-configuration) section below.

### Server environment variables

Set environment variables in the environment used to launch JupyterLab. An environment value takes precedence over the saved value and locks the corresponding setting in the UI.

| Variable | Description |
| --- | --- |
| `TAROT_AI_ENABLED` | Enables or disables AI readings. Accepted true values are `1`, `true`, `yes`, and `on`; false values are `0`, `false`, `no`, and `off`. |
| `TAROT_AI_BASE_URL` | Base URL for the OpenAI-compatible service. Use the API base URL, such as `https://api.openai.com/v1`, not the `/chat/completions` endpoint. |
| `TAROT_AI_MODEL` | Model identifier to send to the service. |
| `TAROT_AI_AUTH_MODE` | Authentication mode: `bearer` or `none`. Defaults to Bearer authentication. |
| `TAROT_AI_API_KEY` | Bearer key. For safety, an environment-provided key is used only when `TAROT_AI_BASE_URL` is also set. |
| `TAROT_AI_TIMEOUT_SECONDS` | Request timeout in seconds; valid values are from 5 to 120. Defaults to 30. |

### AI Configuration

AI settings can be managed in the **AI settings** tab in the Tarot sidebar or supplied through the server environment variables above.

In the settings panel:

1. Enable **Enable AI readings**.
2. Enter the service **Base URL** and **Model**.
3. Select **Bearer API key** or **No authentication**. For Bearer authentication, enter the API key.
4. Set the request timeout if needed (5–120 seconds; default 30).
5. Select **Test connection** to send a short synthetic prompt, then select **Save configuration**.

Saving settings does not test the service. A connection test does not save the draft configuration and may incur API charges. The Base URL must be reachable from the machine running the Jupyter Server; `127.0.0.1` refers to that server machine, not necessarily the computer running the browser. Remote services must use HTTPS; HTTP is supported only for loopback addresses.

API keys entered in the UI are held in server memory until the server restarts and are not stored in the browser or written to disk. Environment variables can provide a key for a server-managed deployment. The UI never returns an existing key. Your question and card details are sent to the configured AI server only when you request a real reading; a connection test sends a synthetic prompt instead.

## License

This project is distributed under the [MIT License](LICENSE).
