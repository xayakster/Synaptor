# /scaffold-project Workflow

Create a standardized, agent-ready project with automated directory structure and `.agents/` configuration.

**Source:** `https://github.com/cookiecutter/cookiecutter.git`

## Trigger
- User invokes `/scaffold-project` or requests creating a new repository, app, or service.

## Instructions

1. **Collect Project Parameters**:
   - Project Name (e.g. `My Application`)
   - Project Type (`fullstack`, `frontend`, `python-agent`, `api`)
   - Target Output Directory (default: current directory or workspace subfolder).

2. **Run Scaffolding Engine**:
   ```bash
   python .agents/tools/cookiecutter/project_scaffold.py --name "<Project Name>" --type <type> --output <target_dir>
   ```

3. **Verify Generated Environment**:
   - Check `task_plan.md` initialization.
   - Verify `.agents/` is present and functional.
   - Run tests inside the generated project (`pytest tests/` or `npm test`).
