# health — Context

## Purpose
Single-endpoint module that exposes GET /api/health. Used as a liveness and readiness probe by Docker, load balancers, and CI pipelines. Checks that the FastAPI process is alive and that the Prisma client can reach the database. Requires no authentication.

## Key Files
- router.py → GET /health handler; executes SELECT 1 to verify DB connectivity

## Patterns
- No controller/service/repository split needed — the endpoint is trivially simple.
- Uses get_client() from src.database (not the get_db dependency) to avoid coupling to the DI system.
- Returns success_response on success, error_response with 503 on DB failure.

## Last Updated
2026-04-11 — initial scaffold
