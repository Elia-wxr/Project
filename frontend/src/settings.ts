import { Widget } from '@lumino/widgets';

import { TarotClient } from './api';
import {
  buildSaveBody,
  buildTestBody,
  draftFromSnapshot,
  draftStamp,
  isDirty,
  isFieldLocked,
  keyLabel,
  messageForError,
  saveNotice,
  statusLabel,
  urlChangedWithStoredKey,
  validateDraft,
  type SettingsDraft
} from './settings-form';
import type { AiSettingsSnapshot } from './types';

const template = `
  <section class="jp-TarotSettingsPanel-body" aria-label="AI settings">
    <h2>AI connection</h2>
    <p data-settings-region="status">Status: Loading…</p>
    <p class="jp-TarotSettingsPanel-simulated" data-settings-region="simulated" hidden>Demo (simulated). This mode does not contact an AI server.</p>
    <p data-settings-region="banner" role="status" aria-live="polite"></p>
    <form>
      <fieldset data-settings-region="fields">
        <div class="jp-TarotSettingsPanel-choice">
          <span id="tarot-settings-mode-label">Mode</span>
          <label><input type="radio" name="tarot-settings-mode" value="real"> Real API</label>
          <label><input type="radio" name="tarot-settings-mode" value="demo"> Demo (simulated)</label>
        </div>
        <label>Base URL
          <input name="base_url" type="url" autocomplete="off" spellcheck="false" placeholder="https://api.openai.com/v1">
        </label>
        <p class="jp-TarotSettingsPanel-hint" data-settings-region="base-hint">Use the server's API base URL, not /chat/completions. 127.0.0.1 is the Jupyter server machine, not necessarily the computer running this browser.</p>
        <p class="jp-TarotSettingsPanel-error" data-error="base_url"></p>
        <label>Model
          <input name="model" type="text" autocomplete="off" spellcheck="false" placeholder="Enter a model ID">
        </label>
        <p class="jp-TarotSettingsPanel-error" data-error="model"></p>
        <label>Authentication
          <select name="auth_mode">
            <option value="bearer">Bearer API key</option>
            <option value="none">No authentication</option>
          </select>
        </label>
        <div class="jp-TarotSettingsPanel-key">
          <label>API key
            <input name="api_key" type="password" autocomplete="off" spellcheck="false">
          </label>
          <button type="button" data-settings-action="show">Show</button>
        </div>
        <p data-settings-region="key">Key: Not set</p>
        <p class="jp-TarotSettingsPanel-hint">Entered keys remain in server memory until it restarts. This page never stores a key in the browser.</p>
        <p class="jp-TarotSettingsPanel-error" data-error="api_key"></p>
        <button type="button" data-settings-action="clear">Clear runtime key</button>
        <label>Timeout (seconds)
          <input name="timeout" type="text" inputmode="numeric" autocomplete="off" spellcheck="false">
        </label>
        <p class="jp-TarotSettingsPanel-error" data-error="timeout_seconds"></p>
      </fieldset>
      <p class="jp-TarotSettingsPanel-hint">Testing sends a short synthetic prompt and may incur API charges.</p>
      <div class="jp-TarotSettingsPanel-actions">
        <button type="button" data-settings-action="test">Test connection</button>
        <button type="submit" data-settings-action="save">Save configuration</button>
        <button type="button" data-settings-action="cancel">Cancel</button>
      </div>
    </form>
    <p>Your question and card details are sent to the configured AI server only when you request a real reading.</p>
    <p>For entertainment and self-reflection only.</p>
    <p><button type="button" data-settings-action="reload">Load saved configuration</button></p>
  </section>
`;

export interface TarotSettingsPanelOptions {
  /** Called after a save replaces the effective snapshot. The key is not included. */
  onSaved?: (snapshot: AiSettingsSnapshot) => void;
}

/**
 * AI settings panel. A mounts this widget inside the existing Tarot sidebar.
 * Do not rewrite sidebar.ts here.
 *
 * The panel does not read or write the current card. A failed test or save
 * leaves the card wherever the reading view put it.
 *
 * A should call `confirmDiscard()` before leaving the panel while it is dirty,
 * and `setReadingInProgress()` while a reading request is running.
 */
