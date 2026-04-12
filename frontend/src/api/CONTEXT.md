# api — Context

## Purpose
Axios HTTP client configuration. Single source for all HTTP requests.

## Key Files
- client.ts → Axios instance with baseURL, withCredentials, 401 interceptor

## Patterns
Import `apiClient` (default export) in service files. Never use raw fetch or axios directly.

## Last Updated
2026-04-11 — initial axios client with cookie auth
