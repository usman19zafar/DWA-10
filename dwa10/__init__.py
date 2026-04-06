"""
dwa10-memory — Indestructible memory for Claude.
Free tier: in-session anchor engine.
Pro: zulfr.com
"""

from .session import DWASession
from .core.anchor import Anchor
from .tiers import DWATierError

__version__ = "0.1.0"
__all__ = ["DWASession", "Anchor", "DWATierError"]
