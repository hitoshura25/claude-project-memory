# Trial Set 18 — Qwen Second Clean Sweep — Loop Closed

**Date**: 2026-03-14
**Log**: `run-20260314-162120.log` (1,587 lines — identical length to T15)
**Model**: Qwen 3 Coder 30B (via LM Studio) — `lm_studio/qwen/qwen3-coder-30b`
**Context**: 32,768 tokens
**Skill state**: Identical to T15 and T17 — no changes between runs
**Result**: **18/18 ✅ — second consecutive Qwen clean sweep. 1 ⚠️ (task 2 UUIDStore — reflections exhausted, tests pass)**

---

## Per-Task Results

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

---

## Analysis

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

## Model Comparison at This Point

| Metric | Gemini T12 | Gemini T17 | Qwen T15 | Qwen T18 | Codestral T16 |
|--------|------------|------------|----------|----------|---------------|
| Pass rate | 17/17 ✅ | 18/18 ✅ | 18/18 ✅ | 18/18 ✅ | ❌ halted T7 |
| Degraded | 0 | 0 | 1 ⚠️ (pass) | 1 ⚠️ (pass) | cascade |
| Total calls | 27 | 21 | 23 | 23 | N/A |
| Wire DAG calls | 2 | 1 | 2 | **1** | N/A |
| Log lines | ~1500 | 1,501 | 1,587 | 1,587 | N/A |

---

## Significance

Loop closed: both Gemini (API) and Qwen (local/LM Studio) paths produce reliable clean
sweeps. The skill is stable and the TDD workflow is proven.
