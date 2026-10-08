import os
import subprocess
import sys
import pytest

def test_ui_ux_pro_max_files_and_catalogs():
    skill_dir = os.path.join(".agents", "skills", "ui-ux-pro-max")
    assert os.path.exists(os.path.join(skill_dir, "SKILL.md"))
    
    data_files = ["styles.csv", "colors.csv", "typography.csv", "ux-guidelines.csv", "motion.csv", "products.csv"]
    for df in data_files:
        assert os.path.exists(os.path.join(skill_dir, "data", df)), f"Data file {df} missing"
        
    assert os.path.exists(os.path.join(skill_dir, "data", "stacks", "react.csv"))
    assert os.path.exists(os.path.join(".agents", "rules", "ui-ux-pro-max.md"))
    assert os.path.exists(os.path.join(".agents", "workflows", "ui-ux-pro-max.md"))

def test_ui_ux_pro_max_search_execution():
    search_script = os.path.join(".agents", "skills", "ui-ux-pro-max", "scripts", "search.py")
    assert os.path.exists(search_script)
    
    my_env = os.environ.copy()
    my_env["PYTHONIOENCODING"] = "utf-8"
    
    # Test color search
    res = subprocess.run(
        [sys.executable, search_script, "fintech", "--domain", "color"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=my_env
    )
    assert res.returncode == 0
    assert len(res.stdout) > 0

    # Test typography search
    res_typo = subprocess.run(
        [sys.executable, search_script, "modern tech", "--domain", "typography"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=my_env
    )
    assert res_typo.returncode == 0
    assert len(res_typo.stdout) > 0
