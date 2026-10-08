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
"""Mantis Campaign Launcher.

Launches automated vulnerability review campaigns on target files or repositories.
Supports research graph synthesis, 12-hour budgeting controls, and zero-loss resumption.
"""

import argparse
import asyncio
import os
import re
import sys
from pathlib import Path
from typing import Any, Optional
import warnings

# Suppress noisy ADK preview/experimental feature notices
warnings.filterwarnings("ignore", message=r".*\[EXPERIMENTAL\].*")

# Ensure reference root is in sys.path when script is run directly
_REF_ROOT = str(Path(__file__).resolve().parent.parent)
if _REF_ROOT not in sys.path:
    sys.path.insert(0, _REF_ROOT)

from core.budget import BudgetConfig, parse_duration_seconds, parse_token_budget
from core.config import MantisAuthError
from core.synthesizer import ResearchGraphSynthesizer, WorkflowSynthesizer
from main import pipeline
from scripts.configure import (
    detect_capabilities,
    ensure_configured,
    find_workflow_json,
    is_default_or_unconfigured,
    load_workflow_dict,
    run_preflight_checks,
)


class _LauncherArgumentParser(argparse.ArgumentParser):
    """Exits 64 (EX_USAGE) on CLI usage errors instead of argparse's default 2.

    Exit code 2 is documented by Mantis as "paused at budget" (and main.py
    uses it that way), so a CI wrapper could not distinguish a typo'd flag
    from a resumable pause on the launch.py path.
    """

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(64, f"{self.prog}: error: {message}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = _LauncherArgumentParser(
        description="Mantis Campaign Launcher: Automated Security Review Pipeline"
    )
    parser.add_argument("target", nargs="?", default=".", help="Target source file or repository directory to review")
    parser.add_argument("--workflow", "-w", type=str, default="", help="Path to workflow.json")
    parser.add_argument("--objective", type=str, default="", help="Natural language objective for research graph synthesis")
    parser.add_argument(
        "--sandbox",
        "-s",
        type=str,
        choices=["static-only", "static", "gvisor", "microsandbox", "gce"],
        help="Sandbox execution override",
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        help="Global LLM model override (e.g. gemini-3.7-flash, vertex_ai/claude-opus-5, openai/my-model)",
    )
    parser.add_argument("--api-base", type=str, help="Custom LLM API Base URL for OpenAI-compatible models")
    parser.add_argument(
        "--reasoning-effort",
        type=str,
        choices=["low", "medium", "high"],
        help="Reasoning effort override (low, medium, high)",
    )
    parser.add_argument("--timeout", type=float, help="LLM request timeout in seconds")
    parser.add_argument("--db", "-d", type=str, help="Path to knowledge SQLite database")
    parser.add_argument(
        "--save-config",
        action="store_true",
        help=(
            "Persist CLI overrides (--model, --db, --sandbox, ...) into "
            "workflow.local.json. Without this flag overrides apply to this "
            "run only."
        ),
    )
    parser.add_argument(
        "--flex",
        action="store_true",
        help="Use Vertex AI Gemini Flex tier (routes requests via shared Flex capacity).",
    )

    # Budgeting & Resumption
    parser.add_argument(
        "--max-time",
        type=str,
        default=None,
        help="Wall-clock time ceiling override before graceful pause (e.g. 12h, 24h, 30m, or 'unlimited'; defaults to workflow budget)",
    )
    parser.add_argument(
        "--token-budget",
        type=str,
        default=None,
        help="Token consumption ceiling override before graceful pause (e.g. 10M, 5M, 500k, or 'unlimited'; defaults to workflow budget)",
    )
    parser.add_argument(
        "--no-budget",
        action="store_true",
        help=(
            "Disable the wall-clock and token spend ceilings entirely (for dedicated "
            "hardware or unmetered budgets). Runaway-loop guards stay active."
        ),
    )
    parser.add_argument(
        "--no-replan",
        action="store_true",
        help=(
            "Disable dynamic replanning: freezes the campaign plan at run "
            "start so a rerun holds the same plan (for reproducibility)."
        ),
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=1,
        help=(
            "Number of campaigns to run concurrently (default: 1, the "
            "sequential behaviour). Run-level budget ceilings are shared "
            "across workers; per-campaign guards stay per campaign."
        ),
    )
    parser.add_argument(
        "--focus",
        type=str,
        default="",
        help=(
            "Natural-language directive steering the campaign planner, e.g. "
            "'look for IDOR' or 'find memory corruption issues'"
        ),
    )
    parser.add_argument(
        "--seed-report",
        type=str,
        default="",
        help=(
            "Path to a bug report file; the planner hunts variants of the "
            "described bug, treating file content as untrusted evidence"
        ),
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="Maximum graph steps ceiling override (defaults to workflow budget)",
    )
    parser.add_argument(
        "--max-node-visits",
        type=int,
        default=None,
        help="Maximum visits per graph node ceiling override (defaults to workflow budget)",
    )
    parser.add_argument(
        "--max-llm-calls",
        type=int,
        default=None,
        help="LLM calls ceiling override before graceful pause (0 for unbounded; defaults to workflow budget)",
    )
    parser.add_argument(
        "--max-node-tool-calls",
        type=int,
        default=None,
        help="Per-node visit runaway tool loop ceiling override (defaults to workflow budget)",
    )
    parser.add_argument(
        "--resume",
        type=str,
        default="",
        help="Run ID to resume execution from where it paused",
    )
    parser.add_argument(
        "--inspect",
        action="store_true",
        help="Preview synthesized workflow layout and prompt before execution",
    )
    parser.add_argument(
        "--synthesize-llm",
        action="store_true",
        default=True,
        help="Use LLM to synthesize tailored research graph for --objective (default: True)",
    )
    parser.add_argument(
        "--deterministic-only",
        action="store_false",
        dest="synthesize_llm",
        help="Force deterministic archetype synthesis instead of LLM research graph synthesis",
    )

    # Options
    parser.add_argument(
        "--probe",
        "--probe-llm",
        action="store_true",
        dest="probe_llm",
        help="Perform an active live reachability probe against the configured LLM endpoint during preflight",
    )
    parser.add_argument(
        "--no-auto-configure",
        action="store_true",
        help="Disable automatic environment detection and placeholder resolution",
    )
    parser.add_argument(
        "--preflight-only",
        "--test",
        "--preflight",
        action="store_true",
        help="Run preflight tests and exit without launching pipeline",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Launch interactive configuration wizard before review",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print review plan and target indexing without executing models",
    )

    return parser


