import { Widget } from '@lumino/widgets';

import { TarotClient } from './api';
import { tarotIcon } from './icons';
import { TarotSettingsPanel } from './settings';
import type { SessionRecord } from './types';

// Static markup only: every dynamic value is written with textContent.
const template = `
  <header class="jp-TarotSidebar-header">
    <h2 class="jp-TarotSidebar-title" id="jp-tarot-heading">Tarot</h2>
  </header>
  <div class="jp-TarotSidebar-tabs" role="tablist" aria-label="Tarot views">
    <button type="button" class="jp-TarotSidebar-tab" role="tab" id="jp-tarot-tab-reading"
      aria-controls="jp-tarot-panel-reading" aria-selected="true" tabindex="0"
      data-tab="reading">Reading</button>
    <button type="button" class="jp-TarotSidebar-tab" role="tab" id="jp-tarot-tab-settings"
      aria-controls="jp-tarot-panel-settings" aria-selected="false" tabindex="-1"
      data-tab="settings">AI settings</button>
  </div>
  <div class="jp-TarotSidebar-view" id="jp-tarot-panel-reading" role="tabpanel"
    aria-labelledby="jp-tarot-tab-reading" data-view="reading">
    <p class="jp-TarotSidebar-tagline">For entertainment and self-reflection only.</p>
    <p class="jp-TarotSidebar-privacy">Your question and card details are sent to your
      configured AI server only when you request a real reading.</p>
    <section class="jp-TarotSidebar-section" aria-labelledby="jp-tarot-draw-heading">
      <h3 class="jp-TarotSidebar-heading" id="jp-tarot-draw-heading">Draw a card</h3>
      <form class="jp-TarotSidebar-form">
        <label class="jp-TarotSidebar-label" for="jp-tarot-question">Your question</label>
        <textarea class="jp-TarotSidebar-input" id="jp-tarot-question" rows="3"
          maxlength="2000" required aria-describedby="jp-tarot-question-help"
          placeholder="What should I reflect on?"></textarea>
        <p class="jp-TarotSidebar-hint" id="jp-tarot-question-help">1–2000 characters.</p>
        <button type="submit" class="jp-TarotSidebar-button jp-mod-primary"
          data-action="draw">Draw a card</button>
      </form>
    </section>
    <p class="jp-TarotSidebar-status" data-region="status" role="status"
      aria-live="polite" aria-busy="false"></p>
    <section class="jp-TarotSidebar-section" aria-labelledby="jp-tarot-card-heading">
      <h3 class="jp-TarotSidebar-heading" id="jp-tarot-card-heading">Drawn card</h3>
      <div class="jp-TarotSidebar-card" data-region="current">
        <p class="jp-TarotSidebar-empty">No card drawn yet. Ask a question and draw a card.</p>
      </div>
      <div class="jp-TarotSidebar-actions">
        <button type="button" class="jp-TarotSidebar-button jp-mod-primary"
          data-action="read">Generate reading</button>
        <button type="button" class="jp-TarotSidebar-button" data-action="save">Save as latest</button>
      </div>
    </section>
    <hr class="jp-TarotSidebar-divider">
    <section class="jp-TarotSidebar-section" aria-labelledby="jp-tarot-history-heading">
      <h3 class="jp-TarotSidebar-heading" id="jp-tarot-history-heading">Latest saved reading</h3>
      <button type="button" class="jp-TarotSidebar-button" data-action="latest">View latest</button>
      <div class="jp-TarotSidebar-history" data-region="history">
        <p class="jp-TarotSidebar-empty">Click “View latest” to open the saved record.</p>
      </div>
    </section>
  </div>
  <div class="jp-TarotSidebar-view jp-TarotSidebar-settingsHost" id="jp-tarot-panel-settings"
    role="tabpanel" aria-labelledby="jp-tarot-tab-settings" data-view="settings"
    tabindex="-1" hidden></div>
`;

/**
 * Tarot sidebar: draw one card, read it with the configured AI server, save it,
 * and host the AI settings panel owned by task B-01.
 *
 * The sidebar never reads, stores or echoes an API key: the key lives in
 * `TarotSettingsPanel` and the server only.
 */
export class TarotSidebar extends Widget {
  private readonly question: HTMLTextAreaElement;
  private readonly drawButton: HTMLButtonElement;
  private readonly readButton: HTMLButtonElement;
  private readonly saveButton: HTMLButtonElement;
  private readonly latestButton: HTMLButtonElement;
  private readonly status: HTMLElement;
  private readonly current: HTMLElement;
  private readonly history: HTMLElement;
  private readonly readingView: HTMLElement;
  private readonly settingsHost: HTMLElement;
  private readonly readingTab: HTMLButtonElement;
  private readonly settingsTab: HTMLButtonElement;
  private readonly settingsPanel: TarotSettingsPanel;
  private active: SessionRecord | null = null;
  private saved = false;
  private busy = false;

