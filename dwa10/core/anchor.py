"""
DWA-10 Anchor — the atomic unit of memory.
Each anchor is a versioned, scoped, prioritized fact.
"""

from __future__ import annotations
import hashlib
import math
import time
import uuid
from dataclasses import dataclass, field
from typing import List, Optional

DECAY_LAMBDA = 0.01          # decay rate per second (tunable)
CLASS_MAX = {"P0": 1.0, "P1": 0.8, "P2": 0.5}
REINFORCE_DELTA = 0.05


@dataclass
class Anchor:
    content: str
    scope: str = "Session"           # Global|Thread|Task|Session|Org
    class_: str = "P1"               # P0|P1|P2
    priority: float = 0.5
    version: int = 1
    last_reinforced: float = field(default_factory=time.time)
    token_estimate: int = 0
    origin_ids: List[str] = field(default_factory=list)
    ash_id: str = ""
    anchor_accuracy: str = "estimated"
    dependencies: List[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    usage_count: int = 0

    def __post_init__(self):
        if not self.ash_id:
            self.ash_id = self._compute_ash()
        if not self.token_estimate:
            self.token_estimate = max(1, len(self.content) // 4)

    def _compute_ash(self) -> str:
        return hashlib.sha256(self.content.encode()).hexdigest()[:16]

    def decay(self) -> None:
        """Apply exponential decay based on time since last reinforcement."""
        if self.class_ == "P0":
            return  # P0 never decays
        dt = time.time() - self.last_reinforced
        self.priority = self.priority * math.exp(-DECAY_LAMBDA * dt)

    def reinforce(self) -> None:
        """Boost priority on reference."""
        self.last_reinforced = time.time()
        self.usage_count += 1
        cap = CLASS_MAX.get(self.class_, 0.5)
        self.priority = min(self.priority + REINFORCE_DELTA, cap)

    def utility(self, relevance: float = 1.0) -> float:
        """Utility density = (priority × relevance) / token_estimate."""
        return (self.priority * relevance) / max(1, self.token_estimate)

    def is_alive(self, epsilon: float = 0.01) -> bool:
        return self.priority >= epsilon or self.class_ == "P0"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "scope": self.scope,
            "class": self.class_,
            "priority": round(self.priority, 4),
            "version": self.version,
            "last_reinforced": self.last_reinforced,
            "token_estimate": self.token_estimate,
            "origin_ids": self.origin_ids,
            "ash_id": self.ash_id,
            "anchor_accuracy": self.anchor_accuracy,
            "dependencies": self.dependencies,
            "usage_count": self.usage_count,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Anchor":
        return cls(
            id=d["id"],
            content=d["content"],
            scope=d.get("scope", "Session"),
            class_=d.get("class", "P1"),
            priority=d.get("priority", 0.5),
            version=d.get("version", 1),
            last_reinforced=d.get("last_reinforced", time.time()),
            token_estimate=d.get("token_estimate", 0),
            origin_ids=d.get("origin_ids", []),
            ash_id=d.get("ash_id", ""),
            anchor_accuracy=d.get("anchor_accuracy", "estimated"),
            dependencies=d.get("dependencies", []),
            usage_count=d.get("usage_count", 0),
        )

    def context_line(self) -> str:
        """Compact single-line representation for context injection."""
        return f"[{self.class_}|{self.scope}] {self.content}"
