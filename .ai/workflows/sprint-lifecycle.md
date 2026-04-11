# Workflow: Sprint Lifecycle

## The 3-Agent Handoff (applies to every task in every sprint)

```
USER → TECH LEAD (plan + design + create Task File)
         ↓ Task File
       ENGINEER (implement)
         ↓ completion report
       TECH LEAD (hand to QA)
         ↓ Task File + branch
       QA REVIEWER (review + test + verdict)
         ↓ APPROVED / CHANGES REQUESTED
       TECH LEAD (merge or send back to Engineer)
```

No step is skipped. No agent is spawned out of sequence.

## Sprint Start

1. Tech Lead reads: STATUS.md, completed-tasks.md, module-map.md.
2. Tech Lead identifies the next module in the build sequence.
3. Tech Lead reads the requirements for that module from knowledge-base/product/requirements.md.
4. Tech Lead designs any new database tables and API endpoints.
5. Tech Lead updates knowledge-base/architecture/ files with new designs.
6. Tech Lead creates phase branch: `git checkout -b phase/N-name` from main.
7. Tech Lead decomposes the module into atomic tasks (each task = one Task File).
8. Tech Lead presents the plan to the user for approval.

## Per-Task Execution (repeat for each task)

### 1. Tech Lead creates Task File
Write `.ai/work-trail/tasks/NNNN-slug.md` with full Context Bundle. Copy the exact schema, API contract, code patterns, and architecture rules the Engineer needs. Create task branch.

### 2. Tech Lead spawns Engineer
Command: "Implement Task NNNN. Read .ai/work-trail/tasks/NNNN-slug.md"

### 3. Engineer implements
Reads Task File + CONTEXT.md in modified directories. Writes code. Runs exit signal. Reports completion.

### 4. Tech Lead spawns QA Reviewer
Command: "Review Task NNNN on branch task/NNNN-slug. Read .ai/work-trail/tasks/NNNN-slug.md"

### 5. QA Reviewer verifies
Reviews code diff. Writes tests. Runs pytest. Produces verdict.

### 6. Tech Lead resolves
- If APPROVED: merge, delete task branch, update memory.
- If CHANGES REQUESTED: re-spawn Engineer with QA's feedback. Repeat from step 3.

## Sprint Completion

1. All tasks merged into phase branch.
2. Full test suite passes on phase branch: `pytest` exits 0.
3. Tech Lead merges phase into main with checkpoint.
4. Tech Lead creates `.ai/work-trail/checkpoints/phase-N-name.md`.
5. Tech Lead updates STATUS.md, completed-tasks.md, module-map.md.
6. Tech Lead reports to user.

## Foundation Sprint (Phase 1 Only)

Phase 1 has infrastructure tasks that the Engineer handles directly:

Task 0001: Project scaffolding — Docker Compose, Dockerfile, .env.example, directory structure, pyproject.toml/package.json.
Task 0002: Shared utilities — error classes, response formatters, pagination helper, config loader.
Task 0003: Auth module — user model, register, login, logout, JWT middleware, role guard.
Task 0004: Frontend setup — Vite + React + Tailwind + Router + auth context + login page + layout shell.

Each task follows the same Lead → Engineer → QA → merge cycle.
