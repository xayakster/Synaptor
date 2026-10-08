# Synaptor

[![CI](https://github.com/xayakster/Synaptor/actions/workflows/ci.yml/badge.svg)](https://github.com/xayakster/Synaptor/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-brightgreen)](https://www.python.org/)
[![Node Version](https://img.shields.io/badge/Node.js-18%2B%20%7C%2020%2B%20%7C%2022%2B-green)](https://nodejs.org/)
[![Tests](https://img.shields.io/badge/Tests-36%20Passing-success)](tests/)
[![Security: Hardened](https://img.shields.io/badge/Security-Hardened%20%26%20Audited-blueviolet)](SECURITY.md)

**Synaptor** is an autonomous, multi-agent neural development infrastructure designed for AI-assisted coding assistants (Claude Code, Google Antigravity, Cursor, Copilot CLI, Gemini, Codex).

By combining neural routing, persistent working memory on disk, live documentation search, and multi-domain engineering tools, Synaptor turns any AI coding assistant into a coordinated team of 63 specialized software developers.

---

## 🚀 Key Features

- **63 Specialized Subagents**: Dedicated personas for every stage of development (e.g., `tdd-guide`, `security-reviewer`, `architect`, `planner`, `code-reviewer`, `build-error-resolver`, `e2e-runner`).
- **129 Extensible Skills**: Production-ready skills covering full-stack development, API design, database migrations, security audits, AI evaluations, and performance tuning.
- **Model Context Protocol (MCP)**: Native stdio JSON-RPC integration featuring live documentation search with **Context7**, web search with **Tavily**, local databases with **SQLite**, and error diagnostics with **Sentry**.
- **Planning with Files (`PWF`)**: Persistent working memory system (`task_plan.md`, `findings.md`, `progress.md`) enabling long-running autonomous workflows across context loss and session restarts.
- **Project Scaffolding Engine**: Cookiecutter-compatible zero-dependency generator (`.agents/tools/cookiecutter/project_scaffold.py`) for instantaneous full-stack project initialization.
- **UI/UX Pro Max Intelligence**: High-performance design search engine with indexed style catalogs and design system templates.
- **GSAP Motion & Animation**: Presets, timing curves, and framework-specific patterns for React, Vue, and vanilla DOM animation.
- **Mantis Security Suite**: Autonomous security verification, threat modeling, and invariant validation architecture.
- **RTK Token Compression**: CLI proxy engine optimizing terminal command outputs by 60–90% to conserve model context.
- **Universal Lifecycle Hooks**: Event-driven contextual injection on `SessionStart`, `UserPromptSubmit`, and `PreCompact`.

---

## 🏗 Architecture Overview

```mermaid
flowchart TD
    subgraph Synaptor Core Runtime
        A[User Intent / Task Prompt] --> B[Lifecycle Hooks / planning_hook.py]
        B --> C{Agent Router & Planner}
        C --> D[63 Subagent Personas]
    end

    subgraph Core Capabilities & Skills
        D --> E[129 Specialized Skills]
        D --> F[129 Architectural Rules]
        D --> G[91 Standard Workflows]
    end

    subgraph Tooling Engines
        E --> H[Cookiecutter Scaffolder]
        E --> I[UI/UX Pro Max Search]
        E --> J[GSAP Animation Engine]
        E --> K[Mantis Security Audit]
        E --> L[RTK Output Filter]
    end

    subgraph MCP Infrastructure Layer
        D --> M{MCP Routing Gateway}
        M <-->|stdio JSON-RPC| N[Context7 Live Docs]
        M <-->|stdio JSON-RPC| O[Tavily Web Search]
        M <-->|stdio JSON-RPC| P[SQLite Engines]
        M <-->|stdio JSON-RPC| Q[Sentry Diagnostics]
    end
```

---

## 📁 Repository Structure

```text
.
├── .agents/
│   ├── agents/         # 63 Specialized Subagent Personas (tdd-guide, planner, etc.)
│   ├── skills/         # 129 Production Domain Skills (each with SKILL.md)
│   ├── rules/          # 129 Architecture, Quality & Coding Rules
│   ├── workflows/      # 91 Standard Operational Workflows
│   ├── hooks/          # Lifecycle Event Handlers & Platform Wrappers
│   ├── tools/          # Integrated Tooling (Mantis, Cookiecutter, GSAP, RTK)
│   ├── config/         # MCP Configs, Server Registry & Animation Presets
│   ├── templates/      # Project Scaffolding Templates
│   ├── manifest.json   # Machine-Readable System Manifest
│   └── MANIFEST.md     # Architectural Catalog & Changelog
├── .github/
│   └── workflows/      # GitHub Actions CI Automation
├── scripts/            # Cross-Platform Automation & Health Check Scripts
│   ├── bootstrap-agent-environment.py # One-Command Environment Initializer
│   ├── mcp-health-check.py            # Live MCP stdio Verification
│   └── security-audit-scan.py         # Static Security & Secret Scanner
├── tests/              # Comprehensive Automated Pytest Suite (36+ Tests)
├── .env.example        # Clean Environment Variable Template
├── .gitignore          # Production-Grade Multi-Category Ignore Rules
├── LICENSE             # MIT License
└── README.md           # Developer & Platform Documentation
```

---

## ⚡ Quick Start

### 1. Prerequisites
- **Python**: `3.10` or higher
- **Node.js**: `18.x`, `20.x`, or `22.x`
- **Git**: `2.30+`

### 2. Installation & Bootstrap

Clone the repository and initialize the agent environment:

```bash
git clone https://github.com/xayakster/Synaptor.git
cd Synaptor

# Run automated bootstrap
python scripts/bootstrap-agent-environment.py
```

### 3. Verify System Health

Run the automated MCP health check and security audit scanner:

```bash
# Verify Model Context Protocol (MCP) servers
python scripts/mcp-health-check.py

# Run continuous security and secret scan
python scripts/security-audit-scan.py
```

---

## 🧪 Testing

The repository includes a comprehensive automated test suite covering all 15 integrated subsystems, MCP bridges, project scaffolding, and security invariants.

```bash
# Run full automated test suite
pytest -v tests/
```

All 36+ automated tests execute in under 15 seconds with 100% pass guarantee.

---

## 🔒 Security & Privacy

- **Zero Hardcoded Credentials**: Source code and configuration templates contain strictly zero plaintext secrets.
- **Local Stdio Isolation**: MCP servers communicate locally over standard I/O child processes without external socket exposure.
- **Automated Security Gates**: All pull requests and commits are verified using `scripts/security-audit-scan.py` to prevent credential leakage.
- **Strict Data Redaction**: Diagnostics and logs automatically mask high-entropy strings (e.g., `sk-************ABCD`).

For vulnerability reporting guidelines, see [SECURITY.md](SECURITY.md).

---

## 📄 License

This project is licensed under the terms of the [MIT License](LICENSE).
