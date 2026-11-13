import { URLExt } from '@jupyterlab/coreutils';
import { ServerConnection } from '@jupyterlab/services';

import type {
  AiSettingsSaveRequest,
  AiSettingsSnapshot,
  AiTestRequest,
  AiTestResult,
  SessionRecord
} from './types';

type RecordResponse = { record: SessionRecord };
type LatestResponse = { record: SessionRecord | null };
type ErrorResponse = { error?: { code: string; message: string } };

/**
 * Structured Tarot API error. `status` is the HTTP status.
 * Jupyter auth failures that are not JSON use code `SESSION_EXPIRED`.
 * A failed `fetch` uses code `NETWORK_ERROR`.
 */
export class TarotRequestError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = 'TarotRequestError';
    this.status = status;
    this.code = code;
  }
}

/** Keep Jupyter's URL, authentication and JSON handling out of the widgets. */
export class TarotClient {
  constructor(private readonly settings: ServerConnection.ISettings) {}

  health(): Promise<{ status: 'ok' }> {
    return this.request('health');
  }

  async draw(question: string): Promise<SessionRecord> {
    const result = await this.request<RecordResponse>('draw', { question });
    return result.record;
  }

  async reading(sessionId: string): Promise<SessionRecord> {
    const result = await this.request<RecordResponse>('reading', {
      session_id: sessionId,
      language: 'en'
    });
    return result.record;
  }

  async saveLatest(sessionId: string): Promise<SessionRecord> {
    const result = await this.request<RecordResponse>('history/latest', {
      session_id: sessionId
    });
    return result.record;
  }

  async latest(): Promise<SessionRecord | null> {
    const result = await this.request<LatestResponse>('history/latest');
    return result.record;
  }

  getAiSettings(): Promise<AiSettingsSnapshot> {
    return this.request('ai/settings');
  }

  saveAiSettings(body: AiSettingsSaveRequest): Promise<AiSettingsSnapshot> {
    return this.request('ai/settings', body, 'PUT');
  }

  testAiConnection(body: AiTestRequest): Promise<AiTestResult> {
    return this.request('ai/test', body, 'POST');
  }

  /**
   * GET when `body` is omitted. POST by default, or PUT when `method` is set.
   * `body` may contain nested objects, numbers and booleans.
   */
  private async request<T>(path: string, body?: unknown, method?: 'POST' | 'PUT'): Promise<T> {
    const url = URLExt.join(this.settings.baseUrl, 'tarot', 'api', path);
    const verb = body === undefined ? 'GET' : (method ?? 'POST');
    const init: RequestInit = {
      method: verb,
      cache: 'no-store'
    };
    if (body !== undefined) {
      init.headers = { 'Content-Type': 'application/json' };
      init.body = JSON.stringify(body);
    }
    let response: Response;
    try {
      response = await ServerConnection.makeRequest(url, init, this.settings);
    } catch {
      throw new TarotRequestError(0, 'NETWORK_ERROR', 'Could not reach Tarot. Check the network and try again.');
    }
    const data = await response.json().catch(() => null) as (T & ErrorResponse) | null;
    if (!response.ok || data === null) {
      const code = data?.error?.code
        ?? ((response.status === 401 || response.status === 403) ? 'SESSION_EXPIRED' : 'INTERNAL_ERROR');
      const message = data?.error?.message
        ?? (code === 'SESSION_EXPIRED'
          ? 'Could not reach Tarot. Check your Jupyter session and try again.'
          : 'Something went wrong. Try again.');
      throw new TarotRequestError(response.status, code, message);
    }
    return data;
  }
}
