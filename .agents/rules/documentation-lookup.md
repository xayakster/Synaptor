# Documentation Lookup Rules (Context7 MCP)

## 1. Always Resolve Before Querying
- Always call `resolve-library-id` with `libraryName` (e.g., `Next.js`) and `query` to obtain the validated `/org/project` identifier before calling `query-docs`.
- Exception: If the user explicitly provided the canonical library ID (e.g., `/vercel/next.js`).

## 2. Parameter Naming
- In `resolve-library-id`: Use `libraryName` (string) and `query` (string).
- In `query-docs`: Use `libraryId` (string) and `query` (string).

## 3. High Reputation & Benchmark Score
- When multiple library IDs are returned by `resolve-library-id`, select the one with High source reputation and highest benchmark score (closest to 100).
- If the user specified a specific version, select the matching `/org/project/version` ID.

## 4. Redact Secrets
- Strip all API keys, private tokens, passwords, and user PII from queries sent to Context7.
