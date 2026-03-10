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

### Trial Set 7 — After Conftest + UUIDStore + DAG Redesign (2026-03-10)
**Log**: `run-20260310-105632.log`
**Context**: 32,768 tokens
**Model**: Qwen 3 Coder 30B Q4
**Changes applied before this run** (Trial 6 root causes addressed):
- Conftest: `airflow.utils.task_group` added to `_AIRFLOW_MOCKS`
- Conftest: `sqlite_conn` fixture now sets `row_factory = sqlite3.Row`
- Task 06 (UUIDStore): new test `test_schema_initialized_on_construction` calls `mark_seen()` immediately after `UUIDStore(":memory:")` — directly tests that CREATE TABLE happens in `__init__`
- Task 12 (DAG): redesigned — `_extract_and_ingest` is now a module-level function (not a closure), directly importable and testable; conftest mock list explicitly enumerated in task doc
- Tasks 13–17: no fixture changes; rely on `sqlite_conn`
- `mock_fastavro_writer` fixture removed from conftest; task 04 (MinioWriter) switched to real fastavro roundtrip test with explicit arg-order callout in task doc

**Result**: 9/12 ✅, 3 degraded ⚠️ (tasks 1, 6, 12), halted at task 13 ❌ (tasks 14–18 not run)

| Task | Result | Notes |
|------|--------|-------|
| 01 Settings | ⚠️ DEGRADED | Module-level `settings = Settings()` blows up at import — no env vars |
| 02 BaseRecordExtractor | ✅ | |
| 03 GoogleDriveClient | ✅ | |
| 04 MinioWriter | ✅ | Second clean pass; real fastavro roundtrip passed |
| 05 RabbitmqPublisher | ✅ | |
| 06 UUIDStore | ⚠️ DEGRADED | Still `no such table: seen_uuids` — see analysis |
| 07 StepsExtractor | ✅ | |
| 08 BloodGlucoseExtractor | ✅ | |
| 09 HeartRateExtractor | ✅ | Third consecutive clean pass |
| 10 HRVExtractor | ✅ | |
| 11 SleepExtractor | ✅ | |
| 12 Airflow DAG | ⚠️ DEGRADED | `_extract_and_ingest` not exported at module level |
| 13 ActiveCaloriesExtractor | ❌ HALTED | aider false-positive; `test_dag.py` collection fails |
| 14–18 | NOT RUN | Blocked by task 13 halt |

#### Task 1 — Settings degraded (module-level instantiation at import)
The model wrote `settings = Settings()` at module level in `plugins/config/settings.py`.
`Settings` is a pydantic-settings `BaseSettings` subclass with 7 required fields (no
defaults). When any other module imports `settings`, the instantiation fires immediately at
import time — and without the required env vars set, pydantic raises `ValidationError: 7
validation errors for Settings`.

The test (`test_defaults_applied`) uses `_make_settings()`, which does a deferred
`import plugins.config.settings as mod` inside the function body — specifically to control
when the module loads. But the model placed the instantiation at top level, so even a
deferred import triggers the error. After 3 reflections the model made no progress — it
understood the error message but did not recognize that the fix was to either (a) make the
module-level singleton lazy, or (b) not instantiate at module level at all.

**Current state of settings.py**: Has `settings = Settings()` at module level, unchanged
from what the model wrote.

**Cascading effect**: Task 12 and task 13 both import `from plugins.config.settings import
settings`. With the module-level instantiation present, importing the DAG module also blows
up — which is why the DAG test can't even be collected (see task 12 and task 13 analyses).

#### Task 6 — UUIDStore degraded again (`no such table: seen_uuids`)
Despite the new `test_schema_initialized_on_construction` test that directly calls `mark_seen()`
immediately after construction, the model still produced a `UUIDStore` that doesn't call
CREATE TABLE in `__init__`. Looking at the final state of `uuid_store.py`: the model
implemented `_init_schema()` as a separate method that contains the CREATE TABLE call, and
called `self._init_schema()` from `__init__`. The schema initialization IS present —
but the model used `sqlite3.connect(self.db_path)` for schema init and again separately in
`mark_seen()`.

**Root cause for `:memory:` databases**: Each call to `sqlite3.connect(":memory:")` creates
a completely independent in-memory database. `_init_schema()` creates the table in one
in-memory database instance; `mark_seen()` opens a fresh connection which is a different
empty database entirely — so `seen_uuids` does not exist in that connection. The model's
`_init_schema()` design is correct for file-backed databases (where the file persists between
connections) but broken for `:memory:`.

The model received the `no such table: seen_uuids` error repeatedly across 3 reflections and
each time adjusted `mark_seen()` (swapping timestamp queries, reordering statements) without
ever diagnosing that the root cause was a fresh connection opening a fresh empty database.

**Generic principle this surfaces**: The `:memory:` SQLite database is a trap for any
persistence class that opens a new connection per method call. The correct pattern for `:memory:`
testing is to hold a single connection open for the lifetime of the object. This is a
design constraint that should be explicit in the task doc — either mandate single-connection
design, or use a `file::memory:?cache=shared` URI that allows multiple connections to the
same in-memory database. It is not sufficient to just test for schema initialization in the
gate; the test harness must also prevent the multi-connection anti-pattern from hiding the
real failure.

