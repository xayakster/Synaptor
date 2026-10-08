"""Correlator: joins findings that describe different ends of the same defect.

WHAT THIS IS FOR
----------------
This is the direct answer to "bugs that span many files, repos, or even systems."

Every campaign writes findings independently. Nothing has ever read them back
*together*: measured before building, there is no correlation function anywhere in the
codebase, and `record_exploit_chain` writes an artifact that nothing ever reads. So a
defect whose halves land in two different slices -- a validator that trusts its caller
and a caller that trusts the validator -- is recorded twice, as two unremarkable local
findings, and the composite is never stated by anyone.

Slicing makes this worse, not better. Splitting a repository into subsystems is what
lets a large target be examined at all, and it is also precisely what guarantees that
the two ends of a cross-module defect are seen by different agents who cannot see each
other's work.

WHAT IT DOES
------------
Groups findings by evidence that they concern the same thing:

  * a shared SYMBOL   -- the strongest link. Two findings naming `parse_token` are
                         talking about the same function even from different files.
  * a shared FILE     -- two findings in one file are related by construction.
  * a shared WEAKNESS -- same CWE in adjoining areas is a pattern, not a coincidence.

and emits, for each group, the fact of the overlap plus the operator-authored reason it
might matter. It does NOT decide that a chain exists. Whether two linked findings
compose into an exploit is a judgement about reachability and trust boundaries that
needs the code in front of you, and this module cannot see code.

WHAT IT IS NOT ALLOWED TO DO
----------------------------
Correlation is a HINT, never a verdict. Specifically:

  * It never invents a finding. Every group member is an existing row, and a group of
    one is not emitted at all.
  * It never upgrades severity, status, or confidence. A pair of `medium` findings that
    correlate remain two `medium` findings plus an observation.
  * It never merges findings. Deduplication is a separate, existing concern with its own
    tool; conflating the two would silently delete evidence.
  * Its prose inputs (`title`, `description`) are quoted through CP-4 and never parsed
    for meaning. Only structural fields -- symbols extracted from `code_paths`, CWE
    identifiers, file paths -- drive grouping.

The last point is the security argument. A finding is LLM output, so its prose is
untrusted in exactly the way repository content is. Grouping on validated/structural
fields means a hostile or hallucinated description can, at worst, cause a spurious
grouping the reader can see and dismiss -- never a change in what the system believes.
"""

from __future__ import annotations


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
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# How many groups to report, and how many members to show per group. A correlator on a
# large audit can otherwise produce more text than the findings it describes.
_MAX_GROUPS = 12
_MAX_MEMBERS_SHOWN = 6
_MAX_PROSE = 160

# Link kinds, strongest first. The order is the published contract: a symbol link is
# evidence about one piece of code, a call-graph edge is a direct AST call between
# two findings' functions, and a shared CWE is evidence about a habit.
LINK_SYMBOL = "shared_symbol"
LINK_CALL_GRAPH = "call_graph_edge"
LINK_FILE = "shared_file"
LINK_WEAKNESS = "shared_weakness"

_LINK_ORDER: Tuple[str, ...] = (LINK_SYMBOL, LINK_CALL_GRAPH, LINK_FILE, LINK_WEAKNESS)
_LINK_RANK = {name: i for i, name in enumerate(_LINK_ORDER)}

# Operator-authored. The correlator selects which applies; it never writes the text.
_LINK_NOTE = {
    LINK_SYMBOL: (
        "These findings name the same symbol from different places. If one of them "
        "establishes that the symbol misbehaves and another assumes it does not, the "
        "composite is worse than either alone -- check whether the assumption in one "
        "is the defect in the other."
    ),
    LINK_CALL_GRAPH: (
        "One of these findings sits in a function that calls into the other in the "
        "structural index. Check whether untrusted data or a broken invariant "
        "crosses that call edge."
    ),
    LINK_FILE: (
        "These findings are in the same file. Consider whether they share a root cause, "
        "and whether fixing one leaves the other reachable."
    ),
    LINK_WEAKNESS: (
        "These findings share a weakness class across different areas. That is usually "
        "a pattern rather than a coincidence: the same mistake is likely present in "
        "places nobody has examined yet."
    ),
}

