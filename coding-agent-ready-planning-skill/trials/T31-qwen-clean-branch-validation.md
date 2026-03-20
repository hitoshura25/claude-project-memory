# Trial Set 31 — Qwen Clean Branch Validation

**Date**: 2026-03-19
**Log**: `run-20260319-183832.log` (821 KB, ~62 min)
**Model**: Qwen 3 Coder 30B (via LM Studio)
**Task set**: Fresh regeneration from clean branch (no prior scaffold in git history)
**LLM calls**: 52
**Result**: **8 ✅, 9 ⚠️ degraded, 1 ❌ (services unavailable), 1 ⏭ (integration skipped)**

---

## Per-Task Results

| # | Task | Result | Notes |
|---|------|--------|-------|
| 01 | Settings | ✅ | Clean |
| 02 | UUIDStore | ⚠️ Degraded | **`:memory:` enforcement caught multi-conn** — `test_get_seen_empty` failed immediately. Qwen exhausted 3 reflections without fixing. |
| 03 | Base Extractor | ✅ | **No cascade** — new architecture (`extract(conn, uuids_to_skip)`) doesn't depend on UUIDStore |
| 04 | Google Drive Client | ✅ | Clean |
| 05 | MinIO Writer | ✅ | Clean |
| 06 | RabbitMQ Publisher | ⚠️ Degraded | `settings.rabbitmq_username` — wrong field name; Settings uses a different attribute name |
| 07 | Blood Glucose | ✅ | Clean |
| 08 | Heart Rate | ✅ | Clean |
| 09 | HRV | ✅ | Clean |
| 10 | Steps | ⚠️ Degraded | `SchemaParseException: redefined named type: Timestamp` — Avro schema duplicate named type |
| 11 | Sleep | ✅ | Clean |
| 12 | Active Calories | ⚠️ Degraded | Same Avro schema duplicate named type |
| 13 | Total Calories | ⚠️ Degraded | `TypeError: 'float' object is not subscriptable` — wrong output dict structure |
| 14 | Distance | ⚠️ Degraded | `ExtractionResult.__init__() got unexpected keyword argument 'record_type'` |
| 15 | O2 Saturation | ⚠️ Degraded | `assert 3 == 2` — UUID filtering not applied |
| 16 | Exercise Session | ⚠️ Degraded | Same `ExtractionResult` kwarg issue as task 14 |
| 17 | DAG Assembly | ⚠️ Degraded | `dag.dag_id` returns MagicMock — Airflow mock doesn't set string attributes |
| 18 | Docker Deployment | ✅ | **First Docker pass in trial history!** Full scaffold approach validated |
| 19 | Integration Tests | ❌ | Services unavailable (expected) |

---

## Structural Fix Validations

### `:memory:` enforcement: ✅ Working as designed

The UUIDStore fixture uses `:memory:`. Qwen wrote the multi-connection pattern
(`conn = sqlite3.connect(self.db_path)` in `get_seen_uuids`). The test caught it
immediately at task 2 — `OperationalError: no such table: seen_uuids`.

Critically, **task 3 (Base Extractor) passed despite task 2 being degraded**. The new
architecture (`extract(conn, uuids_to_skip)`) decouples extractors from UUIDStore.
The T23/T29/T30 cascade pattern is eliminated.

However, Qwen exhausted all 3 reflections without switching to the persistent connection
pattern. The enforcement catches the bug but Qwen can't fix it within the reflection
budget. This may indicate the task doc needs the Behavior instruction as well — the
fixture catches the wrong pattern, but without explicit guidance, Qwen doesn't know
*what* the right pattern is.

### Docker scaffold: ✅ First complete pass

Docker task (18) passed for the first time in 31 trials. The full scaffold approach
(Dockerfile + test compose on disk, model creates only production compose) works.

### No cascade: ✅ Architecture validated

Tasks 7, 8, 9, 11 all passed cleanly despite UUIDStore (task 2) being degraded.
The decoupled extractor architecture prevents the cascade that dominated T29.

---

## Failure Categories (Non-Structural)

The 9 degraded tasks fall into 5 distinct categories — none are cascade failures:

| Category | Tasks | Description |
|----------|-------|-------------|
| UUIDStore multi-conn | 02 | Caught by `:memory:` enforcement; Qwen can't fix within 3 reflections |
| Settings field name | 06 | Task doc or implementation uses wrong attribute name |
| Avro duplicate named type | 10, 12 | Schema redefines nested record type instead of string reference |
| ExtractionResult interface | 14, 16 | Model passes `record_type` kwarg not in constructor |
| Output structure / filtering | 13, 15 | Wrong dict structure or UUID filtering not applied |
| Airflow mock + DAG test | 17 | Test asserts on `dag.dag_id` which is MagicMock |

These are task doc content gaps and test design issues in the freshly regenerated
scaffold. They need investigation in the specific task docs and test files.

---

## Clean Branch Impact

This is the first trial run from a completely clean branch with no prior scaffold
in git history. Claude Code generated purely from skill files + design doc, with no
historical artifact contamination. The architecture changes (ExtractionResult,
`extract(conn, uuids_to_skip)`, `get_seen_uuids`) are all novel to this regeneration.

Previous regenerations were partially influenced by committed scaffold from earlier
runs, which explains the non-determinism we attributed to Claude Code compliance —
it was sometimes copying from committed history rather than generating fresh from
skill guidance.
