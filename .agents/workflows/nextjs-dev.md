# Next.js Application Development Workflow

Follow this workflow when building or expanding Next.js applications.

---

## 1. Project Initialization
```bash
npx create-next-app@latest my-app --typescript --tailwind --eslint --app --src-dir=false --import-alias="@/*"
```

## 2. Setting Up Design System & Dependencies
```bash
# Add shadcn/ui and Radix helpers
npx shadcn@latest init

# Optional animation support
npm install gsap
```

## 3. Creating Routes & Layouts
1. Define the persistent layout in `app/layout.tsx` (include font loaders, theme providers, meta tags).
2. Create feature routes under `app/<feature>/page.tsx`.
3. Create fallback `app/<feature>/loading.tsx` and `app/<feature>/error.tsx`.

## 4. Implementing Data Fetching & Mutations
- For reading: Fetch directly in Server Components.
- For writing: Create Server Actions in `app/actions/<action-name>.ts` with Zod validation and `revalidatePath()`.

## 5. Verification & Production Build Check
```bash
npm run build
npm run lint
```
Verify zero TypeScript compilation errors and clean production bundle sizes.
