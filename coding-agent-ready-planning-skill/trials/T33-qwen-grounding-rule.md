# Trial 33 — Qwen Code-Grounding Rule Validation

**Date**: 2026-03-20
**Log**: `run-20260320-121353.log` (1.2 MB)
**Model**: Qwen 3 Coder 30B (via LM Studio)
**Task set**: Fresh regeneration with SKILL.md Step 5 code-grounding rule
**LLM calls**: 46
**Result**: **12 ✅, 5 ⚠️ degraded, Docker exit(1), Integration never ran**

---

## Per-Task Results

| # | Task | Result | Notes |
|---|------|--------|-------|
| 01 | Settings | ✅ | Clean |
| 02 | UUIDStore | ✅ | **Fixed from T31** — persistent `self._conn` correct |
| 03 | Base Extractor | ✅ | Clean |
| 04 | Google Drive Client | ✅ | Clean (was ✅ in T31 too) |
| 05 | MinIO Writer | ✅ | Clean |
| 06 | RabbitMQ Publisher | ⚠️ Degraded | `source="health-connect"` and `user_id="unknown"` instead of `"airflow"` and `settings.user_id`; also `pika.spec.BASIC_NACK` error |
| 07 | Blood Glucose | ✅ | Clean |
| 08 | Heart Rate | ✅ | Clean |
| 09 | HRV | ⚠️ Degraded | `uuid_filter` not applied — `assert 3 == 2`; exhausted 3 reflections |
| 10 | Steps | ✅ | **Fixed from T31** — Avro duplicate named type gone |
| 11 | Sleep | ✅ | Clean |
| 12 | Active Calories | ✅ | **Fixed from T31** — Avro duplicate named type gone |
| 13 | Total Calories | ⚠️ Degraded | `ExtractionResult.__init__() got unexpected keyword argument 'record_type'` |
| 14 | Distance | ✅ | **Fixed from T31** — ExtractionResult kwargs gone |
| 15 | O2 Saturation | ⚠️ Degraded | `uuid_filter` not applied — `assert 3 == 2` |
| 16 | Exercise Session | ⚠️ Degraded | `uuid_filter` not applied + ExtractionResult kwargs |
| 17 | DAG Assembly | ✅ | **Fixed from T31** — dag.dag_id mock issue gone |
| 18 | Docker | exit(1) | Container builds, MinIO+RabbitMQ healthy, Airflow exits(1) |
| 19 | Integration | Never ran | Log ended during Docker task |

---

## Code-Grounding Rule Impact

### Fixed from T31 (5 improvements)

- **UUIDStore (02)**: Persistent `self._conn` — task doc now grounded from test assertions
- **Steps (10) + Active Calories (12)**: Avro duplicate named type gone — grounded schema uses namespace deduplication (`"health.TimeRecord"`)
- **Distance (14)**: ExtractionResult kwargs gone — grounded output structure worked
- **DAG Assembly (17)**: Mock/dag_id gone — grounded callable snippets work

### Remaining failures (5 degraded)

| Category | Tasks | Description |
|----------|-------|-------------|
| RabbitMQ field values | 06 | Model hardcoded `source="health-connect"`, `user_id="unknown"` despite task doc specifying `"airflow"` and `settings.user_id` |
| uuid_filter not applied | 09, 15, 16 | Model returns all rows, ignoring `uuids_to_skip` parameter; exhausts 3 reflections |
| ExtractionResult kwargs | 13, 16 | Model passes extra kwargs (`record_type`, `avro_schema`) to `ExtractionResult()` |

The RabbitMQ and uuid_filter failures are the model ignoring explicit task doc instructions — the docs are correct. The ExtractionResult kwargs issue is a remaining task doc gap: the docs don't explicitly constrain the constructor signature.

---

## Docker exit(1)

Container builds successfully, MinIO and RabbitMQ start healthy, but Airflow container `exited (1)`. Same pattern as T27/T28. This is a scaffold issue (test compose), not a task doc issue.

---

## Comparison to T31

| Metric | T31 (before) | T33 (after) |
|--------|-------------|-------------|
| ✅ tasks | 8 | 12 |
| ⚠️ degraded | 9 | 5 |
| LLM calls | 52 | 46 |
| Avro dup type | 2 tasks | 0 |
| ExtractionResult kwargs | 2 tasks | 2 tasks |
| uuid_filter | 1 task | 3 tasks |
| DAG mock | 1 task | 0 |
| Docker | ✅ | exit(1) |