export class TarotSettingsPanel extends Widget {
  private readonly form: HTMLFormElement;
  private readonly fields: HTMLFieldSetElement;
  private readonly status: HTMLElement;
  private readonly simulated: HTMLElement;
  private readonly banner: HTMLElement;
  private readonly keyStatus: HTMLElement;
  private readonly baseHint: HTMLElement;
  private readonly modeInputs: NodeListOf<HTMLInputElement>;
  private readonly baseUrl: HTMLInputElement;
  private readonly model: HTMLInputElement;
  private readonly authMode: HTMLSelectElement;
  private readonly apiKey: HTMLInputElement;
  private readonly timeout: HTMLInputElement;
  private readonly showButton: HTMLButtonElement;
  private readonly clearButton: HTMLButtonElement;
  private readonly testButton: HTMLButtonElement;
  private readonly saveButton: HTMLButtonElement;
  private readonly cancelButton: HTMLButtonElement;
  private readonly reloadButton: HTMLButtonElement;
  private snapshot: AiSettingsSnapshot | null = null;
  private draft: SettingsDraft | null = null;
  private testedStamp: string | null = null;
  private busy = false;
  private readingInProgress = false;
  private showErrors = false;

  constructor(
    private readonly client: TarotClient,
    private readonly options: TarotSettingsPanelOptions = {}
  ) {
    super();
    this.addClass('jp-TarotSettingsPanel');
    this.node.innerHTML = template;
    this.form = this.node.querySelector('form')!;
    this.fields = this.node.querySelector('[data-settings-region="fields"]')!;
    this.status = this.node.querySelector('[data-settings-region="status"]')!;
    this.simulated = this.node.querySelector('[data-settings-region="simulated"]')!;
    this.banner = this.node.querySelector('[data-settings-region="banner"]')!;
    this.keyStatus = this.node.querySelector('[data-settings-region="key"]')!;
    this.baseHint = this.node.querySelector('[data-settings-region="base-hint"]')!;
    this.modeInputs = this.node.querySelectorAll('input[name="tarot-settings-mode"]');
    this.baseUrl = this.node.querySelector('input[name="base_url"]')!;
    this.model = this.node.querySelector('input[name="model"]')!;
    this.authMode = this.node.querySelector('select[name="auth_mode"]')!;
    this.apiKey = this.node.querySelector('input[name="api_key"]')!;
    this.timeout = this.node.querySelector('input[name="timeout"]')!;
    this.showButton = this.node.querySelector('[data-settings-action="show"]')!;
    this.clearButton = this.node.querySelector('[data-settings-action="clear"]')!;
    this.testButton = this.node.querySelector('[data-settings-action="test"]')!;
    this.saveButton = this.node.querySelector('[data-settings-action="save"]')!;
    this.cancelButton = this.node.querySelector('[data-settings-action="cancel"]')!;
    this.reloadButton = this.node.querySelector('[data-settings-action="reload"]')!;

    this.form.addEventListener('submit', event => {
      event.preventDefault();
      void this.save();
    });
    this.form.addEventListener('input', () => {
      this.pullDraft();
      this.clearPassMark();
      this.showErrors = false;
      this.paint();
    });
    this.form.addEventListener('change', () => {
      this.pullDraft();
      this.clearPassMark();
      this.paint();
    });
    this.showButton.addEventListener('click', () => {
      if (this.draft === null) {
        return;
      }
      this.draft.showKey = !this.draft.showKey;
      this.paint();
    });
    this.clearButton.addEventListener('click', () => {
      if (this.draft === null) {
        return;
      }
      this.draft.clearRuntimeKey = !this.draft.clearRuntimeKey;
      if (this.draft.clearRuntimeKey) {
        this.draft.apiKeyInput = '';
        this.draft.showKey = false;
      }
      this.clearPassMark();
      this.paint();
    });
    this.testButton.addEventListener('click', () => {
      void this.testConnection();
    });
    this.cancelButton.addEventListener('click', () => {
      this.discardDraft('Unsaved changes were discarded, including anything typed into the API key field.');
    });
    this.reloadButton.addEventListener('click', () => {
      void this.reload();
    });
    void this.reload();
  }

  /** A calls this while a reading request is in flight. */
  setReadingInProgress(active: boolean): void {
    this.readingInProgress = active;
    if (active) {
      this.banner.textContent = 'A reading is in progress. AI settings cannot be changed until it finishes.';
    }
    this.paint();
  }