  constructor(private readonly client: TarotClient) {
    super();
    this.id = 'tarot-jupyterlab-sidebar';
    this.title.icon = tarotIcon;
    // The left activity bar shows the icon only; the panel shows the title.
    this.title.label = '';
    this.title.caption = 'Tarot';
    this.addClass('jp-TarotSidebar');
    this.node.innerHTML = template;

    this.question = requireElement<HTMLTextAreaElement>(this.node, '#jp-tarot-question');
    this.drawButton = requireElement<HTMLButtonElement>(this.node, '[data-action="draw"]');
    this.readButton = requireElement<HTMLButtonElement>(this.node, '[data-action="read"]');
    this.saveButton = requireElement<HTMLButtonElement>(this.node, '[data-action="save"]');
    this.latestButton = requireElement<HTMLButtonElement>(this.node, '[data-action="latest"]');
    this.status = requireElement<HTMLElement>(this.node, '[data-region="status"]');
    this.current = requireElement<HTMLElement>(this.node, '[data-region="current"]');
    this.history = requireElement<HTMLElement>(this.node, '[data-region="history"]');
    this.readingView = requireElement<HTMLElement>(this.node, '[data-view="reading"]');
    this.settingsHost = requireElement<HTMLElement>(this.node, '[data-view="settings"]');
    this.readingTab = requireElement<HTMLButtonElement>(this.node, '[data-tab="reading"]');
    this.settingsTab = requireElement<HTMLButtonElement>(this.node, '[data-tab="settings"]');

    // The AI settings panel (task B-01) keeps its own draft and key state.
    this.settingsPanel = new TarotSettingsPanel(client, {
      onSaved: snapshot => {
        if (!snapshot.settings.enabled) {
          this.setStatus('Saved. AI is disabled; readings are unavailable until you enable AI.', 'success');
        } else {
          this.setStatus('Saved.', 'success');
        }
      }
    });
    this.settingsPanel.hide();
    this.settingsHost.append(this.settingsPanel.node);

    this.readingTab.addEventListener('click', () => this.showView('reading'));
    this.settingsTab.addEventListener('click', () => this.showView('settings'));
    this.node
      .querySelector('[role="tablist"]')
      ?.addEventListener('keydown', event => this.onTabKeydown(event as KeyboardEvent));

    this.node.querySelector('form')?.addEventListener('submit', event => {
      event.preventDefault();
      void this.draw();
    });
    this.readButton.addEventListener('click', () => void this.read());
    this.saveButton.addEventListener('click', () => this.save());
    this.latestButton.addEventListener('click', () => void this.loadLatest());
    this.question.addEventListener('input', () => this.clearError());

    this.updateButtons();
  }

  /** Tell the user whether the plugin backend answers; AI connectivity is separate. */
  async checkConnection(): Promise<void> {
    await this.run(async () => {
      await this.client.health();
      this.setStatus('Connected to the Tarot server.', 'info');
    });
  }

  dispose(): void {
    this.settingsPanel.dispose();
    super.dispose();
  }

  private async draw(): Promise<void> {
    const question = this.question.value.trim();
    if (question === '') {
      this.setStatus('Enter a question before drawing a card.', 'error');
      this.question.focus();
      return;
    }
    await this.run(async () => {
      this.setActive(await this.client.draw(question));
      this.setStatus('Card drawn. Unsaved.', 'info');
    });
  }

  private async read(): Promise<void> {
    if (this.active === null) {
      return;
    }
    const sessionId = this.active.session.session_id;
    await this.run(async () => {
      this.setStatus('Generating reading…', 'info');
      this.settingsPanel.setReadingInProgress(true);
      try {
        this.setActive(await this.client.reading(sessionId));
        this.setStatus('Reading ready. Unsaved.', 'info');
      } finally {
        this.settingsPanel.setReadingInProgress(false);
      }
    });
  }

  private save(): void {
    if (this.active === null || this.busy) {
      return;
    }
    const confirmed = window.confirm(
      'This replaces any previously saved reading. Continue?'
    );
    if (!confirmed) {
      return;
    }
    const sessionId = this.active.session.session_id;
    void this.run(async () => {
      await this.client.saveLatest(sessionId);
      if (this.active !== null && this.active.session.session_id === sessionId) {
        this.saved = true;
        this.renderActive();
      }
      this.setStatus('Saved.', 'success');
    });
  }

  private async loadLatest(): Promise<void> {
    await this.run(async () => {
      const record = await this.client.latest();
      if (record === null) {
        renderEmpty(this.history, 'No saved reading yet.');
        this.setStatus('No saved reading yet.', 'info');
        return;
      }
      renderRecord(this.history, record, 'Saved');
      this.setStatus('Loaded the latest saved reading.', 'info');
    });
  }

  private showView(view: 'reading' | 'settings'): void {
    if (view === 'settings') {
      this.readingView.hidden = true;
      this.settingsHost.hidden = false;
      this.settingsPanel.show();
    } else {
      // A dirty settings draft keeps the panel open until the user confirms.
      if (!this.settingsPanel.confirmDiscard()) {
        return;
      }
      this.settingsPanel.hide();
      this.settingsHost.hidden = true;
      this.readingView.hidden = false;
    }
    const onReading = view === 'reading';
    this.readingTab.setAttribute('aria-selected', String(onReading));
    this.readingTab.tabIndex = onReading ? 0 : -1;
    this.settingsTab.setAttribute('aria-selected', String(!onReading));
    this.settingsTab.tabIndex = onReading ? -1 : 0;
  }

