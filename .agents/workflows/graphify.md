---
description: Build or explore an AST codebase intelligence knowledge graph with clustered architectural communities, HTML visualizer, and query tools.
argument-hint: "[--rebuild | --status | query <question> | path <source> <target>]"
---

# Graphify Workflow

This workflow uses Graphify (`https://github.com/Graphify-Labs/graphify.git`) to convert the current codebase, documents, or architecture into a navigable, clustered AST knowledge graph.

---

## ⚡ Execution Modes

### 1. Build or Rebuild Knowledge Graph
```bash
# Build / Incremental scan
python .agents/tools/graphify/graphify_runner.py .

# Force full rebuild (removes orphaned nodes from deleted/renamed files)
python .agents/tools/graphify/graphify_runner.py . --rebuild
```

### 2. Check Freshness Status
```bash
python .agents/tools/graphify/graphify_runner.py . --status
```

### 3. Query Architecture
```bash
# General architectural question
python .agents/tools/graphify/graphify_runner.py . --query "Where is authentication handled and how does it reach the database?"

# Trace dependency path between two components
python .agents/tools/graphify/graphify_runner.py . --path "src/auth/authService.ts" "src/db/usersTable.ts"

# Explain a specific hub/god node
python .agents/tools/graphify/graphify_runner.py . --explain "AppRouter"
```

---

## 🔄 Freshness Rule Reminder

Whenever Graphify is active in a project, all agents MUST automatically invoke an incremental update after any noticeable code changes before answering structural questions or completing tasks. See [.agents/rules/graphify-auto-update.md](../rules/graphify-auto-update.md).
