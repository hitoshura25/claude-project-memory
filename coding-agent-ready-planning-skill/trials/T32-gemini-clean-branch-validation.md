# Trial Set 32 — Gemini Clean Branch Validation

**Date**: 2026-03-19
**Log**: `run-20260319-215020.log` (715 KB, ~11 min)
**Model**: Gemini 3.1 Flash Lite (via Gemini API)
**Task set**: Same as T31 (fresh regeneration from clean branch)
**LLM calls**: 48
**Result**: **16 ✅, 2 ⚠️ degraded, 1 ❌ (services unavailable)**

---

## Per-Task Results

| # | Task | Result | Notes |
|---|------|--------|-------|
| 01 | Settings | ✅ | Clean |
| 02 | UUIDStore | ✅ | **Persistent `self.conn` — correct pattern** |
| 03 | Base Extractor | ✅ | Clean |
| 04 | Google Drive Client | ⚠️ Degraded | `JSONDecodeError` — mock returns bytes, model tries to parse as JSON |
| 05 | MinIO Writer | ✅ | Clean |
| 06 | RabbitMQ Publisher | ✅ | Clean |
| 07 | Blood Glucose | ✅ | Clean |
| 08 | Heart Rate | ✅ | Clean |
| 09 | HRV | ✅ | Clean |
| 10 | Steps | ✅ | Clean |
| 11 | Sleep | ✅ | Clean |
| 12 | Active Calories | ✅ | Clean |
| 13 | Total Calories | ⚠️ Degraded | `KeyError: 'startTime'` — model produced wrong output dict keys |
| 14 | Distance | ✅ | Clean |
| 15 | O2 Saturation | ✅ | Clean |
| 16 | Exercise Session | ✅ | Clean |
| 17 | DAG Assembly | ✅ | Clean |
| 18 | Docker Deployment | ✅ | **Full smoke test pass — health 200** |
| 19 | Integration Tests | ❌ | Services unavailable (expected) |

---

## Structural Fix Validations

### `:memory:` enforcement: ✅ Correct pattern produced

Gemini wrote persistent `self.conn = sqlite3.connect(self.db_path)` in `__init__`,
with all methods using `self.conn`. UUIDStore tests passed on first attempt.

The `:memory:` fixture enforced the correct pattern by design — if Gemini had
written multi-connection, `test_get_seen_empty` would have failed immediately
(same as Qwen in T31).

### Docker full lifecycle: ✅ Complete pass with smoke test

The full Docker lifecycle worked end-to-end:
1. Dockerfile scaffold → built from cache
2. Test compose scaffold → `docker compose up --wait` → all healthchecks passed
3. HTTP 200 on `/health` endpoint
4. Clean teardown

This is the first trial where the smoke test ran the full health check and got
a real HTTP 200 response. Previous Docker passes (T27, T28) failed on missing
env vars before reaching the health check.

### DAG Assembly: ✅ Clean pass

Wiring task passed cleanly (failed in T31/Qwen due to Airflow mock issue).
Gemini correctly handled the mocked Airflow environment.

### No cascade: ✅ Confirmed

All extractor tasks (7–16) ran independently. The two degraded tasks (4, 13)
are unrelated to each other and to UUIDStore.

---

## Failure Analysis

### Task 4 (Google Drive Client) — JSONDecodeError

The mock's `MediaIoBaseDownload` writes raw bytes to the file handle. Gemini's
implementation tried to parse the downloaded content as JSON, hitting
`JSONDecodeError: Expecting value: line 1 column 1 (char 0)`.

This is a task doc gap — the task doc doesn't specify that the downloaded file
is a ZIP archive (binary), not JSON. The model assumes a parseable format.

### Task 13 (Total Calories) — KeyError: 'startTime'

The test expects `rec["startTime"]["epochMillis"]` but the model produced records
with different key names. This is a task doc / interface contract gap — the
expected output dict structure isn't fully specified.

---

## Model Efficiency Comparison (T31 vs T32)

| Metric | T31 (Qwen) | T32 (Gemini) |
|--------|-----------|-------------|
| ✅ tasks | 8 | 16 |
| ⚠️ degraded | 9 | 2 |
| LLM calls | 52 | 48 |
| Duration | ~62 min | ~11 min |
| UUIDStore | ⚠️ (multi-conn, caught) | ✅ (persistent conn) |
| Docker | ✅ | ✅ (full smoke test) |
| DAG Assembly | ⚠️ | ✅ |
| E501 reflections exhausted | multiple | 0 |
| Calls/task | ~2.9 | ~2.7 |

Gemini remains significantly more efficient. Both models share the task 13
(Total Calories) failure, confirming it's a task doc issue not model-specific.

---

## Clean Branch Validation Summary

T31+T32 are the first trials from a completely clean branch. Key findings:

1. **Structural fixes work**: `:memory:` enforcement caught Qwen's multi-conn
   pattern; Docker scaffold passed on both models; no cascade from UUIDStore.
2. **Fresh regeneration produces cleaner architecture**: `ExtractionResult`,
   `extract(conn, uuids_to_skip)` — decoupled from UUIDStore entirely.
3. **Remaining failures are task doc content gaps**, not structural issues:
   Google Drive Client (binary vs JSON), Total Calories (output dict keys),
   Avro schema duplicate types, ExtractionResult interface.
4. **Qwen’s UUIDStore failure is a reflection budget issue**: The `:memory:`
   fixture catches the bug correctly, but Qwen can't fix it within 3 reflections.
   The task doc Behavior instruction ("persistent self._conn") may still be needed
   as guidance even though the fixture enforces it.
