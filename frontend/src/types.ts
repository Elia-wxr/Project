/** Fields consumed by the sidebar. The server can return additional record fields. */
export type Orientation = 'upright' | 'reversed';

export interface DrawnCard {
  card: { name: string; upright: string[]; reversed: string[] };
  position: 'focus';
  orientation: Orientation;
}

export interface SessionRecord {
  schema_version: 1;
  session: {
    session_id: string;
    question: string;
    cards: [DrawnCard];
  };
  reading: {
    summary: string;
    card_interpretations: [string];
    advice: string;
    provider: string;
  } | null;
}

export type AiMode = 'real' | 'demo';
export type AuthMode = 'bearer' | 'none';
export type KeySource = 'none' | 'runtime' | 'environment';
export type AiStatus = 'not_configured' | 'configured' | 'demo';
export type AiSettingField = 'mode' | 'base_url' | 'model' | 'auth_mode' | 'timeout_seconds';

/** Non-sensitive settings. The API key is never part of this object. */
export interface AiSettings {
  mode: AiMode;
  base_url: string;
  model: string;
  auth_mode: AuthMode;
  timeout_seconds: number;
}

/** GET/PUT success body. Never includes the key value. */
export interface AiSettingsSnapshot {
  config_revision: number;
  settings: AiSettings;
  key_present: boolean;
  key_source: KeySource;
  locked_fields: AiSettingField[];
  status: AiStatus;
}

export interface AiSettingsSaveRequest {
  config_revision: number;
  settings: AiSettings;
  api_key?: string;
  clear_api_key?: boolean;
}

export interface AiTestRequest {
  config_revision: number;
  settings: AiSettings;
  api_key?: string;
}

export interface AiTestResult {
  ok: true;
  latency_ms: number;
  message: string;
}

export interface ErrorJSON {
  error: { code: string; message: string };
}
