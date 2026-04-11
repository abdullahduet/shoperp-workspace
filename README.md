# ShopERP — AI-Powered Retail ERP (3-Agent Model)

A production retail back-office system built by a 3-agent AI team using Claude Code.

## Quick Start

```bash
cp -r . your-project/
cd your-project && claude
# Say: "Start sprint 1"
```

## Architecture

- **Backend:** Python 3.12 + FastAPI + Prisma
- **Frontend:** React 18 + TypeScript + Vite + Tailwind
- **Database:** PostgreSQL 16
- **Deployment:** Docker + Docker Compose

## 3-Agent Model

| Agent | Role | Context Source |
|-------|------|---------------|
| Tech Lead | Plans, designs, delegates, merges, owns all memory | Full knowledge base |
| Engineer | Writes all code (backend, frontend, infra, docs) | Task File + CONTEXT.md |
| QA Reviewer | Reviews code, writes tests, quality gate | Task File + code diff |

## Why 3 Agents, Not 8

Each agent spawn creates a new context window. Every handoff pays a cold-start tax. Fewer agents = fewer cold starts = more tokens for actual code. The Lead's design reasoning stays in context. The QA Reviewer's structural observations stay alongside its test strategy.

## Handoff Protocol

```
User → Tech Lead (plan + design + Task File)
         → Engineer (implement)
         → QA Reviewer (review + test + verdict)
         → Tech Lead (merge + update memory)
```

No step is skipped. No agent is spawned out of sequence.

## Workspace Structure

```
├── CLAUDE.md                        ← Master instructions
├── .ai/
│   ├── settings.json                ← Claude Code config
│   ├── agents/                      ← 3 agent definitions
│   ├── memory/                      ← Living project state (4 files)
│   ├── workflows/                   ← 3 process guides
│   ├── templates/                   ← 5 document templates
│   └── work-trail/                  ← Audit trail (STATUS, tasks, decisions, checkpoints)
├── knowledge-base/                  ← Specifications (8 files, read only by Tech Lead)
│   ├── product/                     ← Requirements, module map
│   ├── architecture/                ← System design, DB schema, API contracts
│   ├── standards/                   ← Coding, API, testing standards
│   └── decisions/                   ← Architecture decision records
└── docs/                            ← Generated documentation
```

## Key Innovation: The Task File

The Tech Lead pre-digests the knowledge base into a Context-Bundled Task File. The Engineer reads ONLY the Task File — never the raw knowledge base. This eliminates "forgot to read the API contract" failures and keeps the Engineer's context window focused on code, not spec-searching.