  /**
   * A calls this before switching back to Reading.
   * Returns true when the panel may be hidden. A cancelled confirm keeps the draft.
   */
  confirmDiscard(): boolean {
    if (this.snapshot === null || this.draft === null || !isDirty(this.draft, this.snapshot)) {
      return true;
    }
    const discard = window.confirm('Discard unsaved AI settings, including anything typed into the API key field?');
    if (!discard) {
      return false;
    }
    this.discardDraft('Unsaved changes were discarded, including anything typed into the API key field.');
    return true;
  }

  dispose(): void {
    this.apiKey.value = '';
    if (this.draft !== null) {
      this.draft.apiKeyInput = '';
      this.draft.showKey = false;
    }
    super.dispose();
  }

  private async reload(): Promise<void> {
    this.busy = true;
    this.paint();
    try {
      const snapshot = await this.client.getAiSettings();
      this.applySnapshot(snapshot);
      this.banner.textContent = '';
      this.showErrors = false;
    } catch (error) {
      this.banner.textContent = messageForError(error);
    } finally {
      this.busy = false;
      this.paint();
    }
  }

  private async save(): Promise<void> {
    if (!this.prepareSubmit()) {
      return;
    }
    const body = buildSaveBody(this.draft!, this.snapshot!);
    if (body === null) {
      this.showErrors = true;
      this.paint();
      return;
    }
    this.busy = true;
    this.paint();
    try {
      const snapshot = await this.client.saveAiSettings(body);
      this.applySnapshot(snapshot);
      this.showErrors = false;
      this.banner.textContent = saveNotice(snapshot);
      this.options.onSaved?.(snapshot);
    } catch (error) {
      this.banner.textContent = messageForError(error);
    } finally {
      this.busy = false;
      this.paint();
    }
  }

  private async testConnection(): Promise<void> {
    if (!this.prepareSubmit() || this.draft!.mode === 'demo') {
      return;
    }
    const body = buildTestBody(this.draft!, this.snapshot!);
    if (body === null) {
      this.showErrors = true;
      this.paint();
      return;
    }
    const stamp = draftStamp(this.draft!);
    this.busy = true;
    this.banner.textContent = 'Testing connection…';
    this.paint();
    try {
      const result = await this.client.testAiConnection(body);
      if (this.draft !== null && draftStamp(this.draft) === stamp) {
        this.testedStamp = stamp;
        this.banner.textContent = `Connection test passed (${result.latency_ms} ms). ${result.message} This does not replace a full reading.`;
      }
    } catch (error) {
      this.testedStamp = null;
      this.banner.textContent = messageForError(error);
    } finally {
      this.busy = false;
      this.paint();
    }
  }

  private prepareSubmit(): boolean {
    if (this.busy || this.readingInProgress || this.snapshot === null || this.draft === null) {
      return false;
    }
    this.pullDraft();
    const errors = validateDraft(this.draft, this.snapshot);
    this.showErrors = Object.keys(errors).length > 0;
    if (this.showErrors) {
      this.banner.textContent = 'Check the highlighted settings. Nothing was sent.';
      this.paint();
      return false;
    }
    return true;
  }

  private applySnapshot(snapshot: AiSettingsSnapshot): void {
    this.snapshot = snapshot;
    this.draft = draftFromSnapshot(snapshot);
    this.testedStamp = null;
    this.apiKey.value = '';
  }

  private discardDraft(message: string): void {
    if (this.snapshot === null) {
      return;
    }
    this.draft = draftFromSnapshot(this.snapshot);
    this.testedStamp = null;
    this.showErrors = false;
    this.apiKey.value = '';
    this.banner.textContent = message;
    this.paint();
  }

  private pullDraft(): void {
    if (this.draft === null || this.snapshot === null) {
      return;
    }
    const selected = Array.from(this.modeInputs).find(input => input.checked);
    if (!isFieldLocked(this.snapshot, 'mode') && (selected?.value === 'real' || selected?.value === 'demo')) {
      this.draft.mode = selected.value;
    }
    if (!isFieldLocked(this.snapshot, 'base_url')) {
      this.draft.baseUrl = this.baseUrl.value;
    }
    if (!isFieldLocked(this.snapshot, 'model')) {
      this.draft.model = this.model.value;
    }
    if (!isFieldLocked(this.snapshot, 'auth_mode') && (this.authMode.value === 'bearer' || this.authMode.value === 'none')) {
      this.draft.authMode = this.authMode.value;
    }
    if (!isFieldLocked(this.snapshot, 'timeout_seconds')) {
      this.draft.timeoutText = this.timeout.value;
    }
    this.draft.apiKeyInput = this.apiKey.value;
  }

