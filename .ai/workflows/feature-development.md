# Workflow: Feature Development

## For adding a feature to an existing module.

## Handoff Sequence

```
USER requests feature → TECH LEAD (designs, creates Task File)
  → ENGINEER (implements)
  → QA REVIEWER (reviews + tests)
  → TECH LEAD (merges)
```

## Tech Lead Responsibilities

1. Check if the feature requires schema changes. If yes, design the migration first.
2. Check if the feature requires new API endpoints. If yes, design them first.
3. Update knowledge-base architecture files with new designs.
4. Create Task File with Context Bundle including both existing and new specs.
5. If the change is trivial (add a filter, rename a field): create a minimal Task File with just the delta.

## Small Feature Shortcut

If the change is under 20 lines of code and touches only one file:
- Tech Lead can spawn Engineer with a one-line instruction instead of a full Task File.
- QA Reviewer still verifies. The shortcut does not skip verification.
