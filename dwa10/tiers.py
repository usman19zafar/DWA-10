"""
DWA-10 Tier enforcement.
Free tier: Core anchor engine only (layer 1).
Pro/Corporate: layers 2-5 via zulfr.com.
"""

UPGRADE_URL = "https://zulfr.com/dwa10-pro"

FREE_FEATURES = {
    "in_session_memory",
    "heuristic_extraction",
    "manual_anchoring",
    "context_packing",
    "rolling_summary",
    "export_on_demand",
}

PRO_FEATURES = {
    "cross_session_persistence",
    "llm_assisted_extraction",
    "dependency_graph",
    "multi_agent_memory",
    "compression_hierarchy",
    "audit_logs",
    "team_memory",
}


class DWATierError(Exception):
    """Raised when a free-tier user accesses a Pro feature."""

    def __init__(self, feature: str):
        self.feature = feature
        super().__init__(
            f"\n\n🔒 '{feature}' is a DWA-10 Pro feature.\n"
            f"   Upgrade at: {UPGRADE_URL}\n"
        )


def require_pro(feature: str) -> None:
    """Call this at the top of any Pro-only function."""
    raise DWATierError(feature)
