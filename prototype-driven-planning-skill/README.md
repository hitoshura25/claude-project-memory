# Prototype-Driven Planning Skill — Context Summary

> This is conversation context only. The actual skill files live at
> `~/claude-devtools/skills/prototype-driven-planning/`.

## What This Skill Does

Takes a feature idea through three phases:

1. **Discovery** — Inventory the project, identify core technical risk, research
2. **Tracer Bullet Prototype** — Build minimum code proving core risk, validate
   toolchain (lint, tests, Dockerfile, end-to-end), research cross-cutting concerns
3. **Vetted Design Doc** — Generate a design doc grounded in prototype reality

The design doc is the deliverable. It's a specification validated against working
code, not a hallucinated wish list.

## Skill Structure

```
~/claude-devtools/skills/prototype-driven-planning/
├── SKILL.md                           # ~130 lines, narrow trigger, 3 phases with pauses
└── references/
    ├── phase-1-discovery.md           # Project inventory, core risk, research guidance
    ├── phase-2-prototype.md           # Build/run/iterate, toolchain, end-to-end, research
    ├── phase-3-design-doc.md          # Grounded writing guidance, consumability rules
    └── design-doc-template.md         # Exact output structure for design docs
```

A companion slash command exists at `~/claude-devtools/commands/prototype-plan.md`
for invocation via `/prototype-plan <feature idea>`.

## Key Design Decisions

- **Narrow trigger**: Only activates when prototype-first flow is explicitly requested
- **Pauses between every phase**: User must confirm before proceeding
- **Feature idea via `$ARGUMENTS`**: `/prototype-plan Add health data sync module`
- **Prototype location**: `prototypes/<feature-name>/` within the project
- **Design doc location**: `docs/design/<feature-name>.md`
- **Prototypes are immutable by convention**: No freeze/copy mechanism; the
  `prototypes/` directory convention signals they shouldn't be modified
- **Dockerfile is conditional**: Only for deployable services/jobs; skipped for
  mobile apps, libraries, CLI tools, features added to existing services

## Phase 2 Structure (evolved over 3 iterations)

Phase 2 has four steps, refined through test runs:

1. **Core Code** — Build minimum code proving the core technical risk
2. **Toolchain Validation** — Lint setup, minimal tests, conditional Dockerfile
3. **End-to-End Validation** — Prove the prototype works from the outside
   (Docker health check, mobile UI test, library import test, etc.)
4. **Cross-Cutting Research** — Security, deployment, additional testing patterns

The end-to-end validation step was the key insight from iteration 3: building a
Docker image isn't the same as proving the service works. The prototype must be
validated the way its actual consumer will use it.

## Test Run Results

### Run 1 (session f75b5f43)
- Prototype: 2 files (script + README), no tests, no Docker
- Design doc: Testing and containerization sections were research-based, not proven
- Outcome: Worked but too speculative in toolchain sections

### Run 2 (session a7c48f00)
- Added toolchain validation: lint, 15 tests, Dockerfile that builds
- Design doc: Testing and containerization grounded in working config
- Outcome: Better, but Docker "worked" only meant the image built — not that the
  service was functional

### Run 3 (session d7bd2674) — Current
- Added end-to-end validation: actual `airflow dags test` inside container
- Prototype: 6 files including a real DAG, conftest.py with Airflow module patching
- Design doc: Significantly richer — XCom 48KB limit, `airflow db init` vs
  `db migrate`, FERNET_KEY encryption warning, pika sync compatibility — all
  discovered during actual execution, not research
- 7 distinct toolchain surprises captured in README
- Outcome: Design doc quality is where we want it

## Key Learnings

- **Prototype-first eliminates speculative planning bugs**: The model writes code,
  runs it, and fixes based on real feedback. Design docs observe what worked.
- **Toolchain validation matters as much as core logic**: Lint config, test
  framework setup, Docker entrypoint behavior — these are where implementation
  models get stuck. Proving them in the prototype prevents iteration loops later.
- **End-to-end validation surfaces architectural questions**: The message format
  mismatch between the Airflow publisher and the ETL engine's expected
  `HealthDataMessage` schema only surfaced because the prototype actually published
  to RabbitMQ.
- **"Minimal tests" > "one test"**: The right number of tests is enough to prove
  the toolchain works and the core logic is correct — not one for the sake of one,
  but not exhaustive coverage either.
- **Skill files live locally only**: `~/claude-devtools/` is the home. The
  `claude-project-memory` repo is strictly for conversation context.

## Future Phases (Not Yet Built)

### Phase 4 — Task Decomposition
Break the design doc into implementation tasks. PydanticAI will enforce a strict
schema so each task is structured consistently for implementing models. Tasks
reference the prototype for proven patterns but target a fresh production codebase.

### Phase 5 — Multi-Model Implementation Pipeline
LangGraph orchestrates the model cascade (local Qwen/Codestral via Aider → Gemini
Flash fallback → Claude Opus final review). PydanticAI validates contracts between
phases. Circuit breakers prevent infinite retry loops.
