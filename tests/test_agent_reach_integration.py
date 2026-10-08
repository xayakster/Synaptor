import os
import subprocess
import sys
import pytest

def test_agent_reach_skills_and_references():
    skill_dir = os.path.join(".agents", "skills", "agent-reach")
    assert os.path.exists(os.path.join(skill_dir, "SKILL.md"))
    assert os.path.exists(os.path.join(skill_dir, "SKILL_en.md"))
    
    references = ["dev.md", "search.md", "social.md", "video.md", "web.md", "finance.md", "career.md"]
    for r in references:
        assert os.path.exists(os.path.join(skill_dir, "references", r)), f"Reference {r} missing"
        
    rule_file = os.path.join(".agents", "rules", "agent-reach-policy.md")
    assert os.path.exists(rule_file)
    
    workflow_file = os.path.join(".agents", "workflows", "agent-reach.md")
    assert os.path.exists(workflow_file)

def test_agent_reach_cli_execution():
    cli_path = os.path.join(".agents", "tools", "agent_reach", "cli.py")
    assert os.path.exists(cli_path)
    
    my_env = os.environ.copy()
    my_env["PYTHONIOENCODING"] = "utf-8"
    
    # Test --help
    res = subprocess.run(
        [sys.executable, cli_path, "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=my_env
    )
    assert res.returncode == 0
    assert "agent-reach" in res.stdout.lower() or "usage:" in res.stdout.lower()

def test_agent_reach_package_import():
    # Verify package can be imported directly
    sys_path_code = "import sys; sys.path.insert(0, '.agents/tools'); import agent_reach; print('imported successfully')"
    res = subprocess.run(
        [sys.executable, "-c", sys_path_code],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    assert res.returncode == 0
    assert "imported successfully" in res.stdout
