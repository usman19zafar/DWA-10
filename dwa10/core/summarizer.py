"""
DWA-10 Summarizer.
Triggers a rolling summary when message count or window pressure hits threshold.
Free tier: heuristic compression (no LLM call).
"""

from __future__ import annotations
import time
from typing import List, Optional
from .anchor import Anchor
from .memory import MemoryStore

SUMMARY_MSG_THRESHOLD = 15
SUMMARY_WINDOW_THRESHOLD = 0.70   # 70% of estimated window used


def should_summarize(message_count: int, window_utilization: float) -> bool:
    return (
        message_count >= SUMMARY_MSG_THRESHOLD
        or window_utilization >= SUMMARY_WINDOW_THRESHOLD
    )


def generate_summary(store: MemoryStore, message_count: int) -> Optional[Anchor]:
    """
    Compress low-priority anchors into a single summary anchor.
    Returns the summary Anchor (caller must add to store).
    """
    p2_anchors = [a for a in store.archival.values() if a.class_ == "P2"]
    if len(p2_anchors) < 3:
        return None

    # Sort by utility descending, keep top content
    p2_anchors.sort(key=lambda a: a.utility(), reverse=True)
    top = p2_anchors[:8]

    summary_lines = [f"[Session summary @ msg {message_count}]"]
    for a in top:
        summary_lines.append(f"• {a.content[:80]}")

    summary_content = "\n".join(summary_lines)

    # Retire compressed anchors
    for a in top:
        store.archival.pop(a.id, None)
        store.core.pop(a.id, None)

    summary = Anchor(
        content=summary_content,
        scope="Session",
        class_="P1",
        priority=0.7,
        anchor_accuracy="estimated",
        origin_ids=[a.id for a in top],
    )
    return summary
