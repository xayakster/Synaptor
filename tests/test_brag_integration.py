import os
import json
import subprocess
import sys
import pytest

def test_brag_skill_and_rules():
    skill_file = os.path.join(".agents", "skills", "brag-showcase", "SKILL.md")
    assert os.path.exists(skill_file), "brag-showcase SKILL.md missing"
    
    with open(skill_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "name: brag-showcase" in content
    assert "latent-spaces/brag" in content
    
    rule_file = os.path.join(".agents", "rules", "brag-safety.md")
    assert os.path.exists(rule_file)
    with open(rule_file, "r", encoding="utf-8") as f:
        rule_content = f.read()
    assert "Zero External Uploading / Publishing Invariant" in rule_content
    
    workflow_file = os.path.join(".agents", "workflows", "brag-video.md")
    assert os.path.exists(workflow_file)

def test_brag_preflight_tool():
    tool_script = os.path.join(".agents", "tools", "brag", "brag_preflight.py")
    assert os.path.exists(tool_script)
    
    # Run preflight diagnostic check
    res = subprocess.run(
        [sys.executable, tool_script, "--check"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    assert res.returncode == 0
    assert "Brag Video Toolchain" in res.stdout

    # Test storyboard generation
    res_sb = subprocess.run(
        [sys.executable, tool_script, "--storyboard", "--duration", "30"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    assert res_sb.returncode == 0
    
    storyboard_file = os.path.join("brag-out", "storyboard.json")
    assert os.path.exists(storyboard_file)
    with open(storyboard_file, "r", encoding="utf-8") as f:
        sb_data = json.load(f)
    assert sb_data["total_duration_seconds"] == 30
    assert len(sb_data["scenes"]) >= 4

def test_gitignore_contains_brag_out():
    gitignore_path = ".gitignore"
    assert os.path.exists(gitignore_path)
    with open(gitignore_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "brag-out/" in content
