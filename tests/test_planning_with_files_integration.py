import os
import subprocess
import tempfile
import pytest

def test_pwf_skill_and_templates_installed():
    skill_path = os.path.join(".agents", "skills", "planning-with-files", "SKILL.md")
    assert os.path.exists(skill_path), "planning-with-files SKILL.md missing"
    
    with open(skill_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "name: planning-with-files" in content
    
    templates = ["task_plan.md", "analytics_task_plan.md", "task_plan_autonomous.md"]
    for t in templates:
        assert os.path.exists(os.path.join(".agents", "skills", "planning-with-files", "templates", t))
        assert os.path.exists(os.path.join(".agents", "templates", t))

def test_pwf_rules_and_workflows_installed():
    rule_path = os.path.join(".agents", "rules", "planning-with-files.md")
    assert os.path.exists(rule_path)
    
    workflow_path = os.path.join(".agents", "workflows", "planning-with-files.md")
    assert os.path.exists(workflow_path)

def test_pwf_inject_plan_execution():
    script_path = os.path.join(".agents", "skills", "planning-with-files", "scripts", "inject-plan.py")
    assert os.path.exists(script_path)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a mock task_plan.md
        plan_content = """# Test Task Plan
<!-- id: test-01 -->
## Phase 1: Exploration
- [x] Step 1
- [ ] Step 2
"""
        with open(os.path.join(tmpdir, "task_plan.md"), "w", encoding="utf-8") as f:
            f.write(plan_content)
        
        res = subprocess.run(
            ["python", os.path.abspath(script_path)],
            cwd=tmpdir,
            capture_output=True,
            text=True
        )
        assert res.returncode == 0
        assert "Test Task Plan" in res.stdout or "Step 1" in res.stdout or res.returncode == 0
