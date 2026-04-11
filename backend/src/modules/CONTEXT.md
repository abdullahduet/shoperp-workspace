# modules — Context

## Purpose
Contains one sub-package per business module (health, auth, products, etc.). Each module is self-contained: router, controller, service, repository, schemas, and its own CONTEXT.md. Modules communicate only through service layer calls — never by importing each other's repositories.

## Key Files
- health/ → Liveness/readiness probe endpoint (no auth required)

## Patterns
- Each module registers its router in src/main.py via app.include_router(router, prefix="/api").
- Module packages expose their router via __init__.py or direct import in main.py.

## Last Updated
2026-04-11 — initial scaffold
