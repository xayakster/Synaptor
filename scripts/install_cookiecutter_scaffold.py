import os
import json

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

# 1. Create templates directory
template_root = ".agents/templates/project-templates/cookiecutter-universal-project"
template_content = os.path.join(template_root, "{{cookiecutter.project_slug}}")
ensure_dir(template_content)

# cookiecutter.json
cookiecutter_json = {
    "project_name": "My Agentic App",
    "project_slug": "{{ cookiecutter.project_name.lower().replace(' ', '_').replace('-', '_') }}",
    "description": "A modern, agent-enabled project with robust architecture and automated planning.",
    "author_name": "Developer",
    "version": "0.1.0",
    "project_type": ["fullstack", "frontend", "python-agent", "api"],
    "enable_gsap": ["yes", "no"],
    "enable_planning_with_files": "yes"
}

with open(os.path.join(template_root, "cookiecutter.json"), "w", encoding="utf-8") as f:
    json.dump(cookiecutter_json, f, indent=2)

# Templated README.md
with open(os.path.join(template_content, "README.md"), "w", encoding="utf-8") as f:
    f.write("""# {{ cookiecutter.project_name }}

{{ cookiecutter.description }}

**Author:** {{ cookiecutter.author_name }}
**Version:** {{ cookiecutter.version }}
**Type:** {{ cookiecutter.project_type }}

---

## 🛠️ Project Structure

```text
├── src/                  # Source code (frontend/backend/agents)
├── tests/                # Automated test suite
├── configs/              # Environment and runtime configurations
├── scripts/              # Build and utility scripts
├── .agents/              # Universal Agent Infrastructure
└── task_plan.md          # Active file-based planning
```

## 🚀 Getting Started

1. **Activate Agent Environment**: `.agents/` is pre-wired with planning, token optimization, UI/UX intelligence, and security audits.
2. **Review Plan**: Check `task_plan.md` for active goals and milestones.
""")

# Templated task_plan.md
with open(os.path.join(template_content, "task_plan.md"), "w", encoding="utf-8") as f:
    f.write("""# {{ cookiecutter.project_name }} Task Plan

## Phase 1: Exploration & Setup
- [x] Scaffold project with universal agent architecture
- [ ] Implement core features
- [ ] Write tests and verify functionality

## Decisions & Invariants
- Pre-wired with Universal Agent Infrastructure
- Follows TDD methodology with 80%+ test coverage
""")

# Templated .gitignore
with open(os.path.join(template_content, ".gitignore"), "w", encoding="utf-8") as f:
    f.write("""node_modules/
dist/
build/
__pycache__/
*.pyc
.env
.env.local
.pytest_cache/
.coverage
""")

# Templated package.json
with open(os.path.join(template_content, "package.json"), "w", encoding="utf-8") as f:
    f.write("""{
  "name": "{{ cookiecutter.project_slug }}",
  "version": "{{ cookiecutter.version }}",
  "description": "{{ cookiecutter.description }}",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "test": "vitest run"
  }
}
""")

# Templated pyproject.toml
with open(os.path.join(template_content, "pyproject.toml"), "w", encoding="utf-8") as f:
    f.write("""[project]
name = "{{ cookiecutter.project_slug }}"
version = "{{ cookiecutter.version }}"
description = "{{ cookiecutter.description }}"
requires-python = ">=3.10"
dependencies = []

[tool.pytest.ini_options]
testpaths = ["tests"]
""")

# Templated subdirs
ensure_dir(os.path.join(template_content, "src"))
ensure_dir(os.path.join(template_content, "tests"))
ensure_dir(os.path.join(template_content, "configs"))
ensure_dir(os.path.join(template_content, "scripts"))

# Sample test file
with open(os.path.join(template_content, "tests", "test_core.py"), "w", encoding="utf-8") as f:
    f.write("""def test_smoke():
    assert True
""")

print("Cookiecutter universal project template created.")
