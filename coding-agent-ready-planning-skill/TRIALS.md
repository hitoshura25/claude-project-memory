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
these are fast failures (summarizer gives up immediately). The real hang occurred during
task 9's actual implementation attempts. HeartRateExtractor is structurally different from
other extractors: it requires a JOIN across two tables (parent session + series rows) and
the model must aggregate multiple rows into a single Avro record with a `samples` list —
the base class `_to_avro_dict` contract (one row in → one dict out) doesn't fit. The model
got stuck in a reflection spiral trying to reconcile this mismatch, generating very long
outputs indefinitely. The `--timeout` flag had no effect because streaming was active.

**Note**: The `.task-output-18.tmp` file confirms task 18 was written — the run did reach
the last task. The hang was on a mid-run task that eventually got stuck, not on the final
task. The script's sequential nature means the hang blocks indefinitely at task 9.

#### MinioWriter — fastavro degradation (same as prior runs)
The model attempted three strategies in sequence:
1. `fastavro.writer(avro_buffer, records)` → TypeError: takes at least 3 args
2. `fastavro.writer(avro_buffer, records, None)` → KeyError: 'type' (None is not a valid schema)
3. Back to 2 args → same TypeError

The model was stuck cycling through wrong approaches. It never tried the correct
`fastavro.writer(fo, schema, records)` signature. The test mocks the S3 client so the
fastavro call is exercised for real — the test requires either a real schema dict or for the
test to mock fastavro. The model has no knowledge of the correct arg order.

**Current state of minio_writer.py**: Has `fastavro.writer(avro_buffer, records, None)` —
still wrong. Tests are failing.

#### HeartRateExtractor — fundamental contract mismatch
The model correctly recognized the mismatch between the base class contract and what
HeartRateExtractor needs, but couldn't solve it. Its attempted `_to_avro_dict`
implementation tried to iterate over `row` as if it were a list of rows — but the base
class passes a single `sqlite3.Row` object. The error:
```
TypeError: byte indices must be integers or slices, not str
```
The model was iterating over the bytes of the UUID field, treating it as a sequence.

**Root cause**: HeartRateExtractor needs to override `extract()` entirely (doing its own
GROUP BY aggregation in the query and accumulating samples in a loop), not just
`_to_avro_dict`. The base class template is the wrong abstraction for multi-row-per-record
cases. This needs a task-level note or a dedicated override pattern in the task spec.

#### Summarizer behavior change
Unlike Trial Set 2 where the summarizer ran for 25,000+ tokens before stalling, in this run
the summarizer failed fast ("cannot schedule new futures after shutdown") after every task.
This is a different failure mode — the executor was likely already shut down from a previous
aider invocation. The fast failure is actually harmless (context just grows without
compression). The real spiral came from the model's reflection loop during task 9 itself.

---

## Generated Code Quality Assessment (updated 2026-03-04 after Trial Set 5)

### Infrastructure — Good
- `UUIDStore`: correct (schema, INSERT OR IGNORE, connection lifecycle)
- `GoogleDriveClient`: correct (streaming download loop, right error types)
- `RabbitmqPublisher`: mostly correct (hardcoded timestamp placeholder minor issue)
- `Settings`: correct (pydantic v2, env_prefix, extra="ignore")

### Extractors — Inconsistent

| Extractor | Status | Issue |
|-----------|--------|-------|
| StepsExtractor | OK | Correct if/else for empty seen set |
| BloodGlucoseExtractor | OK | Correct mmol conversion and null guards |
| HRVExtractor | Fragile | Builds `NOT IN ()` before checking empty set; SQLite accepts it accidentally |
| ActiveCaloriesExtractor | Fragile | Same empty-set issue as HRV |
| DistanceExtractor | OK (Trial 5) | Fixed; bytes.fromhex() dedup now correct |
| ExerciseSessionExtractor | OK (Trial 5) | Correctly uses bytes.fromhex() BLOB comparison |
| SleepExtractor | Fragile | row_factory assumption (uses row["key"] access) |
| HeartRateExtractor | Stuck/Crash | Model cannot solve JOIN aggregation within base class contract; needs override pattern |

