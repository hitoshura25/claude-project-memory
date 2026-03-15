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
**Result**: 16/18 completed before interruption.

---

### Trial Set 3 — After Runner Fixes (2026-03-04 morning)
**Result**: 13 completed, 4 degraded.

---

### Trial Set 4 — 12k Context Experiment (2026-03-04 afternoon)
**Result**: Crashed at task 9. **Conclusion**: Do not reduce context below 32k for Qwen 30B.

---

### Trial Set 5 — Reverted Abstract-Class Patch + 32k Context (2026-03-04 evening)
**Result**: Task 18 completed. Script hung on HeartRateExtractor (task 9).

---

### Trial Set 6 — Skill Updates Applied (2026-03-09)
**Model**: Qwen 3 Coder 30B Q4
**Result**: 11/18 ✅, 1 degraded ⚠️ (task 6), halted at task 12 ❌

---

### Trial Set 7 — After Conftest + UUIDStore + DAG Redesign (2026-03-10 morning)
**Model**: Qwen 3 Coder 30B Q4
**Result**: 9/12 ✅, 3 degraded ⚠️ (tasks 1, 6, 12), halted at task 13 ❌

---

### Trial Set 8 — Codestral 22B Head-to-Head (2026-03-10)
**Model**: Codestral 22B v0.1
**Result**: 5/18 ✅, 13 degraded ⚠️. Edit format failures, lint spirals, test file corruption.

---

### Trial Set 9 — Gemini 2.0 Flash Lite Head-to-Head (2026-03-10 afternoon)
**Model**: `gemini/gemini-2.0-flash-lite-preview`
**Result**: 12/13 ✅, 1 degraded ⚠️ (task 13), halted at task 14 ❌

---

### Trial Set 10 — Qwen After Cascade Fix + Settings Fix (2026-03-12)
**Model**: Qwen 3 Coder 30B (via LM Studio)
**Result**: 15/17 ✅, 2 degraded ⚠️ (tasks 2, 17)

---

### Trial Set 11 — Codestral After Cascade Fix (2026-03-12)
**Model**: Codestral 22B v0.1 (via LM Studio)
**Result**: 7/17 ✅, 9 degraded ⚠️. Codestral confirmed disqualified.

---

### Trial Set 12 — Gemini 3.1 Flash Lite — First Clean Sweep (2026-03-12)
**Log**: `run-20260312-132307.log`
**Model**: `gemini/gemini-3.1-flash-lite-preview` (Gemini API)
**Result**: **17/17 ✅** — 27 LLM calls, 0 degraded.

---

### Trial Set 13 — Qwen After import_integrity Fix (2026-03-12)
**Model**: Qwen 3 Coder 30B (via LM Studio)
**Result**: 17/18 ✅, 1 degraded ⚠️ (task 17 wiring — E501 spiral, tests pass)

---

### Trial Set 14 — Qwen Repeat: ISE → OOM on Wire DAG (2026-03-12)
**Model**: Qwen 3 Coder 30B (via LM Studio)
**Result**: 16/18 ✅, 1 ❌ HALTED (task 17 — Metal OOM, DAG file emptied)

---

### Trial Set 15 — Qwen After Callable-Body Snippet Fix (2026-03-14)
**Log**: `run-20260314-121837.log` (1,587 lines)
**Model**: Qwen 3 Coder 30B (via LM Studio)
**Skill state**: Post pass-3 — unconditional code snippets in wiring task Behavior sections
**Result**: **18/18 ✅ — first complete Qwen clean sweep.** 1 ⚠️ (task 2 UUIDStore — tests pass).
Task 17: 2 LLM calls, 0 E501s, no ISE, no OOM.

---

### Trial Set 16 — Codestral Final Confirmation (2026-03-14)
**Log**: `run-20260314-123454.log` (halted at task 7)
**Model**: Codestral 22B v0.1 (via LM Studio)
**Result**: 2/7 ✅, 1 ❌ task 3 edit format failure cascading to all downstream extractors.
**Codestral disqualified — third and final confirmation.**

