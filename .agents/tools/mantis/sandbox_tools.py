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
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.context import current_run_context
from core.llm_gateway import SecretScrubber, wrap_untrusted_content
from google.adk.environment import ExecutionResult

MANTIS_SENTINEL_TOKEN = "MANTIS_REACHED_ENTRYPOINT"

_SANITIZER_SIGNALS = [
    re.compile(r"==\d+==ERROR:\s+(?:AddressSanitizer|UndefinedBehaviorSanitizer|MemorySanitizer|ThreadSanitizer|LeakSanitizer)", re.IGNORECASE),
    re.compile(r"SUMMARY:\s+(?:AddressSanitizer|UndefinedBehaviorSanitizer|MemorySanitizer|ThreadSanitizer):", re.IGNORECASE),
    re.compile(r"runtime error:\s+", re.IGNORECASE),
    re.compile(r"(?:Segmentation fault|SIGSEGV|SIGABRT|core dumped)", re.IGNORECASE),
    re.compile(r"#\d+\s+0x[0-9a-fA-F]+\s+in\s+([a-zA-Z0-9_:]+)", re.IGNORECASE),
]


def check_reached_sink_evidence(
    output: str,
    exit_code: int,
    sink_symbol: str = "",
    sentinel_content: str = "",
) -> Tuple[bool, str]:
    """Deterministically checks whether reached-sink evidence is present per INV-1 and INV-2 invariants.

    Returns:
        Tuple of (evidence_present: bool, reason: str)
    """
    # Fail-closed checks: command not found or missing file is EVIDENCE ABSENT
    if exit_code == 127:
        return False, "EVIDENCE_ABSENT: exit code 127 (command not found)"
    if "No such file or directory" in output and exit_code in (1, 2, 127):
        return False, "EVIDENCE_ABSENT: target or harness file not found"
    if "SANDBOX-UNAVAILABLE" in output:
        return False, "EVIDENCE_ABSENT: sandbox environment unavailable"

    # Channel A: Sidecar Sentinel File / explicit in-path flush token
    if sentinel_content and MANTIS_SENTINEL_TOKEN in sentinel_content:
        return True, "EVIDENCE_PRESENT: in-path sentinel marker MANTIS_REACHED_ENTRYPOINT verified"
    if MANTIS_SENTINEL_TOKEN in output:
        return True, "EVIDENCE_PRESENT: in-path sentinel marker emitted in execution trace"

    # Channel B: Target-produced Sanitizer / Crash backtrace naming sink
    has_sanitizer_or_crash = any(pat.search(output) for pat in _SANITIZER_SIGNALS)
    if has_sanitizer_or_crash:
        if sink_symbol:
            if sink_symbol in output:
                return True, f"EVIDENCE_PRESENT: crash backtrace explicitly confirms sink '{sink_symbol}'"
            return False, f"EVIDENCE_ABSENT: crash occurred but did not reach target sink '{sink_symbol}'"
        return True, "EVIDENCE_PRESENT: sanitizer/crash frame detected in execution output"

    return False, "EVIDENCE_ABSENT: no sentinel token or target-produced crash backtrace observed"


def _is_non_repro_node(ctx) -> bool:
    if ctx is None:
        return False
    active = getattr(ctx, "active_node", "")
    return bool(active and active not in ("reproducer", "patcher"))


def _note_dynamic_evidence(
    ctx,
    output: str,
    exit_code: int,
    sink_symbol: str = "",
    sentinel_content: str = "",
) -> None:
    """Sets ctx.sandbox_executed IFF reached-sink evidence is actually present.

    WHY THIS IS A CHOKEPOINT AND NOT AN INLINE ASSIGNMENT
    -----------------------------------------------------
    `ctx.sandbox_executed` is consumed downstream (main.py's status gate) as "dynamic
    evidence exists for this campaign": it is the sole thing standing between a
    model-asserted `dynamic_confirmed` / `patch_verified` verdict and the knowledge
    base recording it as machine-verified. The flag used to be set by ANY command
    whose exit code was not 127 -- `echo hi` counted as dynamic execution -- which
    made the evidence tier a statement about shell availability, not about the
    exploit reaching its sink. INV-1 requires reached-sink proof: the sentinel token
    flushed from inside the target's execution path, or a target-produced sanitizer
    or crash backtrace. `check_reached_sink_evidence` is the deterministic authority
    for exactly that question, so the flag is now derived from it and from nothing
    else. Every site that used to write the flag routes through here, which keeps
    the tightening un-forkable: a future call site cannot quietly reintroduce the
    "a command ran at all" standard without bypassing this function by hand.

    FAIL DIRECTION
    --------------
    The flag only ever moves False -> True, and only on a positive verdict. It is
    never cleared here: one sentinel-verified execution earlier in the campaign is
    not un-proven by a later failed command, and clearing would let an attacker (or
    an unlucky flake) erase real evidence by running one broken command afterwards.
    Conversely, an exception inside the checker leaves the flag untouched -- when
    the evidence question cannot be answered, the answer is "no evidence" (INV-1
    fail-closed), which costs a re-run rather than laundering a guess into a
    machine-verified status.
    """
    if ctx is None:
        return
    try:
        evidence_present, _reason = check_reached_sink_evidence(
            output=output,
            exit_code=exit_code,
            sink_symbol=sink_symbol,
            sentinel_content=sentinel_content,
        )
        if evidence_present:
            ctx.sandbox_executed = True
    except Exception:
        # Deliberately swallowed: the checker is pure string/regex work and should
        # never raise, but if it does, "could not verify" must degrade to "flag
        # stays as it was", never to "flag set". See FAIL DIRECTION above.
        pass


