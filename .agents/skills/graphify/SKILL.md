---
name: graphify
description: "Codebase intelligence and AST knowledge graph engine. Transforms codebases, documentation, schemas, and architecture into a navigable graph with community detection, graph.json, HTML visualizer, and graph-guided query tools. Use when analyzing code relationships, architecture, dependencies, or answering structural questions."
user-invocable: true
---

# Graphify — Codebase Intelligence & Knowledge Graph Engine

**Upstream:** `https://github.com/Graphify-Labs/graphify.git`  
**License:** Apache-2.0

Graphify transforms any codebase or documentation corpus into an interactive, deterministic Abstract Syntax Tree (AST) knowledge graph with structural relationship mapping, community clustering, and graph-guided queries.

---

## ⚡ Core Capabilities

1. **Deterministic AST Knowledge Graph**:
   - Parses code relationships locally (functions, classes, modules, imports, calls, inheritance, route handlers).
   - Generates `graphify-out/graph.json`, `graphify-out/index.html`, and `graphify-out/GRAPH_REPORT.md`.
2. **Community Detection & God Nodes**:
   - Identifies high-centrality hub modules and clustered architectural domains.
3. **Graph-Guided Query & Path Traversal**:
   - `/graphify query "<question>"`: Breadth-First Search (BFS) for broad architectural context.
   - `/graphify query "<question>" --dfs`: Depth-First Search (DFS) for tracing call chains.
   - `/graphify path "<Source>" "<Target>"`: Computes shortest dependency path between components.
   - `/graphify explain "<Node>"`: Generates grounded structural explanations.
4. **Persistent On-Disk Graph Memory**:
   - Graph state persists in `graphify-out/` across agent context compactions and session restarts.

---

## 🚀 Usage & Commands

```bash
# 1. Full graph generation on current workspace
python .agents/tools/graphify/graphify_runner.py .

# 2. Incremental update (re-extract only changed/new files)
python .agents/tools/graphify/graphify_runner.py . --update

# 3. Full rebuild (clears stale nodes from deleted/renamed files)
python .agents/tools/graphify/graphify_runner.py . --rebuild

# 4. Check graph freshness & status
python .agents/tools/graphify/graphify_runner.py . --status

# 5. Query the knowledge graph
python .agents/tools/graphify/graphify_runner.py . --query "How does authentication flow to the database?"
```

---

## 🔄 Automatic Freshness Invariant

Whenever Graphify is enabled in a project, **the agent MUST automatically refresh the graph after noticeable code changes** (adding/deleting/renaming files, refactoring, modifying APIs, changing DB schemas, or completing major milestones).

See [.agents/rules/graphify-auto-update.md](../../rules/graphify-auto-update.md) for enforcement rules.

---

## 📁 Output Artifacts (`graphify-out/`)

- `graphify-out/graph.json`: Machine-readable node and edge graph.
- `graphify-out/index.html`: Interactive, visual D3/WebGL graph explorer.
- `graphify-out/GRAPH_REPORT.md`: Markdown summary of god nodes, clusters, and architectural health metrics.
- *Note: `graphify-out/` is excluded from git commits via `.gitignore` to prevent repository bloat.*
