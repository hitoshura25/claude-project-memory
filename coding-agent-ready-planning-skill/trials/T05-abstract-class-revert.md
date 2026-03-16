# Trial Set 5 — Reverted Abstract-Class Patch + 32k Context

**Date**: 2026-03-04 evening
**Log**: `run-20260304-155543.log`
**Model**: Qwen 3 Coder 30B Q4
**Context**: 32,768 tokens
**Result**: Task 18 completed. Script hung on HeartRateExtractor (task 9).

---

## Analysis

HeartRateExtractor: fundamental contract mismatch. Needs to override `extract()` entirely
(GROUP BY aggregation in query, accumulating samples in loop), not just `_to_avro_dict`.
Base class template is the wrong abstraction for multi-row-per-record cases.

---

## Generated Code Quality Assessment

### Infrastructure — Good
- `UUIDStore`: correct (schema, INSERT OR IGNORE, connection lifecycle)
- `GoogleDriveClient`: correct (streaming download loop, right error types)
- `RabbitmqPublisher`: mostly correct (hardcoded timestamp placeholder minor issue)
- `Settings`: correct (pydantic v2, env_prefix, extra="ignore")

### Extractors — Inconsistent

| Extractor | Status | Issue |
|-----------|--------|-------|
| StepsExtractor | OK | Correct if/else for empty seen set |
| BloodGlucoseExtractor | OK | Correct mmol conversion and null guards |
| HRVExtractor | Fragile | Builds `NOT IN ()` before checking empty set; SQLite accepts it accidentally |
| ActiveCaloriesExtractor | Fragile | Same empty-set issue as HRV |
| DistanceExtractor | Bug | `seen_uuid_hexes` ignored entirely — re-ingests all records every run |
| SleepExtractor | Crash | `row["key"]` access requires row_factory not set in DAG; also `row[0]` is int not uuid |
| HeartRateExtractor | Crash | Override `extract()` uses `row["uuid"]` by name — requires row_factory |
| ExerciseSessionExtractor | OK | Only extractor using correct `bytes.fromhex()` BLOB comparison |

5 different UUID dedup strategies across 8 extractors — no canonical approach enforced.

### DAG — Multiple Call-Site Bugs
1. `RabbitmqPublisher(rabbitmq_host, rabbitmq_port, ...)` — class takes `(rabbitmq_url,
   exchange, exchange_type)`, Settings has `rabbitmq_url` not host/port → AttributeError
2. `download_file_by_name(file_name, zip_path)` — method takes only `file_name`, returns
   bytes; DAG ignores return value → zip never written to disk
3. 6 of 11 extractors missing from `EXTRACTORS` list (generated after DAG task ran)
4. `TaskGroup.add()` invalid — tasks join groups via `with` context manager

### MinioWriter — Wrong fastavro Arg Order
`fastavro.writer(buffer, records, schema)` — correct is `fastavro.writer(fo, schema, records)`.
Every write fails. Recurring across all models tested.
