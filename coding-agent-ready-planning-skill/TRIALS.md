# Coding Agent Ready Planning Skill — Trial Log

> **Purpose**: Persistent memory across chat sessions for the `devtools:agent-ready-plans` and
> `devtools:implementation-planning` skills. Each entry documents a trial run, findings, and
> any skill/script changes made. Read this at the start of every new chat in this project.
>
> **Skill location**: `~/claude-devtools/skills/agent-ready-plans/`
> **Test project**: `~/health-data-ai-platform` (airflow Google Drive ingestion service)

---

## Skill Overview

Two paired skills:
1. **`devtools:implementation-planning`** — turns a feature idea into a design doc + implementation plan with interface contracts and behavioral specs
2. **`devtools:agent-ready-plans`** — takes those artifacts and produces self-contained task files + scaffold + runner script for local coding agents (Aider + local models via LM Studio)

**Key architectural decision**: Claude Code writes complete, verified tests for each task (TDD approach). The small local model implements the code to make them pass. Claude Code owns test correctness — the small model owns implementation.

---

## Skill File Structure

```
claude-devtools/
  commands/
    agent-ready.md
    plan.md
  skills/
    agent-ready-plans/          <- FLAT under skills/ (nesting causes --plugin-dir failures)
      SKILL.md
      task-template.md
      references/
        writing-guide.md
        tooling.md
      scripts/
        lint-ruff-wrapper.sh
        run-tasks-template.sh
    implementation-planning/
      SKILL.md
      references/
        plan-format.md
        wiring-completeness.md
```

---

## Strategy History

### Strategy 1: Code-Complete Tasks (abandoned)
Claude Code wrote full implementation + tests. Small model transcribed code from plan.

**Result**: Worked well for Codestral 22B (~90% success) because it minimized what the model
had to figure out. Failed when plan had subtle bugs (wrong mock scopes, metaprogramming
patterns) — model exhausted reflections on code it didn't write and couldn't understand.

### Strategy 2: Spec-Based Tasks (abandoned)
Claude Code defines interface contracts + behavioral specs only. Small model writes both
implementation and tests.

**Problem**: Requires a model that can write correct code from specs. Neither Codestral 22B
nor Qwen 30B Q4 clears that bar reliably.

### Strategy 3: TDD — Claude Code Writes Tests (current)
Claude Code writes complete, verified tests per task (Step 3b in SKILL.md). Small model
implements to make them pass. Mutation gate verifies test quality before handoff.

---

## Trial Runs

### Trial Set 1 — Initial Strategy Comparison (2026-02-27 to 2026-03-02)
**Plan**: Airflow Google Drive ingestion service
**Models**: Codestral 22B, Qwen 3 Coder 30B Q4 (via LM Studio)

| Run | Model | Format | Fixtures | Result |
|-----|-------|--------|----------|--------|
| 1 | Codestral 22B | Code-based | None | 12/13 (plan bugs halted) |
| 2 | Codestral 22B | Code-based fixed | None | 6/10 (plan bugs halted) |
| 3 | Codestral 22B | Spec-based | None | 1/15 (wrong imports, cascade) |
| 4 | Qwen 30B Q4 | Spec-based | None | 2/3 (OOM crash) |
| 5 | Qwen 30B Q4 | Spec-based | None | 2/4 (thinking spiral, cascade) |
| 6 | Qwen 30B Q4 | Spec-based | Yes | 1/4 (logic bugs, cascade) |

**Key finding**: Bottleneck is model capability. Codestral reliable as typist (code-based).
Qwen 30B reasons better but fails on non-trivial logic. Spec-based needs ~GPT-4 level model.

---

### Trial Set 2 — TDD Approach (2026-03-03)
**Model**: Qwen 3 Coder 30B Q4
**Tasks**: 18 implementation + 1 deferred
**Result**: 16/18 completed before interruption

**Task 4 (MinioWriter) — DEGRADED**: Model doesn't know `fastavro.writer` API.
Correct: `fastavro.writer(fo, schema, records)`. Model always swapped args 2 and 3.
Recurring bug — also hit by Codestral in Trial 1.

**Tasks 17 + 18 — STUCK (summarizer spiral)**: After task completion, aider fires a
post-task summarization call (~1,557 prompt tokens). Model generates ~25,000 completion
tokens (18-19x ratio). Aider retries every ~10 min indefinitely. Ctrl-C ineffective —
`aider ... | tee` pipeline swallows SIGINT.

---

### Trial Set 3 — After Runner Fixes (2026-03-04 morning)
**Log**: `run-20260304-114920.log`
**Result**: 13 completed, 4 degraded

