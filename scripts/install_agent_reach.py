import os
import shutil

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

src_reach = ".temp_inspection_repos/agent-reach"
dst_skill = ".agents/skills/agent-reach"
ensure_dir(dst_skill)

# 1. Copy Skill and References
src_skill = os.path.join(src_reach, "agent_reach", "skill")
shutil.copy2(os.path.join(src_skill, "SKILL.md"), os.path.join(dst_skill, "SKILL.md"))
shutil.copy2(os.path.join(src_skill, "SKILL_en.md"), os.path.join(dst_skill, "SKILL_en.md"))

dst_refs = os.path.join(dst_skill, "references")
ensure_dir(dst_refs)
src_refs = os.path.join(src_skill, "references")
if os.path.exists(src_refs):
    for f in os.listdir(src_refs):
        shutil.copy2(os.path.join(src_refs, f), os.path.join(dst_refs, f))

# 2. Copy the agent_reach Python package into .agents/tools/agent_reach
dst_package = ".agents/tools/agent_reach"
if os.path.exists(dst_package):
    shutil.rmtree(dst_package)
shutil.copytree(os.path.join(src_reach, "agent_reach"), dst_package)

# 3. Configuration & Examples
dst_config = ".agents/config"
ensure_dir(dst_config)
if os.path.exists(os.path.join(src_reach, ".env.example")):
    shutil.copy2(os.path.join(src_reach, ".env.example"), os.path.join(dst_config, "agent_reach.env.example"))

# Create default agent_reach_config.yaml
with open(os.path.join(dst_config, "agent_reach_config.yaml"), "w", encoding="utf-8") as f:
    f.write("""# Agent Reach Configuration
version: "1.0.0"
read_only_default: true
channels:
  web:
    enabled: true
  rss:
    enabled: true
  github:
    enabled: true
  twitter:
    enabled: true
  reddit:
    enabled: true
  youtube:
    enabled: true
  bilibili:
    enabled: true
  xiaohongshu:
    enabled: true
""")

# 4. Patch Python scripts in agent_reach for cross-platform utf-8 stdout safety and sys.path
for root, dirs, files in os.walk(dst_package):
    for f in files:
        if f.endswith(".py"):
            fp = os.path.join(root, f)
            with open(fp, "r", encoding="utf-8", errors="ignore") as file:
                content = file.read()
            
            header = """import sys, os
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
_PKG_PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PKG_PARENT not in sys.path:
    sys.path.insert(0, _PKG_PARENT)
"""
            if "sys.stdout.reconfigure" not in content:
                if content.startswith("#!"):
                    parts = content.split("\n", 1)
                    new_content = parts[0] + "\n" + header + (parts[1] if len(parts) > 1 else "")
                else:
                    new_content = header + content
                with open(fp, "w", encoding="utf-8") as file:
                    file.write(new_content)

print("Agent Reach components installed successfully.")
