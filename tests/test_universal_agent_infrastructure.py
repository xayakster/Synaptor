import os
import subprocess
import json
import sys
import pytest

def test_manifest_integrity():
    json_path = os.path.join(".agents", "manifest.json")
    md_path = os.path.join(".agents", "MANIFEST.md")
    
    assert os.path.exists(json_path), "manifest.json missing"
    assert os.path.exists(md_path), "MANIFEST.md missing"
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    repos = [r["name"] for r in data.get("upstream_repositories", [])]
    expected_repos = [
        "planning-with-files",
        "rtk",
        "mantis",
        "agent-reach",
        "cookiecutter",
        "ui-ux-pro-max-skill",
        "gsap",
        "motion",
        "graphify",
        "brag"
    ]
    for er in expected_repos:
        assert er in repos, f"Repo {er} missing from manifest"

def test_existing_configuration_preserved():
    # Verify key pre-existing ECC rules and skills are intact
    assert os.path.exists(os.path.join(".agents", "rules", "common-coding-style.md"))
    assert os.path.exists(os.path.join(".agents", "rules", "common-git-workflow.md"))
    assert os.path.exists(os.path.join(".agents", "skills", "using-superpowers", "SKILL.md"))
    assert os.path.exists(os.path.join(".agents", "skills", "brainstorming", "SKILL.md"))
    assert os.path.exists(os.path.join(".agents", "workflows", "plan.md"))
    assert os.path.exists(os.path.join(".agents", "plugins", "marketplace.json"))

def test_hooks_lifecycle_execution():
    hook_script = os.path.join(".agents", "hooks", "planning_hook.py")
    assert os.path.exists(hook_script)
    
    # Test SessionStart hook event
    res = subprocess.run(
        [sys.executable, hook_script, "session-start"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    assert res.returncode == 0
    output_data = json.loads(res.stdout)
    assert isinstance(output_data, dict)
    
    # Test UserPromptSubmit hook event
    res2 = subprocess.run(
        [sys.executable, hook_script, "user-prompt-submit"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    assert res2.returncode == 0
    output_data2 = json.loads(res2.stdout)
    assert isinstance(output_data2, dict)

def test_bootstrap_check_only():
    bootstrap_script = os.path.join("scripts", "bootstrap-agent-environment.py")
    assert os.path.exists(bootstrap_script)
    
    res = subprocess.run(
        [sys.executable, bootstrap_script, "--check-only"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    assert res.returncode == 0
    assert "Status: SUCCESS" in res.stdout
