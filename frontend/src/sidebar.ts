import { Widget } from '@lumino/widgets';

import { TarotClient } from './api';
import type { SessionRecord } from './types';

const template = `
  <h2>Tarot</h2>
  <p>For entertainment and self-reflection only.</p>
  <p>Your question and card details are sent to Socrates when you request a real reading.</p>
  <form>
    <label for="tarot-question">Your question</label>
    <textarea id="tarot-question" required rows="3"></textarea>
    <button type="submit" data-action="draw">Draw a card</button>
  </form>
  <p data-region="status" role="status" aria-live="polite"></p>
  <section aria-label="Current card" data-region="current"></section>
  <div class="tarot-actions">
    <button type="button" data-action="read">Generate reading</button>
    <button type="button" data-action="save">Save as latest</button>
  </div>
  <section aria-label="Latest saved reading">
    <h3>Latest saved reading</h3>
    <button type="button" data-action="latest">View latest</button>
    <div data-region="history"></div>
  </section>
`;

export class TarotSidebar extends Widget {
  private readonly question: HTMLTextAreaElement;
  private readonly drawButton: HTMLButtonElement;
  private readonly readButton: HTMLButtonElement;
  private readonly saveButton: HTMLButtonElement;
  private readonly latestButton: HTMLButtonElement;
  private readonly status: HTMLElement;
  private readonly current: HTMLElement;
  private readonly history: HTMLElement;
  private active: SessionRecord | null = null;
  private busy = false;

  constructor(private readonly client: TarotClient) {
    super();
    this.id = 'tarot-jupyterlab-sidebar';
    this.title.label = 'Tarot';
    this.title.caption = 'Tarot';
    this.addClass('tarot-sidebar');
    this.node.innerHTML = template;
    // These elements are defined by the fixed template above.
    this.question = this.node.querySelector('textarea')!;
    this.drawButton = this.node.querySelector('[data-action="draw"]')!;
    this.readButton = this.node.querySelector('[data-action="read"]')!;
    this.saveButton = this.node.querySelector('[data-action="save"]')!;
    this.latestButton = this.node.querySelector('[data-action="latest"]')!;
    this.status = this.node.querySelector('[data-region="status"]')!;
    this.current = this.node.querySelector('[data-region="current"]')!;
    this.history = this.node.querySelector('[data-region="history"]')!;

    this.node.querySelector('form')!.addEventListener('submit', event => {
      event.preventDefault();
      void this.run(async () => {
        this.setActive(await this.client.draw(this.question.value));
        this.status.textContent = 'Card drawn. Unsaved.';
      });
    });
    this.readButton.addEventListener('click', () => {
      if (this.active === null) {
        return;
      }
      const sessionId = this.active.session.session_id;
      void this.run(async () => {
        this.status.textContent = 'Generating reading…';
        this.setActive(await this.client.reading(sessionId));
        this.status.textContent = 'Reading ready. Unsaved.';
      });
    });
    this.saveButton.addEventListener('click', () => {
      if (this.active === null || !window.confirm('This replaces any previously saved reading. Continue?')) {
        return;
      }
      const sessionId = this.active.session.session_id;
      void this.run(async () => {
        await this.client.saveLatest(sessionId);
        this.status.textContent = 'Saved.';
      });
    });
    this.latestButton.addEventListener('click', () => {
      void this.run(async () => {
        const record = await this.client.latest();
        if (record === null) {
          this.history.textContent = 'No saved reading yet.';
        } else {
          renderRecord(this.history, record);
        }
      });
    });
    this.updateButtons();
  }

  async checkConnection(): Promise<void> {
    await this.run(async () => {
      await this.client.health();
      this.status.textContent = 'Connected to the Tarot server.';
    });
  }

  private async run(operation: () => Promise<void>): Promise<void> {
    if (this.busy) {
      return;
    }
    this.busy = true;
    this.updateButtons();
    try {
      await operation();
    } catch (error) {
      this.status.textContent = error instanceof Error ? error.message : 'Please try again.';
    } finally {
      this.busy = false;
      this.updateButtons();
    }
  }

  private setActive(record: SessionRecord): void {
    this.active = record;
    renderRecord(this.current, record);
  }

  private updateButtons(): void {
    this.drawButton.disabled = this.busy;
    this.readButton.disabled = this.busy || this.active === null || this.active.reading !== null;
    this.saveButton.disabled = this.busy || this.active === null;
    this.latestButton.disabled = this.busy;
  }
}

function renderRecord(target: HTMLElement, record: SessionRecord): void {
  const { session, reading } = record;
  const { card, orientation } = session.cards[0];
  const heading = document.createElement('h3');
  heading.textContent = `${card.name} · ${orientation === 'upright' ? 'Upright' : 'Reversed'}`;
  target.replaceChildren(heading);
  addParagraph(target, session.question);
  addParagraph(target, card[orientation].join(', '));

  if (reading !== null) {
    if (reading.provider === 'FakeAIProvider') {
      addParagraph(target, 'Demo reading (simulated).');
    }
    addParagraph(target, `Summary: ${reading.summary}`);
    addParagraph(target, `Card: ${reading.card_interpretations[0]}`);
    addParagraph(target, `Advice: ${reading.advice}`);
  }
}

function addParagraph(target: HTMLElement, text: string): void {
  const paragraph = document.createElement('p');
  paragraph.textContent = text;
  target.append(paragraph);
}
