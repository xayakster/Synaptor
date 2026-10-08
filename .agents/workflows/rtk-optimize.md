# /rtk-optimize Workflow

Optimize agent command execution, measure token savings, and configure command output filters.

**Source:** `https://github.com/rtk-ai/rtk.git`

## Usage
Run `/rtk-optimize` or use when auditing agent token efficiency across test and build commands.

## Actions
1. **Check RTK Availability**:
   - Check if native `rtk` binary is present on system PATH (`rtk --version`).
   - If not installed, confirm Python filter `.agents/tools/rtk/rtk_filter.py` is ready.
2. **Execute Token-Filtered Command**:
   - Run tests/builds via `python .agents/tools/rtk/rtk_filter.py <command>`
   - Verify that pass/fail status is preserved while extraneous output is trimmed.
3. **Display Token Metrics**:
   - Calculate raw output tokens vs filtered output tokens.
   - Report token economy metrics.
