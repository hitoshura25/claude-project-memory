# T48 — Qwen 30B: 15✅ 3⚠️ — Settings Module-Level Instantiation Cascade (Chat 10)

**Date**: 2026-03-27
**Model**: Qwen 3 Coder 30B (Q4, 32k context)
**Log**: `run-20260327-103124.log`
**Chat**: 10
**Verdict**: 15✅ 3⚠️ — UUIDStore fix validated (0 E501!); Settings cascade caused 3 failures; Docker + integration both passed cleanly

## Result

| Task | Result | Calls | Notes |
|------|--------|-------|-------|
| 01 Settings | ⚠️ DEGRADED | 4 | `settings = Settings()` at module level — task doc + stub comment told Qwen to do this |
| 02 UUIDStore | ✅ | 1 | **Issue 1/3 fix validated** — 0 E501, correct SQL on first call |
| 03 BaseExtractor | ✅ | 1 | |
| 04 MinIOWriter | ⚠️ DEGRADED | 4 | Cascade from Settings — imports trigger `Settings()` |
| 05 RabbitMQPublisher | ⚠️ DEGRADED | 4 | Cascade from Settings — same cascade |
| 06 BloodGlucose | ✅ | 1 | |
| 07 HeartRate | ✅ | 2 | 1 E501 lint fix |
| 08 HRV | ✅ | 3 | E501 lint fixes |
| 09 Steps | ✅ | 1 | |
| 10 Sleep | ✅ | 1 | |
| 11 ActiveCalories | ✅ | 1 | |
| 12 Distance | ✅ | 1 | |
| 13 TotalCalories | ✅ | 1 | |
| 14 OxygenSaturation | ✅ | 1 | |
| 15 ExerciseSession | ✅ | 1 | |
| 16 Wire DAG | ✅ | 1 | |
| 17 Docker | ✅ | 1 | Smoke test HTTP 200 + **independent verification ✅** (docker prune fix validated) |
| 18 Integration | ✅ | 1 | **No files created** — Qwen correctly did nothing; verification passed |

**Total: 30 LLM calls, 6 E501 occurrences**

## Fixes Validated

### Issue 1/3: UUIDStore SQL — FIXED

UUIDStore passed on the **first call** with **0 E501** (vs 4 calls + 12 E501 in T46). Qwen wrote its own SQL without the double `AND record_type = ?` clause. The combination of multi-line SQL code blocks in the task doc and removing prescriptive implementation detail worked.

### Issue 2: Docker build cache — FIXED

Docker smoke test passed AND independent verification passed. No `failed to prepare extraction snapshot` error. The `docker system prune` removal from the cleanup trap fixed the build cache corruption.

### Issue 4: Integration test as scaffold — FIXED

Integration test task (18) correctly produced no files. Qwen said: "You want me to run integration tests... not creating new files." The test verification passed independently against live services.

## Root Cause: Settings Module-Level Instantiation

The stub file had:
```python
# Stub: settings = None
# Real implementation sets: settings = Settings()
settings = None
```

The task doc Behavior section said:
> Module-level `settings = Settings()` must be assigned after the class definition

The task doc Interface Contract showed:
```python
settings: Settings  # module-level singleton assigned after class definition
```

The task doc Verification section said:
> `settings.py` exists with `Settings` class and module-level `settings = Settings()`

Qwen followed these instructions exactly: it changed `settings = None` to `settings: Settings = Settings()`. This crashes test collection because `Settings()` validates required env vars at instantiation, and the test sets env vars via `monkeypatch` inside the test function (after import).

The test only imports the `Settings` **class** (`from plugins.config.settings import Settings`), not the `settings` instance. So `settings = None` would have been correct — the test constructs `Settings()` explicitly after setting env vars.

**This is a planning-model scaffold/task doc bug.** The stub comment and task doc Behavior section both told Qwen to do the wrong thing. The task doc contradicts the test.

### Cascade to Tasks 4 and 5

MinIOWriter and RabbitMQPublisher both import `from plugins.config.settings import settings` at module level in their implementations. When `settings = Settings()` at module level, importing the settings module triggers validation, which fails because env vars aren't set during test collection.

## E501 Improvement

| Trial | E501 Count | UUIDStore E501 |
|-------|-----------|----------------|
| T46 | 30 | 12 |
| T48 | 6 | 0 |

The multi-line SQL code block guidance in `task-doc-guide.md` eliminated all UUIDStore E501 issues. Remaining 6 E501 are on HeartRate (2) and HRV (4) extractors only.

## LM Studio Logs

No OOM, no crashes. Token counts healthy. All implementation requests were streamed (responses not captured in full in the log). Summarization requests confirm Qwen understood the Settings task correctly but followed the task doc's explicit instruction to instantiate at module level.

## Outcome

Three fixes validated (UUIDStore SQL, Docker prune, integration scaffold). One regression: the planning model generated a task doc and stub that explicitly instruct the implementing model to instantiate Settings at module level, contradicting the test. Fix: the stub must have `settings = None` without misleading comments, and the task doc must not instruct module-level instantiation when the test doesn't require it.
