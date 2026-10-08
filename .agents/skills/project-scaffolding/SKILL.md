---
name: project-scaffolding
description: >-
  Standardized project scaffolding and template generation engine compatible with Cookiecutter. Use to initialize new agent-ready projects with pre-wired architecture, task planning, testing, and .agents infrastructure.
---

# Project Scaffolding & Cookiecutter Engine

**Upstream:** `https://github.com/cookiecutter/cookiecutter.git` (Commit: `c88fbe921c97c58b65f1883ba90a0ab53cc91b34`)

## Overview

The project scaffolding system allows creating new, standardized projects pre-configured with the complete Universal Agent Infrastructure (`.agents/`), file-based planning (`task_plan.md`), test runners, configuration skeletons, and frontend/backend directories.

## Capabilities

1. **Standardized Directory Structures**: Generates consistent layouts (`src/`, `tests/`, `configs/`, `scripts/`, `.agents/`).
2. **Template Variables & Cookiecutter Compatibility**: Replaces Jinja-style variables (`{{ cookiecutter.project_name }}`) in file paths and file bodies.
3. **Automated Agent Integration**: Injects the universal `.agents/` environment on-the-fly during creation without copying raw GitHub repositories.

## Usage

### 1. Scaffold a New Project
```bash
python .agents/tools/cookiecutter/project_scaffold.py --name "Finance Analytics" --type fullstack --output ./projects
```

### 2. Custom Templates
Templates reside in `.agents/templates/project-templates/`. Custom templates can define their own `cookiecutter.json` with domain-specific variables.
