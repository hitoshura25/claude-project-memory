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
        stacks/
          python-pytest.md      <- Python-specific: uv/pip, ruff wrapper, fixtures, mutmut
          typescript-jest.md    <- TypeScript/Jest stub
          kotlin-junit.md       <- Kotlin/JUnit/Gradle stub
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
hard segfault, not a summarizer spiral.

**Root cause — KV cache sizing**: MLX pre-allocates a fixed GPU memory block sized to hold
exactly N token positions. With 12k that block is ~3x smaller than with 32k. Task 9 required
6 reflection loops; by reflection 6 the live conversation had grown to 24 messages. The KV
cache must hold both prompt AND generated output simultaneously — when generated output drove
the total past ~12k mid-generation, the Metal allocator segfaulted.

**Conclusion**: Do not reduce context length below 32k for Qwen 30B on this task set.

---

### Trial Set 5 — Reverted Abstract-Class Patch + 32k Context (2026-03-04 evening)
**Log**: `run-20260304-155543.log`
**Result**: Task 18 completed. Script hung on HeartRateExtractor (task 9).

HeartRateExtractor: fundamental contract mismatch. Needs to override `extract()` entirely
(GROUP BY aggregation in query, accumulating samples in loop), not just `_to_avro_dict`.
Base class template is the wrong abstraction for multi-row-per-record cases.

---

### Trial Set 6 — Skill Updates Applied (2026-03-09)
**Log**: `run-20260309-123229.log`
**Context**: 32,768 tokens
**Model**: Qwen 3 Coder 30B Q4
**Result**: 11/18 ✅, 1 degraded ⚠️ (task 6), halted at task 12 ❌

| Task | Result | Notes |
|------|--------|-------|
| 01–05 | ✅ | Settings, BaseRecordExtractor, GoogleDriveClient, MinioWriter (fixed — mock_fastavro_writer worked), RabbitmqPublisher |
| 06 UUIDStore | ⚠️ | `no such table: seen_uuids` — `__init__` didn't call CREATE TABLE |
| 07–11 | ✅ | StepsExtractor, BloodGlucose, HeartRate (fixed — override pattern worked), HRV, Sleep |
| 12 Airflow DAG | ❌ | `airflow.utils.task_group` not in conftest mock list |
| 13–18 | NOT RUN | |

**Task 6 root cause**: Mutation gate stub already had CREATE TABLE — couldn't detect missing
call. Fix: stub must deliberately omit schema init so tests catch the omission.

**Task 12 root cause**: `airflow.utils` registered in sys.modules but not `airflow.utils.task_group`.
Python sees the parent as a MagicMock object (not a package) — importing a submodule fails.
Fix: every dotted path prefix must be registered separately. Conftest must be verified with a
bare import before task docs are generated.

---

### Trial Set 7 — After Conftest + UUIDStore + DAG Redesign (2026-03-10 morning)
**Log**: `run-20260310-105632.log`
**Context**: 32,768 tokens
**Model**: Qwen 3 Coder 30B Q4
**Result**: 9/12 ✅, 3 degraded ⚠️ (tasks 1, 6, 12), halted at task 13 ❌

| Task | Result | Notes |
|------|--------|-------|
| 01 Settings | ⚠️ | Module-level `settings = Settings()` — ValidationError at import |
| 02–05 | ✅ | |
| 06 UUIDStore | ⚠️ | Still `no such table` — multi-connection `:memory:` trap (each connect creates new DB) |
| 07–11 | ✅ | |
| 12 Airflow DAG | ⚠️ | `_extract_and_ingest` defined as closure despite task doc specifying module-level |
| 13 ActiveCaloriesExtractor | ❌ HALTED | Implementation correct but `test_dag.py` broken from task 12 — **cascade** |
| 14–18 | NOT RUN | Blocked |

**Cascade analysis (task 13)**: ActiveCalories implementation was correct — it was halted
because its test_command included `test_dag.py`, which was broken from task 12. This is the
critical structural problem: extractor tasks had inline DAG wiring steps, meaning `test_dag.py`
was gated in every extractor's command. A single broken DAG task cascades to all downstream
extractors regardless of their individual correctness.

---

