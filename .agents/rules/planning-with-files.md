# File-Based Planning Protocol

**Source:** `https://github.com/OthmanAdi/planning-with-files.git` (Commit: `16e3ba895da9beae61ca55a3036eecfc51aa27d7`)

## Core Rule

Whenever engaged in complex, multi-phase tasks, migrations, long-running agent workflows, or tasks that span context resets/compaction, maintain persistent state on disk using the **Planning with Files** protocol:

1. **`task_plan.md`**: Master state tracking file containing:
   - Current Phase & Status
   - Task Goals & Acceptance Criteria
   - Work Breakdown Structure (Checklists)
   - Decision Log & Architectural Invariants
   - Active Next Actions
2. **`findings.md`**: Research findings, discoveries, codebase analysis, and environment facts.
3. **`progress.md`**: Chronological log of steps completed, verification test outcomes, and phase transitions.

## Lifecycle Discipline

- **At Session Start / Clear / Compact**: Check for existing `task_plan.md` before planning from scratch. Read and resume from the last active checkpoint.
- **Before Modifying Code**: Ensure the active task is reflected in `task_plan.md`.
- **After Completing a Step**: Update the checkbox in `task_plan.md` and record verified outputs in `progress.md`.
- **Never rely exclusively on in-memory context**: Context windows get compacted or truncated; on-disk files are permanent.
