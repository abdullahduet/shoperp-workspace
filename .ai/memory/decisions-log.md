# Decisions Log

Agents MUST check this file before making decisions. Agents MUST update this file after making decisions.

## Format

```
### [YYYY-MM-DD] Decision Title
**Decision:** What was decided
**Reasoning:** Why
**Alternatives:** What else was considered
```

## Project-Level Decisions

### [2026-04-10] Monolithic Architecture
**Decision:** Single backend, single frontend, single database. No microservices.
**Reasoning:** Single-shop ERP. Microservices add network complexity, deployment overhead, and operational cost with zero benefit at this scale.
**Alternatives:** Microservices (rejected — overkill).

### [2026-04-10] Python/FastAPI over Node.js/NestJS
**Decision:** Python 3.12 + FastAPI for the backend.
**Reasoning:** Async-first, native Pydantic validation, automatic OpenAPI docs, stronger data processing ecosystem.
**Alternatives:** NestJS (rejected — more ceremony), Django REST (rejected — heavier).

### [2026-04-10] Prisma over SQLAlchemy
**Decision:** Prisma Client Python as the ORM.
**Reasoning:** Declarative schema, automatic migrations, type-safe queries, less boilerplate than SQLAlchemy.
**Alternatives:** SQLAlchemy (rejected — too much ceremony), raw SQL (rejected — no migration tooling).

### [2026-04-10] Money as Integers
**Decision:** All monetary values stored as integers in smallest currency unit (paisa).
**Reasoning:** Floating point causes rounding errors in financial calculations. Integer arithmetic is exact. Display layer handles formatting.
**Alternatives:** DECIMAL(12,2) (acceptable but integer is safer across all operations).

### [2026-04-10] Soft Delete
**Decision:** `deleted_at` column on all business entities. Never hard delete.
**Reasoning:** Data recovery, audit trail, referential integrity protection.
**Alternatives:** Hard delete (rejected — data loss risk).

### [2026-04-10] JWT in HTTP-Only Cookies
**Decision:** Store JWT in HTTP-only, Secure, SameSite=Lax cookies.
**Reasoning:** XSS protection — JavaScript cannot access HTTP-only cookies.
**Alternatives:** localStorage (rejected — XSS vulnerable), session-based (rejected — adds server state).
