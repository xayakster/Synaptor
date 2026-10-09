# Synaptor: Universal AI Agent Infrastructure

This document provides complete architectural and operational documentation for the reusable **Synaptor** AI agent environment configured in `.agents/`.

---

## 1. Executive Overview

This infrastructure provides a **universal, portable, modular, and non-destructive development system**. It integrates core capabilities, frameworks, architecture specifications, and design intelligence from **18 industry-leading open-source repositories** while preserving 100% of our pre-existing `.agents` skills, rules, hooks, and workflows.

| # | Integrated System | Upstream Source | Commit / Tag | Core Role |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **Planning with Files** | [planning-with-files](https://github.com/OthmanAdi/planning-with-files.git) | `16e3ba895da9` (`v2.4.0`) | On-disk state persistence (`task_plan.md`, `findings.md`, `progress.md`) surviving `/clear` and compaction. |
| 2 | **RTK (Rust Token Killer)** | [rtk](https://github.com/rtk-ai/rtk.git) | `028dfac7fa0b` (`v0.2.0`) | Token-saving CLI output proxy/filtering for git, test runners, linters, and search tools (60-90% savings). |
| 3 | **Google Mantis** | [mantis](https://github.com/google/mantis.git) | `db071ca1375d` | Threat modeling, structural symbol indexing, invariant verification, and patch synthesis. |
| 4 | **Agent Reach** | [Agent-Reach](https://github.com/Panniantong/Agent-Reach.git) | `94f06c1969df` | Multichannel internet data fetching (16+ channels) with privacy-safe doctor diagnostics and MCP tools. |
| 5 | **Cookiecutter** | [cookiecutter](https://github.com/cookiecutter/cookiecutter.git) | `c88fbe921c97` | Reusable project scaffolding & templating engine pre-wiring `.agents/` and tests into new projects. |
| 6 | **UI/UX Pro Max** | [ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill.git) | `1a2c459b35f2` | UI/UX design intelligence (79 styles, 192 product palettes, 74 font pairings, 119 UX guidelines, 22 stacks). |
| 7 | **GSAP Animation** | [GSAP](https://github.com/greensock/GSAP.git) | `13e2b7905464` (`v3.15.0`) | High-performance frontend animation engine and scroll-driven interaction presets. |
| 8 | **Motion** | [Motion](https://github.com/motiondivision/motion.git) | `latest` | Declarative UI animation for React (`motion/react`), Vue (`motion/vue`), spring physics, `layoutId`, and `AnimatePresence`. |
| 9 | **Graphify** | [Graphify](https://github.com/Graphify-Labs/graphify.git) | `latest` | AST codebase knowledge graph, community clustering, D3 visual explorer, and **mandatory automatic freshness updates**. |
| 10 | **Brag** | [Brag](https://github.com/latent-spaces/brag.git) | `latest` | Automated developer showcase video scripting, multi-scene storyboard generation, and local video rendering. |
| 11 | **shadcn/ui** | [shadcn-ui/ui](https://github.com/shadcn-ui/ui.git) | `0132174664c0` | Accessible Radix UI components, CVA variant authority, and on-demand CLI scaffolding (`npx shadcn@latest add`). |
| 12 | **Next.js** | [vercel/next.js](https://github.com/vercel/next.js.git) | `ea119d2702ba` | App Router architecture, Server vs Client components, Server Actions, Route Handlers, Caching, and SEO. |
| 13 | **Tailwind CSS** | [tailwindlabs/tailwindcss](https://github.com/tailwindlabs/tailwindcss.git) | `fa81d697fe57` | CSS variable design tokens, responsive layout utilities, dark mode, and avoiding `@apply` anti-patterns. |
| 14 | **RealWorld** | [realworld-apps/realworld](https://github.com/realworld-apps/realworld.git) | `ebbcdeb8d55b` | Reference REST API contracts, Conduit models, JWT auth headers, and decoupled full-stack separation. |
| 15 | **Node.js Clean Arch** | [node.js-clean-architecture](https://github.com/panagiop/node.js-clean-architecture.git) | `5248815b7612` | 4-layer concentric clean architecture (Entities -> Use Cases -> Controllers -> Repositories) with DI. |
| 16 | **System Design Primer** | [system-design-primer](https://github.com/donnemartin/system-design-primer.git) | `ae9bbd7b02d9` | System design, horizontal scaling, caching strategies (Redis), database sharding, message queues, and CAP theorem. |
| 17 | **Awesome Backend** | [awesome-backend](https://github.com/zhashkevych/awesome-backend.git) | `7d2fab346197` | Structured backend technology decision framework (`backend_tech_matrix.json`) with complexity budgeting. |
| 18 | **Context7 MCP** | [upstash/context7](https://github.com/upstash/context7.git) | `70d2433eaeb7` (`v4.2.0`) | Live documentation lookup server for libraries, frameworks, and APIs. |

---

## 2. Directory Organization

```text
.agents/
├── config/                  # Configuration profiles & schemas
│   ├── rtk_config.json
│   ├── mantis_config.json
│   ├── agent_reach_config.yaml
│   ├── gsap_presets.json
│   ├── motion_presets.json
│   ├── backend_tech_matrix.json
│   ├── mcp_registry.json
│   └── mcp_config.json
├── hooks/                   # Lifecycle hooks (SessionStart, UserPromptSubmit, PreCompact)
│   ├── hooks.json
│   ├── planning_hook.py
│   └── run_planning_hook.cmd
├── rules/                   # Agent operational and behavioral rules
│   ├── graphify-auto-update.md
│   ├── motion-animation-patterns.md
│   ├── brag-safety.md
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
│   ├── graphify/
│   ├── motion-animation/
│   ├── brag-showcase/
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
│   ├── graphify/
│   ├── brag/
│   ├── rtk/
│   ├── mantis/
│   ├── agent_reach/
│   ├── cookiecutter/
│   └── gsap/
├── workflows/               # Slash command workflows
│   ├── graphify.md
│   ├── graphify-update.md
│   ├── motion-setup.md
│   ├── brag-video.md
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
├── manifest.json            # Machine-readable integration manifest (18 systems)
├── MANIFEST.md              # Detailed component manifest
└── README.md                # .agents overview
```

---

## 3. How to Use

### A. Codebase Knowledge Graph & Freshness Invariant
```bash
# Build AST knowledge graph
python .agents/tools/graphify/graphify_runner.py .

# Check freshness & god nodes
python .agents/tools/graphify/graphify_runner.py . --status

# Query shortest dependency path
python .agents/tools/graphify/graphify_runner.py . --path "src/auth.ts" "src/db.ts"
```

### B. Declarative UI Animation & Motion
- Use `motion-animation` skill for React/Vue reactive animations, `layoutId`, gestures, and `AnimatePresence`.
- Standard presets configured in `.agents/config/motion_presets.json`.

### C. Project Showcase Video Generation
```bash
# Preflight environment check
python .agents/tools/brag/brag_preflight.py --check

# Generate storyboard and script
python .agents/tools/brag/brag_preflight.py --storyboard --duration 60

# Preview storyboard
python .agents/tools/brag/brag_preflight.py --preview
```

### D. Scaffolding a New Project
```bash
python .agents/tools/cookiecutter/project_scaffold.py --name "E-Commerce WebApp" --type nextjs-tailwind-shadcn --output ./projects
```

---

## 4. How to Copy to a New Project

To install or sync this complete 18-system environment to a new project:

```bash
# Cross-platform Python installer
python scripts/bootstrap-agent-environment.py /path/to/my-new-project
```

### Idempotency Guarantee
The bootstrap script is **100% idempotent**:
- Merges new components without deleting custom project rules or skills.
- Updates older files without corrupting local configurations.
- Validates all 18 components immediately upon completion.