---

### Trial Set 17 — Gemini 3.1 Flash Lite — Second Clean Sweep (2026-03-14)
**Log**: `run-20260314-130209.log` (1,501 lines)
**Model**: `gemini/gemini-3.1-flash-lite-preview` (Gemini API)
**Result**: **18/18 ✅, 0 degraded** — 21 LLM calls (down from 27 in T12).
Task 17: 1 LLM call, 0 E501s. 12/18 tasks in exactly 1 call.

---

### Trial Set 18 — Qwen Second Clean Sweep — Loop Closed (2026-03-14)
**Log**: `run-20260314-162120.log` (1,587 lines — identical length to T15)
**Model**: Qwen 3 Coder 30B (via LM Studio) — `lm_studio/qwen/qwen3-coder-30b`
**Context**: 32,768 tokens
**Skill state**: Identical to T15 and T17 — no changes between runs
**Result**: **18/18 ✅ — second consecutive Qwen clean sweep. 1 ⚠️ (task 2 UUIDStore — reflections exhausted, tests pass)**

| Task | Calls | E501s | Notes |
|------|-------|-------|-------|
| 01 Settings | 1 | 0 | ✅ |
| 02 UUIDStore | 4 | 8 | ⚠️ — INSERT SQL literal 97 chars; reflections exhausted on lint; tests pass |
| 03 BaseRecordExtractor | 1 | 0 | ✅ |
| 04 GoogleDriveClient | 1 | 0 | ✅ |
| 05 MinIOWriter | 1 | 0 | ✅ |
| 06 RabbitMQPublisher | 1 | 0 | ✅ |
| 07 StepsExtractor | 1 | 0 | ✅ |
| 08 BloodGlucoseExtractor | 1 | 0 | ✅ |
| 09 HeartRateExtractor | 2 | 2 | ✅ — single E501 on child query string, self-fixed |
| 10 HRVRmssdExtractor | 2 | 2 | ✅ — single E501 on query string, self-fixed |
| 11 SleepExtractor | 1 | 0 | ✅ |
| 12–16 | 1 each | 0 | ✅ all clean first attempt |
| 17 Wire DAG | 1 | 0 | ✅ — **single call, zero E501s, no ISE, no OOM** |
| 18 Docker | 1 | 0 | ✅ |

**Runner summary**: `18 tasks succeeded, 1 degraded`
**Total LLM calls: 23**

#### T18 Analysis

**Task 17 Wire DAG: 1 LLM call, 0 E501s, 0 ISE, 0 OOM** — an improvement over T15's 2
calls. The callable-body snippets continue to hold.

**Task 2 UUIDStore ⚠️** — same pattern as T15 (4 calls, 8 E501s, reflections exhausted).
Addressed in Chat 5 by the SQL Constants Pattern upstream fix.

---

### Trial Set 19 — First run on new plan/task architecture (2026-03-15)
**Log**: `run-20260315-140047.log` (337 KB)
**Model**: Qwen 3 Coder 30B (via LM Studio) — `lm_studio/qwen/qwen3-coder-30b`
**Context**: 32,768 tokens
**Skill state**: Post Chat 5 — new implementation plan (regen from scratch), service-gated integration test, SQL constants, no E501 suppression
**Result**: **17/19 ✅, 2 degraded ⚠️ (tasks 06, 18), 1 skipped ⏭ (task 19 — services unavailable)**

| Task | Result | Notes |
|------|--------|-------|
| 01 Settings | ✅ | |
| 02 UUIDStore | ✅ | SQL constants pattern held — 0 E501s |
| 03 BaseRecordExtractor | ✅ | |
| 04 GoogleDriveClient | ✅ | |
| 05 MinIOWriter | ✅ | |
| 06 RabbitMQPublisher | ⚠️ | `test_connection_closed` — `is_closed` mock trap (see below) |
| 07–16 Extractors | ✅ all | |
| 17 Wire DAG | ✅ | |
| 18 Docker | ⚠️ | No per-task test_command → fell back to global suite → hit task 06's failing test |
| 19 Integration | ⏭ | Services unavailable — correctly skipped, not halted |

