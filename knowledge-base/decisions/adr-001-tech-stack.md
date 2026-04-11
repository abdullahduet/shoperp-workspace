# ADR-001: Tech Stack Selection

**Date:** 2026-04-10
**Status:** Accepted

## Context

ShopERP is a single-shop retail back-office ERP. The tech stack must balance productivity, type safety, ecosystem maturity, and hiring availability.

## Decision

### Backend: Python 3.12 + FastAPI

FastAPI provides async-first performance, automatic OpenAPI documentation, native Pydantic validation, and dependency injection. Python is the most productive language for business logic and has the strongest data ecosystem.

### ORM: Prisma Client Python

Prisma provides type-safe database access, declarative schema management, automatic migrations, and consistent query patterns. It avoids the complexity of SQLAlchemy while providing more structure than raw SQL.

### Frontend: React 18 + TypeScript + Vite

React has the largest ecosystem of UI components and patterns. TypeScript adds type safety. Vite provides fast development builds. TanStack Query handles server state caching.

### Database: PostgreSQL 16

The industry standard for relational data. Supports UUID primary keys, JSONB for flexible fields, full-text search, and advanced indexing.

### Styling: Tailwind CSS

Utility-first CSS eliminates style naming conflicts and dead CSS. Combined with shadcn/ui component patterns for consistent UI.

### Deployment: Docker + Docker Compose

Consistent environments across development and production. Single `docker compose up` for local development.

## Consequences

- Python ecosystem requires explicit type hints for safety (no compile-time checking without mypy).
- Prisma Client Python is less mature than the Node.js version. If limitations are encountered, raw SQL via Prisma's `query_raw` is the fallback.
- React requires more boilerplate than alternatives like Vue or Svelte, but the ecosystem and hiring pool compensate.

## Alternatives Considered

- **Node.js + NestJS:** Rejected. TypeScript on both sides has appeal, but Python's data processing and async capabilities are stronger for ERP business logic.
- **SQLAlchemy:** Rejected. Too much ceremony for a straightforward CRUD application. Prisma's declarative approach is more productive.
- **Django:** Rejected. Django REST Framework adds significant overhead. FastAPI is leaner and faster for API-first applications.
