"""
DWA-10 Export / Import.
Dual format: JSON (machine) + Markdown (human).
Free tier: in-session only — export is manual/on-demand.
"""

from __future__ import annotations
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from .anchor import Anchor
from .memory import MemoryStore

FORMAT_VERSION = "DWA10-free-v1.0"


# ── EXPORT ───────────────────────────────────────────────────────────────────

def export_json(store: MemoryStore, session_id: Optional[str] = None) -> dict:
    anchors = [a.to_dict() for a in store.all_anchors()]
    stats = store.stats()
    return {
        "session_id": session_id or str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "anchors": anchors,
        "meta": {
            "total_anchors": stats["total"],
            "active_anchors": stats["core"],
            "archival_anchors": stats["archival"],
            "export_format_version": FORMAT_VERSION,
        },
    }


def export_markdown(store: MemoryStore, session_id: Optional[str] = None) -> str:
    data = export_json(store, session_id)
    lines = [
        "# DWA-10 Session Export",
        f"\n**Session ID:** {data['session_id']}",
        f"**Timestamp:** {data['timestamp']}",
        f"**Format:** {FORMAT_VERSION}",
        "\n## Anchors\n",
    ]
    for a in data["anchors"]:
        lines += [
            f"- **[{a['class']}|{a['scope']}]** {a['content'][:120]}",
            f"  - Priority: {a['priority']} | Version: {a['version']} | ASH-ID: {a['ash_id']}",
            f"  - Accuracy: {a['anchor_accuracy']} | Tokens: {a['token_estimate']}",
            "",
        ]
    meta = data["meta"]
    lines += [
        "## Meta",
        f"Total: {meta['total_anchors']} | Active: {meta['active_anchors']} | Archival: {meta['archival_anchors']}",
    ]
    return "\n".join(lines)


def save(store: MemoryStore, path: str = "dwa10_memory", session_id: Optional[str] = None) -> None:
    """Save both JSON and Markdown exports to disk."""
    data = export_json(store, session_id)
    Path(f"{path}.json").write_text(json.dumps(data, indent=2))
    Path(f"{path}.md").write_text(export_markdown(store, session_id))


# ── IMPORT ───────────────────────────────────────────────────────────────────

def load(store: MemoryStore, path: str = "dwa10_memory") -> int:
    """Load from JSON file into store. Returns number of anchors loaded."""
    json_path = Path(f"{path}.json")
    if not json_path.exists():
        return 0

    data = json.loads(json_path.read_text())
    count = 0
    for d in data.get("anchors", []):
        a = Anchor.from_dict(d)
        store.add(a)
        count += 1
    return count


def load_from_dict(store: MemoryStore, data: dict) -> int:
    """Load from an already-parsed JSON dict."""
    count = 0
    for d in data.get("anchors", []):
        a = Anchor.from_dict(d)
        store.add(a)
        count += 1
    return count
