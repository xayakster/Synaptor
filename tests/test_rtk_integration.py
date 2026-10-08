import os
import subprocess
import sys
import pytest

def test_rtk_skills_and_rules():
    skill_path = os.path.join(".agents", "skills", "rtk-token-killer", "SKILL.md")
    assert os.path.exists(skill_path)
    
    rule_path = os.path.join(".agents", "rules", "rtk-token-optimization.md")
    assert os.path.exists(rule_path)
    
    workflow_path = os.path.join(".agents", "workflows", "rtk-optimize.md")
    assert os.path.exists(workflow_path)
    
    config_path = os.path.join(".agents", "config", "rtk_config.json")
    assert os.path.exists(config_path)

def test_rtk_filter_execution():
    filter_tool = os.path.join(".agents", "tools", "rtk", "rtk_filter.py")
    assert os.path.exists(filter_tool)
    
    # Test running python command through rtk_filter
    res = subprocess.run(
        [sys.executable, filter_tool, sys.executable, "-c", "print('hello rtk')"],
        capture_output=True,
        text=True
    )
    assert res.returncode == 0
    assert "hello rtk" in res.stdout

def test_rtk_filter_truncation():
    filter_tool = os.path.join(".agents", "tools", "rtk", "rtk_filter.py")
    
    # Generate 300 lines of output to verify truncation
    code = "for i in range(300): print(f'line {i}')"
    res = subprocess.run(
        [sys.executable, filter_tool, sys.executable, "-c", code],
        capture_output=True,
        text=True
    )
    assert res.returncode == 0
    assert "lines omitted to save tokens" in res.stdout
    assert "line 0" in res.stdout
    assert "line 299" in res.stdout
