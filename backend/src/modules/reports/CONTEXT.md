# reports — Context

## Purpose
Provides read-only analytical reports across sales, purchases, expenses, inventory, and profitability. All endpoints are admin/manager-only except low-stock (any authenticated user). Supports optional CSV export via `?format=csv` query param.

## Key Files
- schemas.py → Python dataclasses (not Pydantic) for all report shapes; serialised with `dataclasses.asdict()`
- repository.py → Raw DB queries only; no aggregation logic
- service.py → All aggregation, grouping, and CSV generation
- controller.py → Parse query params, call service, return JSON or CSV Response
- router.py → Route definitions with role-based auth dependencies

## Patterns
- All money values are integers (paisa). No floats.
- `_parse_datetime_range` / `_parse_date_range` helpers unify optional date parsing.
- CSV export: `service.*_to_csv(report)` returns a string; controller wraps it in `fastapi.responses.Response` with `text/csv` media type.
- `format` is a Python built-in; query param aliased as `fmt` locally to avoid shadowing.

## Last Updated
2026-04-12 — initial implementation (task/0016)
