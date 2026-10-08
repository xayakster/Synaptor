---
name: shadcn-ui
description: Reusable UI component system using Radix UI primitives, Tailwind CSS, and on-demand CLI scaffolding (npx shadcn@latest add). Use when building accessible, customizable React and Next.js user interfaces.
---

# shadcn/ui Component System & Architecture

`shadcn/ui` is not an npm component library package. It is a **component distribution and scaffolding architecture** where reusable components are copied directly into the project's source code (`components/ui/`), giving full ownership, zero runtime overhead, and total customizability.

---

## 1. Core Architecture & Philosophy

- **Ownership & Control**: Code lives directly inside your repository (`components/ui/`). You own and customize every line.
- **Accessible Primitives**: Built on top of Radix UI headless accessible primitives (WAI-ARIA compliant, full keyboard navigation, screen reader support).
- **Tailwind CSS Styling**: Styled with Tailwind utility classes and CSS variables for flexible design system tokens.
- **Variant Authority**: Component variants are structured cleanly using `class-variance-authority` (cva).
- **Class Merging**: Uses `cn()` helper (`clsx` + `tailwind-merge`) to allow effortless prop-level class overrides without specificity collisions.

---

## 2. CLI Initialization & Configuration

### Initialization Command
```bash
# Initialize shadcn/ui in a Next.js / Vite / React project
npx shadcn@latest init
```

### Configuration (`components.json`)
The `components.json` file at the project root governs component placement and theming:

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": true,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "app/globals.css",
    "baseColor": "zinc",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  }
}
```

---

## 3. On-Demand Component Installation

**Never install all 50+ components upfront.** Install only the specific components required by each feature:

```bash
# Common Essential Primitives
npx shadcn@latest add button card dialog dropdown-menu input label

# Navigation & Layout
npx shadcn@latest add tabs navigation-menu sheet separator

# Data Display & Feedback
npx shadcn@latest add table badge alert toast tooltip progress skeleton

# Form Controls
npx shadcn@latest add form select checkbox radio-group switch textarea
```

---

## 4. Class Merging Utility (`lib/utils.ts`)

Every shadcn/ui project requires the standard class merging utility:

```typescript
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

---

## 5. Component Construction Pattern (CVA)

```typescript
import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground shadow hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90",
        outline: "border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-md px-8",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
```

---

## 6. Composition with UI/UX Pro Max & GSAP

- **UI/UX Pro Max**: Provides design tokens, harmonic palettes, typography hierarchies, and component spacing decisions to configure in `globals.css` and `tailwind.config.ts`.
- **GSAP / Framer Motion**: Animate container entries, staggered lists, and dialog modals while letting shadcn/ui handle DOM structure and accessibility.
- **Client vs Server Boundaries**: Keep shadcn primitives that use React context or event handlers (`Dialog`, `DropdownMenu`, `Tabs`) as client components (`"use client"`), while wrapping them in Server Components for data fetching.
