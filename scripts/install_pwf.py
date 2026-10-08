import os
import shutil

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

# 1. Install planning-with-files skill
src_skill_dir = ".temp_inspection_repos/planning-with-files/skills/planning-with-files"
dst_skill_dir = ".agents/skills/planning-with-files"
ensure_dir(dst_skill_dir)

# Copy SKILL.md
shutil.copy2(os.path.join(src_skill_dir, "SKILL.md"), os.path.join(dst_skill_dir, "SKILL.md"))

# Copy templates
src_templates = os.path.join(src_skill_dir, "templates")
dst_templates = os.path.join(dst_skill_dir, "templates")
ensure_dir(dst_templates)
for f in os.listdir(src_templates):
    shutil.copy2(os.path.join(src_templates, f), os.path.join(dst_templates, f))

# Also copy templates to .agents/templates for global discovery
global_templates = ".agents/templates"
ensure_dir(global_templates)
for f in os.listdir(src_templates):
    shutil.copy2(os.path.join(src_templates, f), os.path.join(global_templates, f))

# Copy scripts
src_scripts = ".temp_inspection_repos/planning-with-files/scripts"
dst_scripts = os.path.join(dst_skill_dir, "scripts")
ensure_dir(dst_scripts)
needed_scripts = [
    "inject-plan.py", "inject-plan.ps1", "inject-plan.sh",
    "resolve-plan-dir.ps1", "resolve-plan-dir.sh",
    "check-complete.ps1", "check-complete.sh",
    "init-session.ps1", "init-session.sh",
    "set-active-plan.ps1", "set-active-plan.sh",
    "phase-status.ps1", "phase-status.sh",
    "ledger-append.ps1", "ledger-append.sh",
    "ledger-summary.ps1", "ledger-summary.sh",
    "attest-plan.ps1", "attest-plan.sh",
    "gate-stop.sh", "skill-hook.sh", "session-catchup.py"
]

for s in needed_scripts:
    sp = os.path.join(src_scripts, s)
    if os.path.exists(sp):
        shutil.copy2(sp, os.path.join(dst_scripts, s))

print("Planning-with-files skill and templates installed.")
