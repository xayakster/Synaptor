#!/usr/bin/env python3
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
import sys, os
_TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
if _TOOL_DIR not in sys.path:
    sys.path.insert(0, _TOOL_DIR)
"""Mantis MCP server: a secure development loop over stdio.

Exposes Mantis's deterministic knowledge -- the tree-sitter structural
index, the persistent findings database, and threat-model-informed security
guidance -- as MCP tools a coding agent calls while editing, plus a
budget-capped scoped scan that runs the full Mantis pipeline over a change
set in the background. The intended loop: edit, call mantis_check_change on
the diff, fix or verify what it raises, and let mantis_scan_change audit
the touched files in parallel; the next check_change sees whatever the scan
found, because both read the same per-repo .mantis/knowledge.db.

Design rules, in force everywhere in this file:

- The server NEVER calls an LLM. Tier-1 tools are deterministic reads over
  the catalog and the findings database; the Tier-2 scan spawns the
  existing pipeline (main.py) as a subprocess that owns its own budget.
- The gate fails CLOSED. A missing index, a missing database, or a file no
  scan has ever covered yields REVIEW with instructions -- never PASS. PASS
  means "every check ran and nothing known intersects this change", not
  "secure".
- Nothing writes outside the repo's .mantis/ directory, and read-only
  tools write nothing at all: sqlite3.connect() creates files, so every
  read path checks existence before opening.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

_REF_ROOT = Path(__file__).resolve().parent.parent
if str(_REF_ROOT) not in sys.path:
    sys.path.insert(0, str(_REF_ROOT))

# Finding statuses that still demand attention. Lowercased for comparison:
# the database folds status casing at the door, but older rows may predate
# that. patch_verified is deliberately absent -- a verified fix is closed.
OPEN_FINDING_STATUSES = {
    "reported",
    "confirmed",
    "viable",
    "reproduced",
    "dynamic_confirmed",
    "static_confirmed",
    "provisionally_valid",
    "valid",
    "needs_research",
}

# Severities (or priorities, when severity is absent) that block the gate.
BLOCKING_SEVERITIES = {"CRITICAL", "HIGH"}

# Callers listed per changed function in the blast radius. A cap, not a
# truncation of the analysis: the verdict reflects every edge, the listing
# stays readable.
MAX_CALLERS_SHOWN = 10

# Maximum server-side wait for mantis_scan_status long-polling, so an MCP
# client can block on a running scan without burning agent turns in a poll loop.
MAX_WAIT_SECONDS = 60.0

# Line proximity window around a diff hunk for findings outside any function.
DIFF_LINE_PROXIMITY = 3

VERDICT_PASS = "PASS"
VERDICT_REVIEW = "REVIEW"
VERDICT_BLOCK = "BLOCK"

_VERDICT_RANK = {VERDICT_PASS: 0, VERDICT_REVIEW: 1, VERDICT_BLOCK: 2}


class MantisState:
    """Per-repo paths and live scan registry for one server process."""

    def __init__(self, repo_root: str):
        self.repo = Path(repo_root).resolve()
        self.home = self.repo / ".mantis"
        self.db_path = str(self.home / "knowledge.db")
        self.scans: Dict[str, Dict[str, Any]] = {}
        self._scan_events: Dict[str, threading.Event] = {}
        self._lock = threading.Lock()

    def ensure_home(self) -> None:
        """Creates .mantis/ and the knowledge database. Write paths only."""
        self.home.mkdir(parents=True, exist_ok=True)
        if not os.path.exists(self.db_path):
            from core.database import init_db

            init_db(self.db_path)

    def db_exists(self) -> bool:
        return os.path.exists(self.db_path)

    def state_dir(self) -> str:
        from core.structural_index import state_dir_for_db

        return state_dir_for_db(self.db_path)

    def index(self):
        from core.structural_index import StructuralIndex

        return StructuralIndex(self.state_dir())

    def rel(self, filepath: str) -> str:
        """Repo-relative form of a path that may arrive absolute or relative.

        Anything that does not resolve inside the repo returns "" -- refused,
        not reinterpreted. The old fallbacks turned /etc/passwd into
        etc/passwd and passed ../escape through verbatim, handing the scan
        tier paths outside the repository it serves.
        """
        clean = str(filepath or "").replace("\\", "/").strip()
        if not clean:
            return ""
        p = Path(clean)
        if p.is_absolute():
            try:
                clean = str(p.resolve().relative_to(self.repo)).replace("\\", "/")
            except (OSError, ValueError):
                return ""
        else:
            clean = clean.removeprefix("./")
        if ".." in Path(clean).parts:
            return ""
        return clean


# --- Tier 1: deterministic reads -------------------------------------------------


def reindex(state: MantisState) -> Dict[str, Any]:
    """Builds or incrementally refreshes the structural index for the repo."""
    from core.structural_index import build_structural_index

    state.ensure_home()
    t0 = time.time()
    manifest = build_structural_index(str(state.repo), state.state_dir()) or {}
    coverage = manifest.get("coverage") or {}
    return {
        "status": manifest.get("status", "unknown"),
        "files_indexed": coverage.get("indexed_files"),
        "total_files": coverage.get("total_files"),
        "elapsed_seconds": round(time.time() - t0, 2),
        "state_dir": state.state_dir(),
    }


def _resolve_symbol_rows(idx, name: str, filepath: str = "") -> List[Dict[str, Any]]:
    """Catalog rows for a symbol name, filtered by component-aligned path suffix."""
    res = idx.resolve_symbol(name, limit=50)
    rows = res.get("results") or []
    if filepath:
        want = str(filepath).replace("\\", "/").strip("/")
        rows = [
            r for r in rows
            if r.get("file_path") == want or str(r.get("file_path", "")).endswith("/" + want)
            or want.endswith("/" + str(r.get("file_path", "")))
        ]
    return rows


def find_symbol(state: MantisState, name: str, offset: int = 0) -> Dict[str, Any]:
    idx = state.index()
    if not idx.available():
        return {"available": False, "hint": "No structural index. Call mantis_reindex first."}
    out = idx.resolve_symbol(name, limit=20, offset=offset)
    out["available"] = True
    return out


def find_callers(state: MantisState, symbol: str, filepath: str = "") -> Dict[str, Any]:
    idx = state.index()
    if not idx.available():
        return {"available": False, "hint": "No structural index. Call mantis_reindex first."}
    rows = _resolve_symbol_rows(idx, symbol, filepath)
    if not rows:
        return {"available": True, "resolved": False,
                "hint": f"Symbol '{symbol}' not in the catalog."}
    if len({r["symbol_id"] for r in rows}) > 1 and not filepath:
        return {"available": True, "resolved": False, "ambiguous": True,
                "candidates": [
                    {"file_path": r.get("file_path"), "qualified_name": r.get("qualified_name"),
                     "start_line": r.get("start_line")} for r in rows[:10]
                ],
                "hint": "Disambiguate with the filepath argument."}
    out = idx.find_callers(rows[0])
    out.update({"available": True, "resolved": True, "symbol": rows[0].get("qualified_name")})
    return out


def find_callees(state: MantisState, symbol: str, filepath: str = "") -> Dict[str, Any]:
    idx = state.index()
    if not idx.available():
        return {"available": False, "hint": "No structural index. Call mantis_reindex first."}
    rows = _resolve_symbol_rows(idx, symbol, filepath)
    if not rows:
        return {"available": True, "resolved": False,
                "hint": f"Symbol '{symbol}' not in the catalog."}
    out = idx.find_callees(rows[0])
    out.update({"available": True, "resolved": True, "symbol": rows[0].get("qualified_name")})
    return out


def function_at(state: MantisState, filepath: str, line: int) -> Dict[str, Any]:
    idx = state.index()
    if not idx.available():
        return {"found": False, "available": False,
                "hint": "No structural index. Call mantis_reindex first."}
    out = idx.enclosing_symbol(state.rel(filepath), int(line))
    out["available"] = True
    return out


def _finding_view(f: Dict[str, Any]) -> Dict[str, Any]:
    """The fields a dev-loop consumer needs; drops embeddings and bulk prose."""
    return {
        "id": f.get("id"),
        "title": f.get("title"),
        "severity": f.get("severity"),
        "priority": f.get("priority"),
        "status": f.get("status"),
        "filepath": f.get("filepath"),
        "line_numbers": f.get("line_numbers"),
        "code_paths": f.get("code_paths"),
        "cwe": f.get("cwe"),
        "lineage_id": f.get("lineage_id"),
    }


def get_findings(state: MantisState, filepath: str = "", status: str = "") -> Dict[str, Any]:
    if not state.db_exists():
        return {"findings": [], "hint": "No findings database yet. Run mantis_scan_change."}
    from core.database import read_findings

    rows = read_findings(state.db_path)
    rel = state.rel(filepath) if filepath else ""
    out = []
    for f in rows:
        if rel and not _finding_matches(state, str(f.get("filepath") or ""), rel):
            continue
        if status and str(f.get("status") or "").lower() != status.lower():
            continue
        out.append(_finding_view(f))
    return {"findings": out, "total": len(out)}


def security_guidance(state: MantisState, filepath: str, full: bool = False) -> Dict[str, Any]:
    if not state.db_exists():
        return {"hint": "No knowledge database yet. Run mantis_scan_change to build one."}
    from core.database import query_security_guidance

    return query_security_guidance(state.db_path, state.rel(filepath), full=full)


# Operator resolutions. The operator owns the repository and the database;
# withholding a closure tool would not remove the capability, only push it to
# raw sqlite. What the tool preserves is label honesty: machine statuses
# (patch_verified, dynamic_confirmed) stay reserved for the verification
# pipeline, and the database's monotonic guard still refuses a dismissal
# over machine-verified evidence.
RESOLUTION_STATUSES = ("mitigated", "false_positive")


def resolve_finding(state: MantisState, finding_id: int, resolution: str,
                    reason: str) -> Dict[str, Any]:
    """Closes one finding with an operator verdict and an audit trail."""
    res = str(resolution or "").strip().lower()
    if res not in RESOLUTION_STATUSES:
        return {"error": f"resolution must be one of {list(RESOLUTION_STATUSES)}: "
                         "'mitigated' means the defect was fixed, "
                         "'false_positive' means the report is wrong."}
    if not str(reason or "").strip():
        return {"error": "A non-empty reason is required: it is the audit "
                         "trail for overriding the scanner."}
    if not state.db_exists():
        return {"error": "No findings database."}
    try:
        fid = int(finding_id)
    except (TypeError, ValueError):
        return {"error": f"finding_id must be an integer, got {finding_id!r}."}
    from core.database import read_findings, update_finding_status_by_id

    def row_for(i):
        for f in read_findings(state.db_path):
            if f.get("id") == i:
                return f
        return None

    row = row_for(fid)
    if row is None:
        return {"error": f"No finding with id {fid}."}
    old_status = str(row.get("status") or "")
    update_finding_status_by_id(state.db_path, fid, str(row.get("run_id") or ""), res)
    new_status = str((row_for(fid) or {}).get("status") or "")
    applied = new_status.lower() == res
    with open(state.home / "resolutions.log", "a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "at": time.time(),
            "finding_id": fid,
            "lineage_id": row.get("lineage_id"),
            "title": row.get("title"),
            "old_status": old_status,
            "new_status": new_status,
            "resolution": res,
            "reason": str(reason).strip(),
        }) + "\n")
    out = {"finding_id": fid, "old_status": old_status,
           "new_status": new_status, "applied": applied}
    if not applied:
        if (res == "false_positive"
                and old_status.lower() in ("dynamic_confirmed", "patch_verified")):
            out["note"] = ("The monotonic status guard refused the transition: "
                           "a dismissal never overwrites machine-verified "
                           "evidence (dynamic_confirmed, patch_verified).")
        else:
            out["note"] = ("The monotonic status guard refused the transition: "
                           f"'{old_status}' is already a terminal status and "
                           "is preserved.")
    return out


# --- The gate ---------------------------------------------------------------------


_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def parse_unified_diff(diff_text: str) -> Dict[str, List[int]]:
    """New-side changed line numbers per file from a unified diff. Never raises."""
    changed: Dict[str, List[int]] = {}
    current = ""
    new_line = 0
    for raw in str(diff_text or "").splitlines():
        if raw.startswith("+++ "):
            path = raw[4:].strip()
            path = path.split("\t")[0]
            if path.startswith("b/"):
                path = path[2:]
            current = "" if path == "/dev/null" else path
            if current:
                changed.setdefault(current, [])
            continue
        m = _HUNK_RE.match(raw)
        if m:
            new_line = int(m.group(1))
            continue
        if not current or new_line <= 0:
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            changed[current].append(new_line)
            new_line += 1
        elif raw.startswith("-") and not raw.startswith("---"):
            # Old-side line: the new-side counter does not advance, but the
            # deletion itself anchors here -- a hunk that only removes lines
            # (the deleted-guard regression) must still map to its enclosing
            # function, or the blast radius comes back empty.
            changed[current].append(max(1, new_line))
        elif raw.startswith("\\"):
            continue  # "\ No newline at end of file"
        else:
            new_line += 1
    return {f: sorted(set(lines)) for f, lines in changed.items()}


def _paths_match(a: str, b: str) -> bool:
    """Component-aligned equality: exact, or one a path-suffix of the other."""
    a = str(a or "").replace("\\", "/").strip("/")
    b = str(b or "").replace("\\", "/").strip("/")
    if not a or not b:
        return False
    return a == b or a.endswith("/" + b) or b.endswith("/" + a)


def _finding_matches(state, stored: str, query: str) -> bool:
    """Strict matching for the gate layer. Findings store canonical
    root-relative paths, so when `query` names a real file in the repo both
    sides are canonical and only exact equality is a match — otherwise
    duplicate basenames cross-match (an edit to foo/util.h gets BLOCKed by
    findings on bar/util.h; ubiquitous in C/C++ trees). Component-aligned
    suffix matching (_paths_match) stays as the fallback for absolute,
    historical, or deleted paths, where exactness is unknowable."""
    s = str(stored or "").replace("\\", "/").strip("/")
    q = str(query or "").replace("\\", "/").strip("/")
    if not s or not q:
        return False
    try:
        if (state.repo / q).is_file():
            return s == q
    except OSError:
        pass
    return _paths_match(s, q)


def _uncovered(state: MantisState, rel_files: List[str]) -> Optional[List[str]]:
    """Changed files no recorded campaign ever covered, else None if unknowable.

    Delegates to core.cost.uncovered_files, which owns the ancestor-directory
    coverage rule (scanning repo/lib covers lib/anything). The ledger stores
    targets as the pipeline received them, so each file is probed in both its
    absolute and repo-relative spellings and covered if either one is.
    """
    from core.cost import uncovered_files

    abs_map = {rel: str(state.repo / rel) for rel in rel_files}
    probes = list(abs_map.values()) + list(abs_map)
    unc = uncovered_files(state.db_path, probes)
    if unc is None:
        return None
    unc_set = set(unc)
    return [rel for rel, ab in abs_map.items() if ab in unc_set and rel in unc_set]


def check_change(state: MantisState, files: Optional[List[str]] = None,
                 diff: str = "") -> Dict[str, Any]:
    """The deterministic gate: what Mantis knows about this change, as a verdict.

    BLOCK  -- an open HIGH/CRITICAL finding intersects the change.
    REVIEW -- something demands human/agent attention: open findings of any
              severity touch the change or its callers, a changed file has
              never been scanned, or the index/database needed to decide is
              missing (fail-closed).
    PASS   -- every check ran and nothing known intersects this change.
    """
    raw_changed: Dict[str, List[int]] = parse_unified_diff(diff)
    for f in files or []:
        raw_changed.setdefault(str(f or ""), [])
    changed: Dict[str, List[int]] = {}
    rejected: List[str] = []
    for f, lines in raw_changed.items():
        r = state.rel(f)
        if r:
            changed.setdefault(r, []).extend(lines or [])
        elif f:
            rejected.append(f)
    changed = {f: sorted(set(lines)) for f, lines in changed.items()}

    verdict = VERDICT_PASS
    reasons: List[str] = []
    next_actions: List[str] = []

    def raise_to(level: str, reason: str, action: str = "") -> None:
        nonlocal verdict
        if _VERDICT_RANK[level] > _VERDICT_RANK[verdict]:
            verdict = level
        reasons.append(reason)
        if action and action not in next_actions:
            next_actions.append(action)

    if not changed and not rejected:
        return {"verdict": VERDICT_REVIEW,
                "reasons": ["No changed files given: pass `files` or a unified `diff`."],
                "blast_radius": [], "findings": [], "next_actions": []}

    # A path the gate cannot map into this repo is named, not dropped:
    # silently narrowing the change set is the fail-open direction.
    for f in rejected:
        raise_to(VERDICT_REVIEW,
                 f"'{f}' is outside this repository: not gated.",
                 "Run the gate from the repository the change belongs to.")

    # Fail-closed context checks.
    idx = state.index()
    if not idx.available():
        raise_to(VERDICT_REVIEW, "Structural index missing: blast radius unknown.",
                 "Run mantis_reindex, then re-run mantis_check_change.")
    if not state.db_exists():
        raise_to(VERDICT_REVIEW, "No findings database: change set has never been audited.",
                 "Run mantis_scan_change on the changed files.")

    # Blast radius: changed lines -> enclosing functions -> direct callers.
    blast: List[Dict[str, Any]] = []
    radius_files = set(changed)
    if idx.available():
        for rel_fp, lines in changed.items():
            for line in lines or []:
                enc = idx.enclosing_symbol(rel_fp, line)
                if not enc.get("found"):
                    continue
                entry = {
                    "file": enc.get("file_path", rel_fp),
                    "function": enc.get("qualified_name") or enc.get("signature"),
                    "start_line": enc.get("start_line"),
                    "end_line": enc.get("end_line"),
                    "callers": [],
                }
                if any(b["file"] == entry["file"] and b["function"] == entry["function"]
                       for b in blast):
                    continue
                sym = {"symbol_id": enc.get("symbol_id"),
                       "name": str(enc.get("qualified_name") or "").split(".")[-1]}
                if sym["symbol_id"]:
                    callers = idx.find_callers(sym, limit=MAX_CALLERS_SHOWN)
                    for c in callers.get("results") or []:
                        entry["callers"].append({
                            "caller": c.get("caller") or c.get("callee_name"),
                            "file": c.get("file_path"),
                            "line": c.get("line"),
                        })
                        if c.get("file_path"):
                            radius_files.add(str(c["file_path"]))
                blast.append(entry)

    # Findings intersecting the change and its radius.
    hits: List[Dict[str, Any]] = []
    if state.db_exists():
        from core.database import read_findings

        for f in read_findings(state.db_path):
            if str(f.get("status") or "").lower() not in OPEN_FINDING_STATUSES:
                continue
            f_fp = str(f.get("filepath") or "")
            matched_files = [c for c in changed if _finding_matches(state, f_fp, c)]
            in_file = bool(matched_files)
            in_radius = not in_file and any(_finding_matches(state, f_fp, r) for r in radius_files)
            if not in_file and not in_radius:
                continue

            # When a diff gives changed line numbers and the finding records its
            # own lines, distinguish findings that intersect the modified
            # hunk/function ("direct", which BLOCKs on HIGH/CRITICAL) from
            # pre-existing file debt elsewhere in the same file
            # ("unrelated_in_file", which raises REVIEW instead of BLOCK so a
            # two-line registration in a legacy router does not block on eight
            # unrelated findings 400 lines away). Missing line info on either
            # side fails closed to "direct".
            direct = False
            if in_file:
                diff_lines = sorted({
                    ln for c in matched_files for ln in (changed.get(c) or [])
                })
                f_lines = [
                    int(x) for x in (f.get("line_numbers") or [])
                    if isinstance(x, int) and not isinstance(x, bool)
                ]
                if not diff_lines or not f_lines:
                    direct = True
                elif any(abs(fl - cl) <= DIFF_LINE_PROXIMITY
                         for fl in f_lines for cl in diff_lines):
                    direct = True
                else:
                    for b in blast:
                        b_file = str(b.get("file") or "")
                        b_start = b.get("start_line")
                        b_end = b.get("end_line")
                        if (isinstance(b_start, int) and isinstance(b_end, int)
                                and any(_finding_matches(state, b_file, c) for c in matched_files)
                                and any(b_start <= fl <= b_end for fl in f_lines)):
                            direct = True
                            break

            view = _finding_view(f)
            if direct:
                view["relationship"] = "direct"
            elif in_file:
                view["relationship"] = "unrelated_in_file"
            else:
                view["relationship"] = "caller_radius"
            hits.append(view)
            sev = str(f.get("severity") or f.get("priority") or "").upper()
            if direct and sev in BLOCKING_SEVERITIES:
                raise_to(VERDICT_BLOCK,
                         f"Open {sev} finding '{f.get('title')}' touches changed file {f_fp}.",
                         "Fix the finding (or mark it false_positive with evidence) before merging.")
            elif in_file:
                raise_to(VERDICT_REVIEW,
                         f"Open finding '{f.get('title')}' ({sev or 'unrated'}) in the "
                         f"{'change' if direct else f'same file (outside changed lines): {f_fp}'}"
                         + (f": {f_fp}." if direct else "."),
                         "Review the listed findings against this change.")
            else:
                raise_to(VERDICT_REVIEW,
                         f"Open finding '{f.get('title')}' ({sev or 'unrated'}) in the "
                         f"caller radius: {f_fp}.",
                         "Review the listed findings against this change.")

        # Coverage: a changed file no scan ever recorded is unknown ground.
        uncovered = _uncovered(state, list(changed))
        if uncovered is None:
            raise_to(VERDICT_REVIEW,
                     "Coverage ledger unreadable: scan history unknown.",
                     "Check .mantis/knowledge.db, then run mantis_scan_change.")
        else:
            for rel_fp in uncovered:
                raise_to(VERDICT_REVIEW,
                         f"'{rel_fp}' has never been scanned by Mantis.",
                         "Run mantis_scan_change on the changed files.")

    return {
        "verdict": verdict,
        "reasons": reasons,
        "blast_radius": blast,
        "findings": hits,
        "next_actions": next_actions,
    }


# --- Tier 2: the parallel audit ----------------------------------------------------


def _scan_cmd(state: MantisState, target: str, max_llm_calls: int, model: str) -> List[str]:
    """The exact pipeline invocation for one changed file. Pure, for tests."""
    cmd = [sys.executable, str(_REF_ROOT / "main.py"), target,
           "--db", state.db_path, "--yes",
           # Anchor finding filepaths at the repository: a single-file scan
           # would otherwise store bare basenames ("login.ts"), which two
           # same-named files in one repo could cross-match at the gate.
           "--path-root", str(state.repo)]
    if max_llm_calls > 0:
        cmd += ["--max-llm-calls", str(max_llm_calls)]
    if model:
        cmd += ["--model", model]
    return cmd


def scan_change(state: MantisState, files: List[str],
                max_llm_calls: int = 150, model: str = "") -> Dict[str, Any]:
    """Audits the changed files with the full pipeline, in the background."""
    rels: List[str] = []
    for f in files or []:
        r = state.rel(f)
        if not r:
            continue
        probe = state.repo / r
        try:
            # rel() refused the lexical escapes; this refuses the physical
            # one -- an in-repo symlink whose target lives outside the repo.
            probe.resolve().relative_to(state.repo)
        except (OSError, ValueError):
            continue
        if probe.is_file():
            rels.append(r)
    rels = list(dict.fromkeys(rels))
    if not rels:
        return {"error": "No scannable files inside the repository. "
                         "Pass repo-relative paths."}
    state.ensure_home()
    scans_dir = state.home / "scans"
    scans_dir.mkdir(exist_ok=True)
    scan_id = uuid.uuid4().hex[:12]
    log_path = scans_dir / f"{scan_id}.log"
    done_event = threading.Event()
    record = {
        "scan_id": scan_id,
        "files": rels,
        "status": "running",
        "started": time.time(),
        "returncodes": [],
        "log": str(log_path),
    }
    with state._lock:
        state.scans[scan_id] = record
        state._scan_events[scan_id] = done_event

    def _run() -> None:
        index_restored = False
        try:
            with open(log_path, "ab") as log:
                for rel_fp in rels:
                    cmd = _scan_cmd(state, str(state.repo / rel_fp), max_llm_calls, model)
                    log.write(f"\n=== mantis scan {rel_fp} ===\n".encode())
                    log.flush()
                    try:
                        proc = subprocess.run(cmd, stdout=log, stderr=log, cwd=str(_REF_ROOT))
                        code = proc.returncode
                    except Exception as exc:  # the loop must survive one bad file
                        log.write(f"[mcp] scan failed to launch: {exc!r}\n".encode())
                        code = -1
                    with state._lock:
                        record["returncodes"].append(code)
                # The pipeline just rebuilt the shared catalog rooted at the
                # scanned FILE, so repo-rooted paths stopped resolving and the
                # gate's blast radius went blind (found against Juice Shop:
                # callers vanished after the first scan). Restore the repo-rooted
                # index before the record flips to done, so a poller that sees
                # "done" never sees the clobbered catalog.
                try:
                    result = reindex(state)
                    index_restored = result.get("status") in ("complete", "partial")
                except Exception as exc:
                    log.write(f"[mcp] reindex after scan failed: {exc!r}\n".encode())
                    index_restored = False
        finally:
            with state._lock:
                record["index_restored"] = index_restored
                codes = record["returncodes"]
                if codes and all(c == 0 for c in codes):
                    record["status"] = "done"
                elif codes and all(c in (0, 2) for c in codes):
                    # The pipeline exits 2 on a graceful budget pause (findings so
                    # far are already in the database; the run is resumable with
                    # --resume). It is not a failure, so do not label it as one.
                    record["status"] = "paused_at_budget"
                else:
                    record["status"] = "finished_with_errors"
                record["ended"] = time.time()
                done_event.set()

    threading.Thread(target=_run, name=f"mantis-scan-{scan_id}", daemon=True).start()
    return {"scan_id": scan_id, "files": rels, "log": str(log_path),
            "hint": "Poll mantis_scan_status (pass wait_seconds to block); "
                    "findings land in the shared database and the next "
                    "mantis_check_change will see them."}


def scan_status(state: MantisState, scan_id: str,
                wait_seconds: float = 0) -> Dict[str, Any]:
    with state._lock:
        record = dict(state.scans.get(scan_id) or {})
        done_event = state._scan_events.get(scan_id)
    if not record:
        return {"error": f"Unknown scan_id '{scan_id}' (scans do not survive server restarts; "
                         "findings they wrote do)."}
    try:
        wait_s = min(max(0.0, float(wait_seconds or 0)), MAX_WAIT_SECONDS)
    except (TypeError, ValueError):
        wait_s = 0.0
    if wait_s > 0 and record.get("status") == "running" and done_event is not None:
        done_event.wait(timeout=wait_s)
        with state._lock:
            record = dict(state.scans.get(scan_id) or {})
    out = dict(record)
    if state.db_exists():
        from core.database import read_findings

        rows = read_findings(state.db_path)
        out["findings_in_scanned_files"] = sum(
            1 for f in rows
            if any(_finding_matches(state, str(f.get("filepath") or ""), r) for r in record["files"])
        )
    return out


# --- MCP wiring ---------------------------------------------------------------------


def build_server(state: MantisState):
    """Registers the tools on an MCP server. Import deferred so everything
    above stays testable without the SDK installed."""
    try:  # mcp >= 2.0
        from mcp.server.mcpserver import MCPServer
    except ImportError:  # mcp 1.x: the same class, named FastMCP. The 2.x
        # fastmcp module still exists but raises on import, so 2.x must be
        # probed first -- the fallback order is load-bearing.
        from mcp.server.fastmcp import FastMCP as MCPServer

    srv = MCPServer(
        "mantis",
        instructions=(
            "Mantis secure-development-loop server. For every change: call "
            "mantis_check_change with the unified diff (or changed files); "
            "resolve what it raises; run mantis_scan_change so the full audit "
            "pipeline reviews the change in parallel. PASS means no known "
            "issues intersect the change -- keep the index fresh with "
            "mantis_reindex after large pulls."
        ),
    )

    @srv.tool()
    def mantis_check_change(files: Optional[List[str]] = None, diff: str = "") -> dict:
        """Deterministic security gate for a change set. Give it the unified diff
        (preferred: enables line-level blast radius) or a list of changed files.
        Returns verdict PASS/REVIEW/BLOCK with reasons, blast radius, and
        intersecting findings. Fails closed: missing index or unscanned files
        yield REVIEW, never PASS."""
        return check_change(state, files, diff)

    @srv.tool()
    def mantis_scan_change(files: List[str], max_llm_calls: int = 150, model: str = "") -> dict:
        """Launches the full Mantis audit pipeline over the given files in the
        background (budget-capped). Findings accumulate in the repo's
        .mantis/knowledge.db, where mantis_check_change reads them."""
        return scan_change(state, files, max_llm_calls=max_llm_calls, model=model)

    @srv.tool()
    def mantis_scan_status(scan_id: str, wait_seconds: int = 0) -> dict:
        """Status of a background scan started by mantis_scan_change. Pass
        wait_seconds (up to 60) to block until the scan finishes or the timeout
        elapses instead of polling in a tight loop."""
        return scan_status(state, scan_id, wait_seconds=wait_seconds)

    @srv.tool()
    def mantis_reindex() -> dict:
        """Builds or incrementally refreshes the structural index (tree-sitter
        symbol/call-graph catalog) for the repository."""
        return reindex(state)

    @srv.tool()
    def mantis_find_symbol(name: str, offset: int = 0) -> dict:
        """Looks up a function/class/macro definition by name in the catalog."""
        return find_symbol(state, name, offset=offset)

    @srv.tool()
    def mantis_find_callers(symbol: str, filepath: str = "") -> dict:
        """Direct call sites of a symbol: who can reach this code."""
        return find_callers(state, symbol, filepath=filepath)

    @srv.tool()
    def mantis_find_callees(symbol: str, filepath: str = "") -> dict:
        """Direct callees of a symbol: what this code reaches."""
        return find_callees(state, symbol, filepath=filepath)

    @srv.tool()
    def mantis_function_at(filepath: str, line: int) -> dict:
        """The innermost function enclosing file:line, with its exact extent."""
        return function_at(state, filepath, line)

    @srv.tool()
    def mantis_get_findings(filepath: str = "", status: str = "") -> dict:
        """Recorded findings, optionally filtered by file and status."""
        return get_findings(state, filepath=filepath, status=status)

    @srv.tool()
    def mantis_security_guidance(filepath: str, full: bool = False) -> dict:
        """Threat-model-informed security guidance for a file: active threats,
        invariants, historical vulnerabilities, and triaged false positives."""
        return security_guidance(state, filepath, full=full)

    @srv.tool()
    def mantis_resolve_finding(finding_id: int, resolution: str, reason: str) -> dict:
        """Closes a finding with an operator verdict: 'mitigated' (the defect
        was fixed) or 'false_positive' (the report is wrong). Requires a
        reason, which is appended to .mantis/resolutions.log as the audit
        trail. Machine statuses (patch_verified, dynamic_confirmed) remain
        reserved for the verification pipeline, and a dismissal never
        overwrites machine-verified evidence."""
        return resolve_finding(state, finding_id, resolution, reason)

    return srv


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Mantis MCP server (stdio)")
    parser.add_argument("--repo", default=os.environ.get("MANTIS_MCP_REPO", "."),
                        help="Repository root to serve (default: cwd)")
    parser.add_argument("--check", action="store_true",
                        help="One-shot gate instead of serving: read a unified "
                             "diff on stdin (or take --files), print the verdict "
                             "JSON, exit 0=PASS 1=REVIEW 2=BLOCK.")
    parser.add_argument("--files", nargs="*", default=None,
                        help="Changed files for --check when no diff is piped.")
    args = parser.parse_args(argv)
    state = MantisState(args.repo)
    if not state.repo.is_dir():
        print(f"error: --repo '{args.repo}' is not a directory", file=sys.stderr)
        return 3
    if args.check:
        diff = "" if sys.stdin.isatty() else sys.stdin.read()
        out = check_change(state, files=args.files, diff=diff)
        print(json.dumps(out, indent=2, default=str))
        return {VERDICT_PASS: 0, VERDICT_REVIEW: 1, VERDICT_BLOCK: 2}[out["verdict"]]
    build_server(state).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
