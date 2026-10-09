---
description: Generate a project showcase video script, interactive storyboard, and developer demo trailer using Brag.
argument-hint: "[--check | --storyboard | --preview | --render]"
---

# Brag Video Showcase Workflow

This workflow guides the generation of project showcase trailers, release demos, and architecture walkthrough videos using Brag (`https://github.com/latent-spaces/brag.git`).

---

## ⚡ Workflow Steps

### Step 1: Preflight Environment Diagnostic
Check if the local workstation has the required rendering toolchains (Node.js, FFmpeg):
```bash
python .agents/tools/brag/brag_preflight.py --check
```

### Step 2: Generate Narrative Script & Storyboard
Analyze the current repository, README, and capabilities to compose a high-impact developer video script:
```bash
python .agents/tools/brag/brag_preflight.py --storyboard --duration 60
```
This generates `brag-out/storyboard.json` and `brag-out/SCRIPT.md`.

### Step 3: Review Storyboard & Scrub Secrets
Review the generated scenes:
- Slide 1: Problem Hook & Title
- Slide 2: Core Architecture & Value
- Slide 3: Code & Live Demo Highlights
- Slide 4: Performance Metrics & Benchmarks
- Slide 5: CTA & GitHub Links

*Verify that no API keys or sensitive data are included in slide snippets.*

### Step 4: Render Video (Optional / On Demand)
When confirmed, render the final MP4 video locally:
```bash
python .agents/tools/brag/brag_preflight.py --render --out brag-out/showcase.mp4
```

---

## 🔒 Safety Reminders
- Rendering is executed 100% locally.
- Do not publish or upload media files to third-party services automatically.
