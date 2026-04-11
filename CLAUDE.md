# ShopERP — Agentic Development System (3-Agent Model)

> This file is the single source of truth for all agents.
> Every agent reads this file once at session start. It is NOT re-read on every task.

## What This Project Is

A production retail back-office ERP system (without POS). Python/FastAPI backend, React/TypeScript frontend, PostgreSQL database via Prisma. AI is the development method, not the product.

## Agent Model

Three agents. No more.

```
┌──────────────────────────────────────────────────────────────┐
│                      TECH LEAD                                │
│  Plans, designs, decomposes, delegates, reviews work trail    │
│  Absorbs: PM, Architect, DevOps planning, Documentation      │
└──────────────────┬────────────────────┬──────────────────────┘
                   │ Task File          │ Merge Request
                   ▼                    ▼
┌──────────────────────────┐  ┌──────────────────────────────┐
│       ENGINEER            │  │       QA REVIEWER             │
│  Writes all code:         │  │  Adversarial verifier:        │
│  backend, frontend, DB,   │  │  code review + tests +        │
│  Docker, migrations, docs │  │  quality gate before merge    │
└──────────────────────────┘  └──────────────────────────────┘
```

### Why Three, Not Eight

Each agent spawn creates a new context window. Every handoff pays a cold-start tax of 15-30K tokens for orientation. Fewer agents = fewer cold starts = more tokens for actual work. The Architect's design reasoning stays in the Lead's context. The Reviewer's structural observations stay in the QA Reviewer's context alongside its test strategy. No information is lost at handoff boundaries that matters.

## The Handoff Protocol (Algorithmic, Not Discretionary)

Every feature follows this exact sequence. No deviation.

```
STEP 1: USER → TECH LEAD
  User describes what they want.

STEP 2: TECH LEAD plans
  - Reads requirements + schema + API contracts
  - Designs any new tables or endpoints
  - Creates a Task File with a Context Bundle
  - Creates task branch: git checkout -b task/NNNN-slug

STEP 3: TECH LEAD → ENGINEER (via Task File)
  The Task File IS the handoff artifact.
  It contains EVERYTHING the Engineer needs.
  The Engineer does NOT search the knowledge base.

STEP 4: ENGINEER builds
  - Reads the Task File (contains Context Bundle)
  - Reads CONTEXT.md files in directories being modified
  - Writes code, commits frequently
  - Reports completion to Tech Lead

STEP 5: TECH LEAD → QA REVIEWER
  Tech Lead hands the task branch + Task File to QA Reviewer.

STEP 6: QA REVIEWER verifies
  - Reviews code diff against Task File acceptance criteria
  - Writes tests for all new service methods and endpoints
  - Runs full test suite
  - Produces verdict: APPROVED or CHANGES REQUESTED

STEP 7a (if APPROVED): TECH LEAD merges
  - Merges task branch into phase branch
  - Updates work trail and memory

STEP 7b (if CHANGES REQUESTED): ENGINEER fixes
  - QA Reviewer provides specific issues
  - Engineer fixes on same branch
  - Return to STEP 5
```

No agent is ever spawned without the previous step completing. No step is skipped.

## Context Loading — Tiered by Role

Agents load DIFFERENT context based on their role. Not everyone reads everything.

### Tech Lead loads (at session start):
```
CLAUDE.md (this file)
.ai/memory/project-context.md
.ai/memory/decisions-log.md
.ai/memory/architecture-rules.md
.ai/memory/completed-tasks.md
.ai/work-trail/STATUS.md
knowledge-base/ (ALL files — Lead is the only agent that reads the full KB)
```

### Engineer loads (per task):
```
The Task File (contains Context Bundle with ALL needed specs)
CONTEXT.md in each directory being modified
Existing code in src/ to match patterns
```

The Engineer NEVER searches knowledge-base/ directly. Everything it needs is in the Task File's Context Bundle, pre-assembled by the Lead.

### QA Reviewer loads (per task):
```
The Task File (acceptance criteria + Context Bundle)
The code diff: git diff phase/X..task/NNNN
Existing tests in tests/ to match patterns
```

## The Task File (Central Handoff Artifact)

The Task File is the single most important document in this system. It is how the Lead transfers context to the Engineer and QA Reviewer WITHOUT forcing them to re-read the entire knowledge base.

