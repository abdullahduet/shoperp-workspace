# Task NNNN: [Title]

## Branch: task/NNNN-[slug]
## Assigned to: engineer
## Status: not started | in progress | in review | completed

## Context Bundle

Everything the Engineer needs is in this section. The Engineer does NOT read knowledge-base/ files.

### Schema

```sql
-- Paste exact CREATE TABLE statements needed for this task
```

### API Contract

```
| Method | Path | Description | Auth | Roles |
|--------|------|-------------|------|-------|

Request body: { field: type }
Response: { success: true, data: { ... } }
```

### Code Patterns to Follow

If prior modules exist: "Follow the exact pattern in src/modules/products/service.py"

If first module: paste the controller/service/repository pattern from coding-standards.md.

### Architecture Rules That Apply

List specific numbered rules from architecture-rules.md:
- Rule #N: [quoted rule text]

## What to Build

Specific description of what to implement. Include exact file paths:
- `src/modules/<module>/router.py`
- `src/modules/<module>/controller.py`
- etc.

## Acceptance Criteria

- [ ] Criterion 1 — specific and measurable
- [ ] Criterion 2 — specific and measurable
- [ ] Criterion 3 — specific and measurable

## Known Pitfalls

Specific things that commonly go wrong with this type of task.

## Exit Signal

The exact command that proves done:
```bash
pytest tests/unit/modules/<module>/ -v
# Expected: X passed, 0 failed
```

## Outcome (filled by Lead after merge)

What was actually built. Merge commit hash. Any deviations.
