---
name: nodejs-clean-architecture
description: Clean Architecture patterns for Node.js and TypeScript backends (Domain Entities, Application Use Cases, Interface Adapters/Controllers, and Infrastructure Repositories with Dependency Inversion).
---

# Node.js Clean Architecture Patterns

This guide outlines enterprise backend design using **Clean Architecture** (Hexagonal / Ports & Adapters) principles in Node.js and TypeScript.

---

## 1. The Four Concentric Layers

```text
+-------------------------------------------------------------+
| Frameworks & Drivers (Express, Fastify, Prisma, PostgreSQL) |
|   +-----------------------------------------------------+   |
|   | Interface Adapters (Controllers, Presenters, Gateways)|  |
|   |   +---------------------------------------------+   |   |
|   |   | Application Business Rules (Use Cases)      |   |   |
|   |   |   +-------------------------------------+   |   |   |
|   |   |   | Enterprise Business Rules (Entities)|   |   |   |
|   |   |   +-------------------------------------+   |   |   |
|   |   +---------------------------------------------+   |   |
|   +-----------------------------------------------------+   |
+-------------------------------------------------------------+
               Dependency Direction: Outward → Inward
```

### Layer Responsibilities
1. **Domain Entities (`src/domain/entities/`)**: Pure business logic and data structures. No external framework dependencies (no ORM decorators, no HTTP references).
2. **Use Cases / Interactors (`src/application/use_cases/`)**: Orchestrates the flow of data to and from entities, executing specific business operations (e.g., `CreateUserUseCase`, `CheckoutOrderUseCase`).
3. **Interface Adapters (`src/adapters/controllers/`, `src/adapters/repositories/`)**: Translates data between the internal use case format and external transport/persistence formats.
4. **Infrastructure / Frameworks (`src/infrastructure/`)**: Database drivers, HTTP servers (Express/Fastify), queue listeners, cloud SDKs.

---

## 2. Directory Layout

```text
src/
├── domain/
│   ├── entities/          # User.ts, Order.ts
│   └── errors/            # DomainError.ts
├── application/
│   ├── contracts/         # IUserRepository.ts, IEmailService.ts (Ports)
│   └── use_cases/         # CreateUser.ts, AuthenticateUser.ts
├── adapters/
│   ├── controllers/       # UserController.ts
│   └── presenters/        # UserPresenter.ts
└── infrastructure/
    ├── database/          # PrismaUserRepository.ts (Adapters)
    ├── webserver/         # expressApp.ts, routes.ts
    └── config/            # env.ts
```

---

## 3. Implementation Example: Dependency Inversion

### Step 1: Port / Repository Interface (Application Layer)
```typescript
// src/application/contracts/IUserRepository.ts
import { User } from "@/domain/entities/User"

export interface IUserRepository {
  findById(id: string): Promise<User | null>
  findByEmail(email: string): Promise<User | null>
  create(user: User): Promise<User>
  update(user: User): Promise<User>
}
```

### Step 2: Use Case (Application Layer)
```typescript
// src/application/use_cases/CreateUser.ts
import { User } from "@/domain/entities/User"
import { IUserRepository } from "@/application/contracts/IUserRepository"

export class CreateUserUseCase {
  constructor(private readonly userRepository: IUserRepository) {}

  async execute(input: { username: string; email: string; passwordHash: string }): Promise<User> {
    const existing = await this.userRepository.findByEmail(input.email)
    if (existing) {
      throw new Error("Email already registered")
    }
    const user = new User(input.username, input.email, input.passwordHash)
    return await this.userRepository.create(user)
  }
}
```

### Step 3: Infrastructure Implementation (Adapter Layer)
```typescript
// src/infrastructure/database/PrismaUserRepository.ts
import { IUserRepository } from "@/application/contracts/IUserRepository"
import { User } from "@/domain/entities/User"
import { PrismaClient } from "@prisma/client"

export class PrismaUserRepository implements IUserRepository {
  constructor(private readonly prisma: PrismaClient) {}

  async findByEmail(email: string): Promise<User | null> {
    const record = await this.prisma.user.findUnique({ where: { email } })
    if (!record) return null
    return new User(record.username, record.email, record.passwordHash, record.id)
  }

  async create(user: User): Promise<User> {
    const created = await this.prisma.user.create({
      data: { username: user.username, email: user.email, passwordHash: user.passwordHash }
    })
    return new User(created.username, created.email, created.passwordHash, created.id)
  }

  async findById(id: string): Promise<User | null> { /* ... */ return null }
  async update(user: User): Promise<User> { /* ... */ return user }
}
```

---

## 4. Architectural Selection Heuristics

- **Use Clean Architecture when**: The application has complex core business domain logic, long maintenance lifespan, multiple external consumers (REST, GraphQL, CLI, gRPC), or requires testability without running live databases.
- **Avoid Clean Architecture when**: The project is a simple CRUD utility, small script, or standard prototyping Next.js app where direct Server Actions and ORM calls are far more productive.
