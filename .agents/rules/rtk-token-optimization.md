# RTK Token Optimization Rule

**Source:** `https://github.com/rtk-ai/rtk.git` (Commit: `028dfac7fa0b467ecda938e55e5ca803ef5094f0`)

## Command Execution & Context Economy

1. **Avoid Wasteful Full Dumps**:
   - Avoid executing unconstrained commands that dump hundreds or thousands of lines into the conversation context (e.g. raw `git log`, `npm test` with verbose reporter, unpaginated `find .`).
   - Use token-optimized command invocations or filter proxies where appropriate.

2. **Interpreting Condensed Outputs**:
   - Condensed output preserves exit codes and error diagnostics while eliding non-actionable boilerplate.
   - If an error occurs, inspect the focused stack trace or failure summary.
   - If deeper context is needed, query specific sub-paths or targeted test cases rather than dumping the entire suite.

3. **Fallback & Parity**:
   - If native `rtk` binary is available on PATH, leverage `rtk <command>`.
   - Otherwise, leverage the built-in python filter `.agents/tools/rtk/rtk_filter.py <command>`.
