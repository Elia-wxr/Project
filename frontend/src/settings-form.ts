import type {
  AiSettingField,
  AiSettings,
  AiSettingsSaveRequest,
  AiSettingsSnapshot,
  AiTestRequest
} from './types';
import { normalizeBaseUrl, parseTimeout, validateBaseUrl, type BaseUrlResult } from './validate';

export interface SettingsDraft {
  mode: AiSettings['mode'];
  baseUrl: string;
  model: string;
  authMode: AiSettings['auth_mode'];
  timeoutText: string;
  apiKeyInput: string;
  showKey: boolean;
  clearRuntimeKey: boolean;
}

export interface FieldErrors {
  base_url?: string;
  model?: string;
  timeout_seconds?: string;
  api_key?: string;
}

const FALLBACK: Record<string, string> = {
  INVALID_REQUEST: 'Check the highlighted settings and try again.',
  SESSION_NOT_FOUND: 'Draw a card again. This session is no longer active.',
  SESSION_CONFLICT: 'The session changed. Refresh the card before continuing.',
  READING_IN_PROGRESS: 'A reading is in progress. Wait before changing AI settings. You can still view history.',
  CONFIG_CONFLICT: 'Settings changed on the server. Your draft is kept. Load the saved configuration, then try again.',
  AI_UNAVAILABLE: 'Could not use the configured AI server. Check the Base URL, model and API key. The card was not changed.',
  AI_RATE_LIMITED: 'The AI server is rate limiting requests. Wait, then try the test again yourself.',
  AI_TIMEOUT: 'The connection test timed out. Try again. The card was not changed.',
  AI_BAD_RESPONSE: 'The AI server returned a response this page could not use. The card was not changed.',
  STORAGE_ERROR: 'Settings could not be saved. The previous configuration is unchanged.',
  INTERNAL_ERROR: 'Something went wrong. Try again.',
  SESSION_EXPIRED: 'Could not reach Tarot. Check your Jupyter session and try again.',
  NETWORK_ERROR: 'Could not reach Tarot. Check the network and try again. The card was not changed.'
};

export function draftFromSnapshot(snapshot: AiSettingsSnapshot): SettingsDraft {
  return {
    mode: snapshot.settings.mode,
    baseUrl: snapshot.settings.base_url,
    model: snapshot.settings.model,
    authMode: snapshot.settings.auth_mode,
    timeoutText: String(snapshot.settings.timeout_seconds),
    apiKeyInput: '',
    showKey: false,
    clearRuntimeKey: false
  };
}

export function isFieldLocked(snapshot: AiSettingsSnapshot, field: AiSettingField): boolean {
  return snapshot.locked_fields.includes(field);
}

/** Identity of the draft that a passing test applies to. Key text is not stored. */
export function draftStamp(draft: SettingsDraft): string {
  return JSON.stringify({
    mode: draft.mode,
    baseUrl: draft.baseUrl,
    model: draft.model,
    authMode: draft.authMode,
    timeoutText: draft.timeoutText,
    hasTypedKey: draft.apiKeyInput.length > 0,
    clearRuntimeKey: draft.clearRuntimeKey
  });
}

export function isDirty(draft: SettingsDraft, snapshot: AiSettingsSnapshot): boolean {
  const saved = snapshot.settings;
  if (!isFieldLocked(snapshot, 'mode') && draft.mode !== saved.mode) {
    return true;
  }
  if (!isFieldLocked(snapshot, 'base_url') && draft.baseUrl.trim() !== saved.base_url) {
    return true;
  }
  if (!isFieldLocked(snapshot, 'model') && draft.model !== saved.model) {
    return true;
  }
  if (!isFieldLocked(snapshot, 'auth_mode') && draft.authMode !== saved.auth_mode) {
    return true;
  }
  if (!isFieldLocked(snapshot, 'timeout_seconds') && draft.timeoutText.trim() !== String(saved.timeout_seconds)) {
    return true;
  }
  return draft.apiKeyInput.length > 0 || draft.clearRuntimeKey;
}

export function urlChangedWithStoredKey(draft: SettingsDraft, snapshot: AiSettingsSnapshot): boolean {
  if (isFieldLocked(snapshot, 'base_url') || !snapshot.key_present || snapshot.key_source === 'none') {
    return false;
  }
  return normalizeBaseUrl(draft.baseUrl) !== normalizeBaseUrl(snapshot.settings.base_url);
}

function resolveBaseUrl(draft: SettingsDraft, snapshot: AiSettingsSnapshot): BaseUrlResult {
  if (isFieldLocked(snapshot, 'base_url')) {
    return { ok: true, normalized: snapshot.settings.base_url };
  }
  if (draft.mode === 'demo' && draft.baseUrl.trim() === '') {
    return { ok: true, normalized: '' };
  }
  return validateBaseUrl(draft.baseUrl);
}

