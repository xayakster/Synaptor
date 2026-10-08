import os
import shutil

nested_dir = os.path.join(".agents", ".agents")
main_agents_dir = ".agents"

if not os.path.exists(nested_dir):
    print("Nested .agents/.agents does not exist.")
    exit(0)

# 1. Promote plugins
nested_plugins = os.path.join(nested_dir, "plugins")
main_plugins = os.path.join(main_agents_dir, "plugins")

if os.path.exists(nested_plugins):
    os.makedirs(main_plugins, exist_ok=True)
    for item in os.listdir(nested_plugins):
        s = os.path.join(nested_plugins, item)
        d = os.path.join(main_plugins, item)
        if os.path.isdir(s):
            if os.path.exists(d):
                shutil.rmtree(d)
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)
    print("Promoted plugins to .agents/plugins/")

# 2. Promote skills
nested_skills = os.path.join(nested_dir, "skills")
main_skills = os.path.join(main_agents_dir, "skills")

if os.path.exists(nested_skills):
    os.makedirs(main_skills, exist_ok=True)
    for item in os.listdir(nested_skills):
        s = os.path.join(nested_skills, item)
        d = os.path.join(main_skills, item)
        if not os.path.exists(d):
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
            print(f"Promoted new skill: {item}")
        else:
            # Already exists in outer skills
            pass
    print("Promoted all unique skills to .agents/skills/")

# 3. Remove nested .agents/.agents directory
shutil.rmtree(nested_dir)
print("Removed redundant nested directory .agents/.agents successfully.")