  private onTabKeydown(event: KeyboardEvent): void {
    if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') {
      return;
    }
    event.preventDefault();
    const next = this.readingTab.getAttribute('aria-selected') === 'true'
      ? this.settingsTab
      : this.readingTab;
    next.focus();
    next.click();
  }

  private async run(operation: () => Promise<void>): Promise<void> {
    if (this.busy) {
      return;
    }
    this.busy = true;
    this.setBusy(true);
    try {
      await operation();
    } catch (error) {
      this.setStatus(
        error instanceof Error ? error.message : 'Please try again.',
        'error'
      );
    } finally {
      this.busy = false;
      this.setBusy(false);
    }
  }

  private setBusy(busy: boolean): void {
    this.node.setAttribute('aria-busy', String(busy));
    this.status.setAttribute('aria-busy', String(busy));
    this.updateButtons();
  }

  private setActive(record: SessionRecord): void {
    this.active = record;
    this.saved = false;
    this.renderActive();
  }

  private renderActive(): void {
    if (this.active === null) {
      return;
    }
    renderRecord(this.current, this.active, this.saved ? 'Saved' : 'Unsaved');
  }

  private setStatus(text: string, tone: 'info' | 'success' | 'error'): void {
    this.status.textContent = text;
    this.status.dataset.tone = tone;
    this.updateButtons();
  }

  private clearError(): void {
    if (this.status.dataset.tone === 'error') {
      this.setStatus('', 'info');
    }
  }

  private updateButtons(): void {
    const hasCard = this.active !== null;
    const hasReading = this.active !== null && this.active.reading !== null;
    this.drawButton.disabled = this.busy;
    this.readButton.disabled = this.busy || !hasCard || hasReading;
    this.saveButton.disabled = this.busy || !hasCard;
    this.latestButton.disabled = this.busy;
  }
}

function renderEmpty(target: HTMLElement, text: string): void {
  const paragraph = document.createElement('p');
  paragraph.className = 'jp-TarotSidebar-empty';
  paragraph.textContent = text;
  target.replaceChildren(paragraph);
}

function renderRecord(
  target: HTMLElement,
  record: SessionRecord,
  state: 'Unsaved' | 'Saved'
): void {
  const { session, reading } = record;
  const { card, orientation } = session.cards[0];
  const orientationLabel = orientation === 'upright' ? 'Upright' : 'Reversed';
  const nodes: HTMLElement[] = [];

  const name = document.createElement('h4');
  name.className = 'jp-TarotSidebar-cardName';
  name.textContent = card.name;
  nodes.push(name);

  const badges = document.createElement('div');
  badges.className = 'jp-TarotSidebar-badgeRow';
  badges.append(badge(orientationLabel));
  nodes.push(badges);

  const question = document.createElement('p');
  question.className = 'jp-TarotSidebar-message';
  question.textContent = session.question;
  nodes.push(question);

  const keywords = document.createElement('ul');
  keywords.className = 'jp-TarotSidebar-keywords';
  keywords.setAttribute('aria-label', `${orientationLabel} keywords`);
  for (const keyword of card[orientation]) {
    const item = document.createElement('li');
    item.textContent = keyword;
    keywords.append(item);
  }
  nodes.push(keywords);

  if (reading !== null) {
    nodes.push(renderReading(reading));
  }

  const stateLine = document.createElement('p');
  stateLine.className = 'jp-TarotSidebar-state';
  stateLine.textContent = state;
  nodes.push(stateLine);

  target.replaceChildren(...nodes);
}

function renderReading(reading: NonNullable<SessionRecord['reading']>): HTMLElement {
  const block = document.createElement('div');
  block.className = 'jp-TarotSidebar-reading';
  block.append(
    readingPart('Summary', reading.summary),
    readingPart('Card', reading.card_interpretations[0]),
    readingPart('Advice', reading.advice)
  );
  if (reading.provider !== 'FakeAIProvider' && reading.provider !== '') {
    const provider = document.createElement('p');
    provider.className = 'jp-TarotSidebar-hint';
    provider.textContent = `Provider: ${reading.provider}`;
    block.append(provider);
  }
  return block;
}

function readingPart(label: string, text: string): HTMLElement {
  const part = document.createElement('div');
  part.className = 'jp-TarotSidebar-readingPart';
  const heading = document.createElement('span');
  heading.className = 'jp-TarotSidebar-readingLabel';
  heading.textContent = label;
  const body = document.createElement('p');
  body.className = 'jp-TarotSidebar-message';
  body.textContent = text;
  part.append(heading, body);
  return part;
}

function badge(text: string): HTMLElement {
  const element = document.createElement('span');
  element.className = 'jp-TarotSidebar-badge';
  element.textContent = text;
  return element;
}

function requireElement<T extends Element>(root: ParentNode, selector: string): T {
  const element = root.querySelector<T>(selector);
  if (element === null) {
    throw new Error(`Tarot sidebar template is missing ${selector}.`);
  }
  return element;
}
