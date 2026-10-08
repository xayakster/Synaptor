import os
import sys
import json

# Ensure utf-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

repos = ["planning-with-files", "rtk", "mantis", "agent-reach"]

summary = {}

for r in repos:
    r_path = os.path.join(".temp_inspection_repos", r)
    print(f"================== REPO: {r} ==================")
    if not os.path.exists(r_path):
        print("Does not exist")
        continue
    
    repo_summary = {
        "readme_head": "",
        "key_dirs": [],
        "key_files": [],
        "all_files": []
    }
    
    # Read README.md if exists
    readme_candidates = [f for f in os.listdir(r_path) if f.lower() == "readme.md"]
    if readme_candidates:
        readme_path = os.path.join(r_path, readme_candidates[0])
        with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            head = "".join(lines[:60])
            repo_summary["readme_head"] = head
            print("--- README (first 30 lines) ---")
            print("".join(lines[:30]))
    
    for root, dirs, files in os.walk(r_path):
        if ".git" in root:
            continue
        rel = os.path.relpath(root, r_path)
        for d in dirs:
            if d.lower() in [".agents", ".claude", "skills", "rules", "hooks", "commands", "workflows", "tools", "mcp", "config", "src", "bin", "scripts", "templates"]:
                repo_summary["key_dirs"].append(os.path.normpath(os.path.join(rel, d)))
        for f in files:
            rel_f = os.path.normpath(os.path.join(rel, f)) if rel != "." else f
            repo_summary["all_files"].append(rel_f)
            if any(k in f.lower() for k in ["skill", "rule", "hook", "workflow", "command", "prompt", "manifest", "config", "agent", "task", "spec", "pyproject.toml", "package.json", "cargo.toml", "cmakelists.txt", "makefile"]):
                repo_summary["key_files"].append(rel_f)
                
    summary[r] = repo_summary
    print(f"Key Dirs count: {len(repo_summary['key_dirs'])}")
    print(f"Key Files count: {len(repo_summary['key_files'])}")
    print(f"Total Files count: {len(repo_summary['all_files'])}\n")

with open(".temp_inspection_repos/detailed_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)
print("Saved detailed summary to .temp_inspection_repos/detailed_summary.json")
