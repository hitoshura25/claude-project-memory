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

---

### Trial Set 3 — After Runner Fixes (2026-03-04 morning)
**Log**: `run-20260304-114920.log`
**Result**: 13 completed, 4 degraded

---

### Trial Set 4 — 12k Context Experiment (2026-03-04 afternoon)
**Log**: `run-20260304-150619.log`
**Context**: 12,000 tokens
**Result**: Crashed at task 9. **Conclusion**: Do not reduce context below 32k for Qwen 30B.

---

### Trial Set 5 — Reverted Abstract-Class Patch + 32k Context (2026-03-04 evening)
**Log**: `run-20260304-155543.log`
**Result**: Task 18 completed. Script hung on HeartRateExtractor (task 9).

---

### Trial Set 6 — Skill Updates Applied (2026-03-09)
**Log**: `run-20260309-123229.log`
**Model**: Qwen 3 Coder 30B Q4
**Result**: 11/18 ✅, 1 degraded ⚠️ (task 6), halted at task 12 ❌

---

### Trial Set 7 — After Conftest + UUIDStore + DAG Redesign (2026-03-10 morning)
**Log**: `run-20260310-105632.log`
**Model**: Qwen 3 Coder 30B Q4
**Result**: 9/12 ✅, 3 degraded ⚠️ (tasks 1, 6, 12), halted at task 13 ❌

---

### Trial Set 8 — Codestral 22B Head-to-Head (2026-03-10)
**Model**: Codestral 22B v0.1
**Result**: 5/18 ✅, 13 degraded ⚠️, 0 halts. Codestral-specific failure modes: edit format
failures, lint spirals, test file corruption, incomplete ABC.

---

### Trial Set 9 — Gemini 2.0 Flash Lite Head-to-Head (2026-03-10 afternoon)
**Model**: `gemini/gemini-2.0-flash-lite-preview` (Gemini API)
**Result**: 12/13 ✅, 1 degraded ⚠️ (task 13), halted at task 14 ❌

---

### Trial Set 10 — Qwen Coder After Cascade Fix + Settings Fix (2026-03-12)
**Log**: `run-20260312-112908.log`
**Model**: Qwen 3 Coder 30B (via LM Studio)
**Result**: 15/17 ✅, 2 degraded ⚠️ (tasks 2, 17)

---

### Trial Set 11 — Codestral 22B After Cascade Fix (2026-03-12)
**Log**: `run-20260312-115442.log`
**Model**: Codestral 22B v0.1 (via LM Studio)
**Result**: 7/17 ✅, 9 degraded ⚠️, 1 warning. Codestral confirmed disqualified.

---

### Trial Set 12 — Gemini 3.1 Flash Lite Preview — First Clean Sweep (2026-03-12)
**Log**: `run-20260312-132307.log`
**Model**: `gemini/gemini-3.1-flash-lite-preview` (Gemini API)
**Result**: **17/17 ✅** — 27 LLM calls total, zero degraded tasks.

---

### Trial Set 13 — Qwen After import_integrity Fix (2026-03-12)
**Model**: Qwen 3 Coder 30B (via LM Studio)
**Result**: 17/18 ✅, 1 degraded ⚠️ (task 17 wiring — E501 spiral, tests pass)

---

### Trial Set 14 — Qwen Repeat Run: ISE → OOM on Wire DAG (2026-03-12)
**Log**: `run-20260312-171153.log` (5,553 lines)
**Model**: Qwen 3 Coder 30B (via LM Studio)
**Result**: 16/18 ✅, 1 ❌ HALTED (task 17 — Metal OOM, DAG file emptied)

---

### Trial Set 15 — Qwen After Wiring Task Callable-Body Snippet Fix (2026-03-14)
**Log**: `run-20260314-121837.log` (1,587 lines)
**Model**: Qwen 3 Coder 30B (via LM Studio)
**Skill state**: Post pass-3 writing-guide fix — unconditional code snippets in wiring task Behavior
**Result**: **18/18 ✅ — first complete Qwen clean sweep.** 1 ⚠️ (task 2 UUIDStore — tests pass).
Task 17: 2 LLM calls, zero E501 errors, no ISE, no OOM. Snippet rule confirmed effective.

---

### Trial Set 16 — Codestral Final Confirmation (2026-03-14)
**Log**: `run-20260314-123454.log` (1,793 lines — halted at task 7)
**Model**: Codestral 22B v0.1 (via LM Studio)
**Result**: 2/7 ✅, 4 ⚠️ (tests pass), 1 ❌ (task 3 — edit format failure, cascade to task 7)

Task 3 (BaseRecordExtractor): all 4 LLM calls rejected by aider — correct code produced but
filename header omitted every time. `extract()` never applied, stub remained. Every downstream
extractor hit `NotImplementedError` from base. **Codestral disqualified — third confirmation.**

---

### Trial Set 17 — Gemini 3.1 Flash Lite Preview — Second Clean Sweep (2026-03-14)
**Log**: `run-20260314-130209.log` (1,501 lines)
**Model**: `gemini/gemini-3.1-flash-lite-preview` (Gemini API)
**Skill state**: Same as T15/T16 (post all fixes, including callable-body snippets in wiring task)
**Result**: **18/18 ✅, 0 degraded — perfect clean sweep**

