# T06 — First Clean Run (21/21)

**Date**: 2026-04-05
**Skill**: implementation
**Executors**: Aider+Qwen (local, /no_think) → Gemini → Claude escalation
**Result**: ✅ 21/21 passed, 0 failed, 0 degraded
**Duration**: ~2h 19m

---

## Configuration

- **Executor chain**: Aider+Qwen3 Coder 30B (local via LM Studio) → Gemini CLI → Claude CLI
- **Aider settings**: `/no_think`, `temperature: 0.7` (from Step 1b research)
- **EXECUTOR_TIMEOUT**: 600s
- **Roles**: test→Claude, implementation→escalation chain, scaffold→escalation chain
- **Task count**: 21 (re-decomposed with stub-aware schema from T05)

## Task Execution Summary

- **task-17** (rabbitmq publisher): 2 retries needed
- **task-02**: 1 retry needed
- **All others**: Passed on first attempt

## Qwen Performance

Much improved with `/no_think` + `temperature: 0.7` compared to prior runs
(T01/T04). One repetition loop on task-09 (24K tokens) but pipeline recovered
via escalation to Gemini. I001 import ordering remains the top retry cause,
handled by lint auto-fix post-step.

## Code Quality Issues Found Post-Run

Although all 21 tasks passed the pipeline's lint/test gates, manual post-run
review revealed several issues that the pipeline could not catch:

1. **HRV field name mismatch**: Parser uses SQLite column name
   `heart_rate_variability_millis`. Avro schema expects `rmssd_ms`. Task doc
   said `rmssd_ms > 0`. Implementing model followed prototype code, not task
   description. Would fail at runtime when writing to Avro.

2. **drive_downloader.py structlog**: Task doc said "use structlog.get_logger()".
   Prototype reference section showed complete prototype code using
   `logging.getLogger`. Model copied prototype verbatim, ignored prose
   instruction.

3. **test_integration.py broken signatures**: Task-21 had no access to actual
   function signatures of `MinIOUploader`, `HealthDataPublisher`, or
   `write_avro` — not in its `depends_on` chain. Model guessed API signatures
   and got them all wrong. File passes lint but would crash on execution.

4. **messages.py empty deduplication fields**: Deduplication field values left
   empty/default.

5. **sleep schema missing duration_ms**: Schema definition incomplete.

## Root Cause Analysis

All five issues trace back to **split authority**: the implementing model
received both task description prose AND raw prototype code (via
`prototype_references`), and when they conflicted, the model followed the
working code over the prose instructions. Additionally, task-21 lacked
interface dependencies for the modules it needed to call.

## Design Decision

**Remove `prototype_references` from the pipeline entirely.** Task docs must
be the sole source of truth for the implementing model. The prototype and
design doc are inputs to the *decomposition process* — the decomposing model
reads them, extracts what's relevant, and distills patterns into task
descriptions as inline code snippets with correct field names, imports, and
conventions already applied.

New concept: **output field contracts** — when a task produces structured data
that another task consumes via a schema, both tasks must specify exact field
names. The decomposing model reconciles source names with output names at
decomposition time.

## Skill Changes Triggered

- Remove `PrototypeReference` class and `prototype_references` field from
  task schema (decomposition skill)
- Remove `prototype_path` from `TaskDecomposition` (decomposition skill)
- Replace "Writing Prototype References" with "Writing Inline Patterns" and
  "Output Field Contracts" in task-writing-guide.md (decomposition skill)
- Remove prototype/design doc from implementation skill's input table
- Remove `PROTOTYPE_DIR` from generated config.py template
- Remove Reference Code block from prompt template
- Update Principles section re: prototype role

## Tags

`clean-sweep`, `prototype-reference`, `cross-task-drift`

## Progression

T05 → T06: Stub workflow validated, `/no_think` + model settings applied,
test file inclusion for Aider. First complete run. Post-run review revealed
cross-task field name drift and broken integration tests, leading to
`prototype_references` removal design.
