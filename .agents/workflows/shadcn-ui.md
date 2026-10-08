# shadcn/ui Component Setup & Addition Workflow

Follow this workflow to safely initialize and add UI components to a Next.js or React application.

---

## Step 1: Preflight Verification
1. Ensure project has Tailwind CSS installed and configured (`tailwind.config.ts` or CSS variables in `globals.css`).
2. Verify TypeScript is enabled.

## Step 2: Initialize shadcn/ui
Run the CLI initialization command:
```bash
npx shadcn@latest init
```
Select:
- Style: `Default` or `New York`
- Base color: `Slate`, `Zinc`, or `Neutral`
- CSS variables: `Yes`

## Step 3: Add Required Components On-Demand
Only add the components needed for the current feature:
```bash
npx shadcn@latest add button card input form dialog
```

## Step 4: Verify Utility Function
Ensure `lib/utils.ts` exists and provides:
```typescript
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

## Step 5: Test Accessibility and Visual Rendering
- Verify focus rings are visible on keyboard Tab navigation.
- Verify color contrast in both light and dark mode.