# Symbols too generic to be evidence of anything. Grouping on these produces enormous
# meaningless clusters -- every codebase has a `main` and a `get`.
_SYMBOL_STOPWORDS = frozenset({
    "main", "init", "get", "set", "run", "new", "call", "test", "handler", "handle",
    "process", "execute", "start", "stop", "read", "write", "open", "close", "parse",
    "load", "save", "update", "delete", "create", "check", "validate", "data", "value",
    "result", "self", "this", "none", "null", "true", "false",
})

_SYMBOL_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")
_CODE_EXT_RE = re.compile(r"\.[A-Za-z0-9]{1,6}$")


def _clip(text: Any, limit: int = _MAX_PROSE) -> str:
    s = str(text or "").strip()
    return s if len(s) <= limit else s[:limit] + " [...]"


def _load_structural_index(db_path: str = ""):
    """Loads the structural index adjacent to db_path (or current_run_context), else None."""
    try:
        target_db = str(db_path or "").strip()
        if not target_db:
            from core.context import current_run_context

            ctx = current_run_context.get()
            if ctx and getattr(ctx, "db_path", None):
                target_db = str(ctx.db_path).strip()
        if not target_db:
            return None
        from core.structural_index import StructuralIndex, state_dir_for_db

        idx = StructuralIndex(state_dir_for_db(target_db))
        return idx if idx.available() else None
    except Exception:
        return None


def _enclosing_symbols_for_row(idx: Any, row: Dict[str, Any]) -> set:
    """Enclosing catalog symbol leaf names for a finding's filepath and line_numbers."""
    out: set = set()
    if idx is None:
        return out
    try:
        path = str(row.get("filepath") or "").strip()
        if not path:
            return out
        raw_lines = row.get("line_numbers")
        if isinstance(raw_lines, str):
            import json

            raw_lines = json.loads(raw_lines)
        if not isinstance(raw_lines, (list, tuple)):
            return out
        for ln in raw_lines[:5]:
            if isinstance(ln, int) and not isinstance(ln, bool) and ln > 0:
                enc = idx.enclosing_symbol(path, ln)
                if enc.get("found"):
                    qname = str(enc.get("qualified_name") or "").strip()
                    leaf = qname.split(".")[-1] if qname else ""
                    if (leaf and leaf != "<module>"
                            and _SYMBOL_RE.fullmatch(leaf)
                            and leaf.lower() not in _SYMBOL_STOPWORDS):
                        out.add(leaf)
    except Exception:
        pass
    return out


def _symbols_from_code_paths(code_paths: Any) -> set:
    """Extracts symbol names from `code_paths` entries.

    Three shapes are in circulation, all of them produced by the existing pipeline and
    all accepted by `database.extract_target_symbol`:

      * `svc/auth/token.py:parse_token`     -- file and symbol
      * `svc/auth/token.py:42:parse_token`  -- file, line and symbol
      * `parse_token`                       -- a bare symbol, no location

    Line numbers are never symbols: two findings at line 42 of different files have
    nothing to do with each other. Requiring a colon would silently discard every
    bare-symbol entry, which is the form carrying the clearest cross-area signal.
    """
    out: set = set()
    if isinstance(code_paths, str):
        # Stored as a JSON string in some rows; tolerate both without raising.
        try:
            import json

            code_paths = json.loads(code_paths)
        except Exception:
            return out
    if not isinstance(code_paths, (list, tuple, set)):
        return out
    for entry in code_paths:
        text = str(entry or "").strip()
        if not text:
            continue
        if ":" in text:
            tail = text.rsplit(":", 1)[1].strip()
        else:
            # A bare entry is only a symbol if it is not itself a path or a filename.
            if "/" in text or "\\" in text:
                continue
            tail = text
        if not tail or _CODE_EXT_RE.search(tail):
            continue
        # A line number is not a symbol: two findings at line 42 of different files
        # have nothing to do with each other. Enforced by _SYMBOL_RE, which requires a
        # leading letter or underscore -- an explicit isdigit() check here would be
        # unreachable, and an unreachable guard cannot be tested, so it rots.
        if not _SYMBOL_RE.fullmatch(tail):
            continue
        if tail.lower() in _SYMBOL_STOPWORDS:
            continue
        out.add(tail)
    return out


