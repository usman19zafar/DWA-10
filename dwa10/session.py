"""
DWA-10 Session — drop-in wrapper around Anthropic SDK.
Free tier: in-session memory with automatic anchor management.

Usage:
    from dwa10 import DWASession

    session = DWASession(api_key="sk-...")
    response = session.chat("My name is John and I'm building a SaaS.")
    print(response)
"""

from __future__ import annotations
import uuid
import time
from typing import List, Optional, Dict, Any

try:
    import anthropic
except ImportError:
    anthropic = None  # type: ignore

from .core.anchor import Anchor
from .core.memory import MemoryStore
from .core.packer import pack
from .core.extractor import extract_anchors, manual_anchor
from .core.summarizer import should_summarize, generate_summary
from .core import export as _export
from .tiers import require_pro, DWATierError

DEFAULT_MODEL = "claude-sonnet-4-20250514"
DEFAULT_MAX_TOKENS = 1024
CONTEXT_WINDOW_ESTIMATE = 180_000  # tokens


class DWASession:
    """
    A memory-enhanced Claude session.

    Parameters
    ----------
    api_key : str, optional
        Anthropic API key. Falls back to ANTHROPIC_API_KEY env var.
    model : str
        Claude model to use.
    token_budget : int
        Max tokens reserved for anchor context block.
    system : str, optional
        Base system prompt. Memory context is prepended automatically.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        token_budget: int = 800,
        system: Optional[str] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ):
        if anthropic is None:
            raise ImportError(
                "anthropic package required: pip install anthropic"
            )

        self._client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        self.model = model
        self.token_budget = token_budget
        self.base_system = system or "You are a helpful assistant."
        self.max_tokens = max_tokens

        self.session_id = str(uuid.uuid4())
        self.store = MemoryStore()
        self.history: List[Dict[str, str]] = []
        self.message_count = 0
        self._used_tokens = 0

    # ── PUBLIC API ────────────────────────────────────────────────────────────

    def chat(self, user_message: str) -> str:
        """Send a message, returns Claude's response string."""
        self.message_count += 1
        msg_id = str(uuid.uuid4())

        # 1. Pack anchor context
        context_block, selected = pack(self.store, self.token_budget)

        # 2. Build system prompt
        if context_block:
            system = f"{context_block}\n\n{self.base_system}"
        else:
            system = self.base_system

        # 3. Append user message to history
        self.history.append({"role": "user", "content": user_message})

        # 4. Call Claude
        response = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=self.history,
        )

        assistant_text = response.content[0].text
        self._used_tokens = getattr(response.usage, "input_tokens", 0)

        # 5. Append assistant reply to history
        self.history.append({"role": "assistant", "content": assistant_text})

        # 6. Extract anchors from BOTH user message and response
        for text in [user_message, assistant_text]:
            new_anchors = extract_anchors(text, origin_id=msg_id)
            for a in new_anchors:
                self.store.add(a)

        # Reinforce selected anchors (they were referenced)
        for a in selected:
            a.reinforce()

        # 7. Rolling summary check
        window_util = self._used_tokens / CONTEXT_WINDOW_ESTIMATE
        if should_summarize(self.message_count, window_util):
            summary = generate_summary(self.store, self.message_count)
            if summary:
                self.store.add(summary)

        return assistant_text

    def anchor(
        self,
        content: str,
        scope: str = "Session",
        class_: str = "P1",
    ) -> Anchor:
        """Manually anchor a critical fact. Always exact accuracy."""
        a = manual_anchor(content, scope=scope, class_=class_)
        return self.store.add(a)

    def memory_stats(self) -> dict:
        """Return current memory state."""
        s = self.store.stats()
        s["message_count"] = self.message_count
        s["session_id"] = self.session_id
        return s

    def export_json(self) -> dict:
        """Export full memory as JSON dict."""
        return _export.export_json(self.store, self.session_id)

    def export_markdown(self) -> str:
        """Export memory as human-readable Markdown string."""
        return _export.export_markdown(self.store, self.session_id)

    def save(self, path: str = "dwa10_memory") -> None:
        """Save memory to disk (JSON + Markdown)."""
        _export.save(self.store, path, self.session_id)

    def load(self, path: str = "dwa10_memory") -> int:
        """Load memory from disk. Returns anchors loaded."""
        return _export.load(self.store, path)

    # ── PRO STUBS ─────────────────────────────────────────────────────────────

    def enable_cross_session(self, *args, **kwargs):
        """Cross-session persistence — Pro feature."""
        require_pro("cross_session_persistence")

    def enable_multi_agent(self, *args, **kwargs):
        """Multi-agent memory sharing — Pro feature."""
        require_pro("multi_agent_memory")

    def enable_audit_log(self, *args, **kwargs):
        """Audit logging — Corporate feature."""
        require_pro("audit_logs")

    def __repr__(self) -> str:
        s = self.store.stats()
        return (
            f"<DWASession model={self.model} "
            f"msgs={self.message_count} "
            f"anchors={s['total']}>"
        )