async def run_sandbox(command: str) -> str:
    """Executes a command securely inside the configured sandbox. Use this to compile or run the reproduction script."""
    ctx = current_run_context.get()
    if ctx is None or ctx.sandbox is None:
        return "ERROR: No active sandbox environment (sandbox unavailable)."

    try:
        sandbox_type = type(ctx.sandbox).__name__
        is_static = sandbox_type in ("StaticOnlyEnvironment", "StaticOnlySandbox")

        if is_static:
            ctx.static_sandbox_attempts = getattr(ctx, "static_sandbox_attempts", 0) + 1
            if ctx.static_sandbox_attempts >= 3:
                if not _is_non_repro_node(ctx):
                    return (
                        f"ERROR: Sandbox execution permanently blocked in static-only mode (attempt {ctx.static_sandbox_attempts}). "
                        f"Dynamic execution is disabled. Do NOT call run_sandbox again. "
                        f"STOP calling tools immediately and submit your stage verdict using the 'set_model_response' tool "
                        f"(e.g. set_model_response(route='failed_repro', reason='Dynamic execution disabled in static-only mode')) "
                        f"or as structured JSON text (e.g. {{\"route\": \"failed_repro\", \"reason\": \"Dynamic execution disabled in static-only mode\"}}) "
                        f"in your model response to conclude this stage."
                    )
                return (
                    f"ERROR: Sandbox execution permanently blocked in static-only mode (attempt {ctx.static_sandbox_attempts}). "
                    f"Dynamic execution is disabled. Do NOT call run_sandbox again."
                )
            if not _is_non_repro_node(ctx):
                return (
                    "exit=127\n"
                    "SANDBOX-UNAVAILABLE: static-only sandbox; dynamic execution is disabled.\n"
                    "Do NOT retry running sandbox commands. In static-only mode, dynamic execution cannot be run. "
                    "Please update candidate findings in workspace/findings/ with repro_status='not_attempted', "
                    "STOP calling tools immediately, and submit your stage verdict using the 'set_model_response' tool "
                    "or as structured JSON text (e.g. {\"route\": \"failed_repro\", \"reason\": \"Dynamic execution disabled in static-only mode\"}) "
                    "in your model response."
                )
            return (
                "exit=127\n"
                "SANDBOX-UNAVAILABLE: static-only sandbox; dynamic execution is disabled.\n"
                "Do NOT retry running sandbox commands."
            )

        res = await ctx.sandbox.execute(command)
        if isinstance(res, ExecutionResult):
            raw_output = f"{res.stdout}{res.stderr}".strip()
            is_unavail = "SANDBOX-UNAVAILABLE" in raw_output or "SANDBOX-UNAVAILABLE" in res.stderr
            if is_unavail:
                ctx.static_sandbox_attempts = getattr(ctx, "static_sandbox_attempts", 0) + 1
                if ctx.static_sandbox_attempts >= 3:
                    if not _is_non_repro_node(ctx):
                        return (
                            f"ERROR: Sandbox execution permanently blocked (sandbox unavailable, attempt {ctx.static_sandbox_attempts}). "
                            f"Dynamic execution is disabled. Do NOT call run_sandbox again. "
                            f"STOP calling tools immediately and submit your stage verdict using the 'set_model_response' tool "
                            f"or as structured JSON text (e.g. {{\"route\": \"failed_repro\", \"reason\": \"Sandbox unavailable\"}}) "
                            f"in your model response to conclude this stage."
                        )
                    return (
                        f"ERROR: Sandbox execution permanently blocked (sandbox unavailable, attempt {ctx.static_sandbox_attempts}). "
                        f"Dynamic execution is disabled. Do NOT call run_sandbox again."
                    )
            else:
                # Evidence, not liveness: the flag is only set when THIS command's
                # own trace carries reached-sink proof (sentinel token or a
                # target-produced crash), via the chokepoint above. The old rule --
                # any exit code but 127 -- certified "a shell existed", and the
                # downstream status gate read that as "the exploit was dynamically
                # verified". Callers going through run_sandbox_with_evidence also
                # get the sidecar sentinel file considered; a bare run_sandbox call
                # only has its output to speak for it, which is exactly as much as
                # it proved.
                _note_dynamic_evidence(ctx, raw_output, res.exit_code)

            if not raw_output:
                return f"exit={res.exit_code}"
            scrubbed_output = SecretScrubber.scrub(raw_output)
            wrapped_output = wrap_untrusted_content(scrubbed_output, filename="sandbox_output")
            return f"exit={res.exit_code}\n{wrapped_output}"
        if isinstance(res, str):
            is_unavail = "SANDBOX-UNAVAILABLE" in res
            if is_unavail:
                ctx.static_sandbox_attempts = getattr(ctx, "static_sandbox_attempts", 0) + 1
                if ctx.static_sandbox_attempts >= 3:
                    if not _is_non_repro_node(ctx):
                        return (
                            f"ERROR: Sandbox execution permanently blocked (sandbox unavailable, attempt {ctx.static_sandbox_attempts}). "
                            f"Dynamic execution is disabled. Do NOT call run_sandbox again. "
                            f"STOP calling tools immediately and submit your stage verdict using the 'set_model_response' tool "
                            f"or as structured JSON text (e.g. {{\"route\": \"failed_repro\", \"reason\": \"Sandbox unavailable\"}}) "
                            f"in your model response to conclude this stage."
                        )
                    return (
                        f"ERROR: Sandbox execution permanently blocked (sandbox unavailable, attempt {ctx.static_sandbox_attempts}). "
                        f"Dynamic execution is disabled. Do NOT call run_sandbox again."
                    )
            elif res.startswith("exit="):
                # Same evidence standard as the ExecutionResult branch, applied to
                # the stringified transport some sandbox backends use. The exit code
                # is parsed out of the "exit=N" prefix so the checker sees the same
                # two inputs either way; an unparseable prefix falls through with
                # the flag untouched, because a malformed transcript is not proof
                # of anything (fail-closed, INV-1).
                head, _, body = res.partition("\n")
                try:
                    parsed_exit = int(head.split("=", 1)[1].strip())
                except (ValueError, IndexError):
                    parsed_exit = None
                if parsed_exit is not None:
                    _note_dynamic_evidence(ctx, body, parsed_exit)
            return SecretScrubber.scrub(res)
        return SecretScrubber.scrub(str(res))
    except Exception as e:
        return f"ERROR: Sandbox execution failed: {SecretScrubber.scrub(str(e))}"


