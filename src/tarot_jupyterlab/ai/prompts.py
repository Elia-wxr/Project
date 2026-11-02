"""Prompt construction for AI tarot readings.

The prompt is deliberately bounded: it contains only the user question,
the drawn cards with their spread positions, orientation keywords and the
strict output format.  No history, storage objects, API keys or other
user data are ever embedded.
"""

from __future__ import annotations

from tarot_jupyterlab.errors import InvalidSessionError
from tarot_jupyterlab.models import DrawnCard, ReadingLanguage, Session

#: Instruction line for each supported reading language.
LANGUAGE_INSTRUCTION: dict[ReadingLanguage, str] = {
    "zh-CN": "Write the entire reading in Simplified Chinese (简体中文).",
    "en": "Write the entire reading in English.",
    "bilingual": (
        "Write every section in both English and Simplified Chinese, e.g. an English "
        "sentence followed by its 简体中文 translation."
    ),
}

_PROMPT_TEMPLATE = """\
You are a thoughtful tarot reader. This reading is for entertainment and self-reflection only; do not give medical, legal, financial or psychological advice.

Question:
{question}

Card facts (drawn cards, in spread position order):
{card_facts}

{language_instruction}

Output format (follow it exactly and do not add any text outside the tags):
<summary>
A concise 2-4 sentence overview of the reading as a whole, at most 100 words.
</summary>
<card>
An interpretation of one drawn card, at most 60 words. Repeat one <card> block per drawn card, in the same order as the card facts above.
</card>
<advice>
Actionable closing advice drawn from all the cards together, at most 100 words.
</advice>
"""


def build_reading_prompt(session: Session, *, language: ReadingLanguage = "zh-CN") -> str:
    """Build a bounded prompt from the question and drawn cards.

    The prompt separates the user question, the card facts (name, spread
    position, arcana, orientation and the orientation-specific keywords),
    the requested response language and the strict output format.

    Raises:
        InvalidSessionError: when the question is empty, the session has
            no drawn cards, or ``language`` is not a supported reading
            language.
    """
    if language not in LANGUAGE_INSTRUCTION:
        raise InvalidSessionError(f"Unsupported reading language: {language!r}.")
    question = session.question.strip()
    if not question:
        raise InvalidSessionError("Cannot build a reading prompt for an empty question.")
    if not session.cards:
        raise InvalidSessionError("Cannot build a reading prompt without drawn cards.")
    card_facts = "\n".join(
        _card_fact_line(index, drawn) for index, drawn in enumerate(session.cards, start=1)
    )
    return _PROMPT_TEMPLATE.format(
        question=question,
        card_facts=card_facts,
        language_instruction=LANGUAGE_INSTRUCTION[language],
    )


def _card_fact_line(index: int, drawn: DrawnCard) -> str:
    keywords = drawn.card.upright if drawn.orientation == "upright" else drawn.card.reversed
    return (
        f'{index}. Position "{drawn.position}" — {drawn.card.name} '
        f"({drawn.card.arcana}, {drawn.orientation})\n" + "   Keywords: " + ", ".join(keywords)
    )


__all__ = ["LANGUAGE_INSTRUCTION", "build_reading_prompt"]
