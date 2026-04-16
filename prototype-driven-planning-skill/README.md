# Prototype-Driven Planning Skills — Project Context

> **Purpose**: Persistent memory across chat sessions for the prototype-driven
> skill set (planning → task decomposition → implementation).
>
> **Skill locations**:
> - `~/claude-devtools/skills/prototype-driven-planning/`
> - `~/claude-devtools/skills/prototype-driven-task-decomposition/`
> - `~/claude-devtools/skills/prototype-driven-implementation/`
>
> **Commands**:
> - `/prototype-plan <feature>` → planning skill
> - `/prototype-task-decompose <design-doc>` → decomposition skill
> - `/prototype-implement <feature>` → implementation skill
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

## Current State (2026-04-15)

### Built and Validated

**prototype-driven-planning** — 3 phases (Discovery → Tracer Bullet → Design Doc)
with mandatory pauses. Design doc template includes Tooling section with lint,
auto-fix, test, bootstrap, and service root fields.

**prototype-driven-task-decomposition** — 3 phases (Analysis → Task Generation →
Validation/Output). Produces `tasks/<feature>/tasks.json` with strict TDD
pairing enforced by PydanticAI schema validators.

### Updated — Implementation Skill (2026-04-15)

**prototype-driven-implementation** — LangGraph pipeline that executes tasks via
configurable coding agent executors.

#### Run 9 Results (2026-04-13)

17 tasks (re-decomposed), ~1h 47m. 8 passed, 4 degraded (lint fail/test pass),
1 failed (task-13 rabbitmq test), 1 skipped, 3 not_run.

**Improvements from T08:**
- Runtime dropped from 6.9h to 1.8h (MAX_RETRIES=1 working)
- No I001 lint loops (AIDER_LINT_CMD fix held)
- No Gemini 429 rate limits this run
- TeeWriter captured full log
- 12/13 reached tasks succeeded (92% reach-success rate)

**Issues identified:**
1. `EXECUTOR_TIMEOUT` still 600s despite skill template saying 300s — Claude
   Code retained the value from a previous pipeline's `config.py` via memory
2. `ruff` not in service `pyproject.toml` dev dependencies — scaffold task
   didn't include it, causing "Failed to spawn: ruff" on early tasks. Self-
   healed mid-run when Gemini coincidentally ran `uv sync`
3. Task-13 (rabbitmq publisher test) failed all tiers — test patches
   `plugins.rabbitmq_publisher.pika.BlockingConnection` but the stub doesn't
   import `pika`, so `patch()` fails at fixture setup
4. E501 on long string literals (SQL, docstrings) caused 4 degraded tasks —
   `ruff format` doesn't break string contents

#### Post-T09 Skill Changes (2026-04-15)

**Task-13 fix — stub mock-import rule (decomposition skill):**
Added rule to `task-writing-guide.md`: stubs must import third-party
dependencies that tests will mock at the module boundary. The decomposing
model includes these imports in stub code even though the stub body doesn't
use them. Framed cross-framework (Python patch, Java Mockito, TypeScript Jest).

**Bootstrap merged into scaffold verification (implementation skill):**
Eliminated the separate `bootstrap` node from the LangGraph graph. Bootstrap
(dependency installation + tool verification) now runs as part of verify_task's
scaffold logic. This means scaffold tasks are fully validated — marker file
exists, dependencies install, lint and test tools are available — before any
subsequent tasks run. If bootstrap fails, the scaffold task fails and can be
retried/escalated like any other task. Previously, bootstrap ran as a
separate node after verify_task had already marked the scaffold as passed,
so bootstrap failures only produced warnings, not task failures.

Files changed: `graph.py` (removed bootstrap node + route), `pipeline_state.py`
(removed `bootstrap_done`), `verify_task.py` (added `_run_scaffold_bootstrap`),
`config.py.template` (replaced 3 bootstrap fields with `SCAFFOLD_BOOTSTRAP_CMD`),
`bootstrap.py` (tombstone — needs manual deletion), all 5 reference docs,
`SKILL.md`.

#### Templating Refactor (2026-04-14)

Major skill change: pipeline files are now split into **templates** (copied
verbatim) and **generated** (project-specific). This eliminates the
non-determinism of Claude Code regenerating stable files from memory or
reference docs, which caused the timeout drift issue.

**Templates (10 files, copied verbatim):**
- `run.py`, `pipeline_state.py`, `graph.py`, `agent_bridge.py`, `requirements.txt`
- `nodes/__init__.py`, `nodes/load_tasks.py`, `nodes/execute_task.py`,
  `nodes/verify_task.py`, `nodes/report.py`
- `config.py.template` (with `{{PLACEHOLDER}}` markers)

**Generated (3 files, per-project):**
- `config.py` — from template, filling placeholders only
- `nodes/compose_prompt.py` — project-specific prompt composition
- `README.md` — project-specific instructions

