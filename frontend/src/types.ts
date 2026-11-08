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
