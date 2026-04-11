# Work Trail — Audit System

## Directory Structure

```
.ai/work-trail/
├── README.md              ← you are here
├── STATUS.md              ← living dashboard
├── tasks/                 ← Task Files (the handoff artifact)
├── decisions/             ← decision logs
└── checkpoints/           ← phase completion snapshots
```

## Who Writes What

The **Tech Lead** is the sole author. The Engineer and QA Reviewer do not write to this directory. The Lead creates Task Files before work, updates them after merge, and maintains STATUS.md.

## Task File Lifecycle

1. Tech Lead creates Task File with Context Bundle BEFORE spawning Engineer.
2. Engineer reads Task File, implements, reports completion.
3. QA Reviewer reads Task File, reviews code, writes tests, produces verdict.
4. Tech Lead updates Task File with: status=completed, outcome, merge commit hash.

## Numbering

Tasks: 0001, 0002, 0003, ... (global, monotonic, zero-padded to 4 digits)
Decisions: 0001, 0002, 0003, ... (separate sequence)
