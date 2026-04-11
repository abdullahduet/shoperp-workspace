# components/layout — Context

## Purpose
Top-level page shell layouts. Every page renders inside one of these layouts.

## Key Files
- AuthLayout.tsx → centered card wrapper for unauthenticated pages (login)
- AppLayout.tsx → full app shell with collapsible sidebar, header, logout, <Outlet />

## Patterns
Layouts use <Outlet /> (React Router v6) not {children} for nested routes. AppLayout reads current user via useCurrentUser hook.

## Last Updated
2026-04-11 — initial auth and app layouts
