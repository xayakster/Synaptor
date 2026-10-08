# Backend Clean Architecture Rules

## 1. Strict Inward Dependency Rule
- Inner layers (Domain Entities and Use Cases) must never import from outer layers (Express, Fastify, Prisma, TypeORM, HTTP request objects).
- All infrastructure dependencies must be injected via interfaces (Dependency Inversion).

## 2. Decoupled Business Logic
- Business rules and validations belong in Entities (`domain/`) and Use Cases (`application/use_cases/`).
- Controllers (`adapters/controllers/`) should only parse HTTP inputs, call the use case, and format the HTTP response.

## 3. Testability Without Infrastructure
- Use cases must be 100% unit-testable using mock/in-memory repository implementations without starting a database or web server.

## 4. Complexity Matching Heuristic
- Do not impose full Clean Architecture on simple scripts or straightforward CRUD utilities.
- Use layered Clean Architecture for long-lived backends with nontrivial business domain logic.
