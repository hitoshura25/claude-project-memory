# Trial Set 10 — Qwen After Cascade Fix + Settings Fix

**Date**: 2026-03-12
**Log**: `run-20260312-112908.log`
**Model**: Qwen 3 Coder 30B (via LM Studio) — `lm_studio/qwen/qwen3-coder-30b`
**Context**: 32,768 tokens
**Skill state**: Post cascade-fix (component/wiring separation) + post settings fix (no module-level singleton in interface contracts)
**Result**: 15/17 ✅, 2 degraded ⚠️ (tasks 2, 17), task 16 completed with lint warnings

---

## Per-Task Results

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

---

## Cascade Isolation Confirmed

Tasks 07–16 all passed with `test_command` scoped to their own test files only. UUIDStore's
broken state did NOT cascade to any extractor. Settings fix confirmed: Task 01 passed on
first attempt with no module-level instantiation.

---

## Root Cause: Task 02 — UUIDStore SQLite Multi-Column IN Clause

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

---

## Root Cause: Task 17 — Docker UUIDStore Full-Suite Leak

Runner ran full suite for verification (no `test_command`), picked up 7 failing UUIDStore
tests. Docker files were likely generated correctly — this is a verification artifact.

---

## Skill Changes

- `references/stacks/python-pytest.md`: SQLite Trap Patterns — Trap 2 (multi-column IN clause)
