# Graphify Automated Freshness & Maintenance Rule

**Upstream:** `https://github.com/Graphify-Labs/graphify.git`  
**Applies To:** All projects and workflows utilizing Graphify codebase intelligence

---

## ⚡ Mandatory Freshness Invariant

When Graphify is active or `graphify-out/` exists in the repository:

1. **Automatic Refresh After Code Changes**:
   - The agent **MUST** trigger an automatic graph update (`python .agents/tools/graphify/graphify_runner.py . --update`) after any noticeable code changes before concluding its turn or answering high-level architectural questions.
   - **Noticeable Code Changes Include**:
     - Addition, deletion, or renaming of source files.
     - Significant refactoring across modules or classes.
     - Introduction or modification of API routes, endpoints, or data models.
     - Database schema migrations or ORM alterations.
     - Modifications to dependencies, package manifests, or build configurations.
     - Completion of major feature milestones or bug fixes.

2. **Full Rebuild Trigger**:
   - If files were deleted, moved, or extensively renamed, an incremental update might leave orphaned or stale nodes. The agent **MUST** execute a full rebuild:
     ```bash
     python .agents/tools/graphify/graphify_runner.py . --rebuild
     ```

3. **Grounded Architectural Querying**:
   - When answering questions regarding "How does X connect to Y?", "What are the dependencies of Z?", or "Where are the architectural bottlenecks?", the agent **MUST** consult `graphify-out/graph.json` or query via the Graphify runner tool before making assertions.

4. **Zero Repository Bloat**:
   - Generated graph outputs (`graphify-out/index.html`, `graphify-out/graph.json`, `graphify-out/GRAPH_REPORT.md`) are local development artifacts and **MUST NEVER** be committed to version control. They must be ignored in `.gitignore`.
