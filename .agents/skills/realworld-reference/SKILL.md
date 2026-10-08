---
name: realworld-reference
description: Full-stack reference specification and architectural patterns based on the RealWorld Conduit standard (REST API contracts, JWT auth, CRUD data models, frontend/backend separation).
---

# RealWorld Reference Architecture & API Specification

The **RealWorld (Conduit)** standard defines a battle-tested full-stack specification for real-world medium.com-style blogging applications. It provides reference contracts for authentication, CRUD endpoints, pagination, relationships, and error envelopes.

---

## 1. Core Data Models & Relationships

```text
User (id, email, username, bio, image, password_hash)
  │
  ├── Articles (title, slug, description, body, tagList, createdAt, updatedAt, authorId)
  │     │
  │     ├── Comments (id, body, createdAt, updatedAt, authorId, articleId)
  │     └── Favorites (userId, articleId)
  │
  └── Follows (followerId, followedUserId)
```

---

## 2. Standard REST API Endpoints & Contracts

### Authentication & Users
- `POST /api/users` — Register new user (Body: `{ "user": { "username", "email", "password" } }`)
- `POST /api/users/login` — Authenticate existing user (Returns: User object with JWT `token`)
- `GET /api/user` — Get current user profile (Header: `Authorization: Token <jwt>`)
- `PUT /api/user` — Update current user info

### Profiles & Social
- `GET /api/profiles/:username` — Get public author profile
- `POST /api/profiles/:username/follow` — Follow user
- `DELETE /api/profiles/:username/follow` — Unfollow user

### Articles & Feed
- `GET /api/articles` — Query articles (Filters: `?tag=`, `?author=`, `?favorited=`, `?limit=20&offset=0`)
- `GET /api/articles/feed` — Get authenticated user's follow feed
- `GET /api/articles/:slug` — Get single article
- `POST /api/articles` — Create article (Header: `Authorization: Token <jwt>`)
- `PUT /api/articles/:slug` — Update article
- `DELETE /api/articles/:slug` — Delete article

### Comments & Favorites
- `GET /api/articles/:slug/comments` — List comments
- `POST /api/articles/:slug/comments` — Create comment
- `DELETE /api/articles/:slug/comments/:id` — Delete comment
- `POST /api/articles/:slug/favorite` — Favorite article
- `DELETE /api/articles/:slug/favorite` — Unfavorite article

### Tags
- `GET /api/tags` — List popular tags

---

## 3. Standard Request/Response Envelopes

### Success Response Envelope (Always wrapped by entity name)
```json
{
  "article": {
    "slug": "how-to-train-your-dragon",
    "title": "How to train your dragon",
    "description": "Ever wonder how?",
    "body": "It takes a lot of patience...",
    "tagList": ["dragons", "training"],
    "createdAt": "2026-10-08T12:00:00.000Z",
    "updatedAt": "2026-10-08T12:00:00.000Z",
    "favorited": false,
    "favoritesCount": 42,
    "author": {
      "username": "hiccup",
      "bio": "Dragon rider",
      "image": "https://example.com/avatar.jpg",
      "following": false
    }
  }
}
```

### Error Response Envelope (HTTP 422 Unprocessable Entity)
```json
{
  "errors": {
    "email": ["has already been taken"],
    "password": ["is too short (minimum is 8 characters)"]
  }
}
```

---

## 4. Architectural Lessons for AI Agents

1. **Explicit API Contracts**: Always agree on request/response payloads before writing frontend or backend code.
2. **Consistent Enveloping**: Wrap payloads in entity keys (`{ "user": ... }` or `{ "data": ... }`) to avoid top-level array JSON security risks.
3. **Stateless JWT Authentication**: Pass Bearer/Token headers on protected routes, validated via middleware.
4. **Decoupled Development**: Enables frontend and backend to be developed and tested in total isolation using mock contracts.
