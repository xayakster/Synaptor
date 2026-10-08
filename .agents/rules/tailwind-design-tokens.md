# Tailwind CSS & Design Token Rules

## 1. Semantic Token Rule
- Always use semantic color tokens (`bg-background`, `text-foreground`, `bg-primary`, `text-muted-foreground`) rather than hardcoded raw palette colors (`bg-zinc-900`, `text-gray-500`) in application UI.
- Semantic tokens allow effortless multi-theme and dark-mode adaptation.

## 2. No @apply Component Classes
- Do not create custom CSS classes using `@apply` for UI components.
- Extract reusable JSX/TSX components (e.g., `<Button>`, `<Card>`) and style them using inline Tailwind utility strings or `cva()`.

## 3. Responsive Layout Strategy
- Build mobile-first. Default classes represent mobile viewports; use `md:` and `lg:` prefixes to scale up for tablets and desktops.
- Use CSS Grid and Flexbox utilities (`grid grid-cols-1 md:grid-cols-3 gap-6`) for structured layouts.

## 4. Dark Mode Consistency
- When implementing dark mode, configure `"class"` mode in `tailwind.config.ts`.
- Ensure text contrast meets WCAG AA (minimum 4.5:1 ratio for body text, 3:1 for large text).