def _finding_key(row: Dict[str, Any], index: int) -> str:
    """A stable identifier for a finding, for reporting membership.

    `id` when present; otherwise the position, because two findings can legitimately
    share a title and must not collapse into one another here.
    """
    for field in ("id", "lineage_id", "signature"):
        value = row.get(field)
        if value not in (None, ""):
            return str(value)
    return f"#{index}"


def correlate(
    findings: List[Dict[str, Any]],
    max_groups: int = _MAX_GROUPS,
    db_path: str = "",
) -> Dict[str, Any]:
    """Groups findings that appear to concern the same defect.

    Returns:
        {
          "available": whether any group was found,
          "groups":    [{kind, key, members: [...], note}],
          "counts":    {link kind: number of groups},
          "truncated": whether groups were dropped for length,
        }

    Never raises (INV-6). Correlation is an enhancement to the report; failing to
    correlate must not cost the run its findings.
    """
    empty: Dict[str, Any] = {
        "available": False,
        "groups": [],
        "counts": {},
        "truncated": False,
    }
    if not findings or not isinstance(findings, (list, tuple)):
        return empty

    try:
        rows: List[Tuple[str, Dict[str, Any]]] = []
        for index, row in enumerate(findings):
            if isinstance(row, dict):
                rows.append((_finding_key(row, index), row))
        if len(rows) < 2:
            # Correlation needs something to correlate. One finding is not a pattern.
            return empty

        idx = _load_structural_index(db_path)

        by_symbol: Dict[str, List[str]] = {}
        by_grounded: Dict[str, List[str]] = {}
        by_file: Dict[str, List[str]] = {}
        by_cwe: Dict[str, List[Tuple[str, str]]] = {}
        detail: Dict[str, Dict[str, Any]] = {}

        for key, row in rows:
            detail[key] = row
            cp_syms = _symbols_from_code_paths(row.get("code_paths"))
            for symbol in cp_syms:
                by_symbol.setdefault(symbol, []).append(key)
                by_grounded.setdefault(symbol, []).append(key)
            for enc_sym in _enclosing_symbols_for_row(idx, row):
                by_grounded.setdefault(enc_sym, []).append(key)

            path = str(row.get("filepath") or "").strip()
            if path:
                by_file.setdefault(path, []).append(key)

            cwe = str(row.get("cwe") or "").strip()
            if cwe:
                by_cwe.setdefault(cwe, []).append((key, path))

        groups: List[Dict[str, Any]] = []

        def _emit(kind: str, link_key: str, member_keys: List[str]) -> None:
            unique = sorted(set(member_keys))
            if len(unique) < 2:
                return
            groups.append({
                "kind": kind,
                "key": link_key,
                "members": unique,
                "note": _LINK_NOTE.get(kind, ""),
            })

        for symbol, keys in by_symbol.items():
            _emit(LINK_SYMBOL, symbol, keys)

        if idx is not None and len(by_grounded) >= 2:
            seen_edges: set = set()
            for caller_name in sorted(by_grounded):
                caller_keys = by_grounded[caller_name]
                for sym_row in (idx.resolve_symbol(caller_name).get("results") or [])[:5]:
                    for edge in (idx.find_callees(sym_row).get("results") or []):
                        callee_name = str(edge.get("callee_name") or "").strip()
                        if (callee_name and callee_name != caller_name
                                and callee_name in by_grounded):
                            edge_key = f"{caller_name} -> {callee_name}"
                            if edge_key not in seen_edges:
                                seen_edges.add(edge_key)
                                _emit(
                                    LINK_CALL_GRAPH,
                                    edge_key,
                                    caller_keys + by_grounded[callee_name],
                                )

        for path, keys in by_file.items():
            _emit(LINK_FILE, path, keys)
        for cwe, pairs in by_cwe.items():
            # Only interesting ACROSS files. Two instances of the same weakness in one
            # file are already reported by the shared-file link, and emitting both says
            # the same thing twice.
            if len({path for _key, path in pairs if path}) < 2:
                continue
            _emit(LINK_WEAKNESS, cwe, [key for key, _path in pairs])

        if not groups:
            return empty

        # Strongest link kind first, then larger groups, then a stable key order.
        groups.sort(key=lambda g: (_LINK_RANK.get(g["kind"], 99), -len(g["members"]), str(g["key"])))

        counts: Dict[str, int] = {}
        for group in groups:
            counts[group["kind"]] = counts.get(group["kind"], 0) + 1

        truncated = len(groups) > max_groups
        return {
            "available": True,
            "groups": groups[:max_groups],
            "counts": counts,
            "truncated": truncated,
            "_detail": detail,
        }
    except Exception as exc:
        logger.warning("Correlation failed: %s", exc)
        return empty


