# core — Context

## Purpose
Shared infrastructure used by all modules: typed exception hierarchy, standard response helpers. Nothing in this directory contains business logic — it is pure plumbing that enforces the project-wide API response contract.

## Key Files
- exceptions.py → Typed exception hierarchy (AppError and subclasses); raised by service layer
- responses.py → Response factory functions: success_response, paginated_response, error_response

## Patterns
- All services raise subclasses of AppError. Never raise raw exceptions for known error states.
- All controllers call success_response / paginated_response / error_response — never construct JSONResponse directly.
- error_response is also called by the global exception handler in main.py when an AppError bubbles up.

## Last Updated
2026-04-11 — initial scaffold
