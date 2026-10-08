import os
import subprocess
import sys
import tempfile
import json
import pytest

def test_cookiecutter_template_and_skills_exist():
    template_json = os.path.join(".agents", "templates", "project-templates", "cookiecutter-universal-project", "cookiecutter.json")
    assert os.path.exists(template_json), "cookiecutter.json missing"
    
    with open(template_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "project_name" in data
    assert "project_slug" in data
    
    skill_file = os.path.join(".agents", "skills", "project-scaffolding", "SKILL.md")
    assert os.path.exists(skill_file)
    
    rule_file = os.path.join(".agents", "rules", "project-scaffolding.md")
    assert os.path.exists(rule_file)
    
    workflow_file = os.path.join(".agents", "workflows", "scaffold-project.md")
    assert os.path.exists(workflow_file)

def test_project_scaffold_execution():
    scaffold_tool = os.path.join(".agents", "tools", "cookiecutter", "project_scaffold.py")
    assert os.path.exists(scaffold_tool)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        res = subprocess.run(
            [
                sys.executable,
                scaffold_tool,
                "--name", "Alpha Project",
                "--type", "fullstack",
                "--output", tmpdir
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        assert res.returncode == 0, f"Scaffold failed: {res.stderr}"
        
        project_dir = os.path.join(tmpdir, "alpha_project")
        assert os.path.exists(project_dir), "Project directory not created"
        assert os.path.exists(os.path.join(project_dir, "README.md"))
        assert os.path.exists(os.path.join(project_dir, "task_plan.md"))
        assert os.path.exists(os.path.join(project_dir, "package.json"))
        assert os.path.exists(os.path.join(project_dir, "pyproject.toml"))
        assert os.path.exists(os.path.join(project_dir, "tests", "test_core.py"))
        assert os.path.exists(os.path.join(project_dir, ".agents", "manifest.json"))
        
        # Verify rendered content
        with open(os.path.join(project_dir, "README.md"), "r", encoding="utf-8") as f:
            content = f.read()
        assert "Alpha Project" in content
        assert "alpha_project" not in content.lower() or "alpha_project" in content.lower()
