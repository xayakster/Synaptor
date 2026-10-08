# Universal AI Agent Infrastructure

A modular, portable, and cross-platform agent environment designed to power AI coding agents, autonomous workflows, persistent planning, token-efficient command execution, security audits, multichannel internet research, project scaffolding, UI/UX intelligence, frontend animations, full-stack frameworks, styling systems, backend clean architecture, and system design intelligence across all projects.

---

## 🚀 Key Modules & Capabilities (14 Integrated Systems)

### 1. Persistent File-Based Planning (`planning-with-files`)
- **Source:** [planning-with-files](https://github.com/OthmanAdi/planning-with-files.git) (`v2.4.0`)
- **Key Files:** `skills/planning-with-files/`, `rules/planning-with-files.md`, `templates/task_plan.md`
- **What it does:** Preserves agent plan state on disk (`task_plan.md`, `findings.md`, `progress.md`) across context resets, `/clear`, and context compaction.

### 2. Token Reduction & Command Proxy (`rtk-token-killer`)
- **Source:** [rtk](https://github.com/rtk-ai/rtk.git) (`v0.2.0`)
- **Key Files:** `skills/rtk-token-killer/`, `rules/rtk-token-optimization.md`, `tools/rtk/rtk_filter.py`
- **What it does:** Strips noisy progress outputs, repetitive logs, and verbose passes from CLI commands, saving up to 60-90% context tokens.

### 3. Security Auditing & Invariant Verification (`mantis`)
- **Source:** [google/mantis](https://github.com/google/mantis.git)
- **Key Files:** `skills/mantis-security-audit/`, `skills/mantis-configure/`, `skills/mantis-launch/`, `tools/mantis/`
- **What it does:** Structural symbol indexing, threat modeling, reproducer construction, invariant checking, and verified patch synthesis.

### 4. Multichannel Internet Reach (`agent-reach`)
- **Source:** [Agent-Reach](https://github.com/Panniantong/Agent-Reach.git)
- **Key Files:** `skills/agent-reach/`, `rules/agent-reach-policy.md`, `tools/agent_reach/`
- **What it does:** Enables internet queries across 16+ platforms (Twitter/X, Reddit, GitHub, YouTube, XiaoHongShu, Bilibili, Exa search, RSS, Web).

### 5. Project Scaffolding & Template Engine (`cookiecutter`)
- **Source:** [cookiecutter](https://github.com/cookiecutter/cookiecutter.git)
- **Key Files:** `skills/project-scaffolding/`, `rules/project-scaffolding.md`, `tools/cookiecutter/`, `templates/project-templates/`
- **What it does:** Generates standardized, agent-ready projects pre-wired with `.agents/`, `task_plan.md`, configurations, tests, and source directories.

### 6. UI/UX Design Intelligence (`ui-ux-pro-max`)
- **Source:** [ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill.git)
- **Key Files:** `skills/ui-ux-pro-max/`, `rules/ui-ux-pro-max.md`, `skills/ui-ux-pro-max/scripts/search.py`
- **What it does:** 79 searchable styles, 192 product reasoning profiles, 74 font pairings, 119 UX guidelines, 25 chart types, and 22 technology stack profiles.

### 7. High-Performance Frontend Animation (`gsap-animation`)
- **Source:** [GSAP](https://github.com/greensock/GSAP.git) (`v3.15.0`)
- **Key Files:** `skills/gsap-animation/`, `rules/gsap-animation-patterns.md`, `config/gsap_presets.json`, `tools/gsap/`
- **What it does:** Animation presets, ScrollTrigger recipes, React context wrappers, responsive motion with `matchMedia()`, and reduced-motion accessibility.

### 8. Accessible UI Component System (`shadcn-ui`)
- **Source:** [shadcn-ui/ui](https://github.com/shadcn-ui/ui.git)
- **Key Files:** `skills/shadcn-ui/`, `rules/shadcn-ui-patterns.md`, `workflows/shadcn-ui.md`
- **What it does:** On-demand component scaffolding (`npx shadcn@latest add`), Radix UI headless accessible primitives, and CVA variant styling.

### 9. Modern App Router Framework (`nextjs-developer`)
- **Source:** [vercel/next.js](https://github.com/vercel/next.js.git)
- **Key Files:** `skills/nextjs-developer/`, `rules/nextjs-app-router.md`, `workflows/nextjs-dev.md`
- **What it does:** App Router layout architecture, Server vs Client Component boundaries, Server Actions, Route Handlers, Caching, and SEO metadata.

### 10. Design Token & Utility Styling (`tailwind-patterns`)
- **Source:** [tailwindlabs/tailwindcss](https://github.com/tailwindlabs/tailwindcss.git)
- **Key Files:** `skills/tailwind-patterns/`, `rules/tailwind-design-tokens.md`
- **What it does:** Semantic CSS variable design tokens, responsive layout utilities, dark mode theming, and avoiding `@apply` anti-patterns.

### 11. Full-Stack Reference Architecture (`realworld-reference`)
- **Source:** [realworld-apps/realworld](https://github.com/realworld-apps/realworld.git)
- **Key Files:** `skills/realworld-reference/`
- **What it does:** REST API contracts, Conduit data models, JWT authentication headers, standard request/response envelopes, and decoupled frontend/backend testing.

### 12. Backend Clean Architecture (`nodejs-clean-architecture`)
- **Source:** [panagiop/node.js-clean-architecture](https://github.com/panagiop/node.js-clean-architecture.git)
- **Key Files:** `skills/nodejs-clean-architecture/`, `rules/backend-clean-architecture.md`
- **What it does:** 4-layer concentric clean architecture (Entities -> Use Cases -> Controllers -> Repositories) and Dependency Inversion.

### 13. System Design & Scalability Knowledge (`system-design-primer`)
- **Source:** [donnemartin/system-design-primer](https://github.com/donnemartin/system-design-primer.git)
- **Key Files:** `skills/system-design-primer/`, `rules/system-design-principles.md`, `workflows/system-design.md`
- **What it does:** Horizontal scaling, load balancing (L4/L7), caching strategies (Redis), database sharding/replication, message queues (Kafka/RabbitMQ), and CAP theorem trade-offs.

### 14. Backend Technology Decision Matrix (`backend-tech-matrix`)
- **Source:** [zhashkevych/awesome-backend](https://github.com/zhashkevych/awesome-backend.git)
- **Key Files:** `skills/backend-tech-matrix/`, `config/backend_tech_matrix.json`, `workflows/fullstack-architecture-decision.md`
- **What it does:** Curated technology evaluation framework comparing backend frameworks, databases, ORMs, and message brokers with complexity budgeting.

---

## 🛠️ Usage & Workflows

| Workflow / Tool | Command | Description |
| :--- | :--- | :--- |
| **File Planning** | `/planning-with-files` | Initialize or resume on-disk task plan |
| **RTK Optimization** | `/rtk-optimize` | Run command with token reduction proxy |
| **Security Scan** | `/mantis-scan` | Run autonomous security review & preflight |
| **Internet Reach** | `/agent-reach` | Run multi-channel internet query / doctor |
| **Scaffold Project** | `/scaffold-project` | Generate new standardized project structure |
| **UI/UX Intelligence** | `/ui-ux-pro-max` | Search design styles, colors, fonts & UX rules |
| **GSAP Animations** | `/gsap-setup` | Configure GSAP & apply animation presets |
| **shadcn/ui Setup** | `/shadcn-ui` | On-demand component addition & theming |
| **Next.js Dev** | `/nextjs-dev` | App Router project initialization & development |
| **System Design** | `/system-design` | Scalability & distributed architecture planning |
| **Architecture Decision** | `/fullstack-architecture-decision` | Evaluate requirements & select optimal stack |
| **Bootstrap Sync** | `python scripts/bootstrap-agent-environment.py` | Sync / portable install to a new project |

---

## 📦 Copying to a New Project

To equip any new project with this agent infrastructure:
```bash
# Using Python
python scripts/bootstrap-agent-environment.py /path/to/my-new-project

# Using PowerShell
.\scripts\bootstrap.ps1 -TargetPath C:\path\to\my-new-project

# Using Bash
./scripts/bootstrap.sh /path/to/my-new-project
```