**`--timeout` ineffective with streaming**: Aider's `--timeout` caps HTTP connection setup
but LM Studio uses `stream: true`. Once streaming starts, timeout never triggers regardless
of generation length. Summarizer spiral still ran (25,439 tokens at 12:02, 25,536 at 12:12).

**`timeout` shell wrapper tried and reverted**: Wrapping aider in `timeout 600 aider ...`
broke Ctrl-C entirely — `tee` pipeline kept pipe alive after timeout killed aider.

**Git restore bug**: Claude Code saw deleted task files in git HEAD, ran
`git checkout HEAD --` and stopped — never re-reading updated skill files. Step 0 added
to SKILL.md to prevent this.

---

### Trial Set 4 — 12k Context Experiment (2026-03-04 afternoon)
**Log**: `run-20260304-150619.log`
**Context**: 12,000 tokens (reduced from 32k to test if smaller window helps)
**Result**: Crashed at task 9 (HeartRateExtractor) — earlier than task 17-18 in prior runs

**Failure mode**: Metal GPU OOM — `[metal::malloc] Resource limit (499000) exceeded` — a
hard segfault, not a summarizer spiral. The model crashed mid-generation at 15:16:10 after
successfully processing 100% of the prompt at 15:12:17 (4-minute generation before crash).

**Root cause — KV cache sizing**: MLX pre-allocates a fixed GPU memory block sized to hold
exactly N token positions, where N is the configured context length. With 12k that block is
~3x smaller than with 32k. Task 9 required 6 reflection loops; by reflection 6, the live
aider conversation had grown to 24 messages. The prompt for that request was ~3k tokens, but
the KV cache must hold both prompt AND generated output simultaneously. When generated output
tokens drove the total past ~12k mid-generation, the Metal allocator ran out of its pre-reserved
block and segfaulted.

**Why smaller context makes it worse, not better**:
- Reducing context length does NOT reduce the difficulty of the task or the number of reflections
- It DOES reduce how much KV cache memory MLX pre-allocates on the GPU
- A hard task (many reflections, long conversation) hits the smaller ceiling sooner
- The summarizer cannot help: it fired successfully at 15:11:52 (compressing past task history),
  but the current task's 6 reflection messages stay in full and alone exceed 12k

**Confirmed**: With 32k, task 9's 24-message conversation was ~10% of the window — no pressure.
With 12k, the same conversation exceeded 100% of available KV cache mid-generation.

**Conclusion**: Do not reduce context length below 32k for Qwen 30B on this task set. The
summarizer spiral (task 17-18 with 32k) is a different, less catastrophic failure — it stalls
rather than crashing the model process entirely.

---

### Trial Set 5 — Reverted Abstract-Class Patch + 32k Context (2026-03-04 evening)
**Log**: `run-20260304-155543.log`
**Context**: 32,768 tokens (restored from 12k)
**Change**: Reverted the abstract-class-method patch on base extractor plan to test whether
it was helping or hurting prior runs.
**Result**: Task 18 (Docker deployment) completed. Script hung on HeartRateExtractor (task 9).

#### What completed successfully
All tasks ran and passed their full test suites with 95 tests collected at end:
- Task 1 (Settings), Task 2 (BaseRecordExtractor), Task 3 (GoogleDriveClient)
- Task 4 (MinioWriter) — see degraded note below
- Task 5 (RabbitmqPublisher), Task 6 (UUIDStore)
- Tasks 7–8, 10–17 (all extractors except HeartRateExtractor), Task 18 (Docker)

#### Hang location — HeartRateExtractor summarizer spiral
The script did NOT hang at the end (tasks 17-18) as in Trial Set 2. It hung mid-run on
**task 9 (HeartRateExtractor)**. The summarizer spiral triggered immediately after each
successful task completion throughout the run, logging:

```
Summarization failed for model lm_studio/qwen/qwen3-coder-30b: cannot schedule new futures after shutdown
summarizer unexpectedly failed for all models
```

This "cannot schedule new futures after shutdown" message appeared after every task — but
these are fast failures (summarizer gives up immediately). The real spiral came from the
model's reflection loop during task 9 itself.

#### MinioWriter — fastavro degradation (same as prior runs)
The model attempted three strategies in sequence:
1. `fastavro.writer(avro_buffer, records)` → TypeError: takes at least 3 args
2. `fastavro.writer(avro_buffer, records, None)` → KeyError: 'type' (None is not a valid schema)
3. Back to 2 args → same TypeError

**Current state of minio_writer.py**: Has `fastavro.writer(avro_buffer, records, None)` —
still wrong. Tests are failing.