**Runner summary**: `16 tasks completed, 2 degraded, 1 skipped (services unavailable)`

#### T19 Root Cause Analysis

**Task 06 RabbitMQPublisher — `is_closed` mock trap:**

Qwen correctly implemented `connection.close()` inside a `finally` block, but guarded it
with `if connection and not connection.is_closed`. On a `MagicMock`, `is_closed` returns
another `MagicMock` — which is truthy. So `not connection.is_closed` evaluates to `False`,
and `connection.close()` is never called. The test asserts `mock_pika_connection["connection"].close.assert_called()` — which fails.

Qwen correctly identified the mismatch in its reflection ("our code isn't using the same
connection object that gets tracked") but couldn't find the fix within 3 reflections. The
fix is to remove the `is_closed` guard entirely — the `finally` block should always call
`connection.close()` unconditionally when `connection` is not None:

```python
finally:
    if connection is not None:
        connection.close()
```

The `is_closed` guard is a Qwen habit when implementing pika connection lifecycle — it
looks defensive but breaks mock assertions. This is a **task doc fix**: the Behavior section
must explicitly say "call `connection.close()` unconditionally in `finally` — do not guard
with `is_closed`" and the task doc should show the exact `finally` block as a code snippet.

**Task 18 Docker — no per-task test_command:**

The Docker task has `"test_command": ""` in the manifest (empty string). The runner fell
back to the global test suite, which includes the already-failing task 06 test. Aider
then spent 3 reflections trying to fix a RabbitMQ issue in a Docker task, exhausted
reflections, and the task was marked degraded. The Docker files themselves are correct.

This is a **manifest issue**: tasks with no unit tests (infrastructure config, Dockerfiles)
should have `"test_command": null` not `""`. The runner's fallback logic triggers on empty
string. Additionally, the runner's fallback warning message makes this failure mode clear —
but the root cause is the empty string being treated identically to "not set". Fix: the
manifest should use `null` for no-test tasks, and the runner should not fall back to the
global test suite for tasks where `test_command` is explicitly null/empty (it means "no
tests", not "use global").

**Task 19 Integration — correct behavior confirmed:**

The service-gated skip worked exactly as designed. The runner printed the unavailable
services, skipped the task cleanly without halting, and reported `1 skipped (services
unavailable)` in the final summary. The fix from Chat 5 is validated.

**UUIDStore (task 02) — SQL constants pattern confirmed working:**

Zero E501 violations on the UUIDStore task this run. The SQL constants rule applied
correctly. This is a clear improvement over T15/T18 where task 02 degraded with 8 E501s
and exhausted reflections every time.

#### T19 Required Fixes (two actionable issues)

**Fix 1 — `python-pytest.md`**: Add a "pika connection lifecycle" trap to the external
dependency mock fixtures section. The `is_closed` attribute on `MagicMock` is truthy, so
guarding `connection.close()` with `not connection.is_closed` prevents the close from
being called. The Behavior section for any RabbitMQ publisher task must explicitly show the
correct `finally` pattern and prohibit the `is_closed` guard.

**Fix 2 — runner + manifest handling**: Tasks with no unit tests must use `"test_command": null`
in the manifest (not `""`). The runner must treat null/None as "no test command" and must
NOT fall back to the global test suite in that case — the fallback is only appropriate when
a test command is expected but not explicitly set.

---

## Model Comparison Summary

| Metric | Gemini T17 | Qwen T18 | Qwen T19 |
|--------|------------|----------|----------|
| Pass rate | 18/18 ✅ | 18/18 ✅ | 17/19 ✅ (new task set) |
| Degraded | 0 | 1 ⚠️ (pass) | 2 ⚠️ (both addressable) |
| Skipped | N/A | N/A | 1 ⏭ (services — correct) |
| Wire DAG E501s | 0 | 0 | 0 |
| UUIDStore E501s | 0 | 8 | **0** (SQL constants fix confirmed) |
| New failure | — | — | `is_closed` mock trap (RabbitMQ) |

---

## Open Issues

1. **RESOLVED — Wire DAG callable body snippets**: Confirmed in T15/T17/T18/T19.

2. **RESOLVED (Chat 5) — UUIDStore SQL E501**: Confirmed fixed in T19 — 0 E501 violations.

3. **ACTIONABLE — Runner: pre-task file backup + restore on critical export loss**.

4. **RESOLVED (Chat 5) — Integration test deferral**: Service-gating confirmed working in T19.

5. **Codestral — permanently disqualified**.

6. **Context length floor — 32k (Qwen/MLX)**.

7. **ACTIONABLE (T19) — RabbitMQ `is_closed` mock trap**: Qwen guards `connection.close()`
   with `not connection.is_closed`. `MagicMock.is_closed` is truthy, so close is never called.
   Fix: add an explicit `finally` block snippet to the pika fixture section in `python-pytest.md`
   showing `if connection is not None: connection.close()` with a note prohibiting `is_closed`.
   Also add to `conftest.py` fixture notes: `mock_conn.is_closed = False` so the guard works
   if models use it, OR document the unconditional close pattern as the required approach.

8. **ACTIONABLE (T19) — Docker task `test_command` null vs empty string**: Empty string
   `""` in the manifest triggers the runner's global-suite fallback. Tasks with no tests
   must use `null`. Fix in `run-tasks-template.sh`: treat empty string as no-test (same as
   null). Fix in `SKILL.md` manifest example: show `"test_command": null` for infra tasks.

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
| 2026-03-12 | `references/writing-guide.md` | **Fix**: Three-Layer Validation Gate; Layer 0 lint gate; Deferred Tasks clarified; "Do not import any class not listed here" guidance added |
| 2026-03-12 | `references/stacks/python-pytest.md` | **Fix**: SQLite Trap Patterns — Trap 1 (:memory: multi-connection) and Trap 2 (multi-column IN clause) |
| 2026-03-12 (Chat 4) | `implementation-planning/references/plan-format.md` | **Fix**: wiring tasks no longer deferred; `import_integrity` scenario mandatory; only integration tests remain deferred |
| 2026-03-12 (Chat 4) | `references/writing-guide.md` | **Fix**: Wiring Task Tests section added; Layer 1 skipped for wiring; Layer 2 = import integrity check against actual files; manifest examples updated |
| 2026-03-13 (pass 1) | `references/writing-guide.md` | **Fix**: Pre-wrap long call patterns rule added |
| 2026-03-13 (pass 2) | `references/writing-guide.md` | **Fix**: Unconditional code snippets for wiring callable bodies |
| 2026-03-14 (pass 3) | `references/writing-guide.md` | **Fix**: Removed length-prediction gate entirely |
| 2026-03-14 (Chat 5) | `references/stacks/python-pytest.md` | **Fix**: SQL Constants Pattern |
| 2026-03-14 (Chat 5) | `references/writing-guide.md` | **Fix**: Deferred vs Service-Gated Tasks section |
| 2026-03-14 (Chat 5) | `run-tasks-template.sh` | **Fix**: `requires_services` + `service_check_commands` support |
| 2026-03-14 (Chat 5) | `SKILL.md` Step 5 | **Fix**: deferred vs service-gated distinction |
| 2026-03-14 (Chat 5) | `references/stacks/python-pytest.md` | **Fix**: Ruff config section; prohibit `ignore = ["E501"]` |
| 2026-03-14 (Chat 5) | `implementation-planning/references/plan-format.md` | **Fix**: integration tests service-gated throughout; upstream root cause of deferred manifest entries |
| 2026-03-15 (T19, Chat 5) | Open issues logged | RabbitMQ `is_closed` trap (issue #7); Docker null vs empty test_command (issue #8) |