**Key improvements baked into templates:**
- `EXECUTOR_TIMEOUT = 300` and `MAX_RETRIES_PER_TASK = 1` are hardcoded
  literals that Claude Code cannot override from memory
- verify_task runs bootstrap + tool verification as part of scaffold
  verification via `SCAFFOLD_BOOTSTRAP_CMD` and `BOOTSTRAP_TOOL_CHECKS`
- All template files are language-agnostic — platform-specific patterns
  (file extensions, stub error strings, collection error markers, scaffold
  marker files, tool checks) are driven by config fields
- All reference docs updated to point to templates instead of containing
  inline code that could be regenerated with drift

#### All features:
1. `EXECUTORS` + `EXECUTOR_ROLES` config with type-based dispatch
2. Multi-executor dispatch via `agent_bridge.py`
3. Lint auto-fix as a post-executor step in `verify_task`
4. Executor escalation via `escalate_executor` node
5. Phase 1 live CLI research + test prompt verification
6. Phase 1 Step 1b: Aider model settings research for local models
7. Prompt composition with dependency inlining and test-task guidance
8. Enum serialization fix (`model_dump(mode="json")`)
9. Aider test file inclusion for implementation tasks
10. `AIDER_MODEL_EXTRA_ARGS` per-model config
11. Stub files in test tasks with `stub: true` schema field
12. `validate_stub_on_test_tasks_only` and `validate_stub_to_modify` validators
13. verify_task test-task logic: config-driven stub error pattern = pass, collection error = fail
14. Stub writing rules in test-task prompt composition
15. Prototype references removed — task descriptions are sole source of truth
16. Inline patterns and output field contracts in decomposition skill
17. Implementation pipeline no longer reads prototype directory or design doc
18. `AIDER_LINT_CMD` — auto-fix before check in Aider's `--lint-cmd`
19. `TeeWriter` stdout capture in `run.py` for run log completeness
20. `EXECUTOR_TIMEOUT` default reduced from 600s to 300s
21. Integration test Docker lifecycle in test commands (compose up/test/down)
22. Docker availability validation at startup when integration tests present
23. Scaffold task creates `services.compose.yml` for dependency services
24. Integration test task descriptions require exact function signatures
25. Orchestrator/wiring tasks must depend on scaffold if they import config/settings
26. **Pipeline templates** — 10 stable files copied verbatim, 3 generated
27. **Integrated scaffold verification** — scaffold tasks verify marker file,
    run bootstrap, and check lint/test tool availability in a single verify_task
    pass. Failures are retryable/escalatable like any other task.
28. **Config template with placeholders** — prevents value drift from model memory
29. **Language-agnostic templates** — all platform-specific patterns (file extensions,
    stub error strings, collection error markers, scaffold marker files, tool checks)
    driven by config fields, not hardcoded in template code
30. **Stub mock-import rule** — stubs must import third-party dependencies that
    tests will mock at the module boundary (decomposition skill)

---

## Pipeline Run History

### Run 1 (2026-03-31) — Single-tier Aider + Qwen

27 tasks, all attempted. 20/31 invocations hit reflection exhaustion.
Dominant failure: I001/F401 lint loops. See LEARNINGS.md for analysis.

### Run 2 (2026-04-01) — Aider + Gemini Flash (model roles, no CLI research)

18 tasks. Stalled at task-02 (4 attempts). Causes: empty stubs from oversized
scaffold task, enum serialization bug, single-tier test role. Positive: test
file had real assertions (model roles concept validated).

### Run 3 (2026-04-02) — Claude CLI as scaffold/test executor (pre-research fix)

Pipeline hung on task-01 (scaffold via claude CLI). Cause: hardcoded
`--allowedTools "Read,Write,Edit,Bash"` was wrong.

### Run 4 (2026-04-03) — Full escalation: Aider+Qwen → Gemini → Claude

18 tasks, ~2.5 hours. Best run yet — all implementation code produced.
Claude rate limited after ~1 hour. 3 Qwen repetition loops.

### Run 5 (2026-04-04) — Re-decomposed with task sizing

21 tasks. Stalled at task-02 after 4 attempts. verify_task rejected valid test
task due to ModuleNotFoundError from missing stub.

### Run 6 (2026-04-05) — First clean run: Aider+Qwen → Gemini → Claude

21 tasks, ~2h 19m. First clean 21/21 run. Post-run review found field name
drift, wrong signatures, and prototype-over-prose copying.

### Run 7 (2026-04-07) — Re-decomposed with inline patterns

31 tasks. I001 lint loops on all Aider+Qwen tasks, Gemini 429 on escalation.
Led to AIDER_LINT_CMD, TeeWriter, 300s timeout.

### Run 8 (2026-04-09) — Auto-fix + TeeWriter + 300s timeout