def run_launch(
    target: str,
    workflow_path: str = "",
    objective: str = "",
    sandbox: Optional[str] = None,
    model: Optional[str] = None,
    api_base: Optional[str] = None,
    reasoning_effort: Optional[str] = None,
    timeout: Optional[float] = None,
    db_path: Optional[str] = None,
    flex: bool = False,
    auto_configure: bool = True,
    preflight_only: bool = False,
    interactive: bool = False,
    dry_run: bool = False,
    probe_llm: bool = False,
    max_time: Optional[str] = None,
    token_budget: Optional[str] = None,
    no_budget: bool = False,
    no_replan: bool = False,
    parallel: int = 1,
    focus: str = "",
    seed_report: str = "",
    max_steps: Optional[int] = None,
    max_node_visits: Optional[int] = None,
    max_llm_calls: Optional[int] = None,
    max_node_tool_calls: Optional[int] = None,
    resume_run_id: str = "",
    inspect: bool = False,
    synthesize_llm: bool = True,
    save_config: bool = False,
) -> int:
    """Core launch workflow: auto-configures, preflights, and executes the Mantis pipeline."""
    if flex:
        os.environ["VERTEX_FLEX"] = "1"

    # SECURITY (INV-4): component-wise symlink validation. A leaf-only is_symlink()
    # check is bypassed by a hostile checkout shipping an intermediate symlink
    # (repo/link/sub with link -> ../../..), which .resolve() would silently follow.
    from core.paths import validate_scan_target

    target_path, target_err = validate_scan_target(target)
    if target_path is None:
        print(f"❌ Error: {target_err}", file=sys.stderr)
        return 1

    cli_budget_overrides: dict[str, Any] = {}
    try:
        if max_time is not None:
            cli_budget_overrides["max_wall_clock_seconds"] = parse_duration_seconds(max_time)
        if token_budget is not None:
            cli_budget_overrides["max_tokens"] = parse_token_budget(token_budget)
    except ValueError as ve:
        print(f"❌ Error: {ve}", file=sys.stderr)
        return 2
    # --no-budget disables both RUN-level spend ceilings (0 = unbounded). Expressed
    # as CLI overrides so the normal effective-budget merge and the dry-run
    # display both see it; deliberately leaves the runaway-loop guards alone.
    if no_budget:
        cli_budget_overrides["max_wall_clock_seconds"] = 0.0
        cli_budget_overrides["max_tokens"] = 0
    if max_steps is not None:
        cli_budget_overrides["max_graph_steps"] = max_steps
    if max_node_visits is not None:
        cli_budget_overrides["max_node_visits"] = max_node_visits
    if max_llm_calls is not None:
        cli_budget_overrides["max_llm_calls"] = max_llm_calls
    if max_node_tool_calls is not None:
        cli_budget_overrides["max_node_tool_calls"] = max_node_tool_calls

    # Fast path: Preflight validation check without synthesis or execution
    if preflight_only:
        wf_file = find_workflow_json(workflow_path)
        wf_data = load_workflow_dict(wf_file)
        cfg = wf_data.get("config", {})
        overrides = {}
        if sandbox:
            overrides["sandbox"] = {"type": sandbox, "options": {}}
        if model:
            overrides["default_model"] = model
        if api_base:
            overrides["api_base"] = api_base
        if reasoning_effort:
            overrides["reasoning_effort"] = reasoning_effort
        if timeout is not None:
            overrides["timeout"] = timeout
        if db_path:
            overrides["db_path"] = db_path
        if auto_configure and overrides:
            cfg = ensure_configured(
                workflow_path=wf_file,
                auto=True,
                overrides=overrides,
                probe_llm=probe_llm,
                persist_overrides=save_config,
            )
        ok, messages = run_preflight_checks(cfg, target_path=str(target_path), probe_llm=probe_llm)
        if not ok:
            print("\n❌ Preflight Verification Failed:", file=sys.stderr)
            for msg in messages:
                print(f"  {msg}", file=sys.stderr)
            return 1
        print("✅ Preflight validation succeeded.")
        for msg in messages:
            print(f"  {msg}")
        return 0

    # Research Graph Synthesis
    # Set here rather than inside the branch below: the pipeline call at the end of this
    # function reads it unconditionally, and a run without an objective never surveys.
    survey_astm = None
    if objective:
        base_budget = BudgetConfig()
        if workflow_path:
            try:
                base_wf = load_workflow_dict(find_workflow_json(workflow_path))
                raw_b = base_wf.get("budget") or base_wf.get("config", {}).get("budget")
                if raw_b and isinstance(raw_b, dict):
                    base_budget = BudgetConfig.from_dict(raw_b)
            except Exception:
                pass

        synth_budget = BudgetConfig(
            max_wall_clock_seconds=cli_budget_overrides.get("max_wall_clock_seconds", base_budget.max_wall_clock_seconds),
            max_tokens=cli_budget_overrides.get("max_tokens", base_budget.max_tokens),
            max_graph_steps=cli_budget_overrides.get("max_graph_steps", base_budget.max_graph_steps),
            max_node_visits=cli_budget_overrides.get("max_node_visits", base_budget.max_node_visits),
            max_llm_calls=cli_budget_overrides.get("max_llm_calls", base_budget.max_llm_calls),
            max_node_tool_calls=cli_budget_overrides.get("max_node_tool_calls", base_budget.max_node_tool_calls),
        )

        mode_str = "LLM-driven research graph synthesis" if synthesize_llm else "deterministic archetype"
        print(f"✨ Synthesizing targeted research graph for objective: '{objective}' (mode: {mode_str})...")
        synthesizer = ResearchGraphSynthesizer(
            default_model=model or "vertex_ai/gemini-3.7-flash",
            db_path=db_path or "knowledge.db",
        )
        effective_sandbox = sandbox
        if not effective_sandbox:
            try:
                base_wf_dict = load_workflow_dict(find_workflow_json(workflow_path))
                effective_sandbox = base_wf_dict.get("config", {}).get("sandbox", {}).get("type")
            except Exception:
                effective_sandbox = "static-only"
        effective_sandbox = effective_sandbox or "static-only"

        # Survey the repository before synthesizing, so the graph is shaped by what is
        # actually in the target rather than by the objective string alone. An objective
        # that names a domain still wins; this only supplies an answer where there was
        # previously none.
        #
        # Failure here is not fatal. Synthesis without a map is exactly the behaviour
        # that shipped before, so a surveyor problem costs specificity, not the run.
        try:
            from core.surveyor import survey
            survey_astm = survey(str(target_path))
            top = survey_astm.get("slices", [])
            if top:
                print(
                    f"🗺️  Surveyed {survey_astm.get('provenance', {}).get('groups_considered', 0)} "
                    f"candidate areas in {survey_astm.get('provenance', {}).get('elapsed_seconds', 0)}s."
                )
        except Exception as exc:
            print(f"  Surveyor unavailable ({exc}); synthesizing from the objective alone.", file=sys.stderr)
            survey_astm = None

        spec = synthesizer.synthesize(
            objective=objective,
            budget_config=synth_budget,
            target_root=str(target_path),
            sandbox_type=effective_sandbox,
            use_llm=synthesize_llm,
            model=model,
            timeout=timeout,
            astm=survey_astm,
        )
        meta = spec.evolution_metadata or {}
        if meta.get("archetype_source") == "repository":
            print(
                f"  Archetype '{meta.get('archetype')}' inferred from repository content "
                f"(the objective named no domain)."
            )
        if meta.get("sandbox_clamp"):
            clamp = meta["sandbox_clamp"]
            print(
                f"  🔒 Sandbox request '{clamp.get('requested')}' clamped to "
                f"'{clamp.get('effective')}': {clamp.get('reason')}"
            )
        mantis_home = os.environ.get("MANTIS_HOME")
        if mantis_home:
            workspace_dir = (Path(mantis_home) / "workspace").resolve()
        else:
            workspace_dir = (Path(__file__).resolve().parent.parent / "workspace").resolve()
        recipe_path = ResearchGraphSynthesizer.persist_recipe(spec, workspace_dir)
        workflow_path = str(recipe_path)
        print(f"✅ Synthesized recipe saved to: {recipe_path}")

        if inspect:
            print("\n" + "=" * 80)
            print("🔍 Synthesized Research Graph Preview:")
            print("=" * 80)
            print(f"  • Name:        {spec.name}")
            print(f"  • Nodes:       {[n.id for n in spec.nodes]}")
            print(f"  • Edges:       {len(spec.edges)} transitions")
            print(f"  • Archetype:   {spec.evolution_metadata.get('archetype') if spec.evolution_metadata else 'standard'}")
            print(f"  • Synthesis:   {spec.evolution_metadata.get('synthesis_mode') if spec.evolution_metadata else 'unknown'}")
            print("=" * 80)
            return 0

    wf_file = find_workflow_json(workflow_path)
    wf_data = load_workflow_dict(wf_file, load_local=False if objective else True)
    cfg = wf_data.get("config", {})

    # Resolve effective budget: CLI overrides > workflow budget > default BudgetConfig
    wf_budget_raw = wf_data.get("budget") or cfg.get("budget") or {}
    wf_budget = BudgetConfig.from_dict(wf_budget_raw) if wf_budget_raw else BudgetConfig()
    effective_budget = BudgetConfig(
        max_wall_clock_seconds=cli_budget_overrides.get("max_wall_clock_seconds", wf_budget.max_wall_clock_seconds),
        max_tokens=cli_budget_overrides.get("max_tokens", wf_budget.max_tokens),
        max_graph_steps=cli_budget_overrides.get("max_graph_steps", wf_budget.max_graph_steps),
        max_node_visits=cli_budget_overrides.get("max_node_visits", wf_budget.max_node_visits),
        max_llm_calls=cli_budget_overrides.get("max_llm_calls", wf_budget.max_llm_calls),
        max_node_tool_calls=cli_budget_overrides.get("max_node_tool_calls", wf_budget.max_node_tool_calls),
    )

    # Build overrides dict
    overrides = {}
    if sandbox:
        overrides["sandbox"] = {"type": sandbox, "options": {}}
    if model:
        overrides["default_model"] = model
    if api_base:
        overrides["api_base"] = api_base
    if reasoning_effort:
        overrides["reasoning_effort"] = reasoning_effort
    if timeout is not None:
        overrides["timeout"] = timeout
    if db_path:
        overrides["db_path"] = db_path

    # Check unconfigured placeholders and auto-configure
    is_unconf, issues = is_default_or_unconfigured(cfg)
    if is_unconf or interactive or (auto_configure and overrides):
        if interactive:
            from scripts.configure import run_interactive_wizard
            cfg = run_interactive_wizard(wf_file)
        elif auto_configure:
            print("⚙️ Auto-configuring Mantis environment...")
            cfg = ensure_configured(
                workflow_path=wf_file,
                auto=True,
                overrides=overrides if overrides else None,
                probe_llm=probe_llm,
                persist_overrides=save_config,
            )

    # Preflight Check
    ok, messages = run_preflight_checks(cfg, target_path=str(target_path), probe_llm=probe_llm)
    if not ok and auto_configure and not is_unconf and not interactive:
        if os.environ.get("MANTIS_ALLOW_SANDBOX_DOWNGRADE") == "1":
            print("⚙️ Preflight check failed on existing configuration, attempting approved auto-configuration...")
            cfg = ensure_configured(
                workflow_path=wf_file,
                auto=True,
                overrides=overrides if overrides else None,
                probe_llm=probe_llm,
                persist_overrides=save_config,
            )
            ok, messages = run_preflight_checks(cfg, target_path=str(target_path), probe_llm=probe_llm)
        else:
            print(
                "❌ Preflight failed for the configured sandbox. Refusing to "
                "auto-downgrade isolation. Set MANTIS_ALLOW_SANDBOX_DOWNGRADE=1 "
                "to accept a degraded session.",
                file=sys.stderr,
            )

    if not ok:
        print("\n❌ Preflight Verification Failed:", file=sys.stderr)
        for msg in messages:
            print(f"  {msg}", file=sys.stderr)
        print("\nRun 'python3 reference/scripts/configure.py --interactive' or '--auto' to fix configuration.", file=sys.stderr)
        return 1


    if dry_run:
        print("\n📋 Dry-Run Execution Plan:")
        print(f"  • Target:        {target_path}")
        print(f"  • Workflow:      {wf_file}")
        print(f"  • Sandbox:       {cfg.get('sandbox', {}).get('type', 'static-only')}")
        print(f"  • Model:         {model or cfg.get('default_model')}")
        print(f"  • Knowledge DB:  {db_path or cfg.get('db_path', 'knowledge.db')}")
        if effective_budget.max_wall_clock_seconds > 0:
            print(f"  • Max Time:      {effective_budget.max_wall_clock_seconds / 3600:.1f}h")
        else:
            print("  • Max Time:      unlimited")
        if effective_budget.max_tokens > 0:
            print(f"  • Token Budget:  {effective_budget.max_tokens:,}")
        else:
            print("  • Token Budget:  unlimited")
        print(f"  • Max Steps:     {effective_budget.max_graph_steps}")
        print(f"  • Max Visits:    {effective_budget.max_node_visits}")
        if effective_budget.max_llm_calls > 0:
            print(f"  • Max LLM Calls: {effective_budget.max_llm_calls}")
        if effective_budget.max_node_tool_calls > 0:
            print(f"  • Max Node Tool Calls: {effective_budget.max_node_tool_calls}")
        if resume_run_id:
            print(f"  • Resume Run ID: {resume_run_id}")
        return 0

    # Launch Pipeline
    try:
        return asyncio.run(
            pipeline(
                scan_target=str(target_path),
                workflow_path=wf_file,
                model_override=model,
                api_base_override=api_base,
                sandbox_override=sandbox,
                db_override=db_path,
                timeout_override=timeout,
                reasoning_effort_override=reasoning_effort,
                auto_configure=auto_configure and not bool(objective),
                load_local=False if objective else True,
                budget_config=effective_budget if bool(cli_budget_overrides) else None,
                resume_run_id=resume_run_id,
                objective=objective,
                max_llm_calls_override=cli_budget_overrides.get("max_llm_calls"),
                max_node_tool_calls_override=cli_budget_overrides.get("max_node_tool_calls"),
                enable_replan=False if no_replan else None,
                parallel=parallel,
                focus=focus,
                seed_report_path=seed_report,
                # Already paid for above. Surveying chromium costs ~65s; the pipeline
                # would otherwise repeat it to answer the same question.
                precomputed_astm=survey_astm,
            )
        )
    except MantisAuthError as ae:
        print(f"\n{ae}", file=sys.stderr)
        return 1


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    return run_launch(
        target=args.target,
        workflow_path=args.workflow,
        objective=args.objective,
        sandbox=args.sandbox,
        model=args.model,
        api_base=args.api_base,
        reasoning_effort=args.reasoning_effort,
        timeout=args.timeout,
        db_path=args.db,
        flex=args.flex,
        auto_configure=not args.no_auto_configure,
        preflight_only=args.preflight_only,
        interactive=args.interactive,
        dry_run=args.dry_run,
        probe_llm=args.probe_llm,
        max_time=args.max_time,
        token_budget=args.token_budget,
        no_budget=args.no_budget,
        no_replan=args.no_replan,
        parallel=args.parallel,
        focus=args.focus,
        seed_report=args.seed_report,
        max_steps=args.max_steps,
        max_node_visits=args.max_node_visits,
        max_llm_calls=args.max_llm_calls,
        max_node_tool_calls=args.max_node_tool_calls,
        resume_run_id=args.resume,
        inspect=args.inspect,
        synthesize_llm=args.synthesize_llm,
        save_config=args.save_config,
    )


if __name__ == "__main__":
    try:
        sys.exit(main())
    except MantisAuthError as ae:
        print(f"\n{ae}", file=sys.stderr)
        sys.exit(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nProcess aborted by user.")
        sys.exit(130)
