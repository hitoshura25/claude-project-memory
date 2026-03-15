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
calls. The callable-body snippets continue to hold. The 3.3k sent / 1.3k received token
ratio shows a compact, focused generation — no bloat, no spiral.

**Task 2 UUIDStore ⚠️ is the only persistent degradation** — same pattern as T15 (4 calls,
8 E501s, reflections exhausted on the 97-char INSERT SQL literal in `mark_seen`). Tests pass
independently. This is cosmetic-only and the behaviour is fully predictable: Qwen writes the
INSERT string as a single line, linter fires, all 3 reflections spend on formatting rather
than logic. Addressed in Chat 5 by the SQL Constants Pattern upstream fix.

**Tasks 9 and 10 (2 calls each)**: HeartRate and HRV each had one E501 on a long child-table
query string. Qwen resolved both in 1 reflection — a better outcome than the T15 equivalent
where these also needed reflections. Shows Qwen can self-fix short E501 spirals when there's
only one offending line.

**15 of 18 tasks completed in 1 LLM call** — the task set is well-calibrated for Qwen's
capability level with the current skill state.

**Log size stability**: Both T15 and T18 are exactly 1,587 lines (vs T14's 5,553 with the
ISE/OOM spiral). The snippet fix has produced a consistent, bounded execution profile across
multiple Qwen runs.

---

## Model Comparison Summary — Final (post-TDD maturity)

| Metric | Gemini T12 | Gemini T17 | Qwen T15 | Qwen T18 | Codestral T16 |
|--------|------------|------------|----------|----------|---------------|
| Pass rate | 17/17 ✅ | 18/18 ✅ | 18/18 ✅ | 18/18 ✅ | ❌ halted T7 |
| Degraded | 0 | 0 | 1 ⚠️ (pass) | 1 ⚠️ (pass) | cascade |
| Total calls | 27 | 21 | 23 | 23 | N/A |
| Wire DAG calls | 2 | 1 | 2 | **1** | N/A |
| Wire DAG E501s | 0 | 0 | 0 | 0 | N/A |
| Log lines | ~1500 | 1,501 | 1,587 | 1,587 | N/A |
| Self-fixes E501 | ✅ always | ✅ always | ⚠️ sometimes exhausts | ⚠️ sometimes exhausts | ❌ always loops |

**Stable final standings:**
- **Gemini 3.1 Flash Lite**: two clean sweeps (T12, T17). More efficient each run: 27 → 21 calls.
  Zero degraded across both. Reference model for speed and reliability.
- **Qwen 3 Coder 30B**: two consecutive clean sweeps (T15, T18). Consistent 23 calls each,
  consistent 1,587-line logs. One persistent cosmetic ⚠️ (UUIDStore lint, tests always pass).
  Reliable local model when task docs follow the snippet rules.
- **Codestral 22B**: permanently disqualified (T8, T11, T16). Not fixable at skill level.

**The approach is validated**: both the Gemini (API) and Qwen (local/LM Studio) paths
produce reliable clean sweeps. The skill is stable and the TDD workflow is proven.

---

## Open Issues

1. **RESOLVED — Wire DAG callable body snippets**: Confirmed in T15 (Qwen), T17 (Gemini),
   T18 (Qwen). Task 17 now passes in 1 LLM call with 0 E501 errors across all three runs.

2. **RESOLVED (Chat 5) — UUIDStore SQL E501**: Root cause is inline SQL literals in method
   bodies. Fixed upstream in `python-pytest.md` with the "SQL Constants Pattern" — all SQL
   strings must be assigned to named module-level constants, never inlined in method bodies.
   Task docs must show the constant definition in the Behavior section. This is generic Python
   idiom and eliminates the lint surface entirely, regardless of SQL complexity.

3. **ACTIONABLE — Runner: pre-task file backup + restore on critical export loss**: Defence
   in depth against non-deterministic ISE; primary trigger eliminated by snippet fix.

4. **RESOLVED (Chat 5) — Integration test deferral**: Root cause traced to `plan-format.md`
   in the `implementation-planning` skill — that file was the authoritative source saying
   "Phase 8 — Integration Tests — is deferred." Fixed in `plan-format.md`: integration tests
   are now classified as service-gated (not deferred) throughout, with an explicit
   "Deferred Tasks vs Service-Gated Tasks" section and a "Never mark integration tests as
   deferred" rule. The `agent-ready-plans` skill's `writing-guide.md` already had the correct
   classification; `plan-format.md` was the upstream source that contradicted it.

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
| 2026-03-14 (pass 3) | `references/writing-guide.md` | **Fix**: Removed length-prediction gate entirely — unconditional snippets for all wiring callable bodies; confirmed effective in T15, T17, T18 |
| 2026-03-14 (Chat 5) | `references/stacks/python-pytest.md` | **Fix**: SQL Constants Pattern — never inline SQL in method bodies; use named module-level constants; addresses UUIDStore E501 degradation at the source |
| 2026-03-14 (Chat 5) | `references/writing-guide.md` | **Fix**: "Deferred Tasks vs Service-Gated Tasks" section — integration tests reclassified as service-gated (`requires_services`); runner skips rather than halts; decision table added |
| 2026-03-14 (Chat 5) | `run-tasks-template.sh` | **Fix**: `requires_services` + `service_check_commands` support — per-task service health checks; skip with warning when unavailable; `SKIPPED_SERVICES` counter in final summary |
| 2026-03-14 (Chat 5) | `SKILL.md` Step 5 | **Fix**: deferred vs service-gated distinction documented; manifest example updated to show integration test as `requires_services`, not `deferred` |
| 2026-03-14 (Chat 5) | `references/stacks/python-pytest.md` | **Fix**: Added "Ruff Configuration" section with canonical pyproject.toml snippet; explicit prohibition on `ignore = ["E501"]` — suppressing E501 defeats the lint gate; Claude Code introduced this on this run as a workaround and it was caught in review |
| 2026-03-14 (Chat 5) | `implementation-planning/references/plan-format.md` | **Fix**: integration tests reclassified from deferred to service-gated throughout; Phase 8 in Phasing Guidelines updated; "Deferred Tasks vs Service-Gated Tasks" section added with explicit rule "Never mark integration tests as deferred"; document structure template updated to show Phase N+1 without *(deferred)* marker. This was the upstream root cause — agent-ready-plans writing-guide.md already had the correct classification, but plan-format.md contradicted it, causing the generated implementation plan to still say *(deferred)* which then propagated to `"deferred": true` + `"file": null` in the manifest. |