#### Task 12 — Airflow DAG degraded (`_extract_and_ingest` not importable)
`test_dag.py` does `from dags.health_connect_ingest import _extract_and_ingest`. The model
defined `_extract_and_ingest` as a closure (nested function inside `create_dag()`), not as a
module-level function. So when pytest tries to import it from the module, it is not found.

Additionally, importing `dags.health_connect_ingest` triggers the settings cascade failure
from task 1 (see above) — `from plugins.config.settings import settings` at the top of the
DAG file fires module-level Settings instantiation, which raises `ValidationError`.

The model received two distinct errors across 3 reflections: first the settings
`ValidationError`, then (after partially fixing that) the `ImportError: cannot import name
'_extract_and_ingest'`. It addressed each partially but exhausted reflections before resolving
either. Aider eventually exited 0 (false positive), but the runner's independent pytest
verification caught the failure and marked degraded (continued rather than halted, unlike
Trial 6 — the runner's halt/degrade decision is based on whether aider exited 0 or non-zero).

#### Task 13 — ActiveCaloriesExtractor halted (test_dag.py collection failure)
Aider completed the active calories implementation and exited 0 after one reflection that
fixed `from typing import Any, list` (invalid in Python 3.11 — `list` is a builtin, not in
`typing`). However, the runner's independent pytest invocation runs the full test suite, not
just the task-specific test file. `test_dag.py` was already broken from task 12, and its
import error caused pytest to exit 2 (collection error) — which the runner correctly
interprets as a real failure.

**Why this halted instead of degraded**: Aider exited 0 (it thought the task succeeded).
The runner's independent verification failed (exit 2). This is the same false-positive
detection that halted Trial 6 at task 12. The runner prints "Tests are failing but aider
reported success" and stops with `re-run with: ./run-tasks.sh --start 13`.

**Root cause**: The `test_dag.py` breakage from task 12 bleeds into all subsequent tasks
because the runner's final verification runs the full suite. Any task from 13 onward will
appear to fail as long as `test_dag.py` cannot be collected.

---

## Generated Code Quality Assessment (updated 2026-03-10 after Trial Set 7)

### Infrastructure

| Component | Status | Notes |
|-----------|--------|-------|
| Settings | ⚠️ | Module-level `settings = Settings()` blows up at import without env vars; needs lazy singleton or deferred init |
| BaseRecordExtractor | ✅ | |
| GoogleDriveClient | ✅ | streaming download loop, correct error types |
| MinioWriter | ✅ | fixed in Trial 6, confirmed again in Trial 7 |
| RabbitmqPublisher | ✅ | minor: hardcoded timestamp placeholder |
| UUIDStore | ⚠️ | Multi-connection design broken for `:memory:`; needs single persistent connection |

### Extractors

| Extractor | Status | Notes |
|-----------|--------|-------|
| StepsExtractor | ✅ | |
| BloodGlucoseExtractor | ✅ | |
| HeartRateExtractor | ✅ | 3rd consecutive clean pass |
| HRVExtractor | ✅ | |
| SleepExtractor | ✅ | |
| ActiveCaloriesExtractor | ⚠️ | Aider succeeded but test_dag.py cascade blocked verification |
| Distance, TotalCalories, O2Sat, ExerciseSession | NOT RUN | Blocked by task 13 halt |

### DAG — blocked
`_extract_and_ingest` defined as a closure (not module-level). Settings cascade also blocks
import. Both need fixing before tasks 13–18 can be verified.

---

## Open Issues

1. **Settings — module-level instantiation**: `settings = Settings()` at module top-level
   causes `ValidationError` at import time in any test environment without env vars. Needs
   to be lazy (e.g. `_settings = None` + a `get_settings()` accessor) or removed from module
   level entirely. This cascades into DAG task 12 and all subsequent tasks.

2. **UUIDStore — multi-connection `:memory:` trap**: Schema is initialized correctly but in
   a separate connection from the one used by `mark_seen()`. For `:memory:` databases each
   `sqlite3.connect(":memory:")` is a fresh empty database. Fix: hold a single connection as
   `self._conn` for the object lifetime, or use `file::memory:?cache=shared` URI mode.

3. **Airflow DAG — `_extract_and_ingest` as closure**: Model nested it inside `create_dag()`
   rather than defining it at module level. Test imports it from module scope — not found.
   Fix: move `_extract_and_ingest` out of `create_dag()` to module level.

4. **Task 13+ blocked by test_dag.py**: Any run starting at task 13 will halt immediately
   because the full-suite verification catches the `test_dag.py` collection error from the
   broken DAG. Must fix task 12 first, then re-run from task 12.

5. **Summarizer fast failures**: "cannot schedule new futures after shutdown" after each task —
   harmless but noisy. Real fix: `stream: false` in aider config or LM Studio `max_tokens` cap.

6. **Context length — do not reduce below 32k**: See Trial Set 4.

7. **Tasks 14–18 not run**: Once tasks 1, 6, 12 are fixed, re-run from task 12.

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