def render_correlations_for_agent(correlation: Dict[str, Any]) -> str:
    """Renders correlations, fencing the prose and leaving structure plain.

    Same split as `memory.render_memory_for_agent`, for the same reason: counts, link
    kinds and CWE identifiers are validated or structural and read as facts, while
    finding titles are prose an earlier LLM wrote and must arrive quoted.

    Returns "" when there is nothing to say, so callers can append unconditionally.
    """
    if not isinstance(correlation, dict) or not correlation.get("available"):
        return ""

    groups = correlation.get("groups") or []
    if not groups:
        return ""
    detail = correlation.get("_detail") or {}

    counts = correlation.get("counts") or {}
    header = [
        "CORRELATED FINDINGS (observations, not conclusions):",
        "  "
        + ", ".join(
            f"{counts[kind]} by {kind.replace('_', ' ')}"
            for kind in _LINK_ORDER
            if counts.get(kind)
        )
        + ".",
    ]
    if correlation.get("truncated"):
        header.append("  Showing the strongest links only.")

    body: List[str] = []
    for group in groups:
        body.append(f"[{group.get('kind')}] {group.get('key')}")
        for member in (group.get("members") or [])[:_MAX_MEMBERS_SHOWN]:
            row = detail.get(member) or {}
            body.append(
                f"  - {row.get('filepath') or '(path not recorded)'}: "
                f"{_clip(row.get('title'))}"
            )
        body.append(f"  {group.get('note')}")

    from core.llm_gateway import wrap_untrusted_content

    fenced = wrap_untrusted_content("\n".join(body), filename="correlated_findings")
    return (
        "\n\n"
        + "\n".join(header)
        + "\n"
        + fenced
        + "\n  The groupings above were computed by matching symbols, paths and "
        "weakness classes. They are a reason to LOOK, never evidence that a chain "
        "exists: establish reachability yourself before claiming one, and do not "
        "raise any finding's severity on the strength of a grouping alone."
    )


def summarize_correlations(correlation: Dict[str, Any]) -> str:
    """One operator-facing line. Contains no repository or LLM-authored bytes."""
    if not isinstance(correlation, dict) or not correlation.get("available"):
        return ""
    counts = correlation.get("counts") or {}
    parts = [
        f"{counts[kind]} by {kind.replace('_', ' ')}"
        for kind in _LINK_ORDER
        if counts.get(kind)
    ]
    if not parts:
        return ""
    return "Correlated findings: " + ", ".join(parts) + "."


