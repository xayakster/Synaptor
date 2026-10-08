"""Phase 0: Deterministic Topographic Reconnaissance -- the Surveyor.

Produces a ranked map of a repository ("which areas are worth auditing, in what
order") *before* any model is involved. Nothing here calls an LLM; the ranking is a
weighted formula over five measurable signals, so it is reproducible and reviewable.

Why this exists
---------------
Measured on chromium (506,522 tracked files), the pipeline previously handed the agent
the first 1,000 filenames in lexicographic order and let it start reading. That is
`ATL_OWNERS` through `agents/` -- alphabetical accident, not relevance.

NORMATIVE constraints (design §2, §4.2, §4.3)
---------------------------------------------
1. File enumeration goes through CP-1 `get_vetted_staging_files` ONLY. A local
   `os.walk` follows repo-planted symlinks out of the checkout and indexes host files
   (`~/.ssh`, `~/.aws`) -- exactly the class CP-1 closed.
2. The scan root resolves through CP-3 `validate_scan_target` before first contact.
3. Every git invocation goes through CP-2 `_run_safe_git_command`, and
   `_validate_git_jail` must pass first. Phase 0 runs before any RunContext exists, so
   the Surveyor establishes the jail itself rather than inheriting one.
4. Build manifests are parsed as TEXT. No build-system binary is ever invoked: `gn`,
   `cmake`, `bazel` and `mvn` all evaluate repository-controlled code. This module does
   not parse XML at all -- it regexes for the handful of fields it wants -- which means
   there is no XXE surface to disable in the first place.

Scope honesty
-------------
Attack-surface scoring reads file *contents*, which cannot be done exhaustively at ELR
scale: 462k files at ~200 us each is minutes of wall clock before any analysis starts.
Content scanning is therefore SAMPLED -- each group gets a strided sample of up to
`_SAMPLE_FILES_PER_GROUP` files, drawn against a repository-wide `_MAX_SAMPLED_FILES`
budget. This trades recall for a bounded runtime, and it is the main reason a slice can
be missed. See `_scan_group_surface`.
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
import hashlib
import json
import logging
import math
import os
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Optional, Union

from core.environments.staging import get_vetted_staging_files
from core.paths import validate_scan_target

logger = logging.getLogger(__name__)

SURVEYOR_VERSION = "2.1"
ASTM_SCHEMA_VERSION = "2.1"

# --- Tuning -------------------------------------------------------------------------

# Slices emitted. The consumer builds one workflow per slice, so this bounds the whole
# downstream campaign, not just this module.
MAX_SLICES = 20

# Total files that may be opened for content scanning, across the whole survey.
#
# A budget rather than a group cap. An earlier version scanned only the top 60 candidate
# groups, which meant every other group scored exactly 0.00 on attack surface -- not
# because it was clean, but because it was never opened -- and forfeited 40% of the
# formula for reasons unrelated to its risk. Measured on chromium (889 groups), a budget
# large enough to reach every group costs seconds, so the cap was buying nothing.
#
# When a repository is large enough to exhaust this, groups are scanned in cheap-rank
# order and the unscanned remainder reports content_sampled=0, so the gap is visible in
# the ASTM rather than silently folded into the score.
_MAX_SAMPLED_FILES = 60_000
_SAMPLE_FILES_PER_GROUP = 40
_MAX_SCAN_BYTES = 64 * 1024

# Complexity sampling bounds. Separate and smaller than the content-scan budget
# because the cost structure differs by an order of magnitude: the pattern pass is
# a regex over bytes, this pass is a full tree-sitter parse. At ~1-3ms per 64KB
# file, the content budget's 60k ceiling would add minutes to an ELR-scale survey
# for a signal that stabilizes on far fewer samples. Groups are visited in the
# same cheap-rank order as the content scan, so when the budget runs out it is the
# implausible tail that goes unmeasured, and complexity_sampled=0 makes the gap
# visible in the ASTM rather than folding it into the score.
_COMPLEXITY_FILES_PER_GROUP = 12
_MAX_PARSED_FILES = 20_000

# A group below this size is noise, not a subsystem.
_MIN_GROUP_FILES = 5

# Point at which additional size stops increasing rank.
#
# Size has to count for something -- a two-file directory with one bind() call is not a
# subsystem -- but past a few thousand files a group has stopped being a unit of work an
# agent can audit and has become a quarter of the repository. Measured on chromium,
# unbounded log-size let chrome/browser (39,357 files, attack-surface signal 0.02) score
# nearly 3x content/browser purely on bulk and commit volume.
_SIZE_SATURATION_FILES = 1500

# Churn history depth. Bounded because chromium and Linux carry 70-90k commits/year.
_CHURN_COMMITS = 2000
_CHURN_GIT_TIMEOUT = 120.0

# Signal weights (design §4.1). Redistributed by `_rebalance_weights` when a signal is
# structurally inapplicable to the repository under survey.
#
# Complexity's share comes out of attack surface and language risk rather than the
# history signals: surface overlaps complexity most (both are content measurements,
# and tangled request handling tends to match both), and language risk is the
# weakest signal of the five -- a prior about the language, not a measurement of
# this code. When tree-sitter or every grammar is absent the complexity signal is
# uniformly zero and `_rebalance_weights` retires it, so the formula degrades to
# the four-signal split rather than spending 10% on nothing.
_W_SURFACE = 0.35
_W_CHURN = 0.25
_W_BOUNDARY = 0.20
_W_LANGUAGE = 0.10
_W_COMPLEXITY = 0.10

# Normalization percentile, and the population below which it degenerates to the max.
_ROBUST_PERCENTILE = 0.95
_ROBUST_MIN_POPULATION = 20

# A signal whose spread (max - min) across all groups is at or below this cannot change
# the ordering, so its weight is redistributed rather than spent. Applies at both
# extremes: uniformly absent and uniformly saturated are equally uninformative.
_SIGNAL_DEAD_FLOOR = 0.01

# Weight of an interface-definition file relative to a build manifest when scoring
# boundaries. An .mojom/.proto file is direct evidence of a trust boundary; a BUILD.gn
# is only evidence that someone drew a module line here.
_W_INTERFACE_FILE = 3.0

# --- Coverage self-disclosure ---------------------------------------------------------
#
# The attack-surface table is 40% of the score and it only knows the idioms someone has
# written a regex for. On a language it does not know it returns zero for every file --
# which is indistinguishable, downstream, from "this code is clean". A repository we can
# see, we can check by hand; a customer's internal Kotlin monorepo we will never see at
# all, and nobody will write in to say the ranking was garbage.
#
# So the survey measures its own hit rate instead of declaring a supported-language list.
# A hard-coded list would rot the moment someone adds a pattern; a measured rate
# self-calibrates. Two distinct gaps are reported separately because they have different
# fixes: an extension outside `_SOURCE_EXT` is never opened at all (add it to the
# language tables), while an extension that is opened but never matches is a hole in
# `_SURFACE_PATTERNS` (write the patterns).
#
# Thresholds below are empirical. Measured match rates: juice-shop 32.4% of opened files
# matched some idiom, chromium 14.3%.
_MAX_COVERAGE_EXTS = 40

# Below this share of opened files matching anything, the attack-surface signal is
# declared weak for the repository as a whole.
#
# Deliberately far below both measured rates. Chromium sits at 14.3% and its ranking is
# demonstrably sound -- the top slices are its IPC, network and browser-process surfaces
# -- so a threshold that fired there would fire on a healthy repository, and a warning
# that cries wolf is a warning nobody reads. This line is set to catch the case the
# existing machinery misses: `_rebalance_weights` already retires a signal that is
# uniformly zero (spread <= `_SIGNAL_DEAD_FLOOR`), so total blindness is handled. What is
# not handled is a table matching a handful of files by accident -- nonzero spread, so
# the signal survives and keeps its 40%, while being almost entirely noise.
_COVERAGE_WEAK_RATE = 0.05

# Per-extension callouts are RELATIVE to the repository's own mean rather than to a fixed
# rate, because a fixed rate cannot tell "we understand this language and it is genuinely
# low-surface" from "we are catching crumbs". Measured: an absolute 10% cutoff flagged
# chromium's `.h` at 8.5%, where low surface is correct -- headers are declarations.
#
# The floor is a FRACTION of the mean, not the mean itself. Half of any distribution
# falls below its own mean, so reporting everything under it would name well-covered
# languages: chromium's `.cc` matches at 14.0% against a 14.25% mean and would have been
# listed as a blind spot. At a third of the mean the same run reports `.java` (1,337
# files, 4.3%), `.rs`, `.sh`, `.m` and `.hpp` -- which is the Android, shell and
# Objective-C surface we genuinely do not read -- and juice-shop reports nothing, being
# one well-covered language.
_COVERAGE_MIN_VOLUME = 25  # noise floor: fewer opened files than this proves nothing
_COVERAGE_RELATIVE_FLOOR = 1.0 / 3.0
_COVERAGE_MAX_REPORTED = 5

# Never-opened extensions are reported by share of the repository, so a stray `.foo` does
# not generate a disclosure. No attempt is made to filter out binary assets: a
# hand-maintained "not really code" list is the same rotting table this module refuses to
# keep, and wrongly filtering hides a real gap. `.png` in the output is obvious to a
# reader; a silently dropped `.kt` would not be.
_CENSUS_MIN_SHARE = 0.02

# --- Signal tables ------------------------------------------------------------------

_UNSAFE_EXT = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx", ".m", ".mm", ".s", ".asm"}
_INTERPRETED_EXT = {".py", ".js", ".jsx", ".ts", ".tsx", ".rb", ".php", ".pl", ".sh", ".bash", ".lua"}
_MEMORY_SAFE_EXT = {".rs", ".go", ".java", ".kt", ".swift", ".cs", ".scala", ".ml", ".hs", ".erl", ".ex"}

_SOURCE_EXT = _UNSAFE_EXT | _INTERPRETED_EXT | _MEMORY_SAFE_EXT

# Memory-unsafe code carries the classic corruption classes outright; interpreted code
# trades those for injection and deserialization; memory-safe compiled code still has
# logic flaws but a far smaller share of the historical CVE mass.
_LANGUAGE_RISK = {"unsafe": 1.0, "interpreted": 0.6, "safe": 0.25, "other": 0.0}

# Attack-surface patterns. Weighted because "this file calls bind()" is far stronger
# evidence of external reachability than "this file mentions argv".
#
# The table MUST cover both native and interpreted surface. An earlier native-only
# version scored every JavaScript server directory at exactly 0.00, which did not look
# like a bug -- it looked like a low-risk directory -- and silently reduced the formula
# to its remaining 60% on any web codebase. Measured on juice-shop, that ranked two test
# directories above the vulnerable routes. A signal that returns zero for a whole
# language is worse than no signal, because it is indistinguishable from a real finding.
_SURFACE_PATTERNS: tuple[tuple[re.Pattern, float, str], ...] = (
    # --- Native / systems surface ---
    (re.compile(r"\b(?:bind|listen|accept|recvfrom|recvmsg|WSARecv)\s*\("), 3.0, "network_listener"),
    (re.compile(r"\bSOCK_(?:STREAM|DGRAM|RAW)\b|\bAF_INET6?\b"), 2.0, "network_listener"),
    (re.compile(r"\bioctl\s*\(|\bSYSCALL_DEFINE\d|\bcopy_(?:from|to)_user\s*\("), 3.0, "syscall_surface"),
    (re.compile(r"\bmojo::|\bIPC_MESSAGE_|\bgrpc::|\bDBus[A-Z]|\bBinder\b|\bAIDL\b"), 2.5, "ipc_endpoint"),
    (re.compile(r"\b(?:setuid|seteuid|setgid|setresuid|setgroups)\s*\(|\bCAP_[A-Z_]{3,}"), 3.0, "privilege"),
    (re.compile(r"\b(?:memcpy|strcpy|strcat|sprintf|alloca|gets)\s*\("), 1.5, "unsafe_api"),
    (re.compile(r"\b(?:getopt|getopt_long|ArgumentParser|OptionParser)\b"), 1.0, "cli_parser"),
    # --- Request-handling surface (the entry point for most web vulnerabilities) ---
    (re.compile(r"\breq\.(?:query|body|params|cookies|headers|files)\b"), 3.0, "request_handler"),
    (re.compile(r"\brequest\.(?:args|form|json|files|cookies|headers)\b"), 3.0, "request_handler"),
    (re.compile(r"@(?:app|bp|router)\.(?:route|get|post|put|delete|patch)\b"), 2.5, "request_handler"),
    (re.compile(r"\b(?:app|router)\.(?:get|post|put|delete|patch|use|all)\s*\("), 2.0, "request_handler"),
    (re.compile(r"\b(?:RequestMapping|GetMapping|PostMapping|HttpServlet)\b"), 2.5, "request_handler"),
    # --- Injection sinks ---
    (re.compile(r"\b(?:eval|execScript)\s*\(|\bnew\s+Function\s*\("), 3.0, "code_injection"),
    (re.compile(r"\bchild_process\b|\bexecSync\s*\(|\bspawnSync\s*\(|\bsubprocess\.(?:run|Popen|call)\b"), 3.0, "command_injection"),
    (re.compile(r"\bos\.system\s*\(|\bpopen\s*\(|\bshell\s*=\s*True\b"), 3.0, "command_injection"),
    (re.compile(r"\bsequelize\.query\s*\(|\.raw\s*\(|\bexecute\s*\(\s*[\"'`].*(?:SELECT|INSERT|UPDATE|DELETE)"), 3.0, "sql_injection"),
    (re.compile(r"\b(?:SELECT|INSERT|UPDATE|DELETE)\b.{0,40}(?:\+\s*\w+|\$\{|%s|\bformat\s*\()"), 2.5, "sql_injection"),
    # --- Deserialization / parsing ---
    (re.compile(r"\b(?:Deserialize|deserialize|Unmarshal|unmarshal|ParseFrom)\w*\s*\("), 2.0, "deserialization"),
    (re.compile(r"\bpickle\.loads?\b|\byaml\.load\s*\(|\bunserialize\s*\(|\bObjectInputStream\b"), 3.0, "deserialization"),
    # --- Path handling / file surface ---
    (re.compile(r"\b(?:sendFile|readFileSync|createReadStream)\s*\(|\bfs\.(?:readFile|open|unlink)\b"), 2.0, "path_handling"),
    (re.compile(r"\bos\.path\.join\s*\(|\bopen\s*\(\s*(?:os\.path\.join|request|req)"), 1.5, "path_handling"),
    # --- AuthN / AuthZ ---
    (re.compile(r"\bjsonwebtoken\b|\bjwt\.(?:sign|verify|decode)\b|\bpassport\b|\bbcrypt\b"), 2.0, "authn"),
    (re.compile(r"\b(?:authorize|isAuthenticated|checkPermission|require_role|@login_required)\b"), 2.0, "authz"),
    # --- Outbound / SSRF ---
    (re.compile(r"\baxios\.(?:get|post|request)\s*\(|\brequests\.(?:get|post)\s*\(|\burllib\.request\b"), 1.5, "outbound_request"),
    # --- Crypto ---
    (re.compile(r"\bSSL_[a-z]|\bEVP_[A-Za-z]|\bRAND_bytes\b|\bcrypto::|\bcrypto\.create(?:Cipher|Hash|Hmac)"), 1.5, "crypto"),
)

# Build manifests mark module boundaries. Matched by NAME only and read as text.
_BUILD_MANIFESTS = {
    "BUILD.gn", "BUILD.bazel", "BUILD", "CMakeLists.txt", "Makefile", "makefile",
    "pom.xml", "build.gradle", "build.gradle.kts", "package.json", "Cargo.toml",
    "go.mod", "setup.py", "pyproject.toml", "meson.build", "Kconfig", "configure.ac",
}

# Interface definition files mark TRUST boundaries, which is what the boundary signal is
# supposed to be measuring. Each one describes data that crosses a process, privilege or
# service boundary and is deserialized on the far side by code that did not produce it
# -- historically one of the densest sources of exploitable bugs in large codebases.
#
# This replaced a raw count of build manifests. That count was a size proxy and nothing
# more: measured on chromium, chrome/browser holds 1,996 BUILD.gn files against ipc/'s
# single one, so normalizing by the maximum scored the actual IPC layer at 0.0005 and
# handed a 0.20-weighted perfect 1.00 to the largest directory in the tree. Size was
# already counted twice elsewhere (group file count and the saturation factor); this
# made it three times, and put a directory with an attack-surface score of 0.023 at the
# top of the ranking.
_INTERFACE_EXT = {
    ".mojom", ".proto", ".idl", ".aidl", ".thrift", ".graphql", ".gql", ".avsc",
    ".capnp", ".fbs", ".ice", ".ridl",
}
_INTERFACE_NAME_RE = re.compile(r"(?:openapi|swagger|asyncapi)[\w.-]*\.(?:ya?ml|json)$", re.IGNORECASE)

# Paths that are real code but almost never the interesting attack surface. Demoted
# rather than excluded: a test directory can still hold the only parser in the tree.
_DEMOTED_SEGMENTS = {
    "test", "tests", "testing", "testdata", "test_data", "unittest", "unittests",
    "doc", "docs", "example", "examples", "sample", "samples", "demo", "demos",
    "third_party", "vendor", "node_modules", "fixtures", "mock", "mocks", "benchmark",
    "benchmarks", "tools", "build", "out", "dist",
}
_DEMOTION_FACTOR = 0.35

_ARCHETYPE_BY_TAG = {
    "syscall_surface": "kernel_syscall_audit",
    "ipc_endpoint": "ipc_sandbox_escape",
    "network_listener": "network_protocol_audit",
    "deserialization": "deserialization_audit",
    "privilege": "privilege_escalation_audit",
    "crypto": "crypto_misuse_audit",
    "unsafe_api": "memory_safety_audit",
    "cli_parser": "input_parsing_audit",
    "request_handler": "web_request_handling_audit",
    "code_injection": "code_injection_audit",
    "command_injection": "command_injection_audit",
    "sql_injection": "sql_injection_audit",
    "path_handling": "path_traversal_audit",
    "authn": "authentication_audit",
    "authz": "authorization_audit",
    "outbound_request": "ssrf_audit",
}

# What to actually hunt in an area of each measured kind.
#
# This table is the specialization. Before it existed, the archetype was a label: the
# three synthesis families differ by one researcher tool and two patcher tools, so a
# directory measured as `crypto_misuse_audit` and one measured as `sql_injection_audit`
# received byte-identical instructions. The survey already distinguishes seventeen kinds
# of area; everything downstream collapsed them into "look for bugs".
#
# SECURITY -- why a lookup table and not generated text. The archetype is derived from
# repository bytes, so it is attacker-influenced: a directory can be shaped to measure as
# any kind its author wants. Here that influence is confined to CHOOSING A KEY. Every
# byte of every directive below is operator-authored and fixed at import; a repository
# can redirect attention to a different entry, which is the intended power of the survey,
# but it cannot author a single word of what the agent is told. Selection is influence;
# authorship would be injection. An unrecognized key selects nothing.
#
# Each entry names the sink, because "audit the crypto" is not a task -- "find where a
# key or IV is reused across messages" is.
_AUDIT_FOCUS: Dict[str, str] = {
    "kernel_syscall_audit": (
        "Syscall and ioctl entry points. Follow every argument from userspace inward: "
        "unchecked copy_from_user sizes, TOCTOU between validation and use, missing "
        "capability checks, and integer truncation in size or index arguments."
    ),
    "ipc_sandbox_escape": (
        "The trust boundary between processes. Treat every message field as "
        "attacker-chosen, including ones a cooperating peer would never vary: handle or "
        "descriptor confusion, missing origin checks on the receiving side, and state "
        "that a compromised low-privilege peer can drive into the high-privilege one."
    ),
    "network_protocol_audit": (
        "Parsing of bytes off the wire before any authentication has run. Length fields "
        "trusted against the real buffer, state machines that accept messages out of "
        "order, and resource growth an unauthenticated peer can trigger."
    ),
    "deserialization_audit": (
        "Object reconstruction from untrusted input. Which types can be instantiated, "
        "what runs during construction, and whether a type allowlist exists at all -- "
        "gadget reachability matters more than the parser itself."
    ),
    "privilege_escalation_audit": (
        "Where a privilege is acquired, dropped, or assumed. Missing or unchecked "
        "drop-privilege return values, setuid/sudo invocation, and operations performed "
        "while still elevated that use attacker-influenced paths or arguments."
    ),
    "crypto_misuse_audit": (
        "Misuse rather than algorithm strength. Key or IV/nonce reuse, ECB, predictable "
        "or non-cryptographic randomness for secrets, comparison of secrets with "
        "non-constant-time equality, and verification whose result is computed but never "
        "branched on."
    ),
    "memory_safety_audit": (
        "Lifetime and bounds. Use-after-free across ownership handoffs, off-by-one in "
        "index and length arithmetic, unchecked arithmetic feeding an allocation size, "
        "and unbounded copies into fixed buffers."
    ),
    "input_parsing_audit": (
        "The parser's disagreement with its consumer. Inputs accepted here but "
        "interpreted differently downstream, unbounded repetition or nesting, and "
        "argument or flag injection where parsed values are passed onward."
    ),
    "web_request_handling_audit": (
        "Request handlers and what reaches them unvalidated. Parameters flowing into "
        "queries, file paths, templates or redirects; mass assignment; and inconsistent "
        "authorization between handlers that serve the same resource."
    ),
    "code_injection_audit": (
        "Anywhere input becomes executable text: eval, dynamic import, template "
        "compilation, reflection by name. Follow the string backwards to its origin "
        "rather than outward from the sink."
    ),
    "command_injection_audit": (
        "Process execution. Shell-interpreted invocation, argument construction by "
        "string concatenation, PATH and environment inheritance, and filenames or "
        "arguments beginning with a dash."
    ),
    "sql_injection_audit": (
        "Query construction. Concatenation or interpolation into SQL, identifiers and "
        "ORDER BY clauses that parameterization cannot cover, and ORM escape hatches "
        "that accept raw fragments."
    ),
    "path_traversal_audit": (
        "Path handling. Traversal sequences surviving normalization, symlinks followed "
        "outside an intended root, validation performed before rather than after "
        "canonicalization, and archive extraction writing outside its destination."
    ),
    "authentication_audit": (
        "Who the caller is proven to be. Token and session validation that omits "
        "signature, expiry, audience or issuer; algorithm confusion; verification that "
        "silently succeeds on malformed input; and credential comparison or storage."
    ),
    "authorization_audit": (
        "Whether the authenticated caller may do this to this object. Object-level "
        "checks missing where route-level ones exist, authorization decided before the "
        "target is resolved, and paths reaching the same resource without the check."
    ),
    "ssrf_audit": (
        "Outbound requests whose destination is influenced by input. Redirect following, "
        "DNS rebinding and parser-disagreement bypasses of host allowlists, and metadata "
        "or loopback endpoints reachable from the requesting host."
    ),
    "general_appsec_audit": (
        "No single idiom dominated here, so work from the data rather than from a "
        "pattern: identify what crosses into this area from outside, and follow those "
        "values to wherever they are trusted."
    ),
}


def focus_directive(archetype: str) -> str:
    """Operator-authored instruction for an area of this measured kind, or "".

    The argument is repository-derived and is used ONLY as a lookup key; see the note on
    `_AUDIT_FOCUS`. An unknown kind returns "" rather than a default, so a new Surveyor
    tag produces silence instead of a misleading specialization -- and the exhaustiveness
    test fails, which is the intended way to find out.
    """
    return _AUDIT_FOCUS.get(str(archetype), "")

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slug(text: str) -> str:
    """Lowercase identifier safe to embed in an id. Never empty."""
    cleaned = _SLUG_RE.sub("_", str(text).lower()).strip("_")
    return cleaned[:60] or "root"


def _classify_extension(ext: str) -> str:
    if ext in _UNSAFE_EXT:
        return "unsafe"
    if ext in _INTERPRETED_EXT:
        return "interpreted"
    if ext in _MEMORY_SAFE_EXT:
        return "safe"
    return "other"


def _group_key(rel_path: str, depth: int = 2) -> str:
    """Directory group a file belongs to: its first `depth` path components."""
    parts = [p for p in rel_path.split("/") if p]
    if len(parts) <= 1:
        return "."
    return "/".join(parts[: min(depth, len(parts) - 1)])


class _Group:
    """Accumulator for one candidate slice."""

    __slots__ = (
        "key", "files", "lang_counts", "manifest_count", "interface_count",
        "surface_score", "surface_tags", "scanned",
        "complexity_total", "complexity_files", "function_total",
    )

    def __init__(self, key: str):
        self.key = key
        self.files: list[tuple[Path, str]] = []
        self.lang_counts: dict[str, int] = defaultdict(int)
        self.manifest_count = 0
        self.interface_count = 0
        self.surface_score = 0.0
        self.surface_tags: dict[str, float] = defaultdict(float)
        self.scanned = 0
        # Filled by `_scan_group_complexity`: summed G over parsed files, how many
        # files actually parsed, and how many named functions those files held.
        self.complexity_total = 0
        self.complexity_files = 0
        self.function_total = 0

    @property
    def language(self) -> str:
        ranked = sorted(self.lang_counts.items(), key=lambda kv: (-kv[1], kv[0]))
        for name, count in ranked:
            if name != "other" and count:
                return name
        return "other"

    def language_risk(self) -> float:
        total = sum(self.lang_counts.values())
        if not total:
            return 0.0
        return sum(_LANGUAGE_RISK[k] * n for k, n in self.lang_counts.items()) / total

    def is_demoted(self) -> bool:
        return any(seg in _DEMOTED_SEGMENTS for seg in self.key.lower().split("/"))


def _normalize(values: dict[str, float]) -> dict[str, float]:
    """Scales a signal to [0, 1] across groups so weights mean what they say.

    Normalized against a high PERCENTILE rather than the maximum, and clipped. Dividing
    by the maximum makes every score hostage to a single outlier: measured on chromium,
    one small directory with an extreme commit-per-file density pushed the churn signal
    of all fifteen top-ranked groups into the 0.001-0.005 band, so a 25%-weighted signal
    contributed nothing to the ordering while still appearing in the output as though it
    had. Clipping at the percentile costs the ability to distinguish among the most
    extreme few groups -- which are already ranked top -- and buys a signal that
    discriminates across the rest of the distribution.
    """
    if not values:
        return {}
    positives = sorted(v for v in values.values() if v > 0)
    if not positives:
        return {k: 0.0 for k in values}
    # Percentile needs a population to be meaningful; below that, fall back to the max.
    if len(positives) >= _ROBUST_MIN_POPULATION:
        index = min(len(positives) - 1, int(len(positives) * _ROBUST_PERCENTILE))
        top = positives[index]
    else:
        top = positives[-1]
    if top <= 0:
        return {k: 0.0 for k in values}
    return {k: min(1.0, v / top) for k, v in values.items()}


def _rebalance_weights(
    signals: dict[str, dict[str, float]], weights: dict[str, float]
) -> tuple[dict[str, float], list[str]]:
    """Redistributes the weight of any signal that does not vary across groups.

    The test is SPREAD, not magnitude. A signal has to separate groups to earn its
    weight, and it fails to do that at either extreme:

    * Uniformly zero -- juice-shop carries exactly two build manifests, both at module
      roots, so the boundary signal was 0.00 for every candidate group and 20% of the
      formula evaporated without a word.
    * Uniformly high -- a single-language repository scores every group identically on
      language risk. Normalization then maps all of them to 1.00, which adds the same
      constant to every score and cannot reorder anything, while still consuming 15%.

    The second case is the one that matters for the general rule: an earlier version of
    this function tested `max(values) > floor` and so caught only the first. Both are the
    same failure -- a signal that looks like it is contributing and is not -- and the
    scores it produces look entirely reasonable either way.
    """
    live: dict[str, float] = {}
    for name, weight in weights.items():
        values = signals.get(name)
        if not values:
            continue
        if max(values.values()) - min(values.values()) > _SIGNAL_DEAD_FLOOR:
            live[name] = weight
    dead = sorted(set(weights) - set(live))
    if not live:
        # Every signal flat: no basis to re-weight, so leave the formula untouched.
        return dict(weights), dead
    scale = sum(weights.values()) / sum(live.values())
    return {name: w * scale for name, w in live.items()}, dead


def _assess_coverage(
    census: dict[str, list],
    coverage: dict[str, list],
) -> dict[str, Any]:
    """Reports how much of this repository the attack-surface table actually understood.

    The ranking's largest single input is a table of regexes someone wrote by hand. On a
    language nobody wrote patterns for it returns zero for every file, and zero is not
    distinguishable downstream from "there is nothing here". On a repository we can see,
    that is a caveat we notice. On a customer's internal monorepo -- which we will never
    see, and about which nobody will complain -- it is a 40%-weighted signal silently
    returning nothing for the entire codebase.

    So the survey reports its own hit rate rather than asserting a list of supported
    languages. A declared list is a second thing to maintain and it starts rotting the
    moment someone adds a pattern; a measured rate is correct by construction and
    improves on its own as the table grows.

    Two gaps, reported separately because the remedies differ:

    * `unopened_languages` -- the extension is not in `_SOURCE_EXT`, so no file was read
      at all and no pattern ever ran. Remedy: extend the language tables.
    * `unrecognized_languages` -- files were read and matched nothing. Remedy: extend
      `_SURFACE_PATTERNS`.

    The second list is relative to this repository's own mean match rate, not to a fixed
    one. A fixed cutoff cannot tell a language we understand that is genuinely
    low-surface from one we are only catching crumbs of: at an absolute 10% it flagged
    chromium's `.h` files, whose low rate is correct, headers being declarations.
    """
    seen_total = sum(v[0] for v in census.values())
    opened_total = sum(v[0] for v in coverage.values())
    matched_total = sum(v[1] for v in coverage.values())
    match_rate = matched_total / opened_total if opened_total else 0.0

    unopened = [
        {"ext": ext, "files": tally[0], "share": round(tally[0] / seen_total, 4)}
        for ext, tally in census.items()
        # tally[1] is the eligible count: zero means no file of this extension can ever
        # be opened, as opposed to merely not having been sampled this run.
        if tally[1] == 0 and seen_total and tally[0] / seen_total >= _CENSUS_MIN_SHARE
    ]
    unopened.sort(key=lambda item: (-item["files"], item["ext"]))

    unrecognized = [
        {
            "ext": ext,
            "opened": tally[0],
            "matched": tally[1],
            "rate": round(tally[1] / tally[0], 3),
        }
        for ext, tally in coverage.items()
        if tally[0] >= _COVERAGE_MIN_VOLUME
        # Nothing at all, or well under what this repository averages. The first clause
        # is not redundant: in a repository the table understands not at all the mean is
        # itself zero, nothing can fall below a fraction of zero, and the list naming
        # which languages were missed would come back empty in exactly the case it most
        # needs to be populated.
        and (tally[1] == 0 or (tally[1] / tally[0]) < match_rate * _COVERAGE_RELATIVE_FLOOR)
    ]
    # Ordered by how many files came back empty, not by rate. The question an operator
    # is asking is "how much of my code did you learn nothing from", and by that measure
    # 1,337 Java files at 4% matter far more than 32 headers at 0%.
    unrecognized.sort(key=lambda item: (-(item["opened"] - item["matched"]), item["ext"]))

    return {
        "files_opened": opened_total,
        "files_matched": matched_total,
        "pattern_match_rate": round(match_rate, 4),
        "scannable_share": round(
            sum(v[1] for v in census.values()) / seen_total, 4
        )
        if seen_total
        else 0.0,
        # True when the table barely engaged with this repository at all. Distinct from
        # `inactive_signals`, which retires a signal only when it is uniformly flat: a
        # table matching a handful of files by accident has spread, keeps its full
        # weight, and is almost entirely noise.
        "attack_surface_weak": bool(opened_total) and match_rate < _COVERAGE_WEAK_RATE,
        "unopened_languages": unopened[:_COVERAGE_MAX_REPORTED],
        "unrecognized_languages": unrecognized[:_COVERAGE_MAX_REPORTED],
    }


def _boundary_density(group: "_Group") -> float:
    """Trust-boundary evidence per source file for one group.

    A named function rather than an expression inlined into `survey()` so that a test
    can exercise the real formula. The first version of this control was inlined, and
    the pin guarding it recomputed the formula inside the test file -- which meant
    reverting the product code to the old size-proxy behaviour left the pin green,
    because the pin was testing its own copy.

    Density, not count: see `_INTERFACE_EXT` for why the raw count was a size proxy.
    """
    weighted = _W_INTERFACE_FILE * group.interface_count + group.manifest_count
    return weighted / max(1, len(group.files))


def _census_key(ext: str, census: dict[str, list]) -> str:
    """Bounded key for the per-extension census.

    Extensions are repository-controlled text and a repository may contain an unbounded
    number of distinct ones, so the key is truncated and the table is capped. Everything
    past the cap lands in one overflow bucket rather than growing without limit.
    """
    key = ext.lower()[:12] or "(none)"
    if key not in census and len(census) >= _MAX_COVERAGE_EXTS:
        return "(other)"
    return key


def _collect_groups(
    vetted: list[tuple[Path, str]],
    census: Optional[dict[str, list]] = None,
) -> dict[str, _Group]:
    """Pass 1: free signals only -- path, extension, manifest names. No file is opened.

    `census` accumulates [seen, eligible] per file extension, where "eligible" means the
    extension is in `_SOURCE_EXT` and the file may therefore be content-scanned later.
    This is the FIRST of two coverage gaps: a language absent from the extension tables
    is invisible before the pattern table ever runs.
    """
    groups: dict[str, _Group] = {}
    for abs_path, rel_path in vetted:
        key = _group_key(rel_path)
        group = groups.get(key)
        if group is None:
            group = groups[key] = _Group(key)
        name = os.path.basename(rel_path)
        ext = os.path.splitext(name)[1].lower()
        group.lang_counts[_classify_extension(ext)] += 1
        if name in _BUILD_MANIFESTS:
            group.manifest_count += 1
        if ext in _INTERFACE_EXT or _INTERFACE_NAME_RE.search(name):
            group.interface_count += 1
        if ext in _SOURCE_EXT:
            group.files.append((abs_path, rel_path))
        if census is not None:
            tally = census.setdefault(_census_key(ext, census), [0, 0])
            tally[0] += 1
            tally[1] += 1 if ext in _SOURCE_EXT else 0
    return groups


def _scan_group_surface(
    group: _Group,
    budget: int,
    coverage: Optional[dict[str, list]] = None,
) -> int:
    """Pass 2: sampled content read for attack-surface patterns. Returns files opened.

    Sampling, not exhaustive enumeration. The sample is taken at a fixed stride across
    the group's sorted file list rather than from the front, so a group does not get
    judged entirely by whatever sorts first (which, being alphabetical, is the very bias
    this module exists to remove).

    `coverage` accumulates [scanned, matched] per file extension across the whole
    survey. It is passed in rather than stored on the group because it is a property of
    the pattern table's fit to the repository, not of any one directory -- and because
    _Group uses __slots__.
    """
    source_files = sorted(group.files, key=lambda item: item[1])
    if not source_files or budget <= 0:
        return 0

    allowance = min(_SAMPLE_FILES_PER_GROUP, budget)
    stride = max(1, len(source_files) // allowance)
    sample = source_files[::stride][:allowance]

    opened = 0
    for abs_path, rel in sample:
        try:
            with open(abs_path, "rb") as handle:
                blob = handle.read(_MAX_SCAN_BYTES)
        except OSError:
            continue
        opened += 1
        group.scanned += 1
        text = blob.decode("utf-8", errors="ignore")
        matched = False
        for pattern, weight, tag in _SURFACE_PATTERNS:
            if pattern.search(text):
                group.surface_score += weight
                group.surface_tags[tag] += weight
                matched = True
        if coverage is not None:
            ext = _census_key(os.path.splitext(rel)[1], coverage)
            tally = coverage.setdefault(ext, [0, 0])
            tally[0] += 1
            tally[1] += 1 if matched else 0
    return opened


def _scan_group_complexity(group: _Group, budget: int) -> int:
    """Pass 3: sampled tree-sitter parse for cognitive complexity. Returns files read.

    Separate from `_scan_group_surface` rather than folded into it because the two
    passes have different budgets and different failure modes: a regex table cannot
    fail to load, a grammar can. The sample is strided across the sorted file list
    for the same anti-alphabetical reason as the content scan.

    Every degradation is per-file and silent by design: an unreadable file, a
    missing grammar, or unparseable source skips that file and nothing else. Losing
    the whole signal leaves it uniformly zero, which `_rebalance_weights` retires --
    the survey must never abort because complexity could not be measured (INV-6).
    """
    try:
        from core.structural_index import complexity_for_file
    except Exception:
        return 0

    source_files = sorted(group.files, key=lambda item: item[1])
    if not source_files or budget <= 0:
        return 0
    allowance = min(_COMPLEXITY_FILES_PER_GROUP, budget)
    stride = max(1, len(source_files) // allowance)
    sample = source_files[::stride][:allowance]

    opened = 0
    for abs_path, rel in sample:
        try:
            with open(abs_path, "rb") as handle:
                blob = handle.read(_MAX_SCAN_BYTES)
        except OSError:
            continue
        opened += 1
        try:
            measured = complexity_for_file(rel, blob)
        except Exception:
            continue
        if measured is None:
            continue
        group.complexity_total += measured["complexity"]
        group.complexity_files += 1
        group.function_total += measured["functions"]
    return opened


def _churn_by_group(repo_dir: Path, jail_dir: Path) -> dict[str, float]:
    """Churn, revert density and CVE-referencing commits, via CP-2 only.

    Returns an empty mapping on any failure. Churn is 25% of the score, so losing it
    degrades ranking quality but must never abort the survey -- a target with no usable
    history is still worth surveying on its other three signals.
    """
    from tools.research_tools import _run_safe_git_command, _validate_git_jail

    valid, err = _validate_git_jail(repo_dir, jail_dir)
    if not valid:
        logger.info("Surveyor churn signal unavailable: %s", err)
        return {}

    out, ok = _run_safe_git_command(
        [
            "log",
            "--no-show-signature",
            "--no-ext-diff",
            "--no-textconv",
            f"-n{_CHURN_COMMITS}",
            "--name-only",
            "--format=%x1e%s",
        ],
        repo_dir,
        timeout=_CHURN_GIT_TIMEOUT,
    )
    if not ok:
        logger.info("Surveyor churn signal unavailable: %s", out)
        return {}

    scores: dict[str, float] = defaultdict(float)
    for record in out.split("\x1e"):
        if not record.strip():
            continue
        lines = record.splitlines()
        subject = lines[0] if lines else ""
        lowered = subject.lower()
        # A revert says the change was wrong; a CVE/security reference says this area has
        # produced real vulnerabilities. Both are stronger evidence than raw commit count.
        weight = 1.0
        if "revert" in lowered:
            weight += 2.0
        if "cve-" in lowered or "security" in lowered or "vulnerab" in lowered:
            weight += 3.0
        for path in lines[1:]:
            path = path.strip()
            if path:
                scores[_group_key(path)] += weight
    return dict(scores)


def _archetype_for(group: _Group) -> str:
    if group.surface_tags:
        top_tag = max(group.surface_tags.items(), key=lambda kv: (kv[1], kv[0]))[0]
        mapped = _ARCHETYPE_BY_TAG.get(top_tag)
        if mapped:
            return mapped
    return "memory_safety_audit" if group.language == "unsafe" else "general_appsec_audit"


def _complexity_for(file_count: int) -> str:
    """File-count buckets: the FALLBACK when complexity could not be measured.

    Before the measured signal existed this was the only estimate, and it answers a
    different question -- "how much ground is this" rather than "how tangled is it".
    Kept because a survey with no working grammar still owes the planner a size
    statement, and `complexity_basis` discloses which question was answered.
    """
    if file_count < 50:
        return "low"
    if file_count < 500:
        return "medium"
    return "high"


def _measured_complexity_for(mean_complexity: float) -> str:
    """Buckets a group's measured mean G per function.

    Thresholds anchor on SonarSource's long-standing per-function warning level of
    15: a sampled MEAN of 12 across every function in an area -- trivial getters
    included -- means the typical function is near the level a linter would flag
    individually, which is exactly what "high" should claim. Below 4 the typical
    function is one branch or none.
    """
    if mean_complexity < 4.0:
        return "low"
    if mean_complexity < 12.0:
        return "medium"
    return "high"


def _compute_snapshot_id(repo_dir: Path, vetted: list[tuple[Path, str]]) -> str:
    """Identifies the STATE OF THE CODE surveyed, not the run that surveyed it.

    This is the join key for every cross-run comparison, so it has to be equal for
    equal code and different for different code. A run id would be neither: two runs
    over an unchanged repository would appear to be looking at different things, and
    "what changed since last time" could never be answered.

    Preference order:

    1. `git rev-parse HEAD` via CP-2 -- exact, cheap, and the identifier the operator
       already thinks in.
    2. A digest over the vetted relative paths -- for targets with no usable history
       (a dirty tree, an export, a tarball). Coarser: it moves when files are added,
       removed or renamed, but NOT when a file's contents change. That is a deliberate
       limit, not an oversight; hashing 500k file bodies costs more than the survey.

    Prefixed so the two can never be confused downstream, and so a weaker identifier
    cannot silently masquerade as a commit.
    """
    # Lazy, like every other tools import here: core must not import tools at module
    # scope or the two packages form a cycle.
    from tools.research_tools import (
        DEFAULT_GIT_TIMEOUT,
        _run_safe_git_command,
        _validate_git_jail,
    )

    valid, _ = _validate_git_jail(repo_dir, repo_dir)
    if valid:
        out, ok = _run_safe_git_command(
            ["rev-parse", "HEAD"], repo_dir, timeout=DEFAULT_GIT_TIMEOUT
        )
        head = out.strip()
        # Reject anything that is not a plain hex object name: this string is repo-
        # influenced and becomes a database key and a filename component.
        if ok and re.fullmatch(r"[0-9a-f]{7,64}", head):
            return f"git:{head}"

    digest = hashlib.sha256()
    for _, rel in sorted(vetted, key=lambda item: item[1]):
        digest.update(rel.encode("utf-8", errors="replace"))
        digest.update(b"\n")
    return f"tree:{digest.hexdigest()[:32]}"


def survey(
    target: Union[str, Path],
    max_slices: int = MAX_SLICES,
    include_churn: bool = True,
) -> dict[str, Any]:
    """Surveys a repository and returns an ASTM (design §4.4).

    Raises ValueError if the target fails CP-3 validation -- a Surveyor that silently
    surveys a path it could not validate is worse than one that refuses.
    """
    started = time.time()

    resolved, err = validate_scan_target(target)
    if resolved is None:
        raise ValueError(f"Surveyor refused target: {err}")

    vetted = get_vetted_staging_files(resolved)
    snapshot_id = _compute_snapshot_id(resolved, vetted)
    census: dict[str, list] = {}
    groups = _collect_groups(vetted, census)

    sizeable = {k: g for k, g in groups.items() if len(g.files) >= _MIN_GROUP_FILES}
    # Fall back to every group rather than emitting nothing for a small repository.
    candidates = sizeable or groups

    # Rank cheaply first so the expensive pass only touches plausible subsystems.
    def _cheap_rank(group: _Group) -> float:
        base = group.language_risk() * math.log1p(len(group.files))
        return base * (_DEMOTION_FACTOR if group.is_demoted() else 1.0)

    ordered = sorted(candidates.values(), key=lambda g: (-_cheap_rank(g), g.key))
    budget = _MAX_SAMPLED_FILES
    groups_scanned = 0
    coverage: dict[str, list] = {}
    for group in ordered:
        if budget <= 0:
            break
        budget -= _scan_group_surface(group, budget, coverage)
        groups_scanned += 1

    # Pass 3 shares the cheap-rank visit order, so the parse budget drains into the
    # same plausible subsystems the content scan prioritized.
    parse_budget = _MAX_PARSED_FILES
    for group in ordered:
        if parse_budget <= 0:
            break
        parse_budget -= _scan_group_complexity(group, parse_budget)

    churn = _churn_by_group(resolved, resolved) if include_churn else {}

    surface_raw = {g.key: (g.surface_score / g.scanned if g.scanned else 0.0) for g in candidates.values()}
    # Churn as a DENSITY, not a count. A directory with ten times the files mechanically
    # receives roughly ten times the commits, so raw churn is largely a restatement of
    # size -- and size is already accounted for below. Measured on chromium, raw churn put
    # chrome/browser at a perfect 1.00 on the strength of being the biggest directory.
    churn_raw = {
        g.key: churn.get(g.key, 0.0) / max(1, len(g.files)) for g in candidates.values()
    }
    # Boundary as an interface DENSITY. See `_INTERFACE_EXT`: the raw manifest count this
    # replaced was a restatement of directory size.
    boundary_raw = {g.key: _boundary_density(g) for g in candidates.values()}
    language_raw = {g.key: g.language_risk() for g in candidates.values()}
    # Complexity as mean G per PARSED file, not per group member: a file that never
    # parsed must not dilute the mean, and a group where nothing parsed scores 0.0
    # with its complexity_sampled count disclosing why.
    complexity_raw = {
        g.key: (g.complexity_total / g.complexity_files if g.complexity_files else 0.0)
        for g in candidates.values()
    }

    normalized = {
        "attack_surface": _normalize(surface_raw),
        "churn": _normalize(churn_raw),
        "boundaries": _normalize(boundary_raw),
        "language_risk": _normalize(language_raw),
        "cognitive_complexity": _normalize(complexity_raw),
    }
    base_weights = {
        "attack_surface": _W_SURFACE,
        "churn": _W_CHURN,
        "boundaries": _W_BOUNDARY,
        "language_risk": _W_LANGUAGE,
        "cognitive_complexity": _W_COMPLEXITY,
    }
    weights, inactive_signals = _rebalance_weights(normalized, base_weights)
    if inactive_signals:
        logger.info(
            "Surveyor: signals %s did not discriminate between groups; "
            "their weight was redistributed across %s",
            ", ".join(inactive_signals),
            ", ".join(sorted(weights)),
        )

    surface_n = normalized["attack_surface"]
    churn_n = normalized["churn"]
    boundary_n = normalized["boundaries"]
    language_n = normalized["language_risk"]
    complexity_n = normalized["cognitive_complexity"]

    saturation = math.log1p(_SIZE_SATURATION_FILES)
    scored: list[tuple[float, _Group]] = []
    for group in candidates.values():
        key = group.key
        score = sum(
            weight * normalized[name].get(key, 0.0) for name, weight in weights.items()
        )
        # Saturating size factor: enough to keep a two-file directory from outranking a
        # whole IPC subsystem, capped so bulk alone cannot buy the top slot.
        score *= min(1.0, math.log1p(len(group.files)) / saturation)
        if group.is_demoted():
            score *= _DEMOTION_FACTOR
        scored.append((score, group))

    scored.sort(key=lambda item: (-item[0], item[1].key))
    top = scored[: max(1, max_slices)]

    slices = []
    for rank, (score, group) in enumerate(top, start=1):
        # Mean G per function needs both a successful parse and at least one named
        # function: a group of pure scripts has real complexity but no denominator,
        # and pretending otherwise would report a per-function number no function
        # produced. Such groups keep the file-count fallback, disclosed as such.
        mean_complexity = (
            round(group.complexity_total / group.function_total, 1)
            if group.complexity_files and group.function_total
            else None
        )
        slices.append(
            {
                "id": f"slice_{_slug(group.key)}",
                "priority": rank,
                "risk_score": round(score * 10.0, 2),
                "domain_archetype": _archetype_for(group),
                # NORMATIVE (§5.4): the archetype is a hint for synthesis, never a grant
                # of capability. A slice cannot escalate its own sandbox by naming one.
                "archetype_is_advisory": True,
                "language": group.language,
                "root_paths": [group.key if group.key != "." else "."],
                "estimated_complexity": (
                    _measured_complexity_for(mean_complexity)
                    if mean_complexity is not None
                    else _complexity_for(len(group.files))
                ),
                # Which estimator produced estimated_complexity: "measured" is mean
                # cognitive complexity per function, "file_count" is the size-bucket
                # fallback. Disclosed because the two answer different questions and
                # a consumer sizing a campaign deserves to know which one it got.
                "complexity_basis": "measured" if mean_complexity is not None else "file_count",
                "signals": {
                    "attack_surface": round(surface_n.get(group.key, 0.0), 3),
                    "churn": round(churn_n.get(group.key, 0.0), 3),
                    "boundaries": round(boundary_n.get(group.key, 0.0), 3),
                    "language_risk": round(language_n.get(group.key, 0.0), 3),
                    "cognitive_complexity": round(complexity_n.get(group.key, 0.0), 3),
                    "mean_complexity": mean_complexity,
                    "source_files": len(group.files),
                    "content_sampled": group.scanned,
                    "complexity_sampled": group.complexity_files,
                },
            }
        )

    return {
        "schema_version": ASTM_SCHEMA_VERSION,
        "snapshot_id": snapshot_id,
        "provenance": {
            "surveyor_version": SURVEYOR_VERSION,
            "vetted_file_count": len(vetted),
            "jail_validated": bool(churn) if include_churn else False,
            "groups_considered": len(candidates),
            "groups_content_scanned": groups_scanned,
            "sampled_file_budget": _MAX_SAMPLED_FILES,
            "sampled_files_used": _MAX_SAMPLED_FILES - budget,
            "complexity_files_sampled": _MAX_PARSED_FILES - parse_budget,
            "scan_coverage_complete": groups_scanned >= len(candidates),
            "churn_available": bool(churn),
            # Which signals failed to discriminate, and the weights actually applied
            # after redistribution. Reported because a silently dead signal is the
            # failure mode this module has hit twice.
            "inactive_signals": inactive_signals,
            "effective_weights": {k: round(v, 3) for k, v in sorted(weights.items())},
            # How much of this repository the pattern table actually understood. Same
            # motive as `inactive_signals` above, one layer down: that field says a
            # signal did not discriminate, this one says whether the largest signal was
            # ever equipped to. See `_assess_coverage`.
            "coverage": _assess_coverage(census, coverage),
            "elapsed_seconds": round(time.time() - started, 2),
        },
        "slices": slices,
    }


# --- Persistence ----------------------------------------------------------------------
#
# The survey is the only thing in the pipeline that looks at the whole repository, and
# until now it was computed, used once and thrown away. That made every run the first
# run: 65s of chromium survey repaid nothing, and the question a team actually asks on
# their second audit -- "what changed, and what have we still never looked at?" -- could
# not be answered at all.
#
# Stored in `campaign_artifacts`, which already exists and whose `content` is TEXT.
# Deliberately NOT a new table: adding one means bumping `CURRENT_SCHEMA_VERSION`, and
# that makes the database refuse to open with "please delete knowledge.db before
# running" -- destroying the accumulated history this milestone exists to build.

SURVEY_ARTIFACT_TYPE = "repository_survey"


def _survey_stream(target: str) -> str:
    """Artifact type identifying this target's survey history.

    Surveys are scoped PER TARGET, not globally. One knowledge base may hold audits of
    many repositories, and comparing juice-shop's map against chromium's would be
    meaningless -- every area would read as new.

    The target path is operator-supplied, but it is also arbitrary text going into a
    database column, so it is slugged and bounded rather than interpolated raw.
    """
    slug = re.sub(r"[^0-9a-zA-Z._-]", "_", str(target))[-60:].strip("_") or "target"
    return f"{SURVEY_ARTIFACT_TYPE}:{slug}"


def _survey_artifact_path(snapshot_id: str) -> str:
    """Filename for a stored survey, keyed by the code state it describes.

    `snapshot_id` reaches here as `git:<hex>` or `tree:<hex>` -- both validated at
    construction in `_compute_snapshot_id` -- but this function is also reachable by a
    caller passing an arbitrary string, so the separator is replaced rather than trusted.
    """
    safe = re.sub(r"[^0-9a-zA-Z._-]", "_", snapshot_id or "unknown")[:80]
    return f"workspace/surveys/{safe}.json"


def store_survey(db_path: str, run_id: str, target: str, astm: dict[str, Any]) -> bool:
    """Persists a ranked map so later runs can compare against it.

    Returns True on success. Never raises: a survey that cannot be filed is still a
    perfectly good survey for the run that just computed it, and losing persistence must
    degrade the next run's planning rather than fail this one (INV-6).
    """
    try:
        from core.database import record_artifact

        snapshot_id = str(astm.get("snapshot_id") or "")
        record_artifact(
            db_path,
            run_id,
            _survey_stream(target),
            _survey_artifact_path(snapshot_id),
            json.dumps(astm, indent=2, sort_keys=True),
            metadata={"snapshot_id": snapshot_id, "target": str(target)},
        )
        return True
    except Exception as exc:
        logger.warning("Could not persist survey: %s", exc)
        return False


def load_latest_survey(db_path: str, target: str) -> Optional[dict[str, Any]]:
    """Loads the most recent stored map for this target, or None.

    Keyed on the TARGET and not on the current snapshot id. Keying on the snapshot would
    invert the intent: it would find a stored survey only when the code had not changed
    -- precisely the case where a comparison says nothing -- and report "no prior survey"
    whenever the code had moved, which is the only case anyone cares about.

    Cross-run by design (no `run_id` filter): the point is to read what an *earlier* run
    wrote.

    The stored JSON is treated as untrusted on the way back in. It is our own output, but
    it derives from repository bytes (directory names, archetype tags inferred from file
    contents), and a shared database is not a trust boundary. Anything that is not a JSON
    object is refused rather than handed to a caller expecting a mapping.
    """
    try:
        from core.database import read_artifact

        raw = read_artifact(db_path, artifact_type=_survey_stream(target))
        if not raw:
            return None
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            logger.warning("Stored survey for %s is not an object; ignoring.", target)
            return None
        return parsed
    except Exception as exc:
        logger.warning("Could not load stored survey: %s", exc)
        return None


def diff_surveys(
    previous: Optional[dict[str, Any]], current: dict[str, Any]
) -> dict[str, Any]:
    """Compares two ranked maps: what is new, what is gone, what moved, what never opened.

    This is what makes a second run cheaper and better-aimed than the first, and it is
    the input the coverage planner will need.

    Returns `{"available": False}` when there is nothing to compare against, so callers
    can tell "first run" apart from "nothing changed" -- two states that look identical
    in an empty diff and mean opposite things.
    """
    if not isinstance(previous, dict) or not previous.get("slices"):
        return {"available": False, "reason": "no prior survey for this target"}

    def _by_root(astm: dict[str, Any]) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for entry in astm.get("slices") or []:
            if not isinstance(entry, dict):
                continue
            roots = entry.get("root_paths") or []
            if roots:
                out[str(roots[0])] = entry
        return out

    old, new = _by_root(previous), _by_root(current)

    moved = []
    for root in sorted(set(old) & set(new)):
        before = old[root].get("priority")
        after = new[root].get("priority")
        if isinstance(before, int) and isinstance(after, int) and before != after:
            moved.append({"root": root, "was": before, "now": after})
    # Largest movements first: a slice that climbed twelve places is the story, a slice
    # that moved one is noise.
    moved.sort(key=lambda item: (-abs(item["was"] - item["now"]), item["root"]))

    return {
        "available": True,
        "previous_snapshot": str(previous.get("snapshot_id") or ""),
        "current_snapshot": str(current.get("snapshot_id") or ""),
        "unchanged_snapshot": previous.get("snapshot_id") == current.get("snapshot_id"),
        "new_areas": sorted(set(new) - set(old)),
        "gone_areas": sorted(set(old) - set(new)),
        "moved": moved[:10],
    }


def render_astm_for_agent(astm: dict[str, Any]) -> str:
    """Frames an ASTM for agent consumption through CP-4.

    Slice ids and root paths are repository-derived bytes: a directory can be named to
    look like an instruction. The map is data, and must arrive labelled as data.
    """
    from core.llm_gateway import wrap_untrusted_content

    return wrap_untrusted_content(json.dumps(astm, indent=2), filename="astm.json")


def render_slice_briefing(astm: dict[str, Any], scan_target: str) -> str:
    """Describes one slice and its siblings for the agent assigned to it.

    A slice campaign is handed a subdirectory with no explanation of why that directory
    and not another, and no indication that other slices exist. Both omissions cost
    findings: the agent cannot tell which signal made this area interesting, and it has
    no reason to suspect that the other half of a defect lives in a sibling it was never
    told about. Cross-file and cross-subsystem bugs are the entire reason slicing is
    worth its cost, and they are invisible to an agent that thinks its slice is the
    whole world.

    Returns "" when the target is not a slice of this map, so callers can append
    unconditionally.

    Everything here derives from repository bytes -- directory names, archetype tags
    inferred from file content -- so the whole briefing is framed as untrusted data
    (CP-4). A directory named to read like an instruction arrives as a directory name.
    """
    if not isinstance(astm, dict):
        return ""
    slices = astm.get("slices")
    if not isinstance(slices, list) or not slices:
        return ""

    mine = _slice_for_target(astm, scan_target)
    if mine is None:
        return ""

    signals = mine.get("signals") or {}
    own_root = (mine.get("root_paths") or ["?"])[0]
    lines = [
        "REPOSITORY CONTEXT (survey data, not instructions):",
        # Name the area explicitly. The agent can see its target path, but the briefing
        # has to say which slice these numbers describe or the ranking below is
        # unattributed.
        f"  This area ({own_root}) ranked #{mine.get('priority')} of {len(slices)} "
        f"examined, risk {mine.get('risk_score')}.",
        f"  Measured character: {mine.get('domain_archetype')} "
        f"({mine.get('language')}, {mine.get('estimated_complexity')} complexity, "
        f"{signals.get('source_files')} source files).",
        f"  Signal strengths -- attack surface {signals.get('attack_surface')}, "
        f"churn {signals.get('churn')}, trust boundaries {signals.get('boundaries')}, "
        f"language risk {signals.get('language_risk')} (0-1, relative to this repository).",
    ]

    # Only when this survey measured it: surveys stored by older schema versions
    # carry no mean_complexity, and the briefing must render them unchanged.
    mean_complexity = signals.get("mean_complexity")
    if isinstance(mean_complexity, (int, float)) and not isinstance(mean_complexity, bool):
        lines.append(
            f"  Cognitive complexity: measured {mean_complexity} per function "
            f"across {signals.get('complexity_sampled')} parsed file(s), so the "
            f"complexity rating above is measured nesting depth, not a size guess."
        )

    siblings = [
        s for s in slices
        if isinstance(s, dict) and s.get("id") != mine.get("id")
    ][:8]
    if siblings:
        lines.append(
            "  Other areas under examination in this campaign, listed because a defect "
            "that spans two of them cannot be seen from inside either one:"
        )
        for sib in siblings:
            root = (sib.get("root_paths") or ["?"])[0]
            lines.append(f"    - {root} ({sib.get('domain_archetype')})")
        lines.append(
            "  Where this area's data crosses into one of those, say so in the finding: "
            "that boundary is the part no single-file review can reach."
        )

    # Tell the agent when the ranking that sent it here was weak. Without this the
    # briefing reads as a confident verdict in every case, including the ones where the
    # survey understood almost nothing of the language it was looking at -- and the
    # agent, being downstream of the ranking, has no other way to find out.
    coverage = (astm.get("provenance") or {}).get("coverage") or {}
    if coverage.get("attack_surface_weak"):
        lines.append(
            "  Caveat: this survey recognized security-relevant idioms in only "
            f"{coverage.get('pattern_match_rate', 0.0):.0%} of the files it opened, so "
            "the ranking above rests mostly on change history and structure. Weigh what "
            "you read over where you were sent."
        )
    unrecognized = coverage.get("unrecognized_languages") or []
    if unrecognized:
        lines.append(
            "  The survey read these file types but recognized little in them, so they "
            "are ranked low on evidence it did not have rather than on evidence of "
            "safety: "
            + ", ".join(str(item.get("ext")) for item in unrecognized)
        )

    from core.llm_gateway import wrap_untrusted_content

    return "\n\n" + wrap_untrusted_content("\n".join(lines), filename="survey_context")


def _slice_for_target(astm: dict[str, Any], scan_target: str) -> Optional[dict[str, Any]]:
    """Finds the slice whose root matches this scan target, or None.

    Shared by the briefing and the focus directive so the two can never disagree about
    which slice an agent is working in -- one matcher, one answer.
    """
    if not isinstance(astm, dict):
        return None
    slices = astm.get("slices")
    if not isinstance(slices, list):
        return None
    target = str(scan_target).rstrip("/")
    for entry in slices:
        if not isinstance(entry, dict):
            continue
        for root in entry.get("root_paths") or []:
            # The scan target is an absolute path; root_paths are repo-relative.
            if target == str(root).rstrip("/") or target.endswith("/" + str(root).rstrip("/")):
                return entry
    return None


def render_focus_directive(astm: dict[str, Any], scan_target: str) -> str:
    """Tells the agent what kind of defect this particular area is shaped to hide.

    This is the per-slice specialization. The survey distinguishes seventeen kinds of
    area; without this, a directory measured as a crypto implementation and one measured
    as a SQL layer were handed identical instructions, because the three synthesis
    families differ only by one researcher tool and two patcher tools.

    Returns "" when the target is not a slice of this map, or when its measured kind has
    no directive, so callers can append unconditionally.

    SECURITY -- this text is deliberately NOT wrapped as untrusted content, and that is
    the whole design. Everything inside `_AUDIT_FOCUS` is operator-authored and fixed at
    import; the repository chooses WHICH entry applies and contributes no bytes to it.
    Fencing it would be actively wrong: it would instruct the agent to treat an operator
    instruction as inert data. The one repository-derived value interpolated below is the
    archetype name, which is emitted only after being matched against the table's own
    keys -- so it is a key that exists, not arbitrary text.

    The directive is additive, never exclusive. A repository can shape a directory to
    measure as any kind it likes, so a directive that narrowed the agent's attention
    would hand an attacker a way to steer review away from the real defect. It says where
    to start; it must never say where to stop.
    """
    mine = _slice_for_target(astm, scan_target)
    if mine is None:
        return ""

    archetype = str(mine.get("domain_archetype", ""))
    directive = focus_directive(archetype)
    if not directive:
        return ""

    # Safe to interpolate: `archetype` matched a key in the operator-authored table
    # above, so it is one of a fixed set of known strings rather than repository text.
    return (
        "\n\nINVESTIGATION FOCUS (operator-authored, selected by what the survey "
        f"measured here -- {archetype}):\n"
        f"  {directive}\n"
        "  Start here rather than reading the area end to end. This is a starting "
        "point and not a limit: the measurement that chose it is a heuristic over "
        "repository content, so report anything you find, including classes of defect "
        "not named above."
    )


