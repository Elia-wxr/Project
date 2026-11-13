import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  buildSaveBody,
  buildTestBody,
  draftFromSnapshot,
  draftStamp,
  isDirty,
  keyLabel,
  messageForError,
  validateDraft
} from '../../frontend/src/settings-form.ts';
import type { AiSettingsSnapshot } from '../../frontend/src/types.ts';
import { normalizeBaseUrl, parseTimeout, validateBaseUrl } from '../../frontend/src/validate.ts';

const fixtures = join(dirname(fileURLToPath(import.meta.url)), '../fixtures');

function snapshot(patch: Partial<AiSettingsSnapshot> = {}): AiSettingsSnapshot {
  return {
    config_revision: 3,
    settings: {
      mode: 'real',
      base_url: 'https://api.openai.com/v1',
      model: 'demo-model',
      auth_mode: 'bearer',
      timeout_seconds: 30
    },
    key_present: true,
    key_source: 'runtime',
    locked_fields: [],
    status: 'configured',
    ...patch
  };
}

test('base URL rejects secrets, query, fragment, completions, metadata and non-loopback HTTP', () => {
  assert.equal(validateBaseUrl('https://api.openai.com/v1/').ok, true);
  assert.equal(validateBaseUrl('https://user:secret@api.openai.com/v1').ok, false);
  assert.equal(validateBaseUrl('https://api.openai.com/v1?key=1').ok, false);
  assert.equal(validateBaseUrl('https://api.openai.com/v1#frag').ok, false);
  assert.equal(validateBaseUrl('https://api.openai.com/v1/chat/completions').ok, false);
  assert.equal(validateBaseUrl('http://192.168.1.8/v1').ok, false);
  assert.equal(validateBaseUrl('https://192.168.1.8/v1').ok, true);
  assert.equal(validateBaseUrl('https://10.1.2.3/v1').ok, true);
  assert.equal(validateBaseUrl('http://169.254.169.254/').ok, false);
  assert.equal(validateBaseUrl('https://metadata.google.internal/').ok, false);
  assert.equal(validateBaseUrl('http://127.0.0.1:8000/v1').ok, true);
  const normalized = validateBaseUrl('https://api.openai.com/v1/');
  assert.equal(normalized.ok && normalized.normalized, 'https://api.openai.com/v1');
  assert.equal(normalizeBaseUrl('https://api.openai.com/'), 'https://api.openai.com');
});

test('timeout accepts only whole seconds from 5 to 120', () => {
  assert.equal(parseTimeout('30'), 30);
  assert.equal(parseTimeout('5'), 5);
  assert.equal(parseTimeout('120'), 120);
  assert.equal(parseTimeout('4'), null);
  assert.equal(parseTimeout('121'), null);
  assert.equal(parseTimeout('30.5'), null);
  assert.equal(parseTimeout('05'), null);
  assert.equal(parseTimeout('1e1'), null);
  assert.equal(parseTimeout('NaN'), null);
});

test('save body uses numbers and booleans and omits an empty key', () => {
  const saved = snapshot();
  const draft = draftFromSnapshot(saved);
  draft.timeoutText = '45';
  draft.clearRuntimeKey = true;
  const body = buildSaveBody(draft, saved);
  assert.ok(body);
  assert.equal(body.settings.timeout_seconds, 45);
  assert.equal(typeof body.settings.timeout_seconds, 'number');
  assert.equal(body.clear_api_key, true);
  assert.equal(typeof body.clear_api_key, 'boolean');
  assert.equal('api_key' in body, false);
  assert.equal(JSON.stringify(body).includes('sk-'), false);
});

test('a typed key is sent once and is not copied into the draft stamp store', () => {
  const saved = snapshot();
  const draft = draftFromSnapshot(saved);
  draft.apiKeyInput = 'sk-test-value';
  const body = buildSaveBody(draft, saved);
  assert.equal(body?.api_key, 'sk-test-value');
  assert.equal(draftStamp(draft).includes('sk-test-value'), false);
  assert.equal(draftStamp(draft).includes('hasTypedKey'), true);
});

test('replace and clear together is rejected', () => {
  const saved = snapshot();
  const draft = draftFromSnapshot(saved);
  draft.apiKeyInput = 'sk-test-value';
  draft.clearRuntimeKey = true;
  assert.ok(validateDraft(draft, saved).api_key);
  assert.equal(buildSaveBody(draft, saved), null);
});

