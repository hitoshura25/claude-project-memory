# Trial 37 — Gemini Three-Compose + Integration Tests

**Date**: 2026-03-20
**Log**: `run-20260320-224917.log` (487 KB)
**Model**: Gemini 3.1 Flash Lite (via Gemini API)
**Task set**: Same as T36 (three-compose pattern + service_compose + refined grounding)
**LLM calls**: 37
**Result**: **18 ✅, 1 ⚠️ (Total Calories), Integration ✅ (3/3 passed)**

---

## Per-Task Results

| # | Task | Result | Notes |
|---|------|--------|-------|
| 01 | Settings | ✅ | Clean |
| 02 | UUIDStore | ✅ | Clean |
| 03 | Base Extractor | ✅ | Clean |
| 04 | Google Drive Client | ✅ | Clean |
| 05 | MinIO Writer | ✅ | Clean |
| 06 | RabbitMQ Publisher | ✅ | Clean |
| 07 | Blood Glucose | ✅ | Clean |
| 08 | Heart Rate | ✅ | Clean |
| 09 | HRV | ✅ | **Fixed from T34** — ExtractionResult kwargs resolved |
| 10 | Steps | ✅ | Clean |
| 11 | Sleep | ✅ | Clean |
| 12 | Active Calories | ✅ | Clean |
| 13 | Total Calories | ⚠️ Degraded | `ExtractionResult.__init__() got unexpected keyword argument 'schema'`; then uuid_filter `assert 2 == 1` |
| 14 | Distance | ✅ | Clean |
| 15 | O2 Saturation | ✅ | Clean |
| 16 | Exercise Session | ✅ | Clean |
| 17 | DAG Assembly | ✅ | Clean (Gemini handles Airflow mock correctly) |
| 18 | Docker | ✅ | Full smoke test pass |
| 19 | Integration Tests | ✅ | **3/3 passed against live services** |

---

## Three-Compose + service_compose — ✅ Validated

Same as T36: runner auto-started `services.test.compose.yml`, ran integration tests,
tore down cleanly. Integration tests passed on first attempt with no reflections needed.

---

## Total Calories Failure (Task 13)

Gemini hit the ExtractionResult kwargs issue — passed `schema=` to `ExtractionResult()`.
After reflection, returned tuples instead of dicts. After further reflection, failed
`uuid_filter` with `assert 2 == 1`. Exhausted all reflections.

This is the same intermittent pattern from T34 (which hit HRV instead). Not task-specific
— the model occasionally invents extra kwargs on different extractors across runs.

---

## Full Suite Check

1 failed (`test_total_calories_extractor::test_uuid_filter`), 54 passed.
The failure is only from the degraded Total Calories task — all other tests pass.

---

## Cross-Model Comparison (T36 vs T37)

| Metric | T36 (Qwen) | T37 (Gemini) |
|--------|-----------|-------------|
| ✅ tasks | 18 | 18 |
| ⚠️ degraded | 1 (DAG Assembly) | 1 (Total Calories) |
| Integration | ✅ 3/3 | ✅ 3/3 |
| Docker | ✅ | ✅ |
| LLM calls | 39 | 37 |
| Degraded cause | Airflow mock (intermittent) | ExtractionResult kwargs (intermittent) |

Both models hit 18/19 with different intermittent single-task failures.
Neither failure is systematic — they pass in other runs.
