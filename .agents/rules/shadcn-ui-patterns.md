# shadcn/ui Architectural & Usage Rules

## 1. On-Demand Installation
- **Rule**: Never install the entire shadcn component collection upfront.
- **Guideline**: Add only the specific primitives requested or needed for the active user story (e.g., `button`, `input`, `dialog`).

## 2. Component Ownership & Directory Layout
- Standard component location: `components/ui/<component-name>.tsx`
- Feature-composed components: `components/<feature>/<component-name>.tsx` (e.g., `components/auth/user-auth-form.tsx`)
- Utilities location: `lib/utils.ts` (`cn()` function)

## 3. Class Merging & Overrides
- **Always** use `cn()` when accepting a `className` prop in custom components to guarantee safe Tailwind class merging without CSS specificity bugs:
  ```typescript
  <div className={cn("base-classes", variantClasses, className)}>
  ```

## 4. Accessibility & Semantics
- Never remove ARIA attributes or Radix primitive props (e.g., `aria-describedby`, `aria-expanded`).
- Always supply accessible labels (`<Label>` or `aria-label`) for inputs and icon-only buttons.
- Preserve keyboard navigation and focus rings (`focus-visible:ring-2 focus-visible:ring-ring`).

## 5. Next.js App Router Integration
- Primitives requiring browser events or context (`DropdownMenu`, `Dialog`, `Popover`, `Select`) must declare `"use client"` at the top of the file or wrapper.
- Pure presentational primitives (`Badge`, `Separator`, `Card`) can remain Server Components if they contain no interactivity.