### Trial Set 8 — Codestral 22B Head-to-Head (2026-03-10)
**Model**: Codestral 22B v0.1
**Result**: 5/18 ✅, 13 degraded ⚠️, 0 halts

**Codestral-specific failure modes:**
- Leaves `raise NotImplementedError` in method bodies (partial implementation)
- Class naming inconsistency: `MinIOWriter` vs expected `MinioWriter`
- **Edits test files when stuck** — corrupted `test_dag.py` to `assert 1 == 10` by task 18

**Where Codestral beats Qwen**: Task 6 (UUIDStore) — used persistent `self._conn` correctly.
**Where Qwen beats Codestral**: Tasks 3, 4, 5, 7, 9, 11 — better naming discipline, no stubs left.

---

### Trial Set 9 — Gemini 2.0 Flash Lite Head-to-Head (2026-03-10 afternoon)
**Model**: `gemini/gemini-2.0-flash-lite-preview` (Gemini API)
**Result**: 12/13 ✅, 1 degraded ⚠️ (task 13), halted at task 14 ❌

| Task | Qwen T7 | Codestral T8 | Gemini T9 | Notes |
|------|---------|--------------|-----------|-------|
| 01 Settings | ⚠️ | ⚠️ | ✅ | Gemini: LazySettings proxy with @cached_property, self-diagnosed |
| 02–05 | ✅ | mixed | ✅ | |
| 06 UUIDStore | ⚠️ | ✅ | ✅ | Gemini: self._conn persistent connection |
| 07–11 | ✅ | mixed | ✅ | |
| 12 Airflow DAG | ⚠️ | ⚠️ | ✅ | Gemini: first model to pass — but added hallucinated import |
| 13 ActiveCaloriesExtractor | ❌ | ⚠️ | ⚠️ | Gemini: correct impl; cascaded from hallucinated DAG import |
| 14–18 | NOT RUN | mixed | NOT RUN | |

**Task 12 — Gemini passed but hallucinated**: Added `from plugins.extractors.sleep_session_extractor
import SleepSessionExtractor` — a module that doesn't exist. Task 12's test suite passed
(count was 5 including the hallucinated class). Surfaced at task 13 full-suite collection.

**Root cause of all T6-T9 cascades**: Every extractor task had an inline `Modify: dags/...`
step and `test_dag.py` in its `test_command`. When the DAG task degraded, all downstream
extractors failed their gates regardless of their own correctness. This is a structural plan
problem, not a model capability problem.

---

### Trial Set 10 — Qwen Coder After Cascade Fix + Settings Fix (2026-03-12)
**Log**: `run-20260312-112908.log`
**Model**: Qwen 3 Coder 30B (via LM Studio) — `lm_studio/qwen/qwen3-coder-30b`
**Context**: 32,768 tokens
**Skill state**: Post cascade-fix (component/wiring separation) + post settings fix (no module-level singleton in interface contracts)
**Result**: 15/17 ✅, 2 degraded ⚠️ (tasks 2, 17), task 16 completed with lint warnings

| Task | Result | Notes |
|------|--------|-------|
| 01 Settings | ✅ | **Fixed** — no module-level instantiation. Passed cleanly first attempt. |
| 02 UUIDStore | ⚠️ DEGRADED | New SQL bug — see below |
| 03 BaseRecordExtractor | ✅ | |
| 04 GoogleDriveClient | ✅ | |
| 05 MinIOWriter | ✅ | |
| 06 RabbitMQPublisher | ✅ | |
| 07–11 | ✅ | All 5 extractors (Steps, BloodGlucose, HeartRate, HRV, Sleep) |
| 12–15 | ✅ | All 4 secondary extractors (ActiveCalories, Distance, TotalCalories, OxygenSaturation) |
| 16 ExerciseSessionExtractor | ✅ (⚠️ lint) | Tests pass; aider exhausted reflections on E501 lint in pre-written test file |
| 17 Docker | ⚠️ DEGRADED | No test_command — degraded due to UUIDStore full-suite leak |

**Cascade isolation confirmed**: Tasks 07–16 all passed with `test_command` scoped to their
own test files only. UUIDStore's broken state did NOT cascade to any extractor.

**Settings fix confirmed**: Task 01 passed on first attempt with no module-level instantiation.

