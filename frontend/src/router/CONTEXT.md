# router — Context

## Purpose
React Router v6 route definitions and authentication guard.

## Key Files
- index.tsx → AppRoutes component: /login (public), / and product/category/inventory routes (protected)
- ProtectedRoute.tsx → checks useCurrentUser, redirects to /login if unauthenticated

## Patterns
Use <Outlet /> for nested route rendering. ProtectedRoute shows LoadingSkeleton while query is in flight, then redirects or renders children. Static segments (products/new, products/import) must come before dynamic segments (products/:id) to avoid conflicts.

## Last Updated
2026-04-11 — added inventory routes (inventory/movements, inventory/valuation)
