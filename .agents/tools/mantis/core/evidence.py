"""Where evidence comes from, and how much of it may be believed.

WHY THIS EXISTS
---------------
Everything Mantis knows today comes from one directory that is also one git checkout.
That assumption is wired in deeper than it looks: the survey runs one `git log`, CP-1
staging enforces one root by `commonpath` containment, CP-3 validates one scan root, and
even the ranking's group keys are two path components -- which mean nothing once there
are forty repositories.

The bugs worth the most are the ones that cross those boundaries. A 200-file service
that is the authentication boundary for thirty-nine others outranks a million-line
monolith, and no amount of looking inside any single repository can see that, because
the signal lives in the call graph BETWEEN them. Forty repositories is not forty surveys
stapled together.

A monorepo slice, a second git repository, and an internal wiki all answer the same
question -- what do we know about this code, and how far can that be trusted -- so they
get one seam rather than one bespoke integration each. The trust tier is attached at the
SOURCE, because a property bolted on per-consumer is a property the next consumer will
forget.

WHAT IS AND IS NOT HERE
-----------------------
This module defines the interface and the trust rules. It ships exactly ONE
implementation: `LocalCheckout`, describing the single local directory Mantis already
scans. Existing behaviour becomes "the one source" and nothing changes for an existing
run (INV-6).

There is deliberately NO network-capable source, and none is stubbed beyond the contract
a future one would have to satisfy. Every tool in the registry today is filesystem, git,
sqlite or sandbox; none can reach the network. That is not incidental -- it is the reason
exfiltration has never been a live concern in this system. The first source that reads
Confluence or Jira changes the threat model of the whole program, so the rules are
written down here BEFORE anyone implements one, rather than discovered afterwards.

THE TRUST MODEL
---------------
Not "trusted vs untrusted". Everything here is the output of an LLM, a human under
deadline, or an attacker, and those are frequently indistinguishable: hallucination and
injection arrive through the same door and are answered the same way. The real boundary
is STRUCTURED-AND-VALIDATED versus FREE PROSE, applied uniformly to every source.

So a tier does not say "this is true". It says what a claim from this source is ALLOWED
TO DO:

  TIER_CODE     -- bytes on disk under the scan root. The only thing that can support a
                   claim about what the code actually does. Still untrusted as CONTENT:
                   it is fenced before it reaches a model.

  TIER_HISTORY  -- version-control metadata. Says what changed and when, never whether
                   the change was correct.

  TIER_INTENT   -- human prose: wikis, tickets, design docs. Directs attention and
                   describes what the system is FOR. Its highest use is as a spec to
                   measure the implementation against, because a large class of real
                   defects is exactly the gap between stated intent and actual
                   behaviour. It is also the only way to learn the real threat model,
                   which means it can legitimately establish that something is
                   IRRELEVANT given how the software is actually deployed. It can never
                   establish that something is SAFE.

THE HARD LINE
-------------
No source below TIER_CODE may set a verdict field -- `status`, `repro_status`,
`reattack_status`, `patch_status`. Those are governed by INV-1 and INV-2 and require
reached-sink evidence. A wiki page is not evidence of reachability-in-fact.

The blast radius of a fully hostile non-code source is therefore bounded to misdirected
attention plus an attributed, visible re-prioritisation. Never suppression, never a
verdict. Someone who owns the wiki can waste budget; they cannot clear a finding.
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
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Protocol, Tuple, runtime_checkable

logger = logging.getLogger(__name__)


# --- Trust tiers ------------------------------------------------------------------
TIER_CODE = "code"
TIER_HISTORY = "history"
TIER_INTENT = "intent"

# Ordered weakest to strongest, for callers that need to compare authority.
TIER_ORDER = (TIER_INTENT, TIER_HISTORY, TIER_CODE)
TIER_RANK = {name: i for i, name in enumerate(TIER_ORDER)}

# Fields asserting that something was actually observed to happen. INV-1/INV-2 put these
# behind reached-sink evidence, so nothing short of code may touch them.
VERDICT_FIELDS = frozenset({
    "status",
    "repro_status",
    "reattack_status",
    "patch_status",
    "reached_sink",
})


def may_set_verdict(trust_tier: Any) -> bool:
    """Whether a source at this tier may write a verdict field.

    Only TIER_CODE, and only ever TIER_CODE. Written as one function rather than a
    comparison repeated at each call site so there is exactly one place to audit, and
    so an unrecognised tier fails closed instead of defaulting open.
    """
    return str(trust_tier or "") == TIER_CODE


def filter_claim(claim: Any, trust_tier: Any) -> Dict[str, Any]:
    """Strips fields a source at `trust_tier` has no standing to assert.

    Applied at the boundary rather than trusting every consumer to remember the rule.
    A wiki page that says `status: false_positive` is making a claim it cannot support;
    the field is dropped and logged, the rest of the claim survives. Dropping the whole
    claim would let a hostile source suppress its own inconvenient content by attaching
    a forbidden field to it.

    Never raises (INV-6).
    """
    try:
        if not isinstance(claim, dict):
            return {}
        if may_set_verdict(trust_tier):
            return dict(claim)
        out: Dict[str, Any] = {}
        for key, value in claim.items():
            if key in VERDICT_FIELDS:
                logger.warning(
                    "Dropping verdict field %r asserted by a %r-tier source: verdicts "
                    "require reached-sink evidence (INV-1/INV-2).", key, trust_tier,
                )
                continue
            out[key] = value
        return out
    except Exception as exc:
        logger.warning("Claim filtering failed, dropping claim: %s", exc)
        return {}


# --- Egress ------------------------------------------------------------------------
#
# NOTHING IN THIS PROGRAM TALKS TO THE NETWORK, AND THIS MODULE DOES NOT CHANGE THAT.
#
# The contract is recorded now, unimplemented, because these constraints are far easier
# to state correctly before a networked source exists than to retrofit around one that
# already works and has users.
#
# A future networked source MUST satisfy all of:
#
#   1. EGRESS BELONGS TO THE SOURCE, NEVER TO AN AGENT TOOL. No agent may hold a tool
#      that fetches a URL. A source fetches on its own schedule, before analysis, and
#      hands back inert text. An agent that can fetch is an agent that can be instructed
#      to fetch by the very content it is reading -- that is the whole exfiltration
#      channel in a single step.
#
#   2. RETRIEVAL IS NEVER SHAPED BY FINDINGS. The moment a query string can contain a
#      fragment of what was found, the URL is the exfiltration channel, whatever the
#      transport underneath.
#
#   3. NO OUTBOUND BODY. Fetch only. A source that can POST can publish.
#
#   4. ALLOW-LISTED HOSTS, RESOLVED AND PINNED BEFORE THE REQUEST. Otherwise a link
#      inside fetched content redirects the next fetch anywhere.
#
#   5. FETCHED CONTENT IS TIER_INTENT, ALWAYS. It is the most attacker-friendly input in
#      the system: anyone can edit a wiki page, whereas source needs review.
#
# The absence of a network implementation is a security property, not an unfinished
# feature.
class NetworkSourceNotImplemented(NotImplementedError):
    """Raised if anything attempts to construct a networked evidence source.

    Deliberately fail-closed and loud. A quiet fallback to "no documents" would let a
    misconfigured deployment believe it had wiki coverage that it did not have, which is
    worse than having no wiki support at all: it is a blind spot that reports as sight.
    """


@runtime_checkable
class EvidenceSource(Protocol):
    """One place evidence comes from.

    `source_id` rides on every derived fact, so attribution is enforceable rather than
    aspirational: when a finding is challenged six months later, "which source said
    that" must have an answer.
    """

    source_id: str
    trust_tier: str

    def enumerate_files(self) -> Iterable[Tuple[Path, str]]:
        """Files this source can offer, as (path, language). CP-1 still vets them."""
        ...

    def history(self) -> Optional[Dict[str, Any]]:
        """Change signal, or None when this source has no history to give.

        None is a first-class answer, not an error: the survey already treats missing
        churn as a documented degraded mode, so a wiki is not a special case.
        """
        ...

    def documents(self) -> Iterable[Dict[str, Any]]:
        """Prose. Always CP-4 fenced before it reaches a model."""
        ...


class LocalCheckout:
    """The single local directory Mantis already scans. The only implementation.

    Exists so the seam has a real occupant rather than a hypothetical one, and so that
    "one repository" is expressible in the same vocabulary as "forty repositories" when
    that day comes. Behaviour is unchanged for every existing run (INV-6).
    """

    trust_tier = TIER_CODE

    def __init__(self, root: Any, source_id: str = "local"):
        self.root = Path(str(root))
        self.source_id = str(source_id or "local")

    def enumerate_files(self) -> Iterable[Tuple[Path, str]]:
        """Deliberately empty.

        Enumeration stays with CP-1 `get_vetted_staging_files`, the audited chokepoint
        for what may be staged. Reimplementing a walk here would create a second path to
        the same decision, and the second path is the one that does not receive the next
        security fix.
        """
        return []

    def history(self) -> Optional[Dict[str, Any]]:
        """Also deferred: CP-2 owns every git invocation and its jail validation."""
        return None

    def documents(self) -> Iterable[Dict[str, Any]]:
        """A local checkout contributes code, not prose."""
        return []


# --- Source registry ---------------------------------------------------------------
#
# The extension seam. A deployment that has forty repositories, a monorepo slice, or an
# internal wiki cannot send us its code, its schema, or usually even the fact that it is
# running Mantis -- so the integration has to be writable by someone we will never talk
# to, against a contract that is stable enough to write against.
#
# WHY A CONFIG-DECLARED MODULE PATH, AND NOT AUTO-DISCOVERY
#
# Entry points and plugin-directory scanning both mean "code Mantis did not name starts
# running because it was installed". For a program whose entire job is to be pointed at
# somebody's source and report on it honestly, that is the wrong default: the set of
# things that can inject evidence must be readable from the configuration file, by a
# reviewer, without an inventory of the site-packages directory. So a source runs only
# if the workflow names it.
#
# WHAT A HOOK MAY AND MAY NOT DECIDE
#
# A hook supplies CONTENT. It does not get to decide how far its content is believed:
#
#   * `trust_tier` is assigned here, from configuration, and a hook that sets its own
#     attribute cannot raise itself. Otherwise the first wiki integration to declare
#     `trust_tier = "code"` would be able to close findings -- the exact privilege
#     escalation the tier system exists to prevent.
#
#   * TIER_CODE is not available to a configured hook at all. Code authority means "I am
#     bytes on disk under the scan root that CP-1 vetted and CP-3 contained"; a hook is
#     by construction not that. Requesting it is a configuration error, and it is
#     refused loudly rather than quietly downgraded, because a deployment that believes
#     it has code-tier evidence and does not is worse off than one that was told no.
#
#   * Verdicts stay behind `may_set_verdict`, which is unchanged: there is still exactly
#     one place in the program where that question is answered.
_SOURCE_BUILDERS: Dict[str, Any] = {
    "local-checkout": LocalCheckout,
}

# Tiers a configured hook may be given. TIER_CODE is deliberately absent; see above.
CONFIGURABLE_TIERS = (TIER_HISTORY, TIER_INTENT)


class EvidenceSourceConfigError(ValueError):
    """A source was declared that cannot be built as specified.

    Raised rather than skipped. A source that silently fails to load leaves the run
    reporting on less evidence than the operator configured, while looking exactly like
    a run that had it all -- a blind spot that reports as sight, which is the same
    failure mode `NetworkSourceNotImplemented` exists to prevent.
    """


def _load_dotted(path: str) -> Any:
    """Imports `pkg.module:Attr` (or `pkg.module.Attr`) and returns the attribute."""
    import importlib

    text = str(path or "").strip()
    if not text:
        raise EvidenceSourceConfigError("Empty evidence source path.")
    if ":" in text:
        module_name, _, attr = text.partition(":")
    elif "." in text:
        module_name, _, attr = text.rpartition(".")
    else:
        raise EvidenceSourceConfigError(
            f"Evidence source {text!r} is not a module path. Expected "
            f"'package.module:ClassName'."
        )
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        raise EvidenceSourceConfigError(
            f"Cannot import evidence source module {module_name!r}: {exc}"
        ) from exc
    try:
        return getattr(module, attr)
    except AttributeError as exc:
        raise EvidenceSourceConfigError(
            f"Module {module_name!r} has no attribute {attr!r}."
        ) from exc


def build_evidence_source(cfg: Any, target_path: str = "") -> Any:
    """Builds one evidence source from its configuration entry.

    `cfg` is `{"type": ..., "source_id": ..., "trust_tier": ..., "options": {...}}`.
    `type` is either a registered name or a `package.module:ClassName` path.

    Raises `EvidenceSourceConfigError` for anything malformed, and
    `NetworkSourceNotImplemented` for a source that declares network access -- the
    egress rules above are not yet satisfiable by anything in this program, so a source
    that needs the network must fail at construction rather than at the first fetch,
    when it would already be holding findings.
    """
    if not isinstance(cfg, dict):
        raise EvidenceSourceConfigError(
            f"Evidence source entry must be an object, got {type(cfg).__name__}."
        )

    kind = str(cfg.get("type", "") or "").strip()
    if not kind:
        raise EvidenceSourceConfigError("Evidence source entry has no 'type'.")

    # Checked before the class is loaded, not after. Importing a networked source's
    # module already runs its module-level code, and refusing afterwards would mean the
    # refusal happened only after arbitrary import-time side effects.
    if cfg.get("network") or cfg.get("url") or cfg.get("base_url"):
        raise NetworkSourceNotImplemented(
            f"Evidence source {kind!r} declares network access. No networked source "
            f"exists: see the egress contract in core/evidence.py. The absence is a "
            f"security property, not an unfinished feature."
        )

    if kind in _SOURCE_BUILDERS:
        builder = _SOURCE_BUILDERS[kind]
        requested_tier = str(cfg.get("trust_tier", "") or "")
        # A registered built-in carries its own tier, because it is part of the audited
        # program rather than a third-party hook. LocalCheckout is TIER_CODE for the
        # same reason CP-1 and CP-3 are trusted: it IS the vetted local checkout.
        if requested_tier and requested_tier != getattr(builder, "trust_tier", ""):
            raise EvidenceSourceConfigError(
                f"Built-in source {kind!r} has a fixed trust tier of "
                f"{getattr(builder, 'trust_tier', 'unknown')!r}; configuration asked "
                f"for {requested_tier!r}."
            )
        kwargs = dict(cfg.get("options") or {})
        source_id = cfg.get("source_id")
        if source_id:
            kwargs["source_id"] = str(source_id)
        return builder(target_path, **kwargs)

    tier = str(cfg.get("trust_tier", "") or "").strip()
    if tier not in CONFIGURABLE_TIERS:
        raise EvidenceSourceConfigError(
            f"Evidence source {kind!r} must declare trust_tier as one of "
            f"{list(CONFIGURABLE_TIERS)}; got {tier!r}. "
            f"{TIER_CODE!r} is not configurable: only the vetted local checkout speaks "
            f"for what the code does."
        )

    cls = _load_dotted(kind)
    kwargs = dict(cfg.get("options") or {})
    try:
        instance = cls(**kwargs)
    except Exception as exc:
        raise EvidenceSourceConfigError(
            f"Evidence source {kind!r} could not be constructed: {exc}"
        ) from exc

    # Tier and identity are stamped AFTER construction, overwriting whatever the hook
    # set. This is the structural half of the trust model: a hook cannot promote itself
    # by assigning an attribute, because the last write is ours.
    try:
        instance.trust_tier = tier
        instance.source_id = str(cfg.get("source_id") or kind)
    except Exception as exc:
        raise EvidenceSourceConfigError(
            f"Evidence source {kind!r} does not permit trust_tier assignment, so its "
            f"authority cannot be constrained: {exc}"
        ) from exc

    for required in ("enumerate_files", "history", "documents"):
        if not callable(getattr(instance, required, None)):
            raise EvidenceSourceConfigError(
                f"Evidence source {kind!r} does not implement {required}()."
            )
    return instance


def build_evidence_sources(config: Any, target_path: str = "") -> List[Any]:
    """Builds every configured source, always including the local checkout first.

    The local checkout is prepended unconditionally and cannot be configured away. It is
    the only TIER_CODE source, so a configuration that removed it would leave a run in
    which nothing present could support a finding, while still producing a report.

    Ordering is significant to the reader: code first, then whatever was added, so the
    disclosure reads as "here is the ground truth, and here is what else was consulted".
    """
    sources: List[Any] = [LocalCheckout(str(target_path))]
    entries = (config or {}).get("evidence_sources") or []
    if not isinstance(entries, list):
        raise EvidenceSourceConfigError(
            "'evidence_sources' must be a list of source objects."
        )
    for entry in entries:
        sources.append(build_evidence_source(entry, target_path=target_path))
    return sources


def describe_sources(sources: Optional[List[Any]]) -> List[str]:
    """Operator-facing lines naming what was consulted, and at what authority.

    Coverage disclosure already tells the operator what the survey could not see; a
    multi-source run has to extend that rather than quietly widen its inputs. An
    unrecognised tier is reported as such instead of being silently treated as weak,
    because a misconfigured source is exactly the case worth seeing.

    A configured source is reported as NOT YET READ, because it is not. The seam and
    its trust rules exist; no consumer calls `documents()`, `history()` or
    `enumerate_files()` yet. Saying "eng-wiki [intent]: may direct attention only"
    and stopping there would let an operator configure a wiki, watch it appear in the
    banner, and conclude their runbooks were consulted -- the blind spot that reports
    as sight, which is the same failure `NetworkSourceNotImplemented` exists to
    prevent. This line is how the gap stays visible until a consumer lands.

    Never raises (INV-6).
    """
    out: List[str] = []
    try:
        for source in sources or []:
            sid = str(getattr(source, "source_id", "") or "unknown")
            tier = str(getattr(source, "trust_tier", "") or "unknown")
            if tier not in TIER_RANK:
                out.append(f"{sid} [{tier}]: unrecognised tier, treated as intent only")
                continue
            if isinstance(source, LocalCheckout):
                # The local checkout IS the scan: its content reaches the agents
                # through CP-1 staging and the research tools, not through this seam.
                out.append(f"{sid} [{tier}]: may support findings")
                continue
            authority = (
                "may support findings" if may_set_verdict(tier)
                else "may direct attention only"
            )
            out.append(
                f"{sid} [{tier}]: {authority} — declared, NOT YET READ "
                f"(no consumer reads source content yet)"
            )
    except Exception as exc:
        logger.warning("Source description failed: %s", exc)
    return out
