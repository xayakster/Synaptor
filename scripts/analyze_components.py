import os
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

def read_file_safe(path, max_lines=100):
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            return "".join(lines[:max_lines])
    except Exception as e:
        return f"Error reading {path}: {e}"

print("==================================================")
print("1. PLANNING-WITH-FILES DETAILED ANALYSIS")
print("==================================================")
pwf_dir = ".temp_inspection_repos/planning-with-files"
for root, dirs, files in os.walk(pwf_dir):
    rel = os.path.relpath(root, pwf_dir)
    for f in files:
        full_p = os.path.join(root, f)
        if any(f.endswith(ext) for ext in [".md", ".sh", ".json", ".py", ".ps1", ".cmd"]):
            if any(k in f for k in ["SKILL", "hook", "rule", "task_plan", "AGENTS"]):
                print(f"\n--- {os.path.join(rel, f)} ---")
                print(read_file_safe(full_p, 35))

print("\n==================================================")
print("2. RTK DETAILED ANALYSIS")
print("==================================================")
rtk_dir = ".temp_inspection_repos/rtk"
for root, dirs, files in os.walk(rtk_dir):
    rel = os.path.relpath(root, rtk_dir)
    for f in files:
        full_p = os.path.join(root, f)
        if any(k in f.lower() for k in ["skill", "rule", "hook", "prompt", "cargo.toml", "readme", "config", "agent", "workflow"]):
            print(f"\n--- {os.path.join(rel, f)} ---")
            print(read_file_safe(full_p, 25))

print("\n==================================================")
print("3. MANTIS DETAILED ANALYSIS")
print("==================================================")
mantis_dir = ".temp_inspection_repos/mantis"
for root, dirs, files in os.walk(mantis_dir):
    rel = os.path.relpath(root, mantis_dir)
    for f in files:
        full_p = os.path.join(root, f)
        if any(k in f.lower() for k in ["skill", "rule", "hook", "readme", "install", "pyproject", "setup", "requirements"]):
            print(f"\n--- {os.path.join(rel, f)} ---")
            print(read_file_safe(full_p, 30))

print("\n==================================================")
print("4. AGENT-REACH DETAILED ANALYSIS")
print("==================================================")
reach_dir = ".temp_inspection_repos/agent-reach"
for root, dirs, files in os.walk(reach_dir):
    rel = os.path.relpath(root, reach_dir)
    for f in files:
        full_p = os.path.join(root, f)
        if any(k in f.lower() for k in ["skill", "rule", "hook", "pyproject", "readme", "cli", "mcp", "config"]):
            print(f"\n--- {os.path.join(rel, f)} ---")
            print(read_file_safe(full_p, 30))