| Task | Calls | E501s | Notes |
|------|-------|-------|-------|
| 01 Settings | 1 | 0 | ✅ |
| 02 UUIDStore | 2 | 4 | ✅ — fixed E501s in reflection, tests pass |
| 03 BaseRecordExtractor | 1 | 0 | ✅ |
| 04 GoogleDriveClient | 1 | 0 | ✅ |
| 05 MinIOWriter | 1 | 0 | ✅ |
| 06 RabbitMQPublisher | 1 | 0 | ✅ |
| 07 StepsExtractor | 1 | 0 | ✅ |
| 08 BloodGlucoseExtractor | 1 | 0 | ✅ |
| 09 HeartRateExtractor | 2 | 4 | ✅ — fixed E501s in reflection |
| 10 HRVRmssdExtractor | 1 | 0 | ✅ |
| 11 SleepExtractor | 2 | 4 | ✅ — fixed E501s in reflection |
| 12–16 | 1 each | 0 | ✅ all clean first attempt |
| 17 Wire DAG | 1 | 0 | ✅ — **single call, zero E501s** |
| 18 Docker | 1 | 0 | ✅ |

**Runner summary**: `18 tasks succeeded, 0 degraded`

**Total LLM calls: 21** — 6 fewer than T12's 27. Efficiency improvement confirms skill improvements
(callable-body snippets, tighter task docs) are reducing the work Gemini needs to do.

**Zero degraded tasks** — T12 had no degraded either, but T17 is the first run with the full suite
of skill fixes in place and still achieves the same result. Confirmation that the skill changes
didn't break Gemini compatibility.

#### T17 Notable observations

**Task 17 Wire DAG: 1 LLM call, 0 E501s** — T12 completed task 17 in 2 calls with a test
file E501 self-fix. T17 completed it in a single call with zero lint errors at all. The
callable-body snippets in the Behavior section eliminated any lint issues before they could
even surface.

**UUIDStore, HeartRate, Sleep (2 calls each)**: The three tasks that required a reflection
all had E501s on SQL string literals or long query strings — the same category as the
UUIDStore ⚠️ seen in T15 Qwen. Gemini self-fixed all of them within 1 reflection (4 E501s
each, all resolved). Qwen exhausted its budget on the same lines. This confirms the
difference: Gemini resolves lint in 1 reflection; Qwen sometimes needs more.

**12 of 18 tasks completed in exactly 1 LLM call** — no reflections needed at all. For the
majority of the task set Gemini writes clean, lint-passing, test-passing code on the first
attempt.

---

## Model Comparison Summary (Trials 12–17, post-TDD maturity)

| Metric | Gemini T12 | Qwen T15 | Gemini T17 | Codestral T16 |
|--------|------------|----------|------------|---------------|
| Pass rate | 17/17 ✅ | 18/18 ✅ | 18/18 ✅ | ❌ halted T7 |
| Degraded tasks | 0 | 1 ⚠️ (tests pass) | 0 | cascade failure |
| Total LLM calls | 27 | ~21 | 21 | N/A |
| Wire DAG calls | 2 | 2 | **1** | N/A |
| Wire DAG E501s | 0 | 0 | **0** | N/A |
| Self-fixes E501 lint | ✅ | ⚠️ (sometimes exhausts) | ✅ | ❌ always loops |
| Edit format discipline | ✅ | ✅ | ✅ | ❌ critical failure |

**Final model standing:**
- **Gemini 3.1 Flash Lite**: two clean sweeps (T12: 17/17, T17: 18/18). More efficient each run.
  Zero degraded across both. Reference model.
- **Qwen 3 Coder 30B**: 18/18 clean sweep (T15) after snippet fix. 1 cosmetic ⚠️ (tests pass).
  Reliable with appropriate task doc authoring.
- **Codestral 22B**: permanently disqualified (T8, T11, T16). Not fixable at skill level.

---

## Open Issues

1. **RESOLVED (2026-03-14) — Wire DAG callable body snippets**: Confirmed effective in T15
   (Qwen) and T17 (Gemini). Task 17 passes in 1–2 LLM calls with zero E501 errors.

2. **LOW PRIORITY — UUIDStore INSERT SQL E501**: `mark_seen` INSERT query is 100 chars.
   Gemini self-fixes in 1 reflection; Qwen exhausts budget. Tests pass in both cases.
   Can show pre-wrapped form in Behavior section:
   ```python
   query = (
       "INSERT OR IGNORE INTO seen_uuids "
       "(uuid_hex, record_type, seen_at) VALUES (?, ?, ?)"
   )
   ```

3. **ACTIONABLE — Runner: pre-task file backup + restore on critical export loss**: Defence
   in depth against non-deterministic ISE; primary trigger eliminated by snippet fix.

4. **Integration test (task 19) still deferred**: Requires live MinIO + RabbitMQ containers.

5. **Codestral — permanently disqualified**: T8, T11, T16. Not addressable at skill level.

6. **Context length floor — 32k (Qwen/MLX)**: Do not reduce below 32k. See Trial Set 4.

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
| 2026-03-13 (pass 1) | `references/writing-guide.md` | **Fix**: Pre-wrap long call patterns rule added to Core Principles and Wiring Task Tests |
| 2026-03-13 (pass 2) | `references/writing-guide.md` | **Fix**: Tightened rule — now requires code snippets (not prose) for callable bodies in wiring task Behavior sections; explicit exception to "no implementation code" principle |
| 2026-03-14 (pass 3) | `references/writing-guide.md` | **Fix**: Removed length-prediction gate entirely — snippet rule is now unconditional for all wiring task callable bodies; confirmed effective in T15 (Qwen) and T17 (Gemini) |
