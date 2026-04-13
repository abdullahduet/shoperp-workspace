# components/ui — Context

## Purpose
Reusable primitive UI components used across pages and layouts.

## Key Files
- LoadingSkeleton.tsx → full-page spinner for loading states
- ErrorDisplay.tsx → red error box accepting a message prop
- ProductSearchSelect.tsx → searchable autocomplete for product_id fields; exports `ProductSearchSelect` (single) and `ProductMultiSelect` (multi); integrates with RHF via Controller

## Patterns
All UI components are named exports (not default). Keep them stateless and purely presentational.
`ProductSearchSelect` and `ProductMultiSelect` are controlled components — always pair with RHF `Controller` or manage value/onChange externally.

## Last Updated
2026-04-12 — added ProductSearchSelect and ProductMultiSelect
