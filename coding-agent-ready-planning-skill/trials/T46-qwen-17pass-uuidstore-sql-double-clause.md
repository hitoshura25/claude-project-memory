# T46 — Qwen 30B: 17✅ 1⚠️ — UUIDStore SQL Double Clause (Chat 10)

**Date**: 2026-03-26
**Model**: Qwen 3 Coder 30B (Q4, 32k context)
**Log**: `run-20260326-154609.log`
**Chat**: 10
**Verdict**: 17✅ 1⚠️ — best post-refactor result; single failure is recurring UUIDStore SQL parameterization bug; task 19 never ran (Docker cache corruption blocked runner)

## Result

| Task | Result | Calls | Notes |
|------|--------|-------|-------|
| 01 Settings | ✅ | 1 | |
| 02 UUIDStore | ⚠️ DEGRADED | 4 | SQL double `AND record_type = ?` |
| 03 BaseExtractor | ✅ | 1 | ABC + @abstractmethod fine with single `extract` method |
| 04 DriveDownloader | ✅ | 1 | **T45 fix validated** — complete tests, no stub test issue |
| 05 MinIOWriter | ✅ | 1 | |
| 06 RabbitMQPublisher | ✅ | 1 | |
| 07 BloodGlucose | ✅ | 1 | |
| 08 HeartRate | ✅ | 2 | 1 E501 lint fix on UUID conversion |
| 09 HRV | ✅ | 3 | Self-corrected (assert 36==32 → fixed) |
| 10 Steps | ✅ | 2 | 1 E501 lint fix |
| 11 Sleep | ✅ | 1 | |
| 12 ActiveCalories | ✅ | 2 | 1 E501 lint fix |
| 13 Distance | ✅ | 2 | 1 E501 lint fix |
| 14 TotalCalories | ✅ | 2 | 1 E501 lint fix |
| 15 OxygenSaturation | ✅ | 2 | 1 E501 lint fix |
| 16 ExerciseSession | ✅ | 3 | 2 E501 lint fixes |
| 17 Wire DAG | ✅ | 1 | |
| 18 Docker | ✅ | 1 | Smoke test HTTP 200; independent verification failed (Docker Desktop cache) |
| 19 Integration | — | 0 | Never ran — Docker build cache corruption blocked full suite check |

**Total: 31 LLM calls, 30 E501 occurrences**

## Architecture Notes

This regeneration produced a significantly different architecture from T45:

- **Base extractor**: Pure ABC with single `extract(conn)` abstract method. No `_row_to_record` or `_get_all_uuids` split. All extractors override `extract` directly.
- **UUID dedup**: Moved upstream to the DAG. Extractors receive a `conn` and return all rows including `uuid_hex` in each dict. Base class doesn't touch UUIDStore.
- **@abstractmethod**: Back in use, but safe — only one abstract method and every subclass implements it. `test_cannot_instantiate_base` explicitly validates this.
- **DriveDownloader**: Takes `service_account_json_path` string in constructor (not Settings object). Tests are complete — no `raise NotImplementedError` in test bodies.

## Root Cause: UUIDStore SQL Double Clause

The `_FILTER_SEEN_SQL_TEMPLATE` constant is defined as:
```python
_FILTER_SEEN_SQL_TEMPLATE = (
    "SELECT uuid_hex FROM seen_uuids WHERE uuid_hex IN ({}) AND record_type = ?"
)
```

Qwen's `filter_new` implementation appended the clause again:
```python
query = _FILTER_SEEN_SQL_TEMPLATE.format(placeholders) + " AND record_type = ?"
```

Resulting SQL has **two** `AND record_type = ?` clauses → 5 placeholders but only 4 params (`["a", "b", "c", "BloodGlucoseRecord"]`) → `sqlite3.ProgrammingError: Incorrect number of bindings supplied`.

The task doc Behavior section clearly states to use `params = [*uuids, record_type]` with the template, and the template already includes the `record_type` clause. But Qwen read both the constant definition and the behavior prose independently and concatenated the clause twice.

This is the same category of UUIDStore SQL parameterization failure seen in earlier trials (T46 in the compacted transcript had the same error pattern).

## Docker Desktop Cache Corruption

Smoke test passed during the aider run (HTTP 200 on `/health`). The independent verification re-triggered a Docker build that hit:
```
failed to prepare extraction snapshot "extract-365984917-rgIV sha256:...": parent snapshot sha256:...
```

This is a Docker Desktop issue (corrupted build cache), not a code issue. The image was already built and healthy. The runner treated this as a test failure and halted, preventing task 19 from running.

Same error pattern as T46 in the compacted transcript.

## E501 Pattern

30 E501 occurrences across 8 extractors. Each extractor inlines a SQL query for the `SELECT ... WHERE uuid IN (...)` pattern, which exceeds 88 chars. Qwen self-corrects on all of them (breaks into multi-line strings), costing 1 extra call per extractor.

## LM Studio Logs

No OOM, no segfaults, no crashes. Token counts healthy (under 4k per call). 31 total calls is efficient.

## T45 Fixes Validated

- **DriveDownloader tests complete** — no `raise NotImplementedError` in test bodies. The vacuous test detection in validate-stubs.sh would have caught this if present.
- **Settings defaults correct** — actual values from stub.
- **HeartRate + Sleep passed** — @abstractmethod fine with single `extract` method in new architecture.

## Outcome

Best post-refactor result: 17✅ out of 18 that ran (task 19 never started). The single degraded task (UUIDStore) is a recurring SQL parameterization issue where Qwen double-applies a WHERE clause that's already in the template constant. Docker smoke test passed; the independent verification failure is Docker Desktop infrastructure, not code.
