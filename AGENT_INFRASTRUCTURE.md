# Synaptor: Universal AI Agent Infrastructure

This document provides complete architectural and operational documentation for the reusable **Synaptor** AI agent environment configured in `.agents/`.

---

## 1. Executive Overview

This infrastructure provides a **universal, portable, modular, and non-destructive development system**. It integrates core capabilities, frameworks, architecture specifications, and design intelligence from **14 industry-leading open-source repositories** while preserving 100% of our pre-existing `.agents` skills, rules, hooks, and workflows.

| # | Integrated System | Upstream Source | Commit / Tag | Core Role |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **Planning with Files** | [planning-with-files](https://github.com/OthmanAdi/planning-with-files.git) | `16e3ba895da9` (`v2.4.0`) | On-disk state persistence (`task_plan.md`, `findings.md`, `progress.md`) surviving `/clear` and compaction. |
| 2 | **RTK (Rust Token Killer)** | [rtk](https://github.com/rtk-ai/rtk.git) | `028dfac7fa0b` (`v0.2.0`) | Token-saving CLI output proxy/filtering for git, test runners, linters, and search tools (60-90% savings). |
| 3 | **Google Mantis** | [mantis](https://github.com/google/mantis.git) | `db071ca1375d` | Threat modeling, structural symbol indexing, invariant verification, and patch synthesis. |
| 4 | **Agent Reach** | [Agent-Reach](https://github.com/Panniantong/Agent-Reach.git) | `94f06c1969df` | Multichannel internet data fetching (16+ channels) with privacy-safe doctor diagnostics and MCP tools. |
| 5 | **Cookiecutter** | [cookiecutter](https://github.com/cookiecutter/cookiecutter.git) | `c88fbe921c97` | Reusable project scaffolding & templating engine pre-wiring `.agents/` and tests into new projects. |
| 6 | **UI/UX Pro Max** | [ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill.git) | `1a2c459b35f2` | UI/UX design intelligence (79 styles, 192 product palettes, 74 font pairings, 119 UX guidelines, 22 stacks). |
| 7 | **GSAP Animation** | [GSAP](https://github.com/greensock/GSAP.git) | `13e2b7905464` (`v3.15.0`) | High-performance frontend animation engine and scroll-driven interaction presets. |
| 8 | **shadcn/ui** | [shadcn-ui/ui](https://github.com/shadcn-ui/ui.git) | `0132174664c0` | Accessible Radix UI components, CVA variant authority, and on-demand CLI scaffolding (`npx shadcn@latest add`). |
| 9 | **Next.js** | [vercel/next.js](https://github.com/vercel/next.js.git) | `ea119d2702ba` | App Router architecture, Server vs Client components, Server Actions, Route Handlers, Caching, and SEO. |
| 10 | **Tailwind CSS** | [tailwindlabs/tailwindcss](https://github.com/tailwindlabs/tailwindcss.git) | `fa81d697fe57` | CSS variable design tokens, responsive layout utilities, dark mode, and avoiding `@apply` anti-patterns. |
| 11 | **RealWorld** | [realworld-apps/realworld](https://github.com/realworld-apps/realworld.git) | `ebbcdeb8d55b` | Reference REST API contracts, Conduit models, JWT auth headers, and decoupled full-stack separation. |
| 12 | **Node.js Clean Arch** | [node.js-clean-architecture](https://github.com/panagiop/node.js-clean-architecture.git) | `5248815b7612` | 4-layer concentric clean architecture (Entities -> Use Cases -> Controllers -> Repositories) with DI. |
| 13 | **System Design Primer** | [system-design-primer](https://github.com/donnemartin/system-design-primer.git) | `ae9bbd7b02d9` | System design, horizontal scaling, caching strategies (Redis), database sharding, message queues, and CAP theorem. |
| 14 | **Awesome Backend** | [awesome-backend](https://github.com/zhashkevych/awesome-backend.git) | `7d2fab346197` | Structured backend technology decision framework (`backend_tech_matrix.json`) with complexity budgeting. |

---

## 2. Directory Organization

```text
.agents/
├── config/                  # Configuration profiles & schemas
│   ├── rtk_config.json
│   ├── mantis_config.json
│   ├── agent_reach_config.yaml
│   ├── gsap_presets.json
│   └── backend_tech_matrix.json
├── hooks/                   # Lifecycle hooks (SessionStart, UserPromptSubmit, PreCompact)
│   ├── hooks.json
│   ├── planning_hook.py
│   └── run_planning_hook.cmd
├── rules/                   # Agent operational and behavioral rules
│   ├── planning-with-files.md
│   ├── rtk-token-optimization.md
│   ├── mantis-security-standards.md
│   ├── agent-reach-policy.md
│   ├── project-scaffolding.md
│   ├── ui-ux-pro-max.md
│   ├── gsap-animation-patterns.md
│   ├── shadcn-ui-patterns.md
│   ├── nextjs-app-router.md
│   ├── tailwind-design-tokens.md
│   ├── backend-clean-architecture.md
│   ├── system-design-principles.md
│   └── [Preserved 115 rules]
├── skills/                  # Autonomous domain capability skills
│   ├── planning-with-files/
│   ├── rtk-token-killer/
│   ├── rtk-tdd/
│   ├── mantis-security-audit/
│   ├── mantis-configure/
│   ├── mantis-launch/
│   ├── agent-reach/
│   ├── project-scaffolding/
│   ├── ui-ux-pro-max/
│   ├── gsap-animation/
│   ├── shadcn-ui/
│   ├── nextjs-developer/
│   ├── tailwind-patterns/
│   ├── realworld-reference/
│   ├── nodejs-clean-architecture/
│   ├── system-design-primer/
│   ├── backend-tech-matrix/
│   └── [Preserved 175 skills]
├── templates/               # Standardized templates
│   ├── task_plan.md
│   └── project-templates/
│       └── cookiecutter-universal-project/
├── tools/                   # Portable runtime engines and packages
│   ├── rtk/
│   ├── mantis/
│   ├── agent_reach/
│   ├── cookiecutter/
│   └── gsap/
├── workflows/               # Slash command workflows
│   ├── planning-with-files.md
│   ├── rtk-optimize.md
│   ├── mantis-scan.md
│   ├── agent-reach.md
│   ├── scaffold-project.md
│   ├── ui-ux-pro-max.md
│   ├── gsap-setup.md
│   ├── shadcn-ui.md
│   ├── nextjs-dev.md
│   ├── system-design.md
│   ├── fullstack-architecture-decision.md
│   └── [Preserved 80 workflows]
├── manifest.json            # Machine-readable integration manifest (14 systems)
├── MANIFEST.md              # Detailed component manifest
└── README.md                # .agents overview
```

---

## 3. How to Use

### A. Answering "What stack should we use for this project?"
```markdown
/fullstack-architecture-decision
```
Evaluates project constraints against `.agents/config/backend_tech_matrix.json` and recommends an optimal, lowest-complexity stack.

### B. Developing Next.js & UI Components
```bash
# Initialize Next.js project
npx create-next-app@latest my-app --typescript --tailwind --app

# Initialize shadcn/ui
npx shadcn@latest init

# Add components on demand
npx shadcn@latest add button card dialog input
```

### C. Backend Clean Architecture & System Design
- Consult `.agents/skills/nodejs-clean-architecture/` for concentric layers (Entities -> Use Cases -> Repositories).
- Consult `.agents/skills/realworld-reference/` for REST API contracts and authentication headers.
- Consult `.agents/skills/system-design-primer/` for capacity estimation, Redis caching tiers, and database sharding.

### D. Scaffolding a New Project
```bash
python .agents/tools/cookiecutter/project_scaffold.py --name "E-Commerce WebApp" --type nextjs-tailwind-shadcn --output ./projects
```

---

## 4. How to Copy to a New Project

To install or sync this complete 14-system environment to a new project:

```bash
# Cross-platform Python installer
python scripts/bootstrap-agent-environment.py /path/to/my-new-project

# Windows PowerShell
.\scripts\bootstrap.ps1 -TargetPath C:\path\to\my-new-project

# Linux / macOS Bash
./scripts/bootstrap.sh /path/to/my-new-project
```

### Idempotency Guarantee
The bootstrap script is **100% idempotent**:
- It merges new components without deleting custom project rules or skills.
- It updates older files without corrupting local configurations.
- It validates all 14 components immediately upon completion.
