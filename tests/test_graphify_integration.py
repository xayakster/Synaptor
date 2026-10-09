import os
import json
import subprocess
import sys
import pytest

def test_graphify_skill_and_rules():
    skill_file = os.path.join(".agents", "skills", "graphify", "SKILL.md")
    assert os.path.exists(skill_file), "graphify SKILL.md missing"
    
    with open(skill_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "name: graphify" in content
    assert "Graphify-Labs/graphify" in content
    
    rule_file = os.path.join(".agents", "rules", "graphify-auto-update.md")
    assert os.path.exists(rule_file), "graphify auto-update rule missing"
    
    with open(rule_file, "r", encoding="utf-8") as f:
        rule_content = f.read()
    assert "Automatic Refresh After Code Changes" in rule_content
    
    wf_graphify = os.path.join(".agents", "workflows", "graphify.md")
    wf_update = os.path.join(".agents", "workflows", "graphify-update.md")
    assert os.path.exists(wf_graphify)
    assert os.path.exists(wf_update)

def test_graphify_runner_execution(tmp_path):
    runner_script = os.path.join(".agents", "tools", "graphify", "graphify_runner.py")
    assert os.path.exists(runner_script)
    
    # Run graph generation on current workspace
    res = subprocess.run(
        [sys.executable, runner_script, ".", "--status"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    assert res.returncode == 0
    assert "Active graph found" in res.stdout or "No active graph" in res.stdout

    # Test query
    res_query = subprocess.run(
        [sys.executable, runner_script, ".", "--query", "manifest"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    assert res_query.returncode == 0
    assert "[Graphify Query]" in res_query.stdout

def test_gitignore_contains_graphify_out():
    gitignore_path = ".gitignore"
    assert os.path.exists(gitignore_path)
    with open(gitignore_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "graphify-out/" in content