22 tasks, ~6.9 hours. 19/22 passed, 1 failed (task-20), 2 skipped. Timeout
was still 600s due to config drift.

### Run 9 (2026-04-13) — Re-decomposed (17 tasks)

17 tasks, ~1h 47m. 8 passed, 4 degraded, 1 failed (task-13), 1 skipped,
3 not_run. Timeout still 600s (memory contamination). ruff not in dev deps.
Task-13 failed: stub missing pika import for test patching.

---

## Next Steps

- **Run T10** with templated pipeline — validates that templates copy
  correctly, timeout is 300s, and integrated scaffold verification works
- **Aider+Qwen value**: Won 1/6 implementation tasks in T09. Consider
  promoting Gemini to tier-0 for implementation
- **Manual cleanup**: Delete `~/claude-devtools/skills/prototype-driven-implementation/templates/nodes/bootstrap.py`
  (tombstone file from bootstrap merge)

---

## Test Run Results

### Planning Skill
- Session `f75b5f43-fd52-4138-87ad-c7c18589fa07` — First test run
- Session `a7c48f00-b614-4086-a640-b623a00f5a97` — Second test run

### Decomposition Skill
- Session `6d471491-32b7-4f74-a720-8fdbf0060023` — First run (8 tasks)
- Session `b2354707-0024-45db-bb9a-7ff872e39271` — Second run (11 tasks)
- Session `64052f92-5393-4425-8286-1389124c6feb` — Third run (27 tasks)

### Implementation Skill
- **2026-03-31**: Run 1 — 27 tasks, Aider+Qwen. Reflection exhaustion dominant.
- **2026-04-01**: Run 2 — 18 tasks, Aider+Gemini Flash. Enum bug + empty stubs.
- **2026-04-02**: Run 3 — Claude CLI as executor. Hung on task-01.
- **2026-04-03**: Run 4 — 18 tasks, full escalation. All impl code produced.
- **2026-04-04**: Run 5 — 21 tasks. Stalled at task-02 (missing stubs).
- **2026-04-05**: Run 6 — 21 tasks. First clean 21/21 run.
- **2026-04-07**: Run 7 — 31 tasks. I001 lint loops, Gemini 429s.
- **2026-04-09**: Run 8 — 22 tasks, 19/22 passed. Config drift (600s timeout).
- **2026-04-13**: Run 9 — 17 tasks, 8+4 passed/degraded. ruff missing, task-13 failed.

---

## File Map

```
~/claude-project-memory/prototype-driven-planning-skill/
├── README.md                              # This file (read first)
├── LEARNINGS.md                           # Distilled principles (read second)
├── gemini_conversation.txt                # Raw Gemini consultation (historical)
├── references/
│   ├── architecture-rationale.md
│   └── stack-reference.md
└── trials/
    ├── _SUMMARY.md                        # Scoreboard (read third)
    ├── _INDEX.md
    └── T<NN>-<slug>.md

~/claude-devtools/skills/prototype-driven-planning/
├── SKILL.md
└── references/
    ├── design-doc-template.md             # Includes Tooling section
    ├── phase-1-discovery.md
    ├── phase-2-prototype.md               # Includes auto-fix discovery
    └── phase-3-design-doc.md

~/claude-devtools/skills/prototype-driven-task-decomposition/
├── SKILL.md
├── scripts/
│   └── task_schema.py
└── references/
    ├── analysis-guide.md
    ├── task-writing-guide.md              # Updated: stub mock-import rule
    └── output-format.md

~/claude-devtools/skills/prototype-driven-implementation/
├── SKILL.md                     # Updated: no bootstrap.py in layout
├── templates/                   # Verbatim pipeline files (language-agnostic)
│   ├── run.py                   # Entry point with TeeWriter
│   ├── pipeline_state.py        # LangGraph state TypedDicts
│   ├── graph.py                 # StateGraph, routing, pick/retry/escalate nodes
│   ├── agent_bridge.py          # Executor dispatch, subprocess wrappers
│   ├── requirements.txt         # langgraph, pydantic
│   ├── config.py.template       # Config with {{PLACEHOLDER}} markers
│   └── nodes/
│       ├── __init__.py
│       ├── load_tasks.py        # Task loading, schema validation
│       ├── execute_task.py      # Executor dispatch node
│       ├── verify_task.py       # Auto-fix, lint, test, scaffold bootstrap
│       └── report.py            # Final summary
└── references/
    ├── phase-1-analysis.md      # Executor detection, tooling, research
    ├── phase-2-generation.md    # Copy templates, generate 3 files
    ├── langgraph-patterns.md    # State machine design reference
    ├── executor-integration.md  # Executor dispatch and prompt composition
    └── phase-3-handoff.md       # Validation and handoff

~/claude-devtools/commands/
├── prototype-plan.md
└── prototype-task-decompose.md
```
