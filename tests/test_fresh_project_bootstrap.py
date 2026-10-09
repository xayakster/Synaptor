import os
import subprocess
import sys
import tempfile
import json
import pytest

def test_fresh_project_simulation():
    bootstrap_script = os.path.abspath(os.path.join("scripts", "bootstrap-agent-environment.py"))
    
    with tempfile.TemporaryDirectory() as fresh_project_dir:
        print(f"Testing in temporary clean project: {fresh_project_dir}")
        
        my_env = os.environ.copy()
        my_env["PYTHONIOENCODING"] = "utf-8"
        
        # 1. Run bootstrap in fresh directory
        res = subprocess.run(
            [sys.executable, bootstrap_script, fresh_project_dir],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=my_env
        )
        assert res.returncode == 0, f"Bootstrap failed with error: {res.stderr}"
        assert "Status: SUCCESS" in res.stdout
        
        # 2. Verify .agents structure in fresh project
        fresh_agents = os.path.join(fresh_project_dir, ".agents")
        assert os.path.exists(os.path.join(fresh_agents, "skills", "planning-with-files", "SKILL.md"))
        assert os.path.exists(os.path.join(fresh_agents, "skills", "rtk-token-killer", "SKILL.md"))
        assert os.path.exists(os.path.join(fresh_agents, "skills", "mantis-security-audit", "SKILL.md"))
        assert os.path.exists(os.path.join(fresh_agents, "skills", "agent-reach", "SKILL.md"))
        assert os.path.exists(os.path.join(fresh_agents, "skills", "project-scaffolding", "SKILL.md"))
        assert os.path.exists(os.path.join(fresh_agents, "skills", "ui-ux-pro-max", "SKILL.md"))
        assert os.path.exists(os.path.join(fresh_agents, "skills", "gsap-animation", "SKILL.md"))
        assert os.path.exists(os.path.join(fresh_agents, "skills", "motion-animation", "SKILL.md"))
        assert os.path.exists(os.path.join(fresh_agents, "skills", "graphify", "SKILL.md"))
        assert os.path.exists(os.path.join(fresh_agents, "skills", "brag-showcase", "SKILL.md"))
        assert os.path.exists(os.path.join(fresh_agents, "manifest.json"))
        assert os.path.exists(os.path.join(fresh_agents, "MANIFEST.md"))
        
        # 3. Test lifecycle hook in fresh project
        hook_script = os.path.join(fresh_agents, "hooks", "planning_hook.py")
        hook_res = subprocess.run(
            [sys.executable, hook_script, "session-start"],
            cwd=fresh_project_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=my_env
        )
        assert hook_res.returncode == 0
        hook_data = json.loads(hook_res.stdout)
        assert isinstance(hook_data, dict)
        
        # 4. Test UI/UX search query in fresh project
        uupm_search = os.path.join(fresh_agents, "skills", "ui-ux-pro-max", "scripts", "search.py")
        uupm_res = subprocess.run(
            [sys.executable, uupm_search, "saas", "--domain", "color"],
            cwd=fresh_project_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=my_env
        )
        assert uupm_res.returncode == 0
        assert len(uupm_res.stdout) > 0
        
        # 5. Test Cookiecutter scaffolding in fresh project
        scaffold_tool = os.path.join(fresh_agents, "tools", "cookiecutter", "project_scaffold.py")
        scaffold_res = subprocess.run(
            [sys.executable, scaffold_tool, "--name", "Sub App", "--type", "frontend", "--output", fresh_project_dir, "--no-agents"],
            cwd=fresh_project_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=my_env
        )
        assert scaffold_res.returncode == 0
        assert os.path.exists(os.path.join(fresh_project_dir, "sub_app", "README.md"))
        
        # 6. Test Idempotency (Running bootstrap second time in same directory)
        res_idempotent = subprocess.run(
            [sys.executable, bootstrap_script, fresh_project_dir],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=my_env
        )
        assert res_idempotent.returncode == 0
        assert "Status: SUCCESS" in res_idempotent.stdout
