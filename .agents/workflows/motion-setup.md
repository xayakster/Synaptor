---
description: Set up Motion (motion/react, motion/vue, or vanilla motion) in a web project with optimal spring configs and accessible motion presets.
argument-hint: "[react | vue | vanilla | nextjs]"
---

# Motion Setup Workflow

This workflow guides the installation, configuration, and integration of Motion (`https://github.com/motiondivision/motion.git`) into web applications.

---

## 🚀 Installation by Framework

### 1. React / Next.js (App Router & Pages)
```bash
npm install motion
# Or legacy: npm install framer-motion
```

### 2. Vue 3 / Nuxt
```bash
npm install motion
```

### 3. Vanilla JavaScript / TypeScript / Vite
```bash
npm install motion
```

---

## ⚙️ Standard Presets Integration

Synaptor provides standard animation presets at `.agents/config/motion_presets.json`.

Import and use these standard tokens:
```typescript
export const MOTION_PRESETS = {
  spring: {
    snappy: { type: "spring", stiffness: 400, damping: 25 },
    smooth: { type: "spring", stiffness: 300, damping: 30 },
    gentle: { type: "spring", stiffness: 200, damping: 20 },
    bouncy: { type: "spring", stiffness: 500, damping: 15 }
  },
  fade: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 }
  },
  slideUp: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: 15 }
  }
};
```

---

## 🔍 Verification Checklist
- [ ] Ensure `"use client"` is declared at top of Next.js App Router motion components.
- [ ] Test layout animations with `layoutId` across tabs/modals.
- [ ] Test `prefers-reduced-motion` compliance.
- [ ] Confirm no high-frequency layout reflows (`width`/`height` animation in loops).
