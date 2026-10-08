import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

def dump_dir(path, max_files=50):
    for root, dirs, files in os.walk(path):
        rel = os.path.relpath(root, path)
        print(f"\n[DIR: {rel}]")
        for f in files[:max_files]:
            fp = os.path.join(root, f)
            print(f"  - {f} ({os.path.getsize(fp)} bytes)")

print("=== UI-UX-PRO-MAX-SKILL FILES ===")
dump_dir(".temp_inspection_repos/ui-ux-pro-max-skill")

print("\n=== GSAP FILES ===")
dump_dir(".temp_inspection_repos/gsap")
