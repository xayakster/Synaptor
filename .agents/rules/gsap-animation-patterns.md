# GSAP Animation & Performance Rules

**Source:** `https://github.com/greensock/GSAP.git` (Commit: `13e2b790546426a1a2e0e9b409f3f8dc6d6611f2`, `v3.15.0`)

## Animation Discipline & Performance Rules

1. **GPU-Accelerated Properties Only**:
   - Always animate `transform` (`x`, `y`, `scale`, `rotation`) and `opacity`.
   - **NEVER** animate layout properties (`top`, `left`, `margin`, `width`, `height`, `padding`) in high-frequency loops as they cause expensive layout reflows. Use the `Flip` plugin for dimensional morphs.

2. **Clean Scope & Revert**:
   - In single-page applications (React, Vue, Svelte), always scope GSAP animations within `gsap.context()` and call `ctx.revert()` upon component unmount to avoid ghost listeners and memory leaks.

3. **Accessibility (Reduced Motion)**:
   - Always respect the user's motion preferences using `gsap.matchMedia()`:
     ```javascript
     const mm = gsap.matchMedia();
     mm.add("(prefers-reduced-motion: reduce)", () => { ... });
     ```

4. **No Arbitrary Hardcoded Delays**:
   - Use `gsap.timeline()` with relative positioning (`"+=0.2"`, `"<"`) instead of chains of arbitrary `setTimeout` or disconnected `delay` properties.
