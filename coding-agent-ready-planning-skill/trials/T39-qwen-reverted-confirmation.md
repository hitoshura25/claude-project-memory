# Trial 39 — Qwen Reverted to --no-git (Confirmation)

**Date**: 2026-03-21
**Log**: `run-20260321-010819.log` (661 KB)
**Model**: Qwen 3 Coder 30B (via LM Studio)
**Task set**: Same as T36–T38 (three-compose + service_compose)
**Runner change**: Reverted back to `--no-git` (same as T36)
**LLM calls**: 39
**Result**: **17 ✅, 1 ⚠️ (DAG Assembly), Integration 3/3 ✅ (during Aider), verification failed (clock skew)**

---

## Per-Task Results

| # | Task | Result | Notes |
|---|------|--------|-------|
| 01–16 | All service tasks | ✅ | All clean — matches T36 exactly |
| 17 | DAG Assembly | ⚠️ Degraded | Same `dag.dag_id` MagicMock issue as T36 |
| 18 | Docker | ✅ | Full smoke test pass |
| 19 | Integration Tests | ✅/❌ | **3/3 passed during Aider run**; independent verification failed (MinIO clock skew) |

---

## Integration Test Failure Detail

The integration tests passed 3/3 during Aider's execution (line 5922: `3 passed in 0.49s`).
However, the LM Studio summarizer then crashed (`summarizer unexpectedly failed for all models`),
and the runner's independent test verification reran the tests. By this point the MinIO
container's clock had drifted:

```
botocore.exceptions.ClientError: An error occurred (RequestTimeTooSkewed)
when calling the ListBuckets operation: The difference between the request
time and the server's time is too large
```

This is an infrastructure timing issue, not a code failure. The service_compose
services had been running since before task 19 started, and the elapsed time
(including Aider's reflection cycles + summarizer crash) caused the skew.

---

## Comparison: T36 vs T39

| Metric | T36 | T39 |
|--------|-----|-----|
| ✅ service tasks | 17 | 17 |
| ⚠️ degraded | 1 (DAG) | 1 (DAG) |
| Integration (Aider) | ✅ 3/3 | ✅ 3/3 |
| Integration (verify) | ✅ | ❌ (clock skew) |
| LLM calls | 39 | 39 |
| E501 | 18 | 18 |

Results are functionally identical to T36. Confirms the revert to `--no-git` restores
the baseline behavior. The repo map experiment (T38) was strictly worse.

---

## Note on Clock Skew

The `RequestTimeTooSkewed` error suggests the runner should tear down and restart
services if the independent verification is going to rerun integration tests.
Alternatively, the runner could skip independent verification for `requires_services`
tasks since the services may have drifted. Logged as a potential improvement but
not an open issue — the Aider-phase result (3/3 passed) is the authoritative one.
