import os
import shutil

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

src_uupm = ".temp_inspection_repos/ui-ux-pro-max-skill/.claude/skills/ui-ux-pro-max"
dst_uupm = ".agents/skills/ui-ux-pro-max"

if os.path.exists(dst_uupm):
    shutil.rmtree(dst_uupm)
ensure_dir(dst_uupm)

# 1. Copy SKILL.md
shutil.copy2(os.path.join(src_uupm, "SKILL.md"), os.path.join(dst_uupm, "SKILL.md"))

# 2. Copy data/
ensure_dir(os.path.join(dst_uupm, "data"))
shutil.copytree(os.path.join(src_uupm, "data"), os.path.join(dst_uupm, "data"), dirs_exist_ok=True)

# 3. Copy references/
ensure_dir(os.path.join(dst_uupm, "references"))
shutil.copytree(os.path.join(src_uupm, "references"), os.path.join(dst_uupm, "references"), dirs_exist_ok=True)

# 4. Copy scripts/ and ensure Windows UTF-8 stdout safety
src_scripts = os.path.join(src_uupm, "scripts")
dst_scripts = os.path.join(dst_uupm, "scripts")
ensure_dir(dst_scripts)

for f in os.listdir(src_scripts):
    if f.endswith(".py"):
        s_file = os.path.join(src_scripts, f)
        d_file = os.path.join(dst_scripts, f)
        with open(s_file, "r", encoding="utf-8", errors="ignore") as sf:
            content = sf.read()
            
        # Add UTF-8 stdout header
        header = """import sys, os
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
"""
        if "sys.stdout.reconfigure" not in content:
            if content.startswith("#!"):
                parts = content.split("\n", 1)
                new_content = parts[0] + "\n" + header + (parts[1] if len(parts) > 1 else "")
            else:
                new_content = header + content
        else:
            new_content = content
            
        with open(d_file, "w", encoding="utf-8") as df:
            df.write(new_content)

print("UI/UX Pro Max skill, data catalogs, and search scripts installed.")
