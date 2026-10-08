# /gsap-setup Workflow

Configure GSAP and ScrollTrigger dependencies, import animation presets, and implement responsive micro-interactions.

**Source:** `https://github.com/greensock/GSAP.git`

## Trigger
- User invokes `/gsap-setup` or requests UI animations, scroll triggers, hero reveals, or micro-interactions.

## Instructions

1. **Install GSAP**:
   - For Node.js / Bundler projects:
     ```bash
     npm install gsap
     ```
   - For Vanilla HTML: Include CDN scripts in `<head>`.

2. **Select Animation Preset**:
   - Review [`.agents/config/gsap_presets.json`](file:///.agents/config/gsap_presets.json) for appropriate animation recipes (e.g. `hero_reveal`, `staggered_cards`, `scroll_scrub`, `magnetic_button`).

3. **Implement with Context Isolation**:
   - In React: Import `useGsapAnimation` helper from `.agents/tools/gsap/useGsapAnimation.ts`.
   - In Vanilla JS: Use `gsap.context()` or `gsap.timeline()`.

4. **Validate & Test**:
   - Verify 60fps smoothness without layout shifts (CLS < 0.1).
   - Test responsive layout and reduced-motion fallback.
