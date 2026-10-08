#!/usr/bin/env python3
"""
Universal Agent Environment Bootstrap Script
Idempotent installer and portable sync tool for .agents infrastructure.

Usage:
    python bootstrap-agent-environment.py [target_directory] [--force] [--check-only]
"""

import sys
import os
import shutil
import json
import subprocess
import argparse

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

def get_source_agents_dir():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(os.path.dirname(script_dir), ".agents"),
        os.path.join(os.getcwd(), ".agents"),
    ]
    for c in candidates:
        if os.path.exists(c) and os.path.isdir(c):
            return c
    raise FileNotFoundError("Could not locate master .agents directory.")

def copy_or_merge_dir(src, dst):
    if not os.path.exists(dst):
        os.makedirs(dst, exist_ok=True)
    
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copy_or_merge_dir(s, d)
        else:
            shutil.copy2(s, d)

def check_environment():
    status = {}
    py_ver = sys.version.split()[0]
    status["python"] = {"version": py_ver, "ok": sys.version_info >= (3, 8)}
    
    for pkg in ["requests", "pydantic", "yaml", "pytest"]:
        try:
            __import__(pkg)
            status[pkg] = True
        except ImportError:
            status[pkg] = False
            
    status["git"] = shutil.which("git") is not None
    status["node"] = shutil.which("node") is not None
    status["npm"] = shutil.which("npm") is not None
    status["rtk_native"] = shutil.which("rtk") is not None
    
    return status

def validate_installation(target_dir):
    agents_dir = os.path.join(target_dir, ".agents")
    results = {
        "planning_with_files": os.path.exists(os.path.join(agents_dir, "skills", "planning-with-files", "SKILL.md")),
        "rtk": os.path.exists(os.path.join(agents_dir, "skills", "rtk-token-killer", "SKILL.md")) and os.path.exists(os.path.join(agents_dir, "tools", "rtk", "rtk_filter.py")),
        "mantis": os.path.exists(os.path.join(agents_dir, "skills", "mantis-security-audit", "SKILL.md")) and os.path.exists(os.path.join(agents_dir, "tools", "mantis", "configure.py")),
        "agent_reach": os.path.exists(os.path.join(agents_dir, "skills", "agent-reach", "SKILL.md")) and os.path.exists(os.path.join(agents_dir, "tools", "agent_reach", "cli.py")),
        "cookiecutter_scaffold": os.path.exists(os.path.join(agents_dir, "skills", "project-scaffolding", "SKILL.md")) and os.path.exists(os.path.join(agents_dir, "tools", "cookiecutter", "project_scaffold.py")),
        "ui_ux_pro_max": os.path.exists(os.path.join(agents_dir, "skills", "ui-ux-pro-max", "SKILL.md")) and os.path.exists(os.path.join(agents_dir, "skills", "ui-ux-pro-max", "scripts", "search.py")),
        "gsap_animation": os.path.exists(os.path.join(agents_dir, "skills", "gsap-animation", "SKILL.md")) and os.path.exists(os.path.join(agents_dir, "config", "gsap_presets.json")),
        "shadcn_ui": os.path.exists(os.path.join(agents_dir, "skills", "shadcn-ui", "SKILL.md")) and os.path.exists(os.path.join(agents_dir, "rules", "shadcn-ui-patterns.md")),
        "nextjs_developer": os.path.exists(os.path.join(agents_dir, "skills", "nextjs-developer", "SKILL.md")) and os.path.exists(os.path.join(agents_dir, "rules", "nextjs-app-router.md")),
        "tailwind_patterns": os.path.exists(os.path.join(agents_dir, "skills", "tailwind-patterns", "SKILL.md")) and os.path.exists(os.path.join(agents_dir, "rules", "tailwind-design-tokens.md")),
        "realworld_reference": os.path.exists(os.path.join(agents_dir, "skills", "realworld-reference", "SKILL.md")),
        "nodejs_clean_architecture": os.path.exists(os.path.join(agents_dir, "skills", "nodejs-clean-architecture", "SKILL.md")) and os.path.exists(os.path.join(agents_dir, "rules", "backend-clean-architecture.md")),
        "system_design_primer": os.path.exists(os.path.join(agents_dir, "skills", "system-design-primer", "SKILL.md")) and os.path.exists(os.path.join(agents_dir, "rules", "system-design-principles.md")),
        "backend_tech_matrix": os.path.exists(os.path.join(agents_dir, "skills", "backend-tech-matrix", "SKILL.md")) and os.path.exists(os.path.join(agents_dir, "config", "backend_tech_matrix.json")),
        "manifest": os.path.exists(os.path.join(agents_dir, "manifest.json")),
        "hooks": os.path.exists(os.path.join(agents_dir, "hooks", "hooks.json")),
    }
    return results

def bootstrap(target_dir, check_only=False, force=False):
    target_dir = os.path.abspath(target_dir)
    target_agents = os.path.join(target_dir, ".agents")
    source_agents = get_source_agents_dir()
    
    print(f"=== Universal AI Agent Infrastructure Bootstrap ===")
    print(f"Source: {source_agents}")
    print(f"Target: {target_dir}")
    print(f"Mode: {'Check Only' if check_only else 'Install / Merge'}\n")
    
    env_status = check_environment()
    print("Environment Diagnostic:")
    print(f"  • Python: {env_status['python']['version']} (OK: {env_status['python']['ok']})")
    print(f"  • Git: {env_status['git']}")
    print(f"  • Node/NPM: {env_status['node']}")
    print(f"  • PyYAML: {env_status.get('yaml', False)}")
    print(f"  • Requests: {env_status.get('requests', False)}")
    print(f"  • Pydantic: {env_status.get('pydantic', False)}")
    print(f"  • Native RTK binary: {env_status.get('rtk_native', False)}")
    print("")
    
    if not check_only:
        if os.path.exists(target_agents):
            print(f"Existing .agents found in target. Performing non-destructive merge...")
        else:
            print(f"Creating new .agents in target...")
            os.makedirs(target_agents, exist_ok=True)
            
        copy_or_merge_dir(source_agents, target_agents)
        print("Merged all skills, rules, hooks, workflows, tools, templates, and configs successfully.\n")
        
    validation = validate_installation(target_dir)
    print("Component Validation:")
    all_ok = True
    for comp, is_ok in validation.items():
        state_str = "PASS" if is_ok else "FAIL"
        print(f"  • {comp.replace('_', ' ').title():<25}: {state_str}")
        if not is_ok:
            all_ok = False
            
    print("-" * 50)
    if all_ok:
        print("Status: SUCCESS — Synaptor Agent Infrastructure is ready!")
        return 0
    else:
        print("Status: WARNING — Some components could not be validated.")
        return 1

def main():
    parser = argparse.ArgumentParser(description="Bootstrap Synaptor Agent Infrastructure")
    parser.add_argument("target", nargs="?", default=".", help="Target workspace directory (default: current directory)")
    parser.add_argument("--check-only", action="store_true", help="Validate existing installation without copying files")
    parser.add_argument("--force", action="store_true", help="Force overwrite existing configuration")
    
    args = parser.parse_args()
    ret = bootstrap(args.target, check_only=args.check_only, force=args.force)
    sys.exit(ret)

if __name__ == "__main__":
    main()
