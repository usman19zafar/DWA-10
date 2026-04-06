"""
DWA-10 Anchor Extractor (Free Tier).
Hybrid extraction: heuristic NER + keyword patterns.
LLM-assisted extraction is a Pro feature.
"""

from __future__ import annotations
import re
import time
from typing import List, Optional
from .anchor import Anchor

# Patterns that signal high-value facts worth anchoring
_FACT_PATTERNS = [
    r"\bmy name is\b",
    r"\bi am\b.{0,30}\b(developer|designer|manager|engineer|student|founder)\b",
    r"\bi (prefer|like|want|need|use|hate|love)\b",
    r"\bmy (goal|project|budget|deadline|company|team)\b",
    r"\b(always|never|must|should|require|critical|important)\b",
    r"\b\d{4}\b",                        # years
    r"\$[\d,]+",                          # money
    r"\b\d+\s*(days?|weeks?|months?)\b", # time references
    r"\bemail\b.{0,60}@",               # emails
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _FACT_PATTERNS]


def _score_sentence(sentence: str) -> float:
    """Heuristic relevance score 0–1."""
    hits = sum(1 for p in _COMPILED if p.search(sentence))
    return min(hits / 3.0, 1.0)


def _split_sentences(text: str) -> List[str]:
    raw = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in raw if len(s.strip()) > 15]


def extract_anchors(
    text: str,
    origin_id: Optional[str] = None,
    threshold: float = 0.3,
) -> List[Anchor]:
    """
    Extract anchors from text using heuristics.
    Returns list of new Anchor objects (not yet added to store).
    """
    sentences = _split_sentences(text)
    anchors = []

    for sentence in sentences:
        score = _score_sentence(sentence)
        if score < threshold:
            continue

        class_ = "P1" if score >= 0.6 else "P2"
        priority = 0.6 if class_ == "P1" else 0.35

        a = Anchor(
            content=sentence,
            scope="Session",
            class_=class_,
            priority=priority,
            anchor_accuracy="estimated",
            origin_ids=[origin_id] if origin_id else [],
        )
        anchors.append(a)

    return anchors


def manual_anchor(
    content: str,
    scope: str = "Session",
    class_: str = "P1",
    origin_id: Optional[str] = None,
) -> Anchor:
    """User-driven anchoring — always exact accuracy, P0 allowed."""
    return Anchor(
        content=content,
        scope=scope,
        class_=class_,
        priority={"P0": 1.0, "P1": 0.8, "P2": 0.5}.get(class_, 0.5),
        anchor_accuracy="exact",
        origin_ids=[origin_id] if origin_id else [],
    )
