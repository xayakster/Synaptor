# Changelog

All notable changes to **Synaptor** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.2.0] - 2026-10-08

### Added
- **Public GitHub Release Finalization**: Created root `README.md`, `LICENSE` (MIT), `SECURITY.md`, `CHANGELOG.md`, and GitHub Actions CI workflow (`.github/workflows/ci.yml`).
- **Comprehensive Security Scanner**: Added `scripts/security-audit-scan.py` with multi-vector token regex detection, AST code analysis, and automated redaction.
- **Architectural Reorganization**: Dedicated `.agents/agents/` folder housing all 63 subagent personas.
- **Automated Security Tests**: Added `tests/test_security_audit_and_hardening.py`.
- **Production Readiness Audit**: Published `docs/PRODUCTION_READINESS.md`.

### Changed
- **.gitignore Hardening**: Updated `.gitignore` to protect 6 granular categories (secrets, environment, databases, caches, build output, agent state).
- **Cross-Platform Path Portability**: Replaced machine-specific user paths in `.agents/workflows/manager.md` with `%USERPROFILE%` / `$HOME`.

---

## [3.1.0] - 2026-10-08

### Added
- **Context7 Live Documentation MCP Integration**: Integrated `@upstash/context7-mcp` (v4.2.0) over stdio JSON-RPC.
- **Central MCP Registry**: Added `.agents/config/mcp_registry.json` tracking active and modular MCP servers.
- **MCP Health Check Utility**: Added `scripts/mcp-health-check.py` for automated JSON-RPC testing.
- **MCP Routing Rules**: Added `.agents/rules/mcp-routing-rules.md` and updated `documentation-lookup` skill.
- **Automated MCP Tests**: Added `tests/test_mcp_infrastructure.py`.

---

## [3.0.0] - 2026-10-08

### Added
- **Cookiecutter & Project Scaffolding**: Added zero-dependency template engine `.agents/tools/cookiecutter/project_scaffold.py` and `.agents/templates/project-templates/`.
- **UI/UX Pro Max Intelligence**: Integrated full indexed style catalogs and search engine (`.agents/skills/ui-ux-pro-max/`).
- **GSAP Animation Suite**: Integrated `.agents/skills/gsap-animation/`, animation presets `.agents/config/gsap_presets.json`, and tools.
- **Full-Stack Knowledge Integration**: Integrated comprehensive patterns for React, Next.js, Vue, Tailwind CSS, Node.js Clean Architecture, Backend Tech Matrix, and System Design Primer.

---

## [2.0.0] - 2026-10-08

### Added
- **Planning with Files (`PWF`)**: Integrated file-based working memory lifecycle (`task_plan.md`, `findings.md`, `progress.md`).
- **RTK Token Compression**: Integrated output filtering proxy to conserve model context.
- **Mantis Security Suite**: Integrated autonomous security analysis and threat modeling tools.
- **Agent-Reach Integration**: Added multi-agent coordination capabilities.
- **Universal Lifecycle Hooks**: Implemented `.agents/hooks/planning_hook.py` and platform execution wrappers.

---

## [1.0.0] - 2026-10-08

### Added
- Initial baseline `.agents` infrastructure with 63 agents, core skills, rules, and workflows.