async def run_sandbox_with_evidence(
    command: str,
    sentinel_path: Optional[str] = None,
    sink_symbol: str = "",
) -> Dict[str, Any]:
    """Executes a sandbox command and evaluates reached-sink evidence deterministically."""
    raw_res = await run_sandbox(command)
    exit_code = 0
    output = raw_res

    if raw_res.startswith("exit="):
        parts = raw_res.split("\n", 1)
        try:
            exit_code = int(parts[0].split("=")[1])
            output = parts[1] if len(parts) > 1 else ""
        except (ValueError, IndexError):
            pass

    sentinel_content = ""
    if sentinel_path:
        ctx = current_run_context.get()
        # SECURITY (INV-1/INV-4): the sentinel is read ONLY from inside the sandbox.
        # sentinel_path is model-controlled, so a host-filesystem fallback would be both
        # an arbitrary host read and a way to satisfy reached-sink evidence with a file
        # that no exploit ever produced. With no sandbox there is no admissible evidence.
        if ctx and ctx.sandbox:
            try:
                content_bytes = await ctx.sandbox.read_file(Path(sentinel_path))
                sentinel_content = content_bytes.decode("utf-8", errors="replace")
            except Exception:
                pass

    evidence_present, reason = check_reached_sink_evidence(
        output=output,
        exit_code=exit_code,
        sink_symbol=sink_symbol,
        sentinel_content=sentinel_content,
    )

    # This wrapper sees a channel the inner run_sandbox cannot: the sidecar sentinel
    # file, read from inside the sandbox above. A PoC whose sentinel reached the file
    # but never stdout is real reached-sink proof, so the verdict computed here --
    # with every channel populated -- is fed into the same chokepoint the inner call
    # used. The chokepoint is monotonic and positive-only, so a stricter negative
    # here (e.g. a crash that failed to name the requested sink) never erases
    # evidence an earlier verified execution already established.
    if evidence_present:
        _note_dynamic_evidence(
            current_run_context.get(),
            output,
            exit_code,
            sink_symbol=sink_symbol,
            sentinel_content=sentinel_content,
        )

    return {
        "raw": raw_res,
        "exit_code": exit_code,
        "output": output,
        "evidence_present": evidence_present,
        "evidence_reason": reason,
    }


async def apply_patch(diff_content: str) -> str:
    """Applies a specific code patch to the sandbox context. Code modifications only exist inside the sandbox."""
    ctx = current_run_context.get()
    if ctx is None or ctx.sandbox is None:
        return "ERROR: No active sandbox environment (sandbox unavailable)."
    try:
        sandbox_type = type(ctx.sandbox).__name__
        if sandbox_type in ("StaticOnlyEnvironment", "StaticOnlySandbox"):
            return "ERROR: Patch application failed: dynamic sandbox is disabled in static-only mode."
        res = await ctx.sandbox.apply_patch(diff_content)
        return SecretScrubber.scrub(str(res))
    except Exception as e:
        return f"ERROR: Patch application failed: {SecretScrubber.scrub(str(e))}"
