# MCP Server Routing & Tool Selection Rules

This document establishes routing rules to ensure the AI agent selects the most accurate and token-efficient tool for every query type.

---

## 1. Tool Routing Decision Hierarchy

```text
User Question / Development Task
              │
              ├── Is it about third-party library/framework documentation, APIs, syntax, or SDK setup?
              │     └── YES ➔ Use Context7 MCP (resolve-library-id ➔ query-docs)
              │
              ├── Is it about general web information, current tech news, or external articles?
              │     └── YES ➔ Use Tavily Search MCP (or web search)
              │
              ├── Is it about inspecting local files, existing codebase symbols, or project architecture?
              │     └── YES ➔ Use Local Filesystem Tools (view_file, grep_search, list_dir)
              │
              └── Is it about checking active plans or task milestones?
                    └── YES ➔ Use Persistent File Planning (task_plan.md, findings.md, progress.md)
```

---

## 2. Server Responsibilities

| MCP Server / Tool | Primary Purpose | When to Call |
| :--- | :--- | :--- |
| **Context7 MCP** | Up-to-date framework & library documentation | When implementing or troubleshooting external packages (Next.js, Tailwind, React, Prisma, Supabase, etc.). |
| **Tavily Search MCP** | Web search and broad online research | When searching for tutorials, news, benchmarks, or broader community discussions. |
| **SQLite MCP** | Database query execution & schema inspection | When interacting with local SQLite databases. |
| **Code Sandbox MCP** | Containerized sandbox execution | When running untrusted code in an isolated Docker container. |
| **Sentry MCP** | Error tracking & incident diagnostics | When analyzing real-time exceptions and crash traces. |

---

## 3. Best Practices
1. **Never guess API parameters**: If working with a library where versions matter (e.g. React 19 vs 18, Next.js 15 vs 14), resolve the library ID via Context7 and query the exact API contract.
2. **Do not spam queries**: Limit Context7 calls to at most 3 per user request.
3. **No sensitive queries**: Never send API keys, passwords, database URLs, or customer data to external search or documentation MCPs.
