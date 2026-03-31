# Prototype-Driven Planning Skills — Project Context

> **Purpose**: Persistent memory across chat sessions for the prototype-driven
> skill set (planning → task decomposition → implementation).
>
> **Skill locations**:
> - `~/claude-devtools/skills/prototype-driven-planning/`
> - `~/claude-devtools/skills/prototype-driven-task-decomposition/`
> - `~/claude-devtools/skills/prototype-driven-implementation/` (not yet built)
>
> **Commands**:
> - `/prototype-plan <feature>` → planning skill
> - `/prototype-task-decompose <design-doc>` → decomposition skill
>
> **Test project**: `~/health-data-ai-platform` (airflow Google Drive ingestion)

---

## Conversation-Start Protocol

Read these files in order:
1. **This file** — orientation, standings, open issues
2. **`LEARNINGS.md`** — distilled principles (always relevant)
3. **`trials/_SUMMARY.md`** — scoreboard

Load on-demand only when needed:
- `references/architecture-rationale.md` — why prototype-first, multi-model design, tool selection
- `references/stack-reference.md` — tool versions, configs, CLI flags, doc links
- `gemini_conversation.txt` — raw Gemini consultation transcript (historical)
- `trials/_INDEX.md` — structured tags per trial (find trials by failure pattern)
- `trials/T<NN>-*.md` — individual trial detail (read when analyzing a specific trial)

---

## Current State (2026-03-28)

### Built and Validated

**prototype-driven-planning** — 3 phases (Discovery → Tracer Bullet → Design Doc)
with mandatory pauses. Produces `docs/design/<feature>.md` and
`prototypes/<feature>/`. Validated across multiple test runs.

**prototype-driven-task-decomposition** — 3 phases (Analysis → Task Generation →
Validation/Output). Produces `tasks/<feature>/tasks.json` (machine-readable) and
individual `task-NN-<slug>.md` files (human-readable). Key features:

- **Strict TDD task pairing**: Every task has `task_type: "test"` or
  `task_type: "implementation"`. Test tasks write tests first; implementation
  tasks write code and run those tests. A task never writes both.
- **PydanticAI schema** at `scripts/task_schema.py` with `validate_tdd_pairing`
  validator — enforces that implementation tasks with tests depend on at least
  one test task.
- **Scaffold stubs**: Task-01 creates stub modules that raise `NotImplementedError`
  with correct signatures, so test tasks can import and write tests that fail
  for the right reason (not `ImportError`).
- **Numbered questions at Phase 1**: Ambiguities surfaced as explicit numbered
  questions before task generation proceeds.
- **Interface dependencies**: Tasks depend on modules they'll import, so the
  implementing model can read the real interface.
- **`uv run --with pydantic`** for schema validation in Claude Code (venv
  activation doesn't persist across shell sessions).

### Not Yet Built

**prototype-driven-implementation** — The multi-model pipeline that executes
tasks from `tasks.json`. Planned architecture:

- LangGraph state machine processes tasks in topological order
- Each task routed to Aider with a local model (Qwen 3 Coder 30B via LM Studio)
- Aider runs with `--test-cmd` and `--lint-cmd` for TDD feedback loop
- Circuit breakers: after N consecutive failures, escalate to Gemini Flash
- Final review by Claude Opus
- PydanticAI validates contracts between pipeline phases
- Failed tasks marked for human intervention, pipeline continues

---

## Test Run Results

### Planning Skill
- Session `f75b5f43-fd52-4138-87ad-c7c18589fa07` — First test run
- Session `a7c48f00-b614-4086-a640-b623a00f5a97` — Second test run (added E2E validation)

### Decomposition Skill
- Session `6d471491-32b7-4f74-a720-8fdbf0060023` — First run (8 tasks, pre-TDD)
- Session `b2354707-0024-45db-bb9a-7ff872e39271` — Second run (11 tasks, interface deps fixed)
- Session `64052f92-5393-4425-8286-1389124c6feb` — Third run (27 tasks, full TDD pairing,
  schema validation caught and self-corrected a TDD violation on task-27)

### Implementation Skill
See `trials/_SUMMARY.md` for ongoing trial scoreboard.

---

## File Map

```
~/claude-project-memory/prototype-driven-planning-skill/
├── README.md                              # This file (read first)
├── LEARNINGS.md                           # Distilled principles (read second)
├── gemini_conversation.txt                # Raw Gemini consultation (historical)
├── references/
│   ├── architecture-rationale.md          # Why prototype-first, multi-model, tool selection
│   └── stack-reference.md                 # Tool versions, configs, CLI flags, doc links
└── trials/
    ├── _SUMMARY.md                        # Scoreboard (read third)
    ├── _INDEX.md                          # Structured tags per trial
    └── T<NN>-<slug>.md                    # Individual trial records

~/claude-devtools/skills/prototype-driven-planning/
├── SKILL.md
└── references/
    ├── design-doc-template.md
    ├── phase-1-discovery.md
    ├── phase-2-prototype.md
    └── phase-3-design-doc.md

~/claude-devtools/skills/prototype-driven-task-decomposition/
├── SKILL.md
├── scripts/
│   └── task_schema.py          # PydanticAI schema (source of truth)
└── references/
    ├── analysis-guide.md        # Phase 1: reading design docs, numbered questions
    ├── task-writing-guide.md    # Phase 2: TDD pairs, self-containment, sizing
    └── output-format.md         # Phase 3: JSON/markdown output, recovery

~/claude-devtools/commands/
├── prototype-plan.md            # /prototype-plan slash command
└── prototype-task-decompose.md  # /prototype-task-decompose slash command
```
