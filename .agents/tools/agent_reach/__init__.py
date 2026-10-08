# -*- coding: utf-8 -*-
"""Agent Reach — Give your AI Agent eyes to see the entire internet."""


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
__version__ = "1.5.0"
__author__ = "Neo Reid"

from agent_reach.core import AgentReach

__all__ = ["AgentReach"]