  private clearPassMark(): void {
    if (this.testedStamp !== null) {
      this.testedStamp = null;
      this.banner.textContent = '';
    }
  }

  private paint(): void {
    const snapshot = this.snapshot;
    const draft = this.draft;
    const locked = this.busy || this.readingInProgress || snapshot === null || draft === null;
    this.fields.disabled = locked;
    this.node.setAttribute('aria-busy', this.busy ? 'true' : 'false');
    this.reloadButton.disabled = this.busy;
    if (snapshot === null || draft === null) {
      this.status.textContent = 'Status: Unknown';
      this.simulated.hidden = true;
      this.testButton.disabled = true;
      this.saveButton.disabled = true;
      this.cancelButton.disabled = true;
      return;
    }

    this.simulated.hidden = draft.mode !== 'demo';
    this.status.textContent = draft.mode === 'demo'
      ? 'Status: Demo (simulated)'
      : `Status: ${statusLabel(snapshot.status)}`;
    for (const input of this.modeInputs) {
      input.checked = input.value === draft.mode;
      input.disabled = locked || isFieldLocked(snapshot, 'mode');
    }
    this.assign(this.baseUrl, draft.baseUrl, locked || isFieldLocked(snapshot, 'base_url'));
    this.assign(this.model, draft.model, locked || isFieldLocked(snapshot, 'model'));
    this.authMode.value = draft.authMode;
    this.authMode.disabled = locked || isFieldLocked(snapshot, 'auth_mode');
    this.assign(this.timeout, draft.timeoutText, locked || isFieldLocked(snapshot, 'timeout_seconds'));
    this.apiKey.value = draft.apiKeyInput;
    this.apiKey.type = draft.showKey ? 'text' : 'password';
    this.apiKey.disabled = locked || draft.clearRuntimeKey;
    this.showButton.textContent = draft.showKey ? 'Hide' : 'Show';
    this.showButton.setAttribute('aria-pressed', draft.showKey ? 'true' : 'false');
    this.showButton.disabled = locked || draft.apiKeyInput.length === 0;
    this.clearButton.disabled = locked || snapshot.key_source === 'environment' || (!snapshot.key_present && !draft.clearRuntimeKey);
    this.clearButton.textContent = draft.clearRuntimeKey ? 'Undo clear' : 'Clear runtime key';
    this.keyStatus.textContent = keyLabel(snapshot, draft);
    this.baseHint.hidden = false;
    if (urlChangedWithStoredKey(draft, snapshot)) {
      this.baseHint.textContent = 'The saved key belongs to the previous server. Enter a new key or choose No authentication. 127.0.0.1 is the Jupyter server machine, not necessarily this browser.';
    } else {
      this.baseHint.textContent = "Use the server's API base URL, not /chat/completions. 127.0.0.1 is the Jupyter server machine, not necessarily the computer running this browser.";
    }

    const errors = this.showErrors ? validateDraft(draft, snapshot) : {};
    this.writeError('base_url', errors.base_url);
    this.writeError('model', errors.model);
    this.writeError('api_key', errors.api_key);
    this.writeError('timeout_seconds', errors.timeout_seconds);
    this.baseUrl.setAttribute('aria-invalid', errors.base_url ? 'true' : 'false');
    this.model.setAttribute('aria-invalid', errors.model ? 'true' : 'false');
    this.apiKey.setAttribute('aria-invalid', errors.api_key ? 'true' : 'false');
    this.timeout.setAttribute('aria-invalid', errors.timeout_seconds ? 'true' : 'false');

    const passed = this.testedStamp !== null && this.testedStamp === draftStamp(draft);
    if (!passed && this.testedStamp !== null) {
      this.testedStamp = null;
    }
    this.testButton.disabled = locked || draft.mode === 'demo';
    this.saveButton.disabled = locked;
    this.cancelButton.disabled = locked || !isDirty(draft, snapshot);
    if (draft.mode === 'demo' && !this.busy) {
      this.testButton.title = 'Demo mode does not contact an AI server.';
    } else {
      this.testButton.title = '';
    }
  }

  private assign(input: HTMLInputElement, value: string, disabled: boolean): void {
    if (input.value !== value) {
      input.value = value;
    }
    input.disabled = disabled;
  }

  private writeError(name: string, message: string | undefined): void {
    const node = this.node.querySelector(`[data-error="${name}"]`);
    if (node instanceof HTMLElement) {
      node.textContent = message ?? '';
    }
  }
}
