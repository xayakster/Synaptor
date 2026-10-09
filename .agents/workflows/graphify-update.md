---
description: Refresh the Graphify AST knowledge graph after codebase modifications to ensure architectural freshness.
argument-hint: "[--rebuild]"
---

# Graphify Update Workflow

This workflow executes an incremental or full refresh of the Graphify knowledge graph (`graphify-out/graph.json` and `graphify-out/index.html`) to ensure that all downstream queries, path checks, and architectural reasoning reflect recent codebase changes.

---

## ⚡ Execution

### Incremental Refresh (Fast)
Use after editing existing files or creating new components:
```bash
python .agents/tools/graphify/graphify_runner.py . --update
```

### Full Rebuild (Clean)
Use after deleting, moving, or refactoring files to purge stale graph nodes:
```bash
python .agents/tools/graphify/graphify_runner.py . --rebuild
```

---

## 📋 Freshness Verification Checklist
1. [ ] Check that `graphify-out/graph.json` timestamp matches current modification time.
2. [ ] Verify newly added modules and exports appear in the graph.
3. [ ] Confirm dead references or deleted modules have been purged.
