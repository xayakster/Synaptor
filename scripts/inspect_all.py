import os
import subprocess
import json

repos = {
    "planning-with-files": "https://github.com/OthmanAdi/planning-with-files.git",
    "rtk": "https://github.com/rtk-ai/rtk.git",
    "mantis": "https://github.com/google/mantis.git",
    "agent-reach": "https://github.com/Panniantong/Agent-Reach.git"
}

results = {}

for name, url in repos.items():
    repo_dir = os.path.join(".temp_inspection_repos", name)
    if not os.path.exists(repo_dir):
        continue
    
    # Git info
    commit = subprocess.check_output(["git", "-C", repo_dir, "rev-parse", "HEAD"]).decode().strip()
    date = subprocess.check_output(["git", "-C", repo_dir, "log", "-1", "--format=%cd"]).decode().strip()
    msg = subprocess.check_output(["git", "-C", repo_dir, "log", "-1", "--format=%s"]).decode().strip()
    
    # List files
    files = []
    for root, dirs, filenames in os.walk(repo_dir):
        if ".git" in root:
            continue
        rel_root = os.path.relpath(root, repo_dir)
        for f in filenames:
            rel_file = os.path.normpath(os.path.join(rel_root, f)) if rel_root != "." else f
            files.append(rel_file)
            
    results[name] = {
        "url": url,
        "commit": commit,
        "date": date,
        "message": msg,
        "total_files": len(files),
        "files": files
    }

print(json.dumps(results, indent=2))
with open(".temp_inspection_repos/inspection_summary.json", "w") as f:
    json.dump(results, f, indent=2)
