# -*- coding: utf-8 -*-
"""Cross-channel backends.

A backend here is an upstream runtime that serves MULTIPLE channels
(e.g. OpenCLI covers xiaohongshu/reddit/bilibili/twitter through one
browser session), as opposed to the per-platform tools probed inside
each channel file.
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
from .opencli import (  # noqa: F401
    OPENCLI_EXTENSION_URL,
    OPENCLI_PACKAGE,
    OpenCLIStatus,
    opencli_status,
    opencli_summary,
)
