# T01 — Single-Tier Aider + Qwen 3 Coder 30B

| Field | Value |
|-------|-------|
| **Date** | 2026-03-31 |
| **Skill** | prototype-driven-implementation |
| **Executors** | Aider + Qwen 3 Coder 30B (LM Studio) |
| **Escalation** | None (single tier) |
| **Test project** | health-data-ai-platform / airflow-google-drive-ingestion |
| **Result** | ❌ Partial — code produced for all 27 tasks but most exited with unresolved lint errors |

---

## Setup

- 27 tasks from the third decomposition run
- Single executor: Aider with Qwen 3 Coder 30B via LM Studio
- No multi-model escalation — all tasks go to the same model
- Lint: `ruff check` (bare command, not ecosystem runner — this was a known issue)
- Test: `pytest`

## Results

- **Tasks attempted:** 27 (all — no dependency cascade skips)
- **Duration:** ~42 minutes
- **Reflection exhaustion:** 20 out of 31 invocations (counting retries)
- **Clean passes:** 4 tasks (scaffold, schemas, extractors simple test, DAG test, downloader impl)
- **Timeouts:** 1 (task-25, DAG implementation at 600s)

### Dominant Failure Pattern

Qwen 3 Coder could not reliably fix `F401` (unused import, 107 occurrences) and
`I001` (import sorting, 80 occurrences) during Aider's reflection loop. The model
kept rewriting files with the same import ordering issue, sometimes making it worse,
burning through all 3 allowed reflection cycles.

### Code Quality

All expected files were created under `services/airflow-ingestion/` — plugins,
extractors, tests, dags, config, Dockerfile. The model produced code for all 27
tasks, but many exited with unresolved lint issues. The `verify_task` node
classified these as `degraded` rather than `failed`, allowing downstream tasks
to proceed.

## Root Causes

1. **Lint loop exhaustion (primary):** Qwen 3 Coder 30B cannot reliably auto-fix
   `I001`/`F401` ruff errors. Aider's `--auto-lint` feeds errors back after each
   edit, creating a futile retry cycle.
2. **Bare lint commands:** `ruff check` without `uv run` prefix — commands need
   ecosystem runners to work without an activated virtual environment.
3. **No auto-fix step:** Trivially fixable lint errors (`I001`, `F401`) were left
   to the model instead of being auto-fixed by `ruff check --fix` as a post-step.

## Skill Changes

1. Added lint auto-fix (`ruff check --fix`) as a post-executor step in `verify_task`
2. Commands switched to use ecosystem runners (`uv run ruff check`, `uv run pytest`)
3. Led to the multi-model escalation design for subsequent runs

## Key Learnings

- Local ~30B models cannot reliably fix import-related lint errors
- Auto-fix for trivially fixable errors should be a pipeline concern, not a model concern
- 27 tasks was too many — later decomposition runs reduced to 18
