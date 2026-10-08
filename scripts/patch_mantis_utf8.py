import os
import glob

mantis_tools = ".agents/tools/mantis"
for root, dirs, files in os.walk(mantis_tools):
    for f in files:
        if f.endswith(".py"):
            fp = os.path.join(root, f)
            with open(fp, "r", encoding="utf-8", errors="ignore") as file:
                content = file.read()
            
            # Add utf-8 stdout fix if not present
            header = """import sys, os
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
_TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
if _TOOL_DIR not in sys.path:
    sys.path.insert(0, _TOOL_DIR)
"""
            if "sys.stdout.reconfigure" not in content:
                if content.startswith("#!"):
                    parts = content.split("\n", 1)
                    new_content = parts[0] + "\n" + header + (parts[1] if len(parts) > 1 else "")
                else:
                    new_content = header + content
                with open(fp, "w", encoding="utf-8") as file:
                    file.write(new_content)

print("Mantis scripts patched for cross-platform UTF-8 output.")
