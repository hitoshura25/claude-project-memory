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

## Current State (2026-04-06)

### Built and Validated

**prototype-driven-planning** — 3 phases (Discovery → Tracer Bullet → Design Doc)
with mandatory pauses. Design doc template includes Tooling section with lint,
auto-fix, test, bootstrap, and service root fields.

**prototype-driven-task-decomposition** — 3 phases (Analysis → Task Generation →
Validation/Output). Produces `tasks/<feature>/tasks.json` with strict TDD
pairing enforced by PydanticAI schema validators.

### Updated — Implementation Skill (2026-04-06)

**prototype-driven-implementation** — LangGraph pipeline that executes tasks via
configurable coding agent executors.

#### Run 6 Results (2026-04-05)

21 tasks, all passed. First clean 21/21 run. Executors: Aider+Qwen (local,
/no_think, temperature 0.7) → Gemini → Claude escalation chain. Duration ~2h 19m.

task-17 needed 2 retries (rabbitmq publisher), task-02 needed 1 retry. All
others passed first attempt. Qwen had one repetition loop (task-09, 24K tokens)
but pipeline recovered via escalation.

**Post-run code quality issues found:**
- HRV field name mismatch (parser → schema): prototype used
  `heart_rate_variability_millis`, Avro schema uses `rmssd_ms`
- drive_downloader uses `logging` instead of `structlog` (copied from prototype)
- test_integration.py has wrong function signatures (no interface deps)
- messages.py has empty deduplication fields
- sleep schema missing duration_ms

**Root cause:** Split authority between prototype code and task description.
Models follow working code over prose instructions. Led to removing
`prototype_references` from the pipeline entirely.

#### Skill Changes from Run 6 Analysis

1. **Removed prototype references (decomposition + implementation skills)**:
   The `prototype_references` field, `PrototypeReference` class, and
   `prototype_path` field were removed from the task schema. The pipeline no
   longer reads prototype files — task descriptions are the sole source of
   truth for implementing models.

2. **Inline patterns replace prototype references (decomposition skill)**:
   Task-writing-guide now instructs the decomposing model to copy adapted
   code snippets directly into task descriptions with correct field names,
   imports, and conventions already applied.

3. **Output field contracts (decomposition skill)**:
   When a task produces structured data that another task consumes, both
   tasks must specify exact field names. The decomposing model reconciles
   source names with output names at decomposition time.

4. **Implementation skill input simplification**:
   Removed prototype directory and design doc from pipeline inputs. Pipeline
   reads only tasks.json, task_schema.py, and project config files.
   `PROTOTYPE_DIR` removed from generated config.py template.
   Reference Code block removed from prompt template.

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
13. verify_task test-task logic: NotImplementedError = pass, collection error = fail
14. Stub writing rules in test-task prompt composition
15. Prototype references removed — task descriptions are sole source of truth
16. Inline patterns and output field contracts in decomposition skill
17. Implementation pipeline no longer reads prototype directory or design doc

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
`--allowedTools "Read,Write,Edit,Bash"` was wrong — `--allowedTools` in Claude
CLI auto-approves listed tools but doesn't prevent Claude from trying to use
other tools that then hang waiting for approval in headless mode. The correct
flags need to be determined by researching the CLI's official docs.

**Fix:** Updated skill to research CLI docs during Phase 1 executor detection
rather than relying on hardcoded patterns. Next run will regenerate the pipeline
with researched, verified invocation commands.

### Run 4 (2026-04-03) — Full escalation: Aider+Qwen → Gemini → Claude

18 tasks, ~2.5 hours. Best run yet — all implementation code produced.

**Results:** All 6 plugin modules implemented, all 7 test files written, DAG
complete. Tasks 16-18 (Dockerfile, Docker Compose, integration tests) not
reached. Claude CLI rate limit hit after ~1 hour.

