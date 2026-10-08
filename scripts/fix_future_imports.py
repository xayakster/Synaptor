import os
import shutil
import re

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

src_reach = ".temp_inspection_repos/agent-reach"
dst_package = ".agents/tools/agent_reach"

# Clean re-copy from original source
if os.path.exists(dst_package):
    shutil.rmtree(dst_package)
shutil.copytree(os.path.join(src_reach, "agent_reach"), dst_package)

# Function to properly insert header after __future__ imports and docstrings
def patch_file(fp):
    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    lines = content.splitlines(True)
    insert_idx = 0
    
    # Skip shebang
    if insert_idx < len(lines) and lines[insert_idx].startswith("#!"):
        insert_idx += 1
    
    # Skip encoding declaration
    if insert_idx < len(lines) and ("coding:" in lines[insert_idx] or "coding=" in lines[insert_idx]):
        insert_idx += 1
        
    # Skip top-level module docstrings
    if insert_idx < len(lines) and lines[insert_idx].strip().startswith(('"""', "'''")):
        quote = lines[insert_idx].strip()[:3]
        if lines[insert_idx].strip().endswith(quote) and len(lines[insert_idx].strip()) > 3:
            insert_idx += 1
        else:
            insert_idx += 1
            while insert_idx < len(lines):
                if quote in lines[insert_idx]:
                    insert_idx += 1
                    break
                insert_idx += 1

    # Skip __future__ imports
    while insert_idx < len(lines):
        line_str = lines[insert_idx].strip()
        if line_str.startswith("from __future__") or line_str.startswith("#") or not line_str:
            insert_idx += 1
        else:
            break

    header = """
import sys, os
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
    new_lines = lines[:insert_idx] + [header] + lines[insert_idx:]
    with open(fp, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

for root, dirs, files in os.walk(dst_package):
    for f in files:
        if f.endswith(".py"):
            patch_file(os.path.join(root, f))

# Also ensure mantis tools are patched properly with the same logic
dst_mantis = ".agents/tools/mantis"
for root, dirs, files in os.walk(dst_mantis):
    for f in files:
        if f.endswith(".py"):
            # Check if has syntax error
            fp = os.path.join(root, f)
            try:
                compile(open(fp, "r", encoding="utf-8", errors="ignore").read(), fp, 'exec')
            except SyntaxError:
                # Re-copy and patch
                rel_p = os.path.relpath(fp, dst_mantis)
                src_ref = ".temp_inspection_repos/mantis/reference"
                src_fp = os.path.join(src_ref, "core", os.path.relpath(fp, os.path.join(dst_mantis, "core"))) if "core" in rel_p else os.path.join(src_ref, rel_p)
                if os.path.exists(src_fp):
                    shutil.copy2(src_fp, fp)
                    patch_file(fp)

print("Properly patched all python packages preserving __future__ imports.")