#### Task 02 — UUIDStore: SQLite Multi-Column IN Clause

**Error**: `sqlite3.OperationalError: IN(...) element has 1 term - expected 2`

**Root cause**: Model used `WHERE (uuid_hex, record_type) IN (?, ?, ?, ?)` — a multi-column
row-value constructor that SQLite does not support. All 3 reflections tried variations of the
same flattened-params approach; none escaped the pattern.

**Correct approach**: Single-column IN with `AND record_type = ?`:
```python
placeholders = ','.join('?' * len(uuids))
query = f"SELECT uuid_hex FROM seen_uuids WHERE uuid_hex IN ({placeholders}) AND record_type = ?"
cursor = self._conn.execute(query, [*uuids, record_type])
```

**Fix needed**: Task doc Behavior section must provide this SQL pattern explicitly.

#### Task 17 — Docker: UUIDStore Full-Suite Leak

Runner ran full suite for verification (no `test_command`), picked up 7 failing UUIDStore
tests. Docker files were likely generated correctly — this is a verification artifact.

---

### Trial Set 11 — Codestral 22B After Cascade Fix (2026-03-12)
**Log**: `run-20260312-115442.log`
**Model**: Codestral 22B v0.1 (via LM Studio) — `lm_studio/mistralai/codestral-22b-v0.1`
**Context**: 32,768 tokens
**Skill state**: Same as T10 — post cascade-fix + post settings fix
**Result**: 7/17 ✅, 9 degraded ⚠️, 1 warning, 0 halts

| Task | Result | Notes |
|------|--------|-------|
| 01 Settings | ✅ | Passed — settings fix holds for Codestral too |
| 02 UUIDStore | ⚠️ DEGRADED | **Lint spiral** — correct SQL logic but E501 on INSERT string literal; all 3 reflections spent on line-length, never ran tests |
| 03 BaseRecordExtractor | ⚠️ DEGRADED | Lint spiral — E501 on list comprehension in `extract()`; exit 5 (no tests ran) |
| 04 GoogleDriveClient | ⚠️ DEGRADED | **Edit format failure** — when stuck on `no tests ran`, produced prose + command; aider rejected non-conforming output; exit 5 |
| 05 MinIOWriter | ⚠️ DEGRADED | Lint spiral — E501 on `__init__` signature; exit 5 |
| 06 RabbitMQPublisher | ⚠️ DEGRADED | **Test file corruption** — replaced entire test file with `# ... rest of the test code ...` stub; exit 5 |
| 07 StepsExtractor | ✅ | |
| 08 BloodGlucoseExtractor | ✅ | |
| 09 HeartRateExtractor | ⚠️ DEGRADED | **ABC not implemented** — overrode `extract()` but omitted `_row_to_record()` stub; `Can't instantiate abstract class` |
| 10 HRVRmssdExtractor | ✅ | |
| 11 SleepExtractor | ⚠️ DEGRADED | Same as task 09 — `_row_to_record()` missing |
| 12 ActiveCaloriesExtractor | ✅ | |
| 13 DistanceExtractor | ⚠️ DEGRADED | Test file corruption — `# ... rest of the code...` stub; exit 5 |
| 14 TotalCaloriesExtractor | ✅ | |
| 15 OxygenSaturationExtractor | ⚠️ DEGRADED | Test file corruption — `# ... rest of the code...` stub; exit 5 |
| 16 ExerciseSessionExtractor | ✅ (⚠️ lint) | Tests pass; E501 lint in pre-written test file |
| 17 Docker | ⚠️ DEGRADED | UUIDStore full-suite leak |

Codestral confirmed disqualified: lint loops, test file corruption, incomplete ABC, edit format
failures are all consistent model-level behaviours not addressable through task doc improvements.

---

### Trial Set 12 — Gemini 3.1 Flash Lite Preview — Clean Sweep (2026-03-12)
**Log**: `run-20260312-132307.log` (primary); `run-20260312-132242.log` (aborted restart)
**Model**: `gemini/gemini-3.1-flash-lite-preview` (Gemini API)
**Skill state**: Same as T10/T11 — post cascade-fix + post settings fix. No additional task doc changes since T10.
**Result**: **17/17 ✅ — first complete clean sweep across all component tasks**

