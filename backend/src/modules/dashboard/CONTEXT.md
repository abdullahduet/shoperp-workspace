# dashboard — Context

## Purpose
Provides two summary endpoints for the dashboard: a live summary of today's/this month's sales and profit, plus a 12-month revenue trend. Both endpoints require admin or manager role.

## Key Files
- schemas.py → `DashboardSummary` and `TrendItem` dataclasses
- repository.py → Raw DB queries for sales, expenses, and product stock
- service.py → Aggregation logic for summary and trend data
- controller.py → Thin layer calling service and returning JSON
- router.py → Route definitions with `require_roles("admin", "manager")` dependency

## Patterns
- Month profit = month revenue − month expenses (no COGS; simpler than P&L report).
- Trend sorts descending by month (most recent first).
- All money in paisa (integers).

## Last Updated
2026-04-12 — initial implementation (task/0016)