#### HeartRateExtractor — fundamental contract mismatch
**Root cause**: HeartRateExtractor needs to override `extract()` entirely (doing its own
GROUP BY aggregation in the query and accumulating samples in a loop), not just
`_to_avro_dict`. The base class template is the wrong abstraction for multi-row-per-record
cases.

---

### Trial Set 6 — Skill Updates Applied (2026-03-09)
**Log**: `run-20260309-123229.log`
**Context**: 32,768 tokens
**Model**: Qwen 3 Coder 30B Q4
**Changes applied before this run**:
- `plan-format.md`: ABC contract fit verification guidance (verify base class calling convention before writing interface; document `extract()`-level override pattern for multi-row-per-record cases)
- `tooling.md`: Positional argument trap fixture criterion + `mock_fastavro_writer` fixture example
- `run-tasks-template.sh`: Corrected `--timeout` comment (caps HTTP setup only, not streaming)
- New conftest fixture: `mock_fastavro_writer` patches `fastavro.writer`, captures `(schema, records)`, writes `b"AVRO_MOCK_BYTES"` to `fo`
- Task 09 (HeartRateExtractor): respecified to override `extract()` directly with explicit callout that `_to_avro_dict` is NOT used

**Result**: 11/18 ✅, 1 degraded ⚠️ (task 6), halted at task 12 ❌

| Task | Result | Notes |
|------|--------|-------|
| 01 Settings | ✅ | |
| 02 BaseRecordExtractor | ✅ | |
| 03 GoogleDriveClient | ✅ | |
| 04 MinioWriter | ✅ | Fixed — `mock_fastavro_writer` fixture worked |
| 05 RabbitmqPublisher | ✅ | |
| 06 UUIDStore | ⚠️ DEGRADED | `no such table: seen_uuids` — `__init__` didn't call CREATE TABLE |
| 07 StepsExtractor | ✅ | |
| 08 BloodGlucoseExtractor | ✅ | |
| 09 HeartRateExtractor | ✅ | Fixed — override pattern worked, no hang |
| 10 HRVExtractor | ✅ | |
| 11 SleepExtractor | ✅ | |
| 12 Airflow DAG | ❌ HALTED | `airflow.utils.task_group` not in conftest mock list |
| 13–18 | NOT RUN | Blocked by task 12 halt |

#### Notable wins
- **MinioWriter (task 4)**: First clean pass in any trial. The `mock_fastavro_writer` fixture completely bypassed the arg-order trap. The skill fix worked exactly as intended.
- **HeartRateExtractor (task 9)**: Passed cleanly with no hang. The ABC override pattern in `plan-format.md` + the explicit task-level callout prevented the reflection spiral that had blocked every prior run.

#### Task 6 — UUIDStore degraded (`no such table: seen_uuids`)
The model implemented `mark_seen()` correctly — SQL, `INSERT OR IGNORE`, `executemany` all
correct. But `__init__` did not call the table creation step before returning. The error is
immediate: the test fixture creates `UUIDStore(":memory:")` and calls `mark_seen()` directly,
so the table must exist after `__init__` completes. After 3 reflections the model didn't add
the missing call.

**Root cause**: The mutation gate stub for UUIDStore was not testing for missing schema
initialization. A stub with `__init__: pass` would have failed the first `mark_seen` call
and flagged this as a required assertion — but if the stub already had the CREATE TABLE call,
the gate couldn't detect this class of omission.

**Generic principle**: For persistence classes, the mutation gate stub must deliberately omit
schema initialization. This is now documented in `tooling.md`.

#### Task 12 — Airflow DAG halted (`airflow.utils.task_group` not mocked)
The model imported `from airflow.utils.task_group import TaskGroup`. The conftest
`_AIRFLOW_MOCKS` list included `airflow.utils` but not `airflow.utils.task_group`. Python
sees `airflow.utils` as a `MagicMock` object (not a package), so submodule attribute access
as an import raises `ModuleNotFoundError: No module named 'airflow.utils.task_group';
'airflow.utils' is not a package`.

The task doc explicitly told the model "`TaskGroup` is mocked in tests" — a broken promise,
since the conftest never registered that submodule path. The model had no way to fix this
(the fix is in conftest, not in the implementation file). After 3 reflections aider exited 0
(false positive), but the runner's independent test verification caught the failure and halted.

**Why halted (not degraded)**: The runner marks a task degraded when aider exhausts
reflections and exits non-zero. Here aider exited 0 — it thought it succeeded. The runner's
independent pytest verification caught the mismatch and halted with instructions to fix and
re-run from task 12. This is the correct behavior: a false-positive success is more dangerous
than a known failure, so the runner stops rather than propagating a broken module.