| Task | Result | Notes |
|------|--------|-------|
| 01 Settings | ✅ | |
| 02 UUIDStore | ✅ | **SQL pattern correct on first attempt** — `WHERE record_type = ? AND uuid_hex IN (...)` with `[record_type] + uuids` params; single-column IN, no row-value constructor |
| 03 BaseRecordExtractor | ✅ | |
| 04 GoogleDriveClient | ✅ | |
| 05 MinIOWriter | ✅ | |
| 06 RabbitMQPublisher | ✅ | |
| 07–08 | ✅ | StepsExtractor, BloodGlucoseExtractor |
| 09 HeartRateExtractor | ✅ | Override pattern followed correctly; 2 reflections |
| 10 HRVRmssdExtractor | ✅ | |
| 11 SleepExtractor | ✅ | Override pattern followed correctly; 2 reflections |
| 12–15 | ✅ | ActiveCalories, Distance, TotalCalories, OxygenSaturation |
| 16 ExerciseSessionExtractor | ✅ | **Fixed E501 in pre-written test file** — rewrote `CREATE TABLE` string splits and INSERT line across lines; 2 reflections; 4 tests pass |
| 17 Docker | ✅ | 89 tests pass in full-suite verification; no UUIDStore leak |

**Total LLM calls across entire run**: 27 (including all reflections). Extremely efficient.

**Zero test failures, zero degraded tasks, zero halts.**

---

#### T12 Notable Behaviours

**UUIDStore SQL — immediate correct pattern**: Without any hint in the task doc, Gemini used
`WHERE record_type = ? AND uuid_hex IN (placeholders)` with params `[record_type] + uuids`.
This is the correct single-column approach. Also used composite `PRIMARY KEY (uuid_hex, record_type)`
in the schema. Did not attempt the multi-column IN constructor that broke Qwen T10.

**ExerciseSession test file E501 — self-corrected**: Task 16 encountered the same pre-written
test file E501 that caused a lint-only degradation warning in T10 and T11. Gemini fixed it
by splitting the `CREATE TABLE` string literal across three lines and wrapping the INSERT call
— all while keeping the test semantics intact.

**Override tasks (HeartRate, Sleep) — clean in 2 reflections each**: Correctly overrode
`extract()` directly, left `_row_to_record()` raising `NotImplementedError` as required.

**Docker — full 89-test suite pass**: UUIDStore passing (task 02 succeeded) meant the Docker
task's full-suite verification found no leaking failures. This was the same task that degraded
in T10 and T11 purely because of UUIDStore failures propagating into the full suite.

**Aborted first run** (`run-20260312-132242.log`): 93-line truncated log showing an API-level
restart after task 01 completed; UUIDStore stub was in default `raise NotImplementedError`
state. Runner was restarted cleanly and the full run (`132307`) proceeded from scratch.

---

## Model Comparison Summary (Trials 6–12)

| Capability | Qwen T7 | Codestral T8 | Gemini T9 | Qwen T10 | Codestral T11 | Gemini T12 |
|------------|---------|--------------|-----------|----------|---------------|------------|
| Settings — no module-level singleton | ❌ | ❌ | ✅ | ✅ (plan fix) | ✅ (plan fix) | ✅ |
| Follows ABC override instructions | ✅ | ❌ | ✅ | ✅ | ⚠️ (omits stub) | ✅ |
| Implements methods completely | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ |
| Resolves E501 lint reliably | ✅ | ❌ (loops) | ✅ | ✅ | ❌ (loops) | ✅ (self-fixes test file) |
| SQLite :memory: single-connection | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| SQLite multi-column IN clause | N/A | N/A | N/A | ❌ | N/A | ✅ (no problem) |
| Respects test file boundary | ✅ | ❌ (corrupts) | ✅ | ✅ | ❌ (corrupts) | ✅ (improves) |
| Cascade isolation | ❌ (old) | ❌ (old) | ❌ (old) | ✅ | ✅ | ✅ |
| Aider edit format discipline | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ |

**Overall TDD pass rate (component tasks only)**:
Qwen T7: 9/18 · Codestral T8: 5/18 · Gemini T9: 12/13 (halted) · Qwen T10: 15/17 · Codestral T11: 7/17 · **Gemini T12: 17/17**