# --- Hypotheses ---------------------------------------------------------------------
#
# Correlation looks BACKWARD: it joins findings that already exist. A hypothesis looks
# FORWARD: it tells the agent entering an area what to go and check, based on what was
# confirmed elsewhere.
#
# This is the difference between a system that reports and a system that investigates.
# Given a symbol confirmed defective in one subsystem, the question "is it misused
# here too?" is exactly the question no per-slice agent can ask on its own, because it
# cannot see the other slices. It is also the cheapest possible cross-module lead: a
# name to grep for, with a reason attached.
#
# A hypothesis is a QUESTION, never a finding. It is generated mechanically from
# structural fields, it carries no severity, and confirming it requires the same
# evidence any other finding requires. The failure mode to avoid is an agent treating
# "the planner suggested X might be here" as "X is here" -- so the rendered text says
# so explicitly, and nothing downstream consumes hypotheses as input.

_MAX_HYPOTHESES = 8


def generate_hypotheses(
    memory: Optional[Dict[str, Any]],
    scan_item: str,
    max_hypotheses: int = _MAX_HYPOTHESES,
    db_path: str = "",
) -> List[Dict[str, Any]]:
    """Proposes cross-area checks for the agent about to examine `scan_item`.

    Built from CONFIRMED prior findings in OTHER areas: their symbols are worth looking
    for here, and their weakness classes are worth looking for here. Dismissed findings
    are excluded -- a dismissal is context, not a verdict, and building a hypothesis on
    one would let a single mis-triage generate busywork indefinitely.

    Returns a list of `{kind, subject, rationale, source}`, possibly empty. Never
    raises (INV-6).
    """
    try:
        if not isinstance(memory, dict) or not memory.get("available"):
            return []
        confirmed = memory.get("confirmed") or []
        if not confirmed:
            return []

        here = str(scan_item or "").replace("\\", "/").rstrip("/")

        def _is_here(origin: str) -> bool:
            """Whether a finding at `origin` already lives in the area being scanned.

            Compares the finding's DIRECTORIES against the area, not its full path: a
            finding at `svc/auth/token.py` is inside the area `/repo/svc/auth`, but
            neither string contains the other -- the filename is in the way. Comparing
            the raw strings silently suppressed nothing and every agent was handed a
            lead pointing back at the code it was already reading.
            """
            if not origin or not here:
                return False
            # Every directory containing the finding, plus the finding itself.
            probe = origin
            while probe:
                if probe == here or here.endswith("/" + probe) or probe.endswith("/" + here):
                    return True
                cut = probe.rfind("/")
                if cut <= 0:
                    break
                probe = probe[:cut]
            return False

        idx = _load_structural_index(db_path)

        symbols: Dict[str, Dict[str, Any]] = {}
        weaknesses: Dict[str, Dict[str, Any]] = {}

        for item in confirmed:
            if not isinstance(item, dict):
                continue
            origin = str(item.get("filepath") or "").replace("\\", "/")
            # A finding already in this area is not a cross-area hypothesis; the agent
            # is about to read that code anyway, and prior memory already reported it.
            if _is_here(origin):
                continue

            item_symbols = set(_symbols_from_code_paths(item.get("code_paths")))
            if idx is not None:
                item_symbols |= _enclosing_symbols_for_row(idx, item)
            for symbol in item_symbols:
                slot = symbols.setdefault(
                    symbol,
                    {"kind": "symbol_reuse", "subject": symbol, "sources": [], "cwe": ""},
                )
                if origin and origin not in slot["sources"]:
                    slot["sources"].append(origin)
                if not slot["cwe"] and item.get("cwe"):
                    slot["cwe"] = str(item.get("cwe"))

            cwe = str(item.get("cwe") or "").strip()
            if cwe:
                slot = weaknesses.setdefault(
                    cwe, {"kind": "weakness_recurrence", "subject": cwe, "sources": []}
                )
                if origin and origin not in slot["sources"]:
                    slot["sources"].append(origin)

        if idx is not None:
            for slot in symbols.values():
                call_sites: List[str] = []
                for sym_row in (idx.resolve_symbol(slot["subject"]).get("results") or [])[:5]:
                    for c_edge in (idx.find_callers(sym_row).get("results") or []):
                        c_fp = str(c_edge.get("file_path") or "").replace("\\", "/")
                        c_ln = c_edge.get("line")
                        if c_fp and _is_here(c_fp):
                            loc = f"{c_fp}:{c_ln}" if c_ln else c_fp
                            if loc not in call_sites:
                                call_sites.append(loc)
                slot["call_sites"] = call_sites[:3]

        out: List[Dict[str, Any]] = []
        # Symbols first: a named function is a far more specific lead than a weakness
        # class, and a bounded list should spend its slots on the specific ones.
        # Symbols with verified call sites inside `scan_item` rank ahead of blind leads.
        for slot in sorted(
            symbols.values(),
            key=lambda s: (-len(s.get("call_sites") or ()), -len(s["sources"]), s["subject"]),
        ):
            sites = slot.get("call_sites") or []
            if sites:
                rationale = (
                    f"`{slot['subject']}` was confirmed defective elsewhere in this "
                    f"repository and is called in this area ({', '.join(sites)}). "
                    f"Check whether those call sites rely on the behaviour that was "
                    f"found to be wrong."
                )
            else:
                rationale = (
                    f"`{slot['subject']}` was confirmed defective elsewhere in this "
                    f"repository. If this area calls it, check whether it relies on "
                    f"the behaviour that was found to be wrong."
                )
            out.append({
                "kind": "symbol_reuse",
                "subject": slot["subject"],
                "rationale": rationale,
                "source": slot["sources"][:3],
            })
        for slot in sorted(weaknesses.values(), key=lambda s: (-len(s["sources"]), s["subject"])):
            if len(slot["sources"]) < 2:
                # One instance of a weakness is a finding. Two in different places is a
                # habit, and only a habit justifies going looking for a third.
                continue
            out.append({
                "kind": "weakness_recurrence",
                "subject": slot["subject"],
                "rationale": (
                    f"{slot['subject']} has been confirmed in {len(slot['sources'])} "
                    f"other areas of this repository. The same mistake is worth "
                    f"looking for here."
                ),
                "source": slot["sources"][:3],
            })
        return out[:max_hypotheses]
    except Exception as exc:
        logger.warning("Hypothesis generation failed: %s", exc)
        return []


