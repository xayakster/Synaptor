---
name: motion-animation
description: "Declarative animation system for React (motion/react), Vue (motion/vue), and vanilla DOM using Motion (formerly Framer Motion). Covers spring physics, layout morphs (layoutId), enter/exit transitions (AnimatePresence), gestures, scroll-linked animations, and accessible motion (prefers-reduced-motion). Use when building reactive UI animations, interactive micro-interactions, layout transitions, and fluid component states."
user-invocable: true
---

# Motion — Declarative Animation Engine

**Upstream:** `https://github.com/motiondivision/motion.git`  
**License:** MIT

Motion provides a declarative, reactive animation toolkit for React, Vue, and vanilla DOM. It powers physics-based springs, fluid gesture handling, layout morphing (`layoutId`), unmount transitions (`AnimatePresence`), and scroll-driven effects.

---

## ⚡ Core Principles & Capabilities

1. **Spring Physics by Default**:
   - Animations feel natural, tactile, and interruptible with mass, stiffness, and damping.
2. **Declarative State-Driven Animation**:
   - Animate directly from component state, props, or UI status (`initial`, `animate`, `exit`).
3. **Shared Layout Morphing (`layoutId`)**:
   - Smoothly animate elements moving between different DOM positions or components without manual bounding rect calculations.
4. **Exit Animations with `AnimatePresence`**:
   - Animate elements as they are removed from the React/Vue virtual DOM tree.
5. **Interactive Gestures**:
   - `whileHover`, `whileTap`, `whileFocus`, `whileDrag`, and `whileInView`.
6. **Accessibility First**:
   - Native integration with `useReducedMotion()` to respect user motion preferences.

---

## 📦 Package Ecosystem & Imports

| Target Framework | Recommended Package | Import Syntax |
|---|---|---|
| **React (Modern)** | `motion` | `import * as motion from "motion/react"` |
| **React (Legacy)** | `framer-motion` | `import { motion, AnimatePresence } from "framer-motion"` |
| **Vue 3** | `motion` | `import { Motion } from "motion/vue"` |
| **Vanilla JS / DOM** | `motion` | `import { animate, scroll, inView } from "motion"` |
| **Lightweight Bundle** | `motion` | `import { animate } from "motion/mini"` |

---

## 🛠️ Key Patterns & Code Examples

### 1. Spring-Driven Card / Modal (React)

```tsx
import * as motion from "motion/react";
import { AnimatePresence } from "motion/react";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function Modal({ isOpen, onClose }: ModalProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="modal-backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            className="modal-content"
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 15 }}
            transition={{ type: "spring", stiffness: 350, damping: 25 }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2>Modal Dialog</h2>
            <p>Physics-based modal with smooth enter and exit transitions.</p>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
```

### 2. Shared Layout Morphing (`layoutId`)

```tsx
import * as motion from "motion/react";
import { useState } from "react";

const tabs = ["Overview", "Features", "Analytics", "Settings"];

export function TabNavigation() {
  const [selected, setSelected] = useState(tabs[0]);

  return (
    <nav className="flex gap-2">
      {tabs.map((tab) => (
        <button
          key={tab}
          onClick={() => setSelected(tab)}
          className={`relative px-4 py-2 text-sm font-medium ${
            selected === tab ? "text-white" : "text-gray-400"
          }`}
        >
          {tab}
          {selected === tab && (
            <motion.div
              layoutId="activeTabIndicator"
              className="absolute inset-0 bg-blue-600 rounded-lg -z-10"
              transition={{ type: "spring", stiffness: 500, damping: 35 }}
            />
          )}
        </button>
      ))}
    </nav>
  );
}
```

### 3. Scroll-Linked Progress & Reveal

```tsx
import * as motion from "motion/react";
import { useScroll, useSpring } from "motion/react";

export function ScrollProgressBar() {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, {
    stiffness: 100,
    damping: 30,
    restDelta: 0.001
  });

  return (
    <motion.div
      className="fixed top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 to-indigo-500 origin-left z-50"
      style={{ scaleX }}
    />
  );
}
```

### 4. Accessibility & Reduced Motion

```tsx
import * as motion from "motion/react";
import { useReducedMotion } from "motion/react";

export function AccessibleCard({ children }: { children: React.ReactNode }) {
  const shouldReduceMotion = useReducedMotion();

  const animationProps = shouldReduceMotion
    ? { initial: { opacity: 0 }, animate: { opacity: 1 } }
    : {
        initial: { opacity: 0, y: 24 },
        animate: { opacity: 1, y: 0 },
        whileHover: { scale: 1.02, y: -4 },
        transition: { type: "spring", stiffness: 400, damping: 25 }
      };

  return <motion.div {...animationProps} className="card">{children}</motion.div>;
}
```

---

## 🎯 Motion vs. GSAP Decision Matrix

| Scenario / Need | Recommended Engine | Rationale |
|---|---|---|
| **Component Enter / Exit (`AnimatePresence`)** | **Motion** | Built specifically for React/Vue lifecycle hooks. |
| **Shared Layout Morph (`layoutId`)** | **Motion** | Seamless declarative coordinate FLIP animations. |
| **Gestures (Drag, Pinch, Hover, Tap)** | **Motion** | Declarative gesture props and constraint boundaries. |
| **Complex Multi-Step Timelines** | **GSAP** | `gsap.timeline()` offers granular sub-second sequence control. |
| **Canvas / WebGL / SVG Path Morphing** | **GSAP** | GSAP MorpSVG and PixiJS plugins provide ultra-high raw performance. |
| **ScrollTrigger Pinning & Parallax Scenes** | **GSAP** | Advanced pinning, scrub, and trigger coordinate management. |