test('changing the server requires a new key or no authentication', () => {
  const saved = snapshot();
  const draft = draftFromSnapshot(saved);
  draft.baseUrl = 'https://example.test/v1';
  assert.match(keyLabel(saved, draft), /Not set for this server/);
  assert.match(validateDraft(draft, saved).api_key ?? '', /new API key/);
  assert.equal(buildSaveBody(draft, saved), null);
  draft.authMode = 'none';
  assert.equal(validateDraft(draft, saved).api_key, undefined);
  const body = buildSaveBody(draft, saved);
  assert.equal(body?.api_key, undefined);
  assert.equal(body?.settings.auth_mode, 'none');
  assert.equal(body?.settings.base_url, 'https://example.test/v1');
});

test('demo mode can be saved without a server and builds no test request', () => {
  const saved = snapshot();
  const draft = draftFromSnapshot(saved);
  draft.mode = 'demo';
  draft.baseUrl = '';
  draft.model = '';
  assert.equal(validateDraft(draft, saved).base_url, undefined);
  assert.equal(validateDraft(draft, saved).model, undefined);
  assert.equal(buildTestBody(draft, saved), null);
  const save = buildSaveBody(draft, saved);
  assert.equal(save?.settings.mode, 'demo');
  assert.equal(save?.settings.base_url, '');
});

test('any field change produces a new stamp and a dirty draft', () => {
  const saved = snapshot();
  const draft = draftFromSnapshot(saved);
  const before = draftStamp(draft);
  assert.equal(isDirty(draft, saved), false);
  draft.model = 'other-model';
  assert.notEqual(draftStamp(draft), before);
  assert.equal(isDirty(draft, saved), true);
});

test('conflict and missing settings service keep a usable message', () => {
  const conflict = new Error('Settings changed on the server. Your draft is kept. Load the saved configuration, then try again.');
  Object.assign(conflict, { status: 409, code: 'CONFIG_CONFLICT' });
  assert.match(messageForError(conflict), /draft is kept/);
  const missing = new Error('not found');
  Object.assign(missing, { status: 404, code: 'INTERNAL_ERROR' });
  assert.match(messageForError(missing), /not available yet/);
});

test('an environment key cannot be cleared and locked fields stay unchanged', () => {
  const saved = snapshot({
    key_source: 'environment',
    key_present: true,
    locked_fields: ['base_url']
  });
  const draft = draftFromSnapshot(saved);
  draft.clearRuntimeKey = true;
  draft.baseUrl = 'https://evil.example/v1';
  assert.match(validateDraft(draft, saved).api_key ?? '', /cannot be cleared/);
  draft.clearRuntimeKey = false;
  const body = buildSaveBody(draft, saved);
  assert.equal(body?.settings.base_url, 'https://api.openai.com/v1');
});

test('fixtures cover the read snapshot, a 409 conflict and a passing test', () => {
  const read = JSON.parse(readFileSync(join(fixtures, 'ai-settings-read.json'), 'utf8')) as AiSettingsSnapshot;
  const draft = draftFromSnapshot(read);
  assert.equal(isDirty(draft, read), false);
  assert.match(keyLabel(read, draft), /Not set/);
  assert.equal(read.status, 'not_configured');

  const conflict = JSON.parse(readFileSync(join(fixtures, 'ai-settings-save-conflict.json'), 'utf8')) as {
    error: { code: string; message: string };
  };
  const conflictError = new Error(conflict.error.message);
  Object.assign(conflictError, { status: 409, code: conflict.error.code });
  assert.equal(conflict.error.code, 'CONFIG_CONFLICT');
  assert.match(messageForError(conflictError), /draft is kept/);

  const passed = JSON.parse(readFileSync(join(fixtures, 'ai-test-ok.json'), 'utf8')) as {
    ok: boolean;
    latency_ms: number;
    message: string;
  };
  assert.equal(passed.ok, true);
  assert.equal(typeof passed.latency_ms, 'number');
  assert.match(passed.message, /test prompt/);
});

test('a dropped network call is not reported as an expired Jupyter session', () => {
  const dropped = new Error('Could not reach Tarot. Check the network and try again.');
  Object.assign(dropped, { status: 0, code: 'NETWORK_ERROR' });
  assert.match(messageForError(dropped), /network/i);
  assert.doesNotMatch(messageForError(dropped), /Jupyter session/);
});