def render_hypotheses_for_agent(hypotheses: List[Dict[str, Any]]) -> str:
    """Renders hypotheses as questions to investigate.

    Symbols and CWE identifiers are structural -- extracted by regex from a validated
    field, matched as strings -- but they still originate in earlier LLM output, so the
    whole block is fenced. Unlike the coverage note, this text contains subject matter
    the planner did not author.

    Returns "" when there is nothing to propose.
    """
    if not hypotheses:
        return ""

    body: List[str] = []
    for item in hypotheses:
        if not isinstance(item, dict):
            continue
        body.append(f"- [{item.get('kind')}] {item.get('rationale')}")
        sources = item.get("source") or []
        if sources:
            body.append(f"    seen in: {', '.join(str(s) for s in sources)}")
    if not body:
        return ""

    from core.llm_gateway import wrap_untrusted_content

    fenced = wrap_untrusted_content("\n".join(body), filename="cross_area_hypotheses")
    return (
        "\n\nCROSS-AREA LEADS ("
        + str(len(hypotheses))
        + " to check here, derived from findings confirmed elsewhere):\n"
        + fenced
        + "\n  These are QUESTIONS, not findings. Each one says only that something "
        "confirmed elsewhere might also apply here. Investigate them as you would any "
        "other lead: confirm reachability and impact from the code in front of you, "
        "and report nothing you have not established yourself. Finding that a lead "
        "does not apply here is a useful result."
    )

