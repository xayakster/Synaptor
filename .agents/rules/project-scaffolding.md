# Project Scaffolding & Architecture Rules

**Source:** `https://github.com/cookiecutter/cookiecutter.git` (Commit: `c88fbe921c97c58b65f1883ba90a0ab53cc91b34`)

## Project Creation & Structure Protocol

1. **Standardized Layout**:
   - Every new project must follow a clean, modular structure:
     - `src/` for source code
     - `tests/` for automated tests
     - `configs/` for environment/runtime configuration
     - `scripts/` for development and deployment utilities
     - `.agents/` for agent skills, rules, workflows, and hooks
     - `task_plan.md` for active persistent planning.

2. **Template Independence**:
   - Universal templates must be project-independent.
   - Avoid hardcoding machine-specific absolute paths or single-project business logic inside reusable templates.

3. **Pre-Wired Agent Infrastructure**:
   - Whenever scaffolding a new project, automatically initialize the `.agents/` environment via the bootstrap engine so the project is immediately capable of planning, testing, and token-reduced execution.
