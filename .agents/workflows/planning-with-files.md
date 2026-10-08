# /planning-with-files Workflow

Initialize, verify, or resume a persistent file-based planning environment for the current workspace.

**Source:** `https://github.com/OthmanAdi/planning-with-files.git` (v2.4.0)

## Triggers
- User types `/planning-with-files` or `/pwf`
- Complex multi-step task initialization
- Recovering session after `/clear` or context compaction

## Instructions

1. **Check Existing State**:
   - Inspect if `task_plan.md` exists in the workspace root or `.agents/plans/`.
   - If `task_plan.md` exists:
     - Read the active phase, remaining checkboxes, and blocker items.
     - Summarize current status and continue with the next open action.
   - If `task_plan.md` does not exist:
     - Choose the appropriate template from `.agents/templates/`:
       - Standard development: `task_plan.md`
       - Autonomous loops: `task_plan_autonomous.md`
       - Data / Research: `analytics_task_plan.md`
     - Initialize `task_plan.md`, `findings.md`, and `progress.md`.

2. **Execute Phase by Phase**:
   - Mark items `[x]` as they pass automated verification tests.
   - Update `progress.md` with timestamps and test outputs.
   - Append architectural discoveries to `findings.md`.

3. **Verify Completion**:
   - Ensure all acceptance criteria are met before closing the plan.
