---
name: nextjs-developer
description: Modern Next.js application development guide covering App Router, React Server Components (RSC), Server Actions, Route Handlers, data fetching, caching strategies, SEO metadata, and production deployment patterns.
---

# Next.js App Router Architecture & Development Guide

This guide establishes production patterns for Next.js 14+ and 15+ using the **App Router** paradigm (`app/` directory).

---

## 1. App Router Foundations & Layout Architecture

```text
app/
├── layout.tsx         # Root layout with HTML/Body, fonts, global providers
├── page.tsx           # Home page route (/)
├── loading.tsx        # Instant loading skeleton (React Suspense)
├── error.tsx          # Client-side Error Boundary ("use client")
├── not-found.tsx      # Custom 404 page
├── global-error.tsx   # Root layout error handler
├── api/
│   └── [...]/route.ts # Route Handlers (REST endpoints)
└── dashboard/
    ├── layout.tsx     # Nested dashboard layout
    └── page.tsx       # /dashboard route
```

---

## 2. Server Components vs. Client Components

### Decision Tree
```text
Does the component need:
- React state (useState, useReducer)?
- Lifecycle / Effects (useEffect, useLayoutEffect)?
- Browser event listeners (onClick, onChange)?
- Browser APIs (localStorage, window, navigator)?
- Custom hooks depending on context?
    ├── YES -> Declare "use client" at the very top
    └── NO  -> Keep as Server Component (Default, Zero JS bundle)
```

### Best Practice: Push Leaves Down
Keep Server Components as high as possible in the component tree. Pass fetched server data down to small, focused Client Component leaves:

```tsx
// app/users/page.tsx (Server Component)
import { UserListClient } from "@/components/users/user-list-client"
import { db } from "@/lib/db"

export default async function UsersPage() {
  const users = await db.user.findMany() // Direct DB access on server
  return <UserListClient initialUsers={users} />
}
```

---

## 3. Server Actions & Mutations

Use Server Actions for form submissions, data mutations, and cache revalidations:

```typescript
// app/actions/create-post.ts
"use server"

import { revalidatePath } from "next/cache"
import { z } from "zod"
import { db } from "@/lib/db"

const CreatePostSchema = z.object({
  title: z.string().min(3).max(100),
  content: z.string().min(10),
})

export async function createPostAction(prevState: any, formData: FormData) {
  const validated = CreatePostSchema.safeParse({
    title: formData.get("title"),
    content: formData.get("content"),
  })

  if (!validated.success) {
    return { error: validated.error.flatten().fieldErrors, success: false }
  }

  try {
    await db.post.create({ data: validated.data })
    revalidatePath("/posts")
    return { success: true, error: null }
  } catch (err) {
    return { success: false, error: "Database error occurred" }
  }
}
```

---

## 4. Route Handlers (API Endpoints)

```typescript
// app/api/health/route.ts
import { NextResponse } from "next/server"

export async function GET() {
  return NextResponse.json({
    status: "ok",
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
  })
}
```

---

## 5. SEO & Dynamic Metadata

```typescript
// app/posts/[slug]/page.tsx
import type { Metadata } from "next"

type Props = { params: { slug: string } }

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const post = await getPostBySlug(params.slug)
  if (!post) return { title: "Post Not Found" }

  return {
    title: `${post.title} | Antigravity`,
    description: post.summary,
    openGraph: {
      title: post.title,
      description: post.summary,
      images: [post.ogImage],
    },
  }
}
```

---

## 6. Security Principles for Next.js

1. **Environment Variables**:
   - `NEXT_PUBLIC_*`: Exposed to client bundle. NEVER store secrets, private API keys, or database credentials here.
   - Private env vars (e.g., `DATABASE_URL`, `AUTH_SECRET`): Only accessible in Server Components, Server Actions, and Route Handlers.
2. **Server-Side Validation**: Never trust Client Component input. Always validate with Zod or standard schemas inside Server Actions and Route Handlers.
3. **Authentication Verification**: Verify session/auth token on the server before mutating data.
