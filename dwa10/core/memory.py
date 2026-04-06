"""
DWA-10 Memory Store.
CoreMemory   = active anchors (fast access, P0+P1)
ArchivalMemory = dormant anchors (P2 or decayed P1)
"""

from __future__ import annotations
import time
from typing import Dict, List, Optional
from .anchor import Anchor

PROMOTE_THRESHOLD = 3        # usage_count to promote P2 → archival → core
ARCHIVE_PRIORITY_FLOOR = 0.2 # below this P1 moves to archival


class MemoryStore:
    def __init__(self):
        self.core: Dict[str, Anchor] = {}        # id → Anchor
        self.archival: Dict[str, Anchor] = {}    # id → Anchor
        self._ash_index: Dict[str, str] = {}     # ash_id → anchor_id

    # ── WRITE ────────────────────────────────────────────────────────────────

    def add(self, anchor: Anchor) -> Anchor:
        """Add or update anchor. Deduplicates by ASH-ID."""
        existing_id = self._ash_index.get(anchor.ash_id)
        if existing_id:
            existing = self._get(existing_id)
            if existing and anchor.version > existing.version:
                anchor.id = existing.id
                self._store(anchor)
            return self._get(existing_id) or anchor

        self._store(anchor)
        self._ash_index[anchor.ash_id] = anchor.id
        return anchor

    def _store(self, anchor: Anchor) -> None:
        if anchor.class_ == "P0" or anchor.class_ == "P1":
            self.core[anchor.id] = anchor
            self.archival.pop(anchor.id, None)
        else:
            self.archival[anchor.id] = anchor
            self.core.pop(anchor.id, None)

    def _get(self, anchor_id: str) -> Optional[Anchor]:
        return self.core.get(anchor_id) or self.archival.get(anchor_id)

    # ── READ ─────────────────────────────────────────────────────────────────

    def all_active(self) -> List[Anchor]:
        return list(self.core.values())

    def all_anchors(self) -> List[Anchor]:
        return list(self.core.values()) + list(self.archival.values())

    # ── LIFECYCLE ────────────────────────────────────────────────────────────

    def decay_all(self) -> None:
        for a in list(self.core.values()) + list(self.archival.values()):
            a.decay()

    def prune_dead(self) -> int:
        """Remove anchors below epsilon. Returns count pruned."""
        dead = [a for a in self.all_anchors() if not a.is_alive()]
        for a in dead:
            self.core.pop(a.id, None)
            self.archival.pop(a.id, None)
            self._ash_index.pop(a.ash_id, None)
        return len(dead)

    def rebalance(self) -> None:
        """Promote/demote anchors between core and archival based on priority."""
        for a in list(self.core.values()):
            if a.class_ == "P1" and a.priority < ARCHIVE_PRIORITY_FLOOR:
                self.archival[a.id] = a
                del self.core[a.id]

        for a in list(self.archival.values()):
            if a.usage_count >= PROMOTE_THRESHOLD:
                a.class_ = "P1"
                self.core[a.id] = a
                del self.archival[a.id]

    def stats(self) -> dict:
        return {
            "core": len(self.core),
            "archival": len(self.archival),
            "total": len(self.core) + len(self.archival),
        }
