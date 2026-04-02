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

## Current State (2026-04-02)

### Built and Validated

**prototype-driven-planning** — 3 phases (Discovery → Tracer Bullet → Design Doc)
with mandatory pauses. Produces `docs/design/<feature>.md` and
`prototypes/<feature>/`. Design doc template includes a Tooling section with
lint, auto-fix, test, bootstrap, and service root fields.

**prototype-driven-task-decomposition** — 3 phases (Analysis → Task Generation →
Validation/Output). Produces `tasks/<feature>/tasks.json` with strict TDD
pairing enforced by PydanticAI schema validators.

### Updated — Implementation Skill (2026-04-02)

**prototype-driven-implementation** — LangGraph pipeline that executes tasks via
configurable coding agent executors. Major architecture change: **multi-executor
support** replacing the Aider-only model.

#### Key Concepts

**Executors** are coding agent CLIs (Aider, Claude CLI, Gemini CLI). Each is a
named entry in `config.EXECUTORS` with a `type` field that drives dispatch:
- `type: "aider"` — model-agnostic, named after its model (e.g., `aider-local-qwen`)
- `type: "claude"` — uses Pro plan auth, no API key. Optional `model` field.
- `type: "gemini"` — uses Google account or GEMINI_API_KEY. Optional `model` field.

**Executor Roles** map task roles (test/implementation/scaffold) to ordered
escalation chains of executor names. Position 0 is the default; subsequent
positions are escalation tiers.

#### Current features:
1. **`EXECUTORS` + `EXECUTOR_ROLES` config** — executors defined once with type
   and type-specific params; roles map to ordered executor name lists.
2. **Multi-executor dispatch** — `agent_bridge.py` dispatches to aider, claude
   CLI, or gemini CLI based on executor type. Each type has its own command
   construction and prompt delivery.
3. **Lint auto-fix** as a post-executor step in `verify_task`.
4. **Executor escalation** — `escalate_executor` node bumps tier, resets retries.
5. **Phase 1 executor detection** — checks which CLIs are installed and
   authenticated, proposes role assignments for user confirmation.
6. **Prompt composition** — dependency file inlining, import conventions,
   test-task guidance against `NotImplementedError` stubs.
7. **Enum serialization fix** — `model_dump(mode="json")` in load_tasks to
   prevent TaskType enum objects from breaking EXECUTOR_ROLES lookups.
8. **Fail-fast startup validation** — verifies all active executors' CLIs are
   on PATH and auth is configured before any tasks run.

#### Files (implementation skill):
- `SKILL.md` — multi-executor throughout
- `references/phase-1-analysis.md` — executor detection, role confirmation
- `references/phase-2-generation.md` — EXECUTORS/EXECUTOR_ROLES config, enum fix
- `references/langgraph-patterns.md` — escalate_executor node, updated routing
- `references/executor-integration.md` — (renamed from aider-integration.md)
  multi-executor dispatch, per-type command construction, prompt composition
- `references/phase-3-handoff.md` — unchanged

---

## Pipeline Run History

### Run 1 (2026-03-31) — Single-tier Aider + Qwen

27 tasks, all attempted. 20/31 invocations hit reflection exhaustion.
Dominant failure: I001/F401 lint loops. Code quality mixed — schemas excellent,
cross-file interface drift (self.since_ms bug), many test stubs instead of
real assertions. See LEARNINGS.md for detailed analysis.

### Run 2 (2026-04-01) — Aider + Gemini Flash (with model roles)

18 tasks (improved decomposition). Pipeline stalled at task-02 after 4 attempts.
Root causes:
1. **Empty stubs** — scaffold task (19 files) too large for single Gemini Flash
   invocation via Aider. All plugin files created as 0 bytes.
2. **Enum serialization** — `model_dump()` without `mode="json"` produced
   `TaskType.TEST` enum objects instead of `"test"` strings, breaking
   `MODEL_ROLES` key lookup.
3. **Single-tier test role** — `MODEL_ROLES["test"]` had only `["gemini-flash"]`,
   so no escalation was possible when it failed.

**Positive finding:** Test file produced by Gemini Flash (`test_drive_downloader.py`)
contained real assertions with proper mock setups — not `NotImplementedError`
stubs. The model roles concept works for test quality.

### Fixes Applied (2026-04-02)

- Enum fix: `model_dump(mode="json")` documented in phase-2-generation.md
- Multi-executor: `EXECUTORS`/`EXECUTOR_ROLES` replaces `MODELS`/`MODEL_ROLES`
- Claude CLI and Gemini CLI as first-class executors (not just Aider backends)
- Renamed `aider_bridge.py` → `agent_bridge.py`, `aider-integration.md` →
  `executor-integration.md`

---

## Next Steps

- **Re-run full workflow** with multi-executor config (e.g., claude for scaffold
  + test, aider-local-qwen for implementation, claude for escalation)
- **Test scaffold with Claude CLI** — the large scaffold task (19 files) that
  failed with Aider+Gemini may succeed with `claude -p` which has built-in
  file creation tools
- **Validate executor escalation** — confirm that when aider-local-qwen fails,
  the pipeline escalates to claude and succeeds

---

## Test Run Results

### Planning Skill
- Session `f75b5f43-fd52-4138-87ad-c7c18589fa07` — First test run
- Session `a7c48f00-b614-4086-a640-b623a00f5a97` — Second test run (added E2E validation)

### Decomposition Skill
- Session `6d471491-32b7-4f74-a720-8fdbf0060023` — First run (8 tasks, pre-TDD)
- Session `b2354707-0024-45db-bb9a-7ff872e39271` — Second run (11 tasks, interface deps fixed)
- Session `64052f92-5393-4425-8286-1389124c6feb` — Third run (27 tasks, full TDD pairing)

### Implementation Skill
- **2026-03-31**: Run 1 (27 tasks, single-tier Aider+Qwen). All attempted, reflection exhaustion dominant.
- **2026-04-01**: Run 2 (18 tasks, Aider+Gemini Flash with model roles). Stalled at task-02. Enum bug + empty stubs.

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
    ├── design-doc-template.md             # Includes Tooling section
    ├── phase-1-discovery.md
    ├── phase-2-prototype.md               # Includes auto-fix discovery
    └── phase-3-design-doc.md

~/claude-devtools/skills/prototype-driven-task-decomposition/
├── SKILL.md
├── scripts/
│   └── task_schema.py          # PydanticAI schema (source of truth)
└── references/
    ├── analysis-guide.md
    ├── task-writing-guide.md
    └── output-format.md

~/claude-devtools/skills/prototype-driven-implementation/
├── SKILL.md                     # Updated 2026-04-02: multi-executor
└── references/
    ├── phase-1-analysis.md      # Updated 2026-04-02: executor detection
    ├── phase-2-generation.md    # Updated 2026-04-02: EXECUTORS/EXECUTOR_ROLES, enum fix
    ├── langgraph-patterns.md    # Updated 2026-04-02: escalate_executor node
    ├── executor-integration.md  # Updated 2026-04-02: (renamed from aider-integration.md)
    └── phase-3-handoff.md

~/claude-devtools/commands/
├── prototype-plan.md
└── prototype-task-decompose.md
```
