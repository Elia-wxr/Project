import { URLExt } from '@jupyterlab/coreutils';
import { ServerConnection } from '@jupyterlab/services';

import type { SessionRecord } from './types';

type RecordResponse = { record: SessionRecord };
type LatestResponse = { record: SessionRecord | null };
type ErrorResponse = { error?: { code: string; message: string } };

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

  private async request<T>(path: string, body?: Record<string, string>): Promise<T> {
    const url = URLExt.join(this.settings.baseUrl, 'tarot', 'api', path);
    const init: RequestInit = body === undefined
      ? { method: 'GET' }
      : {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        };
    const response = await ServerConnection.makeRequest(url, init, this.settings);
    const data = await response.json().catch(() => null) as (T & ErrorResponse) | null;
    if (!response.ok || data === null) {
      throw new Error(data?.error?.message ?? 'Could not reach Tarot. Check your Jupyter session and try again.');
    }
    return data;
  }
}
