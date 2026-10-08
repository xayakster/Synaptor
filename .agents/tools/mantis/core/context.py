import sys, os
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
_TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
if _TOOL_DIR not in sys.path:
    sys.path.insert(0, _TOOL_DIR)
import contextvars
from dataclasses import dataclass
from typing import Optional

@dataclass
class RunContext:
    jail_dir: str
    db_path: str
    target_file: str = ""
    sandbox: object = None
    run_id: str = ""
    sandbox_executed: bool = False
    snapshot_id: str = ""
    budget_controller: object = None
    static_sandbox_attempts: int = 0
    active_node: str = ""
    # The scan mode this run was launched with ("whole", "file-by-file",
    # "cross-functional"). Empty when the caller predates the field; every
    # consumer must treat empty as "unknown" and fall back to per-campaign
    # behavior (INV-6).
    scan_mode: str = ""
    # The directory finding filepaths should be stored relative to -- the
    # enclosing repository when a scan targets a single file inside one.
    # A file-sized target cannot know its own repository; only the caller
    # does. Empty means "unknown": canonicalization falls back to the
    # jail-anchored behavior that predates the field (INV-6).
    path_root: str = ""

current_run_context: contextvars.ContextVar[Optional[RunContext]] = contextvars.ContextVar(
    "current_run_context", default=None
)