export function validateDraft(draft: SettingsDraft, snapshot: AiSettingsSnapshot): FieldErrors {
  const errors: FieldErrors = {};
  if (!isFieldLocked(snapshot, 'base_url')) {
    const base = resolveBaseUrl(draft, snapshot);
    if (!base.ok) {
      errors.base_url = base.message;
    }
  }
  if (!isFieldLocked(snapshot, 'model') && draft.mode === 'real' && draft.model.trim() === '') {
    errors.model = 'Enter a model ID. You can type it; this page does not require a model list.';
  }
  if (!isFieldLocked(snapshot, 'timeout_seconds') && parseTimeout(draft.timeoutText) === null) {
    errors.timeout_seconds = 'Enter a whole number of seconds from 5 to 120.';
  }
  if (draft.apiKeyInput.length > 0 && draft.apiKeyInput.trim() === '') {
    errors.api_key = 'An API key cannot be only spaces. Leave the field empty to keep the current key.';
  }
  if (draft.clearRuntimeKey && draft.apiKeyInput.trim() !== '') {
    errors.api_key = 'Clear the runtime key or enter a new one, not both.';
  }
  if (draft.clearRuntimeKey && snapshot.key_source === 'environment') {
    errors.api_key = 'An environment key cannot be cleared from this page.';
  }
  if (
    !errors.api_key &&
    draft.mode !== 'demo' &&
    urlChangedWithStoredKey(draft, snapshot) &&
    draft.authMode !== 'none' &&
    draft.apiKeyInput.trim() === ''
  ) {
    errors.api_key = 'Enter a new API key for this server, or choose No authentication.';
  }
  return errors;
}

export function settingsFromDraft(draft: SettingsDraft, snapshot: AiSettingsSnapshot): AiSettings | null {
  const timeout = isFieldLocked(snapshot, 'timeout_seconds')
    ? snapshot.settings.timeout_seconds
    : parseTimeout(draft.timeoutText);
  const base = resolveBaseUrl(draft, snapshot);
  if (timeout === null || !base.ok) {
    return null;
  }
  if (Object.keys(validateDraft(draft, snapshot)).length > 0) {
    return null;
  }
  return {
    mode: isFieldLocked(snapshot, 'mode') ? snapshot.settings.mode : draft.mode,
    base_url: base.normalized,
    model: (isFieldLocked(snapshot, 'model') ? snapshot.settings.model : draft.model).trim(),
    auth_mode: isFieldLocked(snapshot, 'auth_mode') ? snapshot.settings.auth_mode : draft.authMode,
    timeout_seconds: timeout
  };
}

export function buildSaveBody(draft: SettingsDraft, snapshot: AiSettingsSnapshot): AiSettingsSaveRequest | null {
  const settings = settingsFromDraft(draft, snapshot);
  if (settings === null) {
    return null;
  }
  const body: AiSettingsSaveRequest = {
    config_revision: snapshot.config_revision,
    settings
  };
  const typed = draft.apiKeyInput.trim();
  if (typed) {
    body.api_key = typed;
  }
  if (draft.clearRuntimeKey) {
    body.clear_api_key = true;
  }
  return body;
}

export function buildTestBody(draft: SettingsDraft, snapshot: AiSettingsSnapshot): AiTestRequest | null {
  const settings = settingsFromDraft(draft, snapshot);
  if (settings === null || settings.mode === 'demo') {
    return null;
  }
  const body: AiTestRequest = {
    config_revision: snapshot.config_revision,
    settings
  };
  const typed = draft.apiKeyInput.trim();
  if (typed) {
    body.api_key = typed;
  }
  return body;
}

export function statusLabel(status: AiSettingsSnapshot['status']): string {
  if (status === 'demo') {
    return 'Demo';
  }
  if (status === 'configured') {
    return 'Configured (not tested)';
  }
  return 'Not configured';
}

export function keyLabel(snapshot: AiSettingsSnapshot, draft: SettingsDraft): string {
  if (draft.apiKeyInput.length > 0) {
    return 'Key: Entered in this form (not stored in the browser)';
  }
  if (draft.clearRuntimeKey) {
    return 'Key: Runtime key will be cleared when you save';
  }
  if (urlChangedWithStoredKey(draft, snapshot)) {
    return 'Key: Not set for this server. Enter a new key or choose No authentication.';
  }
  if (snapshot.key_source === 'environment') {
    return 'Key: From environment';
  }
  if (snapshot.key_source === 'runtime') {
    return 'Key: Set for this server';
  }
  return 'Key: Not set';
}

export function saveNotice(snapshot: AiSettingsSnapshot): string {
  if (snapshot.status === 'demo') {
    return 'Saved. Demo mode is simulated and was not connected to a server.';
  }
  if (snapshot.status === 'not_configured') {
    return 'Saved. This is not a successful connection. Add the missing key before a real reading.';
  }
  return 'Saved. Configured (not tested). Saving does not call the AI server.';
}

export function messageForError(error: unknown): string {
  if (typeof error === 'object' && error !== null && error instanceof Error) {
    const coded = error as Error & { status?: number; code?: string };
    if (coded.status === 404 && coded.code !== 'SESSION_NOT_FOUND') {
      return 'The AI settings service is not available yet. Drawing a card still works.';
    }
    if (typeof coded.code === 'string' && coded.code.length > 0) {
      return coded.message || FALLBACK[coded.code] || 'Something went wrong. Try again.';
    }
    if (coded.message) {
      return coded.message;
    }
  }
  return 'Something went wrong. Try again.';
}