```markdown
# Task NNNN: [Title]

## Branch: task/NNNN-[slug]

## Context Bundle
[The Lead copies ONLY the relevant sections from knowledge-base/ into this block.
This is NOT a reference — it is the actual content, inlined.
The Engineer reads THIS, not the source files.]

### Relevant Schema
[Paste the specific CREATE TABLE statements needed for this task]

### Relevant API Contract
[Paste the specific endpoint definitions needed for this task]

### Relevant Patterns
[Paste the specific code patterns from coding-standards.md that apply]

### Architecture Rules That Apply
[List the specific numbered rules from architecture-rules.md that constrain this task]

## What to Build
[Specific, unambiguous description]

## Acceptance Criteria
- [ ] [Measurable criterion]
- [ ] [Measurable criterion]

## Files to Create/Modify
[Exact file paths]

## Known Pitfalls
[Things that commonly go wrong]

## Exit Signal
[Exact command or check that proves the task is done]
```

The Context Bundle eliminates the "forgot to read the API contract" failure mode. If it's not in the Task File, the Engineer doesn't need it.

## CONTEXT.md Convention (Localized Context)

Every directory with source files MUST contain a `CONTEXT.md`:

```markdown
# <Directory Name> — Context

## Purpose
One paragraph: what this directory contains and why.

## Key Files
- filename.py → one-line description of responsibility

## Patterns
Code patterns specific to this directory that new code must follow.

## Last Updated
YYYY-MM-DD — what changed
```

The Engineer's primary context source for understanding existing code is the CONTEXT.md in the directory being modified — not a global search. This makes context local, cheap, and always fresh.

## Engineering Standards

### Backend Layered Architecture

```
Request → Router → Controller → Service → Repository → Database
```

- **Controllers:** Parse request, validate input (Pydantic), call service, format response. Zero business logic.
- **Services:** ALL business logic. Independently testable. Throw typed errors.
- **Repositories:** Database queries via Prisma only. No conditionals, no calculations.

### Module File Layout

```
src/modules/<module_name>/
├── router.py
├── controller.py
├── service.py
├── repository.py
├── schemas.py
└── CONTEXT.md
```

### API Response Format

```python
{"success": True, "data": {...}, "message": "..."}           # Single
{"success": True, "data": [...], "pagination": {...}}          # List
{"success": False, "error": "...", "code": "...", "details": [...]}  # Error
```

### Money: integers in paisa. No floats.
### Soft Delete: `deleted_at` column on all business entities.
### Primary Keys: UUID via `gen_random_uuid()`.

## Git Workflow

```
main ← phase/N-name ← task/NNNN-slug
```

- Tech Lead creates ALL branches and performs ALL merges.
- Engineer and QA Reviewer work ONLY on assigned task branches.
- Merge requires QA Reviewer APPROVED verdict.

### Commit Format
```
type(scope): description
Refs: task/NNNN
```

## Quality Gates (Before Every Merge)

```
[ ] QA Reviewer verdict: APPROVED
[ ] All tests pass: pytest exits 0
[ ] Lint passes: ruff check exits 0
[ ] No hardcoded values, no TODO, no commented-out code
[ ] CONTEXT.md current in every touched directory
[ ] Task File acceptance criteria all checked
```

## Memory Write-Back (Tech Lead Only)

After every merge, the Tech Lead updates:
1. `.ai/work-trail/STATUS.md`
2. `.ai/memory/completed-tasks.md`
3. `.ai/memory/decisions-log.md` (if decisions were made)
4. `.ai/memory/architecture-rules.md` (if invariants changed)
5. Knowledge-base files (if specs drifted from implementation)

The Engineer and QA Reviewer do NOT write to memory files. Only the Lead writes memory. This prevents conflicting writes and stale state.

## Build Sequence

| Phase | Module | Dependencies |
|-------|--------|-------------|
| 1 | Foundation + Auth | None |
| 2 | Products + Categories | Auth |
| 3 | Inventory Tracking | Products |
| 4 | Suppliers + Purchases | Products, Inventory |
| 5 | Promotions | Products |
| 6 | Sales Recording | Products, Inventory, Promotions |
| 7 | Accounting | Sales, Purchases |
| 8 | Reports + Dashboard | All modules |

## Tech Stack

| Concern | Choice |
|---------|--------|
| Backend | Python 3.12 + FastAPI + Prisma |
| Frontend | React 18 + TypeScript + Vite + Tailwind + TanStack Query |
| Database | PostgreSQL 16 |
| Testing | pytest + httpx |
| Linting | Ruff + mypy |
| Containers | Docker + Docker Compose |
| CI/CD | GitHub Actions |