### MinioWriter — Broken (fastavro arg order)
Current state: `fastavro.writer(avro_buffer, records, None)` — wrong. Correct is
`fastavro.writer(fo, schema, records)`. Recurring failure across all models and all trials.
The model has no knowledge of the correct signature and cycles through wrong guesses.

### DAG — Multiple Call-Site Bugs (unchanged from prior assessment)
1. `RabbitmqPublisher(rabbitmq_host, rabbitmq_port, ...)` — wrong constructor signature
2. `download_file_by_name(file_name, zip_path)` — ignores return value
3. Missing extractors from `EXTRACTORS` list
4. `TaskGroup.add()` invalid

### BaseRecordExtractor — Duplicate lines in extract() body
The model wrote the inner loop body twice (lines duplicated):
```python
avro_dict = self._to_avro_dict(row)
if avro_dict is not None:
avro_dict = self._to_avro_dict(row)   # ← duplicate
if avro_dict is not None:              # ← duplicate
```
Ruff autocorrected the indentation error. Tests pass because the duplicate is harmless
at runtime, but it's a sign of garbled output in the diff application.

---

## Open Issues

1. **Summarizer spiral / hang**: `--timeout` doesn't work with streaming. The spiral now
   occurs mid-run on the HeartRateExtractor task (task 9) rather than only at end-of-run.
   The summarizer itself fails fast ("cannot schedule new futures after shutdown") — the
   hang is from the model's own reflection loop, not the summarizer.
   - Real fix: `stream: false` in aider config, or server-side `max_tokens` cap in LM Studio.
   - Workaround: HeartRateExtractor needs a different task design (see issue 4).

2. **Context length — do not reduce below 32k**: Smaller context pre-allocates a smaller MLX
   KV cache. Hard tasks with many reflections hit the ceiling mid-generation and segfault the
   model process entirely (worse than a spiral). See Trial Set 4.

3. **fastavro arg order**: Recurring across ALL models and ALL trials. The model has no
   knowledge of the correct `fastavro.writer(fo, schema, records)` signature and will always
   get it wrong. Must be added as an explicit example with correct call in `writing-guide.md`,
   OR the test should mock fastavro so the model never calls it for real.

4. **HeartRateExtractor — base class contract mismatch**: This extractor needs to JOIN two
   tables and aggregate multiple rows into one Avro record (one session = one record with N
   samples). The base class `_to_avro_dict(row)` contract (one row → one dict) doesn't fit.
   The model spirals trying to resolve this. Fix options:
   - Add an override pattern to `writing-guide.md` showing how to override `extract()` directly
     for multi-row-per-record extractors, bypassing `_to_avro_dict`.
   - Alternatively, redesign the task to do the GROUP BY aggregation in SQL and return one
     row per session (using JSON aggregation or a subquery), so `_to_avro_dict` receives a
     pre-aggregated row.

5. **row_factory assumption**: SleepExtractor uses `row["key"]` access which requires
   `conn.row_factory = sqlite3.Row`. Fix: set `row_factory` in `base.extract()` or enforce
   positional index access in `_to_avro_dict` across all extractors.

6. **DAG wiring split**: DAG task (12) ran before extractors 13-17 existed. Consider
   splitting into structure task (early) + wiring task (deferred, after all components exist).

7. **UUID dedup**: Add canonical dedup example to `writing-guide.md`.

---

## Skill Changes Log

| Date | File | Change |
|------|------|--------|
| 2026-03-03 | `run-tasks-template.sh` | Added `--timeout 600` to aider invocation |
| 2026-03-03 | `references/writing-guide.md` | Added ABC call site rule |
| 2026-03-04 | `SKILL.md` | Added Step 0: prohibit `git checkout HEAD` restoration of stale artifacts |
| 2026-03-04 | `SKILL.md` Step 7 | Added: do not restore `run-tasks.sh` from git, always copy from template |
| 2026-03-04 | `run-tasks-template.sh` | Reverted `timeout` shell wrapper; kept `--timeout` aider flag |
