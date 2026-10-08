---
name: backend-tech-matrix
description: Curated backend technology selection and architecture decision framework (framework comparisons, database selection, ORMs, message brokers, caching tiers, and complexity budgeting).
---

# Backend Technology Decision Matrix & Ecosystem Reference

This skill guides technology selection across backend frameworks, databases, ORMs, and message brokers without dogmatically enforcing a single stack.

---

## 1. The Stack Recommendation Process

When asked *"What stack should we use for this project?"*, execute this evaluation pipeline:

```text
1. Project Constraints & Profile
   ├── Product Type: (SaaS, Mobile API, Realtime Dashboard, Internal Tool, E-commerce)
   ├── Team & Language Skill: (TypeScript, Python, Go, Rust, Java)
   ├── Traffic Scale: (MVP < 100 RPS, Growing 1k-10k RPS, High-scale > 50k RPS)
   └── Deployment Environment: (Serverless/Vercel, Docker/Kubernetes, Dedicated VPS)

2. Stack Decision Framework
   ├── Framework Selection (Next.js App Router vs Fastify vs FastAPI vs Gin)
   ├── Database Selection (PostgreSQL vs SQLite vs MongoDB)
   ├── ORM Selection (Prisma vs Drizzle vs SQLAlchemy vs GORM)
   └── Infrastructure Tier (Redis Cache, RabbitMQ/Kafka, S3/R2 Storage)

3. Complexity Budgeting
   └── ALWAYS choose the lowest complexity stack that comfortably meets the 12-month requirements.
```

---

## 2. Standard Recommended Stack Archetypes

### Archetype A: Modern SaaS Web Application (Fastest Time-to-Market)
- **Frontend & Backend**: Next.js (App Router, React 19, Server Actions)
- **Styling & UI**: Tailwind CSS + shadcn/ui + Radix UI
- **Database**: PostgreSQL (Supabase or Neon)
- **ORM**: Prisma or Drizzle ORM
- **Auth**: NextAuth.js / Auth.js or Clerk
- **Cache / Rate Limit**: Upstash Redis

### Archetype B: High-Throughput Dedicated API / Microservice
- **Backend Framework**: Fastify (Node/TS) or FastAPI (Python) or Gin (Go)
- **Architecture**: Node.js Clean Architecture (Use Cases -> Repositories)
- **Database**: PostgreSQL with connection pooling (PgBouncer)
- **Caching & Sessions**: Redis Cluster
- **Asynchronous Work**: RabbitMQ / BullMQ worker pool

### Archetype C: Real-Time Event-Driven System
- **Event Bus / Broker**: Apache Kafka or AWS SQS
- **Backend Services**: Go / Node.js microservices
- **Database**: PostgreSQL (Relational) + ClickHouse (Analytics/Telemetry)
- **Monitoring**: OpenTelemetry + Prometheus + Grafana
