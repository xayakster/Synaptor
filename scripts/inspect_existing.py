import os
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

existing = {
    "rules": os.listdir(".agents/rules") if os.path.exists(".agents/rules") else [],
    "skills": os.listdir(".agents/skills") if os.path.exists(".agents/skills") else [],
    "workflows": os.listdir(".agents/workflows") if os.path.exists(".agents/workflows") else [],
    "hooks": os.listdir(".agents/hooks") if os.path.exists(".agents/hooks") else [],
}

print(f"Existing Rules ({len(existing['rules'])}):")
print(", ".join(existing["rules"]))

print(f"\nExisting Skills ({len(existing['skills'])}):")
print(", ".join(existing["skills"]))

print(f"\nExisting Workflows ({len(existing['workflows'])}):")
print(", ".join(existing["workflows"]))

print(f"\nExisting Hooks ({len(existing['hooks'])}):")
print(", ".join(existing["hooks"]))