**Executor performance:**
- Aider+Qwen: Succeeded on small tasks (avro_writer, watermark_store), timed
  out on complex ones (parser). 3 degenerate repetition loops (27K tokens).
- Gemini: Rescued drive_downloader and minio_uploader. Hit 429 capacity errors
  but internal retry handled them. Produced working code.
- Claude: Rescued parser. Rate limited after ~5 tasks.

**Root causes identified:**
1. Qwen 3 Coder running without thinking mode (temperature 0, no reasoning
   config) caused repetition loops
2. Aider couldn't read test files (not in --file list), so implementation
   attempts were blind to test expectations
3. Parser task too complex for local models (270 lines, 6 parsers in 1 file)

**Fixes applied:** Step 1b model research, test file inclusion, task sizing rules.

### Run 5 (2026-04-04) — Re-decomposed with task sizing

21 tasks (re-decomposed with updated task sizing). Stalled at task-02 after 4
attempts. Claude CLI produced empty output on all retries. Root cause: test
task imports module under test (`from config.settings import Settings`), but
the module doesn't exist yet — `verify_task` treated the `ModuleNotFoundError`
as a collection error instead of recognizing it as expected TDD behavior.

**Fix:** Stub-in-test-task design across both decomposition and implementation
skills. Test tasks now create stub files alongside test files.

### Run 6 (2026-04-05) — First clean run: Aider+Qwen → Gemini → Claude

21 tasks, ~2h 19m. First clean 21/21 run. Qwen improved significantly with
`/no_think` + `temperature: 0.7`. One repetition loop (task-09) recovered via
escalation. Post-run manual review found field name mismatches, wrong function
signatures in integration tests, and prototype-over-prose copying. Led to
`prototype_references` removal from the pipeline.

---

## Next Steps

- **Re-decompose** with updated task-writing-guide (inline patterns + output
  field contracts instead of prototype references)
- **Regenerate pipeline** from updated implementation skill (no prototype
  references in prompt template)
- **T07 run** to validate that self-contained task descriptions eliminate
  the field name drift and signature mismatch issues from T06
- **Fix `_log_path` threading bug** so per-executor logs are captured in
  the run log file (currently unverifiable from artifacts)
- **Explore import-level checks** for tasks without test gates (e.g.,
  integration test tasks that only have lint gates)
- **Explore reducing `EXECUTOR_TIMEOUT`** at the skill level so generated
  `config.py` defaults to 300s (Qwen completes within ~90s; 600s only
  enables failing retry loops)

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
- **2026-04-02**: Run 3 — Claude CLI as executor. Hung on task-01 (wrong CLI flags).
- **2026-04-03**: Run 4 — 18 tasks, Aider+Qwen/Gemini/Claude. All impl code produced.
  Claude rate limited after ~1hr. 3 Qwen repetition loops. Tasks 16-18 not reached.
- **2026-04-04**: Run 5 — 21 tasks (re-decomposed). Stalled at task-02.
  verify_task rejected valid test task due to ModuleNotFoundError from missing
  stub. Led to stub-in-test-task design across both skills.
- **2026-04-05**: Run 6 — 21 tasks, Aider+Qwen/Gemini/Claude. First clean
  21/21 run. Post-run review found field name drift, wrong signatures, and
  prototype-over-prose copying. Led to prototype_references removal.

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
    ├── task-writing-guide.md
    └── output-format.md

~/claude-devtools/skills/prototype-driven-implementation/
├── SKILL.md                     # Multi-executor, research-based
└── references/
    ├── phase-1-analysis.md      # Updated: live CLI research + test prompt
    ├── phase-2-generation.md    # EXECUTORS/EXECUTOR_ROLES, enum fix
    ├── langgraph-patterns.md    # escalate_executor node
    ├── executor-integration.md  # Research-driven patterns (no hardcoded flags)
    └── phase-3-handoff.md

~/claude-devtools/commands/
├── prototype-plan.md
└── prototype-task-decompose.md
```
