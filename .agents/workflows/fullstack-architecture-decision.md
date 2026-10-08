# Full-Stack Architecture Decision Workflow

Follow this structured workflow to evaluate requirements and recommend an optimal technology stack.

---

## Step 1: Requirements Intake & Questioning
Clarify:
1. **Application Purpose**: What does the product do? Who is the end-user?
2. **Traffic & Scale Targets**: Expected users, concurrency, read/write ratio.
3. **Data Shape**: Relational transactions vs unstructured documents vs time-series.
4. **Delivery Timeline**: MVP prototype (days/weeks) vs multi-year enterprise platform.

## Step 2: Query the Decision Matrix
Review candidates from `.agents/config/backend_tech_matrix.json`:
- **Full-Stack Next.js**: When rapid web UI + SSR + integrated server actions are needed.
- **Dedicated Fastify / Express / FastAPI**: When building independent backend APIs for multiple client apps.
- **PostgreSQL**: Default persistent relational store.
- **Redis**: For fast cache-aside, sessions, and rate limiting.
- **Clean Architecture**: When business logic is complex and must be decoupled from frameworks.

## Step 3: Architecture Proposal Presentation
Provide the user with a concise justification including:
- Recommended Frontend, Backend, Database, and Auth layers
- Justification based on velocity, maintainability, and scalability
- Stated trade-offs and complexity score
