---
name: rtk-token-killer
description: >-
  CLI proxy and token reduction engine that filters verbose bash/shell command outputs (git diff, git status, tests, builds, linting, search) by up to 60-90% to conserve context window.
---

# RTK — Rust Token Killer

**Upstream:** `https://github.com/rtk-ai/rtk.git` (Commit: `028dfac7fa0b467ecda938e55e5ca803ef5094f0`)

## Overview

RTK sits between agent tool execution and raw shell output. By stripping redundant boilerplate, progress indicators, passing test suites, and noisy log timestamps, RTK conserves critical agent context tokens without losing diagnostic signals or exit codes.

## Usage Guide

When running terminal commands, wrap verbose commands with the RTK filter tool:

### Supported Commands
- **Git Status / Diff**:
  `python .agents/tools/rtk/rtk_filter.py git status`
  `python .agents/tools/rtk/rtk_filter.py git diff`
- **Test Runners (Pytest / Cargo / NPM / Vitest / Jest)**:
  `python .agents/tools/rtk/rtk_filter.py pytest`
  `python .agents/tools/rtk/rtk_filter.py cargo test`
  `python .agents/tools/rtk/rtk_filter.py npm test`
- **Search / Listing**:
  `python .agents/tools/rtk/rtk_filter.py ls -la`
  `python .agents/tools/rtk/rtk_filter.py find . -name "*.py"`

### Native RTK Binary Support
If the native `rtk` binary is installed on the host system (`cargo install rtk-ai` or `brew install rtk`), the filter tool automatically passes through to the high-performance native engine:
```bash
rtk git status
rtk cargo test
rtk gain --history
```

### Unfiltered Recovery Mode
If a filtered output lacks necessary nuance or debugging context, execute the raw command directly or bypass filtering:
```bash
python .agents/tools/rtk/rtk_filter.py --raw <command>
```
