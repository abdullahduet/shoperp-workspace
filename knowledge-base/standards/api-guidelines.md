# ShopERP — API Guidelines

## Response Format

```python
{"success": True, "data": {...}, "message": "..."}                              # Single
{"success": True, "data": [...], "pagination": {"page": 1, "limit": 20, ...}}   # List
{"success": False, "error": "...", "code": "ERROR_CODE", "details": [...]}       # Error
```

## HTTP Status Codes

| Code | When |
|------|------|
| 200 | Successful GET, PUT, DELETE |
| 201 | Successful POST (created) |
| 400 | Validation error |
| 401 | Missing/invalid auth |
| 403 | Insufficient role |
| 404 | Not found |
| 409 | Conflict (duplicate) |
| 500 | Server error |

## Pagination

Default: 20 items. Max: 100. Params: `page` (1-indexed), `limit`.

## Filtering

- `search`: partial match, case-insensitive
- Filter params: exact match (`category_id`, `status`)
- `sort`: column name. `order`: asc/desc

## Dates

API: ISO 8601 (`2024-01-15T10:30:00Z`). Range filters: `start_date`, `end_date`.

## Auth

JWT in HTTP-only cookie `access_token`. All routes except login require valid JWT.

## Validation Errors

```python
{"success": False, "error": "Validation failed", "code": "VALIDATION_ERROR",
 "details": [{"field": "name", "message": "Field required"}]}
```