**Generic principle**: For any dotted import path `a.b.c` the implementation will use,
`a`, `a.b`, and `a.b.c` must all be registered separately in `sys.modules`. And the conftest
must be verified with a bare module import before task docs are generated. This is now
documented in `tooling.md`.

---

## Generated Code Quality Assessment (updated 2026-03-09 after Trial Set 6)

### Infrastructure

| Component | Status | Notes |
|-----------|--------|-------|
| Settings | ✅ | pydantic v2, env_prefix, extra="ignore" |
| BaseRecordExtractor | ✅ | |
| GoogleDriveClient | ✅ | streaming download loop, correct error types |
| MinioWriter | ✅ | fixed in Trial 6 via mock_fastavro_writer fixture |
| RabbitmqPublisher | ✅ | minor: hardcoded timestamp placeholder |
| UUIDStore | ⚠️ | missing CREATE TABLE in __init__; needs re-run |

### Extractors

| Extractor | Status | Notes |
|-----------|--------|-------|
| StepsExtractor | ✅ | |
| BloodGlucoseExtractor | ✅ | |
| HeartRateExtractor | ✅ | fixed in Trial 6 via override pattern |
| HRVExtractor | ✅ | |
| SleepExtractor | ✅ | row_factory assumption may be fragile |
| ActiveCalories, Distance, TotalCalories, O2Sat, ExerciseSession | NOT RUN | blocked by task 12 halt |

### DAG — blocked
Task 12 halted at import. Tasks 13–18 did not run.

---

## Open Issues

1. **UUIDStore — missing schema init**: `__init__` doesn't call CREATE TABLE. One-line fix.
   Re-run with `--start 6`.

2. **Airflow DAG — conftest mock gap**: `airflow.utils.task_group` missing from `_AIRFLOW_MOCKS`.
   Add it to conftest, then re-run with `--start 12`. Also audit for any other submodule paths
   the DAG uses (e.g. `airflow.utils.task_group` was added by the model spontaneously — scan
   the generated DAG file for all `from airflow.*` imports and cross-check against the mock list).

3. **Tasks 13–18 not run**: Once task 12 is fixed, re-run from task 12 to complete the set.

4. **Summarizer spiral / hang**: `--timeout` doesn't work with streaming. No longer hanging
   (HeartRateExtractor fix eliminated the main spiral source) but the fast summarizer failures
   ("cannot schedule new futures after shutdown") still appear after each task. Harmless but noisy.
   Real fix: `stream: false` in aider config, or server-side `max_tokens` cap in LM Studio.

5. **Context length — do not reduce below 32k**: Smaller context pre-allocates a smaller MLX
   KV cache. Hard tasks with many reflections hit the ceiling mid-generation and segfault the
   model process entirely. See Trial Set 4.

6. **row_factory assumption**: SleepExtractor uses `row["key"]` access. Needs `conn.row_factory
   = sqlite3.Row` set in `base.extract()` or enforced across all extractors.

7. **DAG wiring — tasks 13-17 extractors missing**: The DAG was assembled before extractors
   13-17 (ActiveCalories, Distance, etc.) existed. `EXTRACTORS` list only has 5 entries; the
   remaining extractors need to be wired in as a follow-up or the DAG task needs to be
   deferred until after all extractors exist.

---

## Skill Changes Log

| Date | File | Change |
|------|------|--------|
| 2026-03-03 | `run-tasks-template.sh` | Added `--timeout 600` to aider invocation |
| 2026-03-03 | `references/writing-guide.md` | Added ABC call site rule |
| 2026-03-04 | `SKILL.md` | Added Step 0: prohibit `git checkout HEAD` restoration of stale artifacts |
| 2026-03-04 | `SKILL.md` Step 7 | Added: do not restore `run-tasks.sh` from git, always copy from template |
| 2026-03-04 | `run-tasks-template.sh` | Reverted `timeout` shell wrapper; kept `--timeout` aider flag |
| 2026-03-08 | `references/plan-format.md` | Added ABC contract fit verification guidance; `extract()`-level override pattern for multi-row-per-record extractors |
| 2026-03-08 | `references/tooling.md` | Added positional argument trap fixture criterion; `mock_fastavro_writer` example |
| 2026-03-08 | `run-tasks-template.sh` | Corrected `--timeout` comment (caps HTTP setup only, not streaming generation) |
| 2026-03-09 | `references/tooling.md` | Added "Mocking Framework Modules" subsection: every dotted import path must be registered separately in sys.modules; verification step via bare module import before task doc generation |
| 2026-03-09 | `references/tooling.md` | Added persistence class note to "Verifying Fixtures": mutation gate stub must omit schema initialization so tests catch missing CREATE TABLE |
