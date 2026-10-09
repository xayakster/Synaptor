---
name: brag-showcase
description: "Project showcase video generator and narrative storyboard creator using Brag. Transforms repositories, features, architecture, and milestones into high-impact developer demo videos, release walkthroughs, and animated product trailers. Supports narrative scripting, scene composition, Remotion/FFmpeg rendering, and local-first execution."
user-invocable: true
---

# Brag — Project Showcase Video Generator

**Upstream:** `https://github.com/latent-spaces/brag.git`  
**License:** Apache-2.0 / MIT

Brag enables developers and autonomous agents to transform codebases, release notes, and product architectures into structured developer showcase videos, launch trailers, and animated walkthroughs.

---

## ⚡ Core Capabilities

1. **Automated Narrative Scriptwriting**:
   - Analyzes codebase, README, git commits, or release notes to generate structured 30s, 60s, or 90s video scripts.
   - Narrative Structure:
     - **Hook (0-5s)**: The problem, friction, or status quo.
     - **The Solution (5-20s)**: Core value proposition and hero feature.
     - **Deep Dive / Architecture (20-45s)**: Code snippets, AST graph, or live UI demo.
     - **Benchmark / Impact (45-55s)**: Performance gains, metrics, or test coverage.
     - **Call to Action (55-60s)**: Repository link, install command, and stars.

2. **Multi-Scene Storyboard Composition**:
   - Generates deterministic `brag-out/storyboard.json` describing slide layouts, typography tokens, code highlight ranges, audio cues, and transitions.

3. **Local-First Rendering**:
   - Integrates with local Remotion / React video rendering engines or FFmpeg pipelines.
   - All assets, scripts, and rendered MP4 files remain on the local workstation inside `brag-out/`.

4. **Environment Preflight Diagnostics**:
   - Checks for Node.js, FFmpeg, and canvas dependencies before initiating render operations.

---

## 🚀 Usage & Commands

```bash
# 1. Run preflight environment check
python .agents/tools/brag/brag_preflight.py --check

# 2. Generate video script & storyboard for current project
python .agents/tools/brag/brag_preflight.py --storyboard --duration 60

# 3. Preview storyboard summary
python .agents/tools/brag/brag_preflight.py --preview

# 4. Render project showcase video (Local execution only)
python .agents/tools/brag/brag_preflight.py --render --out brag-out/showcase.mp4
```

---

## 🔒 Safety & Privacy Invariant

- **Strict Local Execution**: Video generation runs completely locally.
- **No Automatic Publishing**: The agent **MUST NEVER** upload, publish, or transmit videos, code snippets, or project metadata to external platforms or video hosting services without explicit user command and confirmation.
- **Resource Capping**: Video rendering should use bounded thread counts and CPU priority to prevent freezing developer systems.

See [.agents/rules/brag-safety.md](../../rules/brag-safety.md) for complete safety rules.
