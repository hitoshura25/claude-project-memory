# Trial Set 11 — Codestral 22B After Cascade Fix

**Date**: 2026-03-12
**Log**: `run-20260312-115442.log`
**Model**: Codestral 22B v0.1 (via LM Studio) — `lm_studio/mistralai/codestral-22b-v0.1`
**Context**: 32,768 tokens
**Skill state**: Same as T10 — post cascade-fix + post settings fix
**Result**: 7/17 ✅, 9 degraded ⚠️, 1 warning, 0 halts

---

## Per-Task Results

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

---

## Analysis

Codestral confirmed disqualified: lint loops, test file corruption, incomplete ABC, edit format
failures are all consistent model-level behaviours not addressable through task doc improvements.

Second data point (after T8) toward permanent disqualification.
