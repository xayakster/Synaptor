import os
import shutil

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

src_mantis = ".temp_inspection_repos/mantis"
src_ref = os.path.join(src_mantis, "reference")

# Copy skills
dst_configure = ".agents/skills/mantis-configure"
ensure_dir(dst_configure)
shutil.copy2(os.path.join(src_ref, "skills", "mantis-configure", "SKILL.md"), os.path.join(dst_configure, "SKILL.md"))

dst_launch = ".agents/skills/mantis-launch"
ensure_dir(dst_launch)
shutil.copy2(os.path.join(src_ref, "skills", "mantis-launch", "SKILL.md"), os.path.join(dst_launch, "SKILL.md"))

# Copy tools & scripts
dst_mantis = ".agents/tools/mantis"
ensure_dir(dst_mantis)

# Copy core directory recursively
dst_core = os.path.join(dst_mantis, "core")
if os.path.exists(dst_core):
    shutil.rmtree(dst_core)
shutil.copytree(os.path.join(src_ref, "core"), dst_core)

# Copy tool files
tool_files = [
    ("tools/research_tools.py", "research_tools.py"),
    ("tools/structural_tools.py", "structural_tools.py"),
    ("tools/sandbox_tools.py", "sandbox_tools.py"),
    ("tools/__init__.py", "__init__.py"),
    ("scripts/configure.py", "configure.py"),
    ("scripts/launch.py", "launch.py"),
    ("scripts/advise.py", "advise.py"),
    ("scripts/mcp_server.py", "mcp_server.py"),
]

for src_rel, dst_rel in tool_files:
    sp = os.path.join(src_ref, src_rel)
    dp = os.path.join(dst_mantis, dst_rel)
    if os.path.exists(sp):
        shutil.copy2(sp, dp)

# Prompts
dst_prompts = os.path.join(dst_mantis, "prompts")
ensure_dir(dst_prompts)
sp_prompt = os.path.join(src_ref, "prompts", "system-researcher.md")
if os.path.exists(sp_prompt):
    shutil.copy2(sp_prompt, os.path.join(dst_prompts, "system-researcher.md"))

# Patch scripts to ensure .agents/tools/mantis is on sys.path portably
for s in ["configure.py", "launch.py", "advise.py", "mcp_server.py"]:
    script_path = os.path.join(dst_mantis, s)
    if os.path.exists(script_path):
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        path_fix = """import sys, os
_TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
if _TOOL_DIR not in sys.path:
    sys.path.insert(0, _TOOL_DIR)
"""
        if "_TOOL_DIR" not in content:
            if content.startswith("#!"):
                lines = content.split("\n", 1)
                new_content = lines[0] + "\n" + path_fix + (lines[1] if len(lines) > 1 else "")
            else:
                new_content = path_fix + content
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(new_content)

print("Mantis suite installed with full portable core package.")
