import os
import sys
import subprocess
import json

sys.stdout.reconfigure(encoding='utf-8')

repos = {
    "cookiecutter": "https://github.com/cookiecutter/cookiecutter.git",
    "ui-ux-pro-max-skill": "https://github.com/nextlevelbuilder/ui-ux-pro-max-skill.git",
    "gsap": "https://github.com/greensock/GSAP.git"
}

results = {}

for name, url in repos.items():
    repo_dir = os.path.join(".temp_inspection_repos", name)
    print(f"================== REPO: {name} ==================")
    if not os.path.exists(repo_dir):
        print("Does not exist")
        continue
    
    commit = subprocess.check_output(["git", "-C", repo_dir, "rev-parse", "HEAD"]).decode().strip()
    date = subprocess.check_output(["git", "-C", repo_dir, "log", "-1", "--format=%cd"]).decode().strip()
    msg = subprocess.check_output(["git", "-C", repo_dir, "log", "-1", "--format=%s"]).decode().strip()
    
    print(f"Commit: {commit}")
    print(f"Date: {date}")
    print(f"Subject: {msg}")
    
    # Read README.md if present
    readme_candidates = [f for f in os.listdir(repo_dir) if f.lower() == "readme.md"]
    if readme_candidates:
        with open(os.path.join(repo_dir, readme_candidates[0]), "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            print("--- README (first 25 lines) ---")
            print("".join(lines[:25]))
            
    # List key files and directories
    key_dirs = []
    key_files = []
    for root, dirs, files in os.walk(repo_dir):
        if ".git" in root:
            continue
        rel = os.path.relpath(root, repo_dir)
        for d in dirs:
            if d.lower() in [".agents", ".claude", "skills", "rules", "hooks", "commands", "workflows", "tools", "src", "dist", "templates", "docs"]:
                key_dirs.append(os.path.normpath(os.path.join(rel, d)))
        for f in files:
            rel_f = os.path.normpath(os.path.join(rel, f)) if rel != "." else f
            if any(k in f.lower() for k in ["skill", "rule", "hook", "workflow", "command", "template", "package.json", "pyproject.toml", "setup.py", "cookiecutter.json"]):
                key_files.append(rel_f)
                
    results[name] = {
        "url": url,
        "commit": commit,
        "date": date,
        "message": msg,
        "key_dirs": key_dirs,
        "key_files": key_files
    }
    print(f"Key Dirs count: {len(key_dirs)}")
    print(f"Key Files count: {len(key_files)}\n")

with open(".temp_inspection_repos/new_repos_summary.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
