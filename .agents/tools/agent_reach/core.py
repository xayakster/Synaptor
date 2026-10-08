# -*- coding: utf-8 -*-
"""
AgentReach — installer, doctor, and configuration tool.

Agent Reach helps AI agents install and configure upstream platform tools
(twitter-cli, yt-dlp, mcporter, gh CLI, etc.). After installation, agents
call the upstream tools directly — no wrapper layer needed.

Usage:
    from agent_reach.doctor import check_all, format_report
    from agent_reach.config import Config

    config = Config()
    results = check_all(config)
    print(format_report(results))
"""


import sys, os
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
_PKG_PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PKG_PARENT not in sys.path:
    sys.path.insert(0, _PKG_PARENT)
from typing import Dict, Optional

from agent_reach.config import Config


class AgentReach:
    """Give your AI Agent eyes to see the entire internet.

    This class provides health-check functionality.
    For reading/searching, use the upstream tools directly
    (see SKILL.md for commands).
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

    def doctor(self) -> Dict[str, dict]:
        """Check all channel availability."""
        from agent_reach.doctor import check_all
        return check_all(self.config)

    def doctor_report(self) -> str:
        """Get formatted health report."""
        from agent_reach.doctor import check_all, format_report
        return format_report(check_all(self.config))
