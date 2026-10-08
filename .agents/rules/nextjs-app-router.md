# Next.js App Router Rules & Standards

## 1. Directory & Routing Architecture
- Use the `app/` directory exclusively for App Router projects.
- Colocate components inside feature directories or `@/components/` rather than cluttering route folders.
- Use `page.tsx` for route entrypoints and `layout.tsx` for persistent shell layouts.

## 2. Server vs Client Component Boundaries
- **Default to Server Components**: Do NOT add `"use client"` unless the component explicitly uses browser APIs, state (`useState`), or event handlers (`onClick`).
- **Isolate Client Components**: Keep Client Components at the leaves of the render tree to minimize client bundle size.

## 3. Data Fetching & Caching
- Fetch data directly in Server Components using `async/await` and direct ORM / database calls.
- Use Next.js extended `fetch(url, { next: { revalidate: 3600 } })` or `unstable_cache` for expensive calculations.
- Always handle loading states with `loading.tsx` and error states with `error.tsx`.

## 4. Server Actions
- Mark server action files with `"use server"` at the top.
- Validate all incoming payloads with Zod schemas.
- Revalidate paths or tags explicitly with `revalidatePath()` / `revalidateTag()`.

## 5. Security & Environment Variables
- Never expose private keys or DB credentials with the `NEXT_PUBLIC_` prefix.
- Validate authentication and user permissions inside every Server Action and Route Handler before executing database updates.
