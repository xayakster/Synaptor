# Motion Animation & Reactivity Rules

**Upstream:** `https://github.com/motiondivision/motion.git`  
**Applies To:** Frontend UI development, React (`motion/react`), Vue (`motion/vue`), and DOM animation layers

---

## ⚡ Core Rules & Engineering Best Practices

### 1. Transform Over Layout
- **Always animate transform properties**: `x`, `y`, `scale`, `rotate`, `opacity`.
- **Avoid animating layout dimensions directly**: Do not animate `width`, `height`, `padding`, `margin`, `top`, `left`.
- When dimension or positional morphs are required across states or components, use the declarative `layout` or `layoutId` prop, which uses hardware-accelerated FLIP techniques under the hood.

### 2. Spring Physics Parameter Discipline
- Avoid jarring or oscillating springs. Use curated, harmonious physics configurations:
  - **Snappy Micro-interactions (Buttons/Taps)**: `{ type: "spring", stiffness: 400, damping: 25 }`
  - **Smooth Modals / Drawers**: `{ type: "spring", stiffness: 300, damping: 30 }`
  - **Subtle Layout Morphs (`layoutId`)**: `{ type: "spring", stiffness: 500, damping: 35 }`
  - **Gentle Staggers**: `{ type: "spring", stiffness: 200, damping: 20 }`

### 3. AnimatePresence & Stable Keys
- Always provide a unique and stable `key` to the direct `motion.*` child inside `<AnimatePresence>`.
- Never use array indices as `key` inside `<AnimatePresence>` for items that can be reordered or removed.
- Set `mode="wait"` or `mode="popLayout"` on `<AnimatePresence>` when switching pages or view states to avoid layout collapsing.

### 4. Layout Morph (`layoutId`) Hygiene
- Ensure `layoutId` strings are globally unique for the pair of morphing elements.
- Wrap shared element layouts in clean container boundaries with `overflow: hidden` or `border-radius` matching.

### 5. Accessibility & Motion Reduction
- Always integrate `useReducedMotion()` for motion-intensive features:
  ```tsx
  const shouldReduceMotion = useReducedMotion();
  const transition = shouldReduceMotion ? { duration: 0 } : { type: "spring", stiffness: 300, damping: 30 };
  ```
- Gracefully degrade scale and movement transforms to gentle opacity fades when reduced motion is preferred.

### 6. SSR & Hydration Safety
- In Next.js App Router (RSC) and Nuxt SSR:
  - Mark animated components with `"use client"` directive when utilizing `motion/react` hooks or event listeners.
  - Avoid rendering server-client mismatched initial style states.
