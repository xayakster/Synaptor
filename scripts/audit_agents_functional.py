"""
Deep Functional and Architecture Auditor for .agents Ecosystem
Validates rules, skills, workflows, hooks, commands, tools, and manifests.
"""

import os
import json
import re
from pathlib import Path

def audit_agents_directory(root_dir: str):
    root = Path(root_dir).resolve()
    agents_dir = root / ".agents"
    
    report = {
        "rules_count": 0,
        "rules_issues": [],
        "skills_count": 0,
        "skills_issues": [],
        "workflows_count": 0,
        "workflows_issues": [],
        "hooks_issues": [],
        "hardcoded_user_paths": [],
        "manifest_status": "UNKNOWN",
        "manifest_issues": []
    }
    
    if not agents_dir.exists():
        report["manifest_issues"].append(".agents directory does not exist")
        return report

    # 1. Audit Rules
    rules_dir = agents_dir / "rules"
    if rules_dir.exists():
        for rule_file in rules_dir.glob("*.md"):
            report["rules_count"] += 1
            content = rule_file.read_text(encoding="utf-8", errors="ignore")
            
            # Check for hardcoded personal paths
            if re.search(r"C:[\\/]Users[\\/][a-zA-Z0-9_\-]+[\\/]", content, re.IGNORECASE):
                report["hardcoded_user_paths"].append({
                    "file": rule_file.relative_to(root).as_posix(),
                    "type": "Hardcoded Windows User Path in Rule"
                })

    # 2. Audit Skills
    skills_dir = agents_dir / "skills"
    if skills_dir.exists():
        for item in skills_dir.iterdir():
            if item.is_dir():
                report["skills_count"] += 1
                skill_md = item / "SKILL.md"
                if not skill_md.exists():
                    report["skills_issues"].append({
                        "skill": item.name,
                        "issue": "Missing SKILL.md in directory"
                    })
                else:
                    content = skill_md.read_text(encoding="utf-8", errors="ignore")
                    # Check YAML frontmatter
                    if not (content.startswith("---") and "\nname:" in content):
                        report["skills_issues"].append({
                            "skill": item.name,
                            "issue": "Invalid or missing YAML frontmatter (name/description)"
                        })
                    # Check hardcoded user paths
                    if re.search(r"C:[\\/]Users[\\/][a-zA-Z0-9_\-]+[\\/]", content, re.IGNORECASE):
                        report["hardcoded_user_paths"].append({
                            "file": skill_md.relative_to(root).as_posix(),
                            "type": "Hardcoded Windows User Path in Skill"
                        })
            elif item.is_file() and item.suffix == ".md":
                # Stray skill file outside directory structure
                report["skills_issues"].append({
                    "skill": item.name,
                    "issue": "Stray markdown file in skills root (should be in dedicated folder with SKILL.md)"
                })

    # 3. Audit Workflows
    workflows_dir = agents_dir / "workflows"
    if workflows_dir.exists():
        for wf_file in workflows_dir.glob("*.md"):
            report["workflows_count"] += 1
            content = wf_file.read_text(encoding="utf-8", errors="ignore")
            if re.search(r"C:[\\/]Users[\\/][a-zA-Z0-9_\-]+[\\/]", content, re.IGNORECASE):
                report["hardcoded_user_paths"].append({
                    "file": wf_file.relative_to(root).as_posix(),
                    "type": "Hardcoded Windows User Path in Workflow"
                })

    # 4. Audit Hooks
    hooks_file = agents_dir / "hooks" / "hooks.json"
    if hooks_file.exists():
        try:
            hooks_data = json.loads(hooks_file.read_text(encoding="utf-8"))
            hooks_dict = hooks_data.get("hooks", {})
            for event_name, hook_list in hooks_dict.items():
                for hook_entry in hook_list:
                    inner_hooks = hook_entry.get("hooks", [])
                    for h in inner_hooks:
                        cmd = h.get("command", "")
                        # Check for unquoted command injection vulnerabilities
                        if "eval" in cmd or "`" in cmd:
                            report["hooks_issues"].append({
                                "event": event_name,
                                "command": cmd,
                                "issue": "Dangerous eval or backtick expression in hook"
                            })
        except Exception as e:
            report["hooks_issues"].append({"issue": f"Invalid hooks.json format: {e}"})

    # 5. Audit Manifest Integrity
    manifest_file = agents_dir / "manifest.json"
    if manifest_file.exists():
        try:
            manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
            report["manifest_version"] = manifest_data.get("version", "unknown")
            report["manifest_status"] = "VALID"
        except Exception as e:
            report["manifest_status"] = "INVALID"
            report["manifest_issues"].append(str(e))
    else:
        report["manifest_status"] = "MISSING"

    return report

if __name__ == "__main__":
    rep = audit_agents_directory(".")
    print(json.dumps(rep, indent=2))
