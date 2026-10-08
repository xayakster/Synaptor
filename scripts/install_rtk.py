import os
import shutil

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

# 1. Skills
dst_skill_dir = ".agents/skills/rtk-token-killer"
ensure_dir(dst_skill_dir)

src_rtk_skills = ".temp_inspection_repos/rtk/.claude/skills"
if os.path.exists(os.path.join(src_rtk_skills, "rtk-tdd")):
    dst_tdd = ".agents/skills/rtk-tdd"
    ensure_dir(dst_tdd)
    shutil.copy2(os.path.join(src_rtk_skills, "rtk-tdd", "SKILL.md"), os.path.join(dst_tdd, "SKILL.md"))
    if os.path.exists(os.path.join(src_rtk_skills, "rtk-tdd", "references")):
        ensure_dir(os.path.join(dst_tdd, "references"))
        for f in os.listdir(os.path.join(src_rtk_skills, "rtk-tdd", "references")):
            shutil.copy2(os.path.join(src_rtk_skills, "rtk-tdd", "references", f), os.path.join(dst_tdd, "references", f))

print("RTK skills copied.")
