# store — Context

## Purpose
Zustand global state stores for client-side state not managed by TanStack Query.

## Key Files
- auth.store.ts → authenticated user state (user, setUser)

## Patterns
Use Zustand v5 syntax: `create<Store>()((set) => ...)`. Server state goes in TanStack Query, not here.

## Last Updated
2026-04-11 — initial auth store
