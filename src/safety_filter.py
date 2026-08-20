"""Two independent safety checks used by the AI chat feature:

1. `is_serious_topic` — run on incoming conversation context *before*
   generating a reply. Detects grief/condolence/crisis talk so the bot can
   suppress AI replies entirely rather than risk joking into a serious
   moment.
2. `is_unsafe_output` — run on Gemini's generated text *before* it's sent.
   Blocks threats, self-harm phrases, and slurs targeting protected
   classes; the caller should regenerate once or suppress rather than send.

Slurs are intentionally not hardcoded in source — they're loaded from
data/blocklist.txt (one term per line, '#' comments ignored), which ships
empty. Fill it in with terms relevant to your community's moderation policy.
"""

from __future__ import annotations

import functools
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

BLOCKLIST_PATH = Path(__file__).resolve().parent.parent / "data" / "blocklist.txt"

THREAT_PATTERNS = [
    r"\bi(?:'ll| will| am going to)\s+(?:kill|hurt|beat up|stab|shoot|attack)"
    r"\s+(?:you|u|him|her|them)\b",
    r"\bi(?:'m| am) going to (?:hurt|kill) you\b",
    r"\bcome to your (?:house|home) and (?:hurt|kill)\b",
]

SELF_HARM_PATTERNS = [
    r"\bkill\s*yourself\b",
    r"\bkys\b",
    r"\byou should die\b",
    r"\bgo die\b",
    r"\bend your life\b",
    r"\bnobody would miss you\b",
]

# Phrases used to *detect* the user is in a serious/crisis moment (distinct
# from SELF_HARM_PATTERNS, which detect the bot's own output attacking someone).
SERIOUS_TOPIC_PATTERNS = [
    r"\bpassed away\b",
    r"\bpassed last (?:night|week|month)\b",
    r"\bmy (?:dad|mom|father|mother|brother|sister|grandma|grandpa|friend) died\b",
    r"\bfuneral\b",
    r"\brip\b.{0,20}\b(19|20)\d{2}\b",
    r"\bi (?:want to|wanna) die\b",
    r"\bi(?:'m| am)? (?:\w+ )?don'?t want to (?:live|be here) anymore\b",
    r"\bsuicidal\b",
    r"\bself[\s-]?harm\b",
    r"\bi(?:'m| am) thinking of ending it\b",
    r"\bcondolences\b",
    r"\bin loving memory\b",
]


@functools.lru_cache(maxsize=1)
def _load_blocklist() -> frozenset[str]:
    if not BLOCKLIST_PATH.exists():
        return frozenset()
    terms = set()
    for line in BLOCKLIST_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip().lower()
        if line and not line.startswith("#"):
            terms.add(line)
    return frozenset(terms)


def is_serious_topic(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in SERIOUS_TOPIC_PATTERNS)


def is_unsafe_output(text: str) -> bool:
    lowered = text.lower()
    if any(re.search(p, lowered) for p in THREAT_PATTERNS + SELF_HARM_PATTERNS):
        return True

    blocklist = _load_blocklist()
    if blocklist:
        words = set(re.findall(r"[a-z']+", lowered))
        if words & blocklist:
            return True

    return False