Gemini 3.1 Flash Lite is the clear winner and the reference model going forward for this scaffold.

---

## Open Issues

1. **DAG wiring task (deferred)**: The DAG wiring task (`18-task-6.1-wire-dag.md`) has not yet
   been generated or run. The codebase is in a clean state (89 tests passing) to generate and
   run it now. When generating: read each extractor source file to get the actual class name and
   import path; enumerate every class explicitly; include "Do not import any class not listed
   here" to prevent the hallucinated-import failure seen in Gemini T9.

2. **Codestral — disqualified**: Confirmed across T8 and T11. Test file corruption is a
   consistent model-level behaviour. No further trials planned.

3. **Summarizer fast failures**: Harmless but noisy. Real fix: `stream: false` or `max_tokens` cap.

4. **Context length floor — 32k (Qwen/MLX)**: See Trial Set 4. Do not reduce below 32k.

---

## Skill Changes Log

| Date | File | Change |
|------|------|--------|
| 2026-03-03 | `run-tasks-template.sh` | Added `--timeout 600` to aider invocation |
| 2026-03-03 | `references/writing-guide.md` | Added ABC call site rule |
| 2026-03-04 | `SKILL.md` | Added Step 0: prohibit `git checkout HEAD` restoration |
| 2026-03-04 | `SKILL.md` Step 7 | Always copy runner from template, not git |
| 2026-03-04 | `run-tasks-template.sh` | Reverted `timeout` shell wrapper; kept `--timeout` flag |
| 2026-03-08 | `references/plan-format.md` | ABC contract fit verification; extract()-level override pattern |
| 2026-03-08 | `references/tooling.md` | Positional argument trap fixture criterion; mock_fastavro_writer |
| 2026-03-08 | `run-tasks-template.sh` | Corrected `--timeout` comment |
| 2026-03-09 | `references/tooling.md` | Dotted mock path registration rule; persistence class stub rule |
| 2026-03-10 | `references/tooling.md` | Refactor: language-neutral; stacks/ table |
| 2026-03-10 | `references/writing-guide.md` | Refactor: language-neutral stub patterns |
| 2026-03-10 | `implementation-planning/references/plan-format.md` | Refactor: language-neutral interface examples |
| 2026-03-10 | `SKILL.md` | Refactor: Steps 2/3/3b generalized; stacks/ in Bundled Resources |
| 2026-03-10 | `references/stacks/python-pytest.md` | New: all Python-specific content |
| 2026-03-10 | `references/stacks/typescript-jest.md` | New: TypeScript/Jest stub |
| 2026-03-10 | `references/stacks/kotlin-junit.md` | New: Kotlin/JUnit/Gradle stub |
| 2026-03-10 | `implementation-planning/references/plan-format.md` | **Fix**: component tasks never modify shared files; wiring always deferred; phasing guidelines rewritten |
| 2026-03-10 | `references/writing-guide.md` | **Fix**: component/wiring structural separation; Deferred Tasks updated |
| 2026-03-11 | `SKILL.md` | **Fix**: removed stale wiring/test-scope bullets from Step 5; updated manifest example |
| 2026-03-11 | `task-template.md` | **Fix**: removed Files to Modify and Wiring sections; added explanation |
| 2026-03-12 | `implementation-planning/references/plan-format.md` | **Fix**: prohibit module-level instantiation of environment-dependent objects in interface contracts |
| 2026-03-12 | `references/writing-guide.md` | **Fix**: Two-Layer Validation Gate → Three-Layer; added Layer 0 (lint gate): run linter against pre-written test files before embedding; must return zero errors before proceeding. Updated Deferred Tasks section to clarify the runner pause is a generation step, not a failure, and added "Do not import any class not listed here" guidance for wiring task docs |
| 2026-03-12 | `references/stacks/python-pytest.md` | **Fix**: expanded Persistence Class Stubs into two sections; added "SQLite Trap Patterns" with Trap 1 (`:memory:` multi-connection) and Trap 2 (multi-column IN clause); both include task doc Behavior entry wording for Claude Code to copy when writing task docs |
