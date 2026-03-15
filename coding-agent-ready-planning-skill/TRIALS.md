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

---

### Trial Set 16 — Codestral Final Confirmation (2026-03-14)
**Log**: `run-20260314-123454.log` (halted at task 7)
**Model**: Codestral 22B v0.1 (via LM Studio)
**Result**: 2/7 ✅, 1 ❌. **Codestral disqualified — third and final confirmation.**

---

### Trial Set 17 — Gemini 3.1 Flash Lite — Second Clean Sweep (2026-03-14)
**Log**: `run-20260314-130209.log` (1,501 lines)
**Model**: `gemini/gemini-3.1-flash-lite-preview` (Gemini API)
**Result**: **18/18 ✅, 0 degraded** — 21 LLM calls. Task 17: 1 call, 0 E501s.

---

### Trial Set 18 — Qwen Second Clean Sweep — Loop Closed (2026-03-14)
**Log**: `run-20260314-162120.log` (1,587 lines)
**Model**: Qwen 3 Coder 30B (via LM Studio)
**Result**: **18/18 ✅, 1 ⚠️ (task 2 UUIDStore — lint, tests pass)**. Total LLM calls: 23.

---

### Trial Set 19 — Qwen on New Task Set (2026-03-15)
**Log**: `run-20260315-140047.log` (337 KB)
**Model**: Qwen 3 Coder 30B (via LM Studio)
**Skill state**: Post Chat 5 — new implementation plan, service-gated integration test, SQL constants, no E501 suppression
**Result**: **17/19 ✅, 2 degraded ⚠️ (tasks 06, 18), 1 skipped ⏭ (task 19 — services unavailable)**

| Task | Result | Notes |
|------|--------|-------|
| 01 Settings | ✅ | |
| 02 UUIDStore | ✅ | **SQL constants fix confirmed — 0 E501s** |
| 03–05 | ✅ | |
| 06 RabbitMQPublisher | ⚠️ | `test_connection_closed` — `is_closed` mock trap |
| 07–17 | ✅ all | including Wire DAG: 1 call, 0 E501s |
| 18 Docker | ⚠️ | Empty `test_command` → global suite fallback → hit task 06 failure |
| 19 Integration | ⏭ | **Service-gating confirmed working** |

**Root causes:** (1) Qwen guards `connection.close()` with `not connection.is_closed` — truthy on MagicMock, close never called. (2) `"test_command": ""` triggers global fallback; Docker task has no tests of its own.

---

### Trial Set 20 — Gemini on New Task Set — Third Clean Sweep (2026-03-15)
**Log**: `run-20260315-142006.log` (237 KB / 2,067 lines)
**Model**: `gemini/gemini-3.1-flash-lite-preview` (Gemini API)
**Skill state**: Identical to T19 — same task set, no skill changes between runs
**Result**: **18/18 ✅, 0 degraded, 1 skipped ⏭ (task 19 — services unavailable)**

| Task | Lines | Notes |
|------|-------|-------|
| 06 RabbitMQPublisher | 177 | ✅ — **no `is_closed` guard; unconditional `connection.close()` in `finally`** |
| 17 Wire DAG | 173 | ✅ — 1 call, 0 E501s |
| 18 Docker | 103 | ✅ — global fallback; 65 tests passed (task 06 clean) |
| 19 Integration | ⏭ | Services unavailable — correctly skipped |

**Runner summary**: `18 tasks completed, 1 skipped (services unavailable)`

**Key findings:** `is_closed` trap is Qwen-specific — Gemini writes unconditional `finally` naturally. Docker global fallback is structurally fragile (safe here only because task 06 passed).

---

## Model Comparison Summary — Updated (T19/T20)

| Metric | Gemini T17 | Gemini T20 | Qwen T18 | Qwen T19 |
|--------|------------|------------|----------|----------|
| Task set | Original | New (Chat 5) | Original | New (Chat 5) |
| Pass rate | 18/18 ✅ | 18/18 ✅ | 18/18 ✅ | 17/19 ✅ |
| Degraded | 0 | 0 | 1 ⚠️ (pass) | 2 ⚠️ (addressable) |
| Skipped | N/A | 1 ⏭ (correct) | N/A | 1 ⏭ (correct) |
| UUIDStore E501 | 0 | self-fixed | 8 (degraded) | **0** |
| RabbitMQ `is_closed` | not triggered | not triggered | not triggered | ⚠️ degraded |

**Standings:**
- **Gemini 3.1 Flash Lite**: three clean sweeps (T12, T17, T20). Reference model.
- **Qwen 3 Coder 30B**: clean on original task set (T15, T18); one new failure on new task set (T19, pika trap). Pending issue #7 fix.
- **Codestral 22B**: permanently disqualified.

---

## Open Issues

1. **RESOLVED — Wire DAG callable body snippets**: T15/T17/T18/T19/T20 all confirmed.

2. **RESOLVED (Chat 5) — UUIDStore SQL E501**: Confirmed fixed in T19 (Qwen 0 E501s) and T20 (Gemini self-fixed).

3. **ACTIONABLE — Runner: pre-task file backup + restore on critical export loss**.

4. **RESOLVED (Chat 5) — Integration test deferral**: Service-gating confirmed working in T19 and T20.

5. **Codestral — permanently disqualified**.

6. **Context length floor — 32k (Qwen/MLX)**.

7. **RESOLVED (Chat 5) — RabbitMQ `is_closed` mock trap**: Fixed in `python-pytest.md`:
   (a) `mock_conn.is_closed = False` added to the pika fixture so the guard evaluates
   correctly even if models use it; (b) "Pika Connection Lifecycle Trap" section added
   documenting the failure mode, showing the correct unconditional `finally` pattern, and
   prohibiting the `is_closed` guard in task doc Behavior sections.

8. **ACTIONABLE (T19/T20) — Docker task `test_command` null vs empty string**: Empty `""`
   triggers the runner's global-suite fallback, which is only safe when all prior tasks pass.
   Under discussion — may remove the fallback entirely rather than fix null vs empty handling.

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
| 2026-03-15 (T19/T20, Chat 5) | `references/stacks/python-pytest.md` | **Fix**: pika `is_closed` mock trap — added `mock_conn.is_closed = False` to fixture; added "Pika Connection Lifecycle Trap" section with correct `finally` pattern and task doc guidance |
