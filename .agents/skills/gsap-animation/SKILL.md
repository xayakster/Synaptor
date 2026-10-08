---
name: gsap-animation
description: >-
  High-performance frontend animation engine using GSAP (GreenSock Animation Platform) and ScrollTrigger. Use when implementing micro-interactions, hero reveals, staggered cards, page transitions, scroll-driven timelines, and responsive animations.
---

# GSAP Animation Skill

**Upstream:** `https://github.com/greensock/GSAP.git` (Commit: `13e2b790546426a1a2e0e9b409f3f8dc6d6611f2`, `v3.15.0`)

## Overview

GSAP is a high-performance, framework-agnostic JavaScript animation library. This skill guides the agent in choosing, configuring, and implementing performant animations in React, Vue, Svelte, and vanilla HTML/JS without layout thrashing.

## 1. Installation & Setup

### NPM (Recommended for bundlers: Vite, Next.js, Webpack)
```bash
npm install gsap
# Or
pnpm add gsap
# Or
yarn add gsap
```

### CDN (For standalone HTML / quick prototypes)
```html
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/ScrollTrigger.min.js"></script>
```

---

## 2. Core Architecture & Best Practices

### Registering Plugins
Always register plugins before using them:
```javascript
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { Flip } from "gsap/Flip";

gsap.registerPlugin(ScrollTrigger, Flip);
```

### Clean Lifecycle Management in React
Always use `gsap.context()` inside `useEffect` or `useLayoutEffect` to prevent memory leaks and duplicate animations:
```typescript
import { useLayoutEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

export function AnimatedCard() {
  const containerRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    const ctx = gsap.context(() => {
      gsap.from(".card", {
        y: 40,
        opacity: 0,
        duration: 0.8,
        stagger: 0.15,
        ease: "power2.out",
        scrollTrigger: {
          trigger: containerRef.current,
          start: "top 80%",
        }
      });
    }, containerRef);

    return () => ctx.revert(); // Clean up on unmount
  }, []);

  return <div ref={containerRef}>...</div>;
}
```

### Responsive & Accessible Motion
Use `gsap.matchMedia()` for responsive and reduced-motion animations:
```javascript
const mm = gsap.matchMedia();

mm.add("(prefers-reduced-motion: no-preference)", () => {
  // Full rich animations
  gsap.to(".hero-title", { y: 0, opacity: 1, duration: 1 });
});

mm.add("(prefers-reduced-motion: reduce)", () => {
  // Instant or minimal fade for accessibility
  gsap.to(".hero-title", { opacity: 1, duration: 0.2 });
});
```

---

## 3. Curated Animation Presets

See [`.agents/config/gsap_presets.json`](file:///.agents/config/gsap_presets.json) for 17 copy-pasteable animation presets including:
- Hero staggered title reveal
- Scroll scrub progress bar
- Magnetic hover button
- FLIP grid-to-modal expansion
- Interactive accordion expand/collapse
