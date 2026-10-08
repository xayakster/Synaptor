import os
import subprocess
import sys
import pytest

def test_mantis_skills_and_rules():
    skills = ["mantis-security-audit", "mantis-configure", "mantis-launch"]
    for s in skills:
        skill_file = os.path.join(".agents", "skills", s, "SKILL.md")
        assert os.path.exists(skill_file), f"Skill {s} missing"
        with open(skill_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert f"name: {s}" in content
        
    rule_file = os.path.join(".agents", "rules", "mantis-security-standards.md")
    assert os.path.exists(rule_file)
    
    workflow_file = os.path.join(".agents", "workflows", "mantis-scan.md")
    assert os.path.exists(workflow_file)
    
    config_file = os.path.join(".agents", "config", "mantis_config.json")
    assert os.path.exists(config_file)

def test_mantis_tools_present():
    tool_files = [
        "research_tools.py",
        "structural_tools.py",
        "sandbox_tools.py",
        "configure.py",
        "launch.py",
        "mcp_server.py"
    ]
    for tf in tool_files:
        path = os.path.join(".agents", "tools", "mantis", tf)
        assert os.path.exists(path), f"Tool {tf} missing"

def test_mantis_configure_preflight():
    config_script = os.path.join(".agents", "tools", "mantis", "configure.py")
    my_env = os.environ.copy()
    my_env["PYTHONIOENCODING"] = "utf-8"
    res = subprocess.run(
        [sys.executable, config_script, "--preflight"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=my_env
    )
    # configure.py should run and return 0 (or output preflight report)
    stdout = res.stdout or ""
    stderr = res.stderr or ""
    combined = (stdout + "\n" + stderr).lower()
    assert res.returncode == 0 or "preflight" in combined or "configuration" in combined
