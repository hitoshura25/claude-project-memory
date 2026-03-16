# Trial Set 22 — Gemini on Revised Task Set with Infra Support

**Date**: 2026-03-16
**Log**: `run-20260316-121437.log` (483 KB)
**Model**: `gemini/gemini-3.1-flash-lite-preview` (Gemini API)
**Skill state**: Identical to T21 — same task set, no skill changes between runs
**Result**: **16/18 ✅, 1 degraded ⚠️ (task 17 Docker), 1 hard-fail ❌ (task 18 — services unavailable)**

---

## Per-Task Results

| Task | Lines | Notes |
|------|-------|-------|
| 01 UUIDStore | 108 | ✅ |
| 02 BaseExtractor | 176 | ✅ |
| 03 GDriveClient | 161 | ✅ |
| 04 MinIOWriter | 103 | ✅ |
| 05 RabbitMQ | 81 | ✅ — `is_closed` fix confirmed again |
| 06–15 Extractors | ~59 avg | ✅ all |
| 16 Wire DAG | 159 | ✅ |
| 17 Docker | 3572 | ⚠️ — see below |
| 18 Integration | ❌ | Hard-fail: services unavailable — correct |

**Runner summary**: `16 tasks completed, 1 degraded, 1 hard-fail (services unavailable)`
**Task 17 LLM calls: 27** (vs Qwen T21's 3) — massive spiral

---

## Task 17 Root Cause — Same Image Tag Error, Deeper Recovery

Gemini followed the same cascade as Qwen but got further, exposing a second layer:

1. **Attempt 1**: Wrote spec-as-given (`FROM apache/airflow:2.9-python3.11`) + fixed hadolint
   warnings (`DL3013`, `DL3042`). Build failed: image tag not found.
2. **Attempt 2**: Fixed the image tag (`2.9.1-python3.11`) — but was still running `pip install`
   as `USER root` inside the official Airflow image. The Airflow base image actively blocks
   root pip installs ("You are running pip as root. Please use 'airflow' user!"). Build failed:
   `pip install` exit code 1.
3. **Attempt 3**: Moved `pip install --user` under `USER airflow`. But `pip install --user`
   inside an Airflow container doesn't work either — the pip binary doesn't exist for the
   airflow user, and uv isn't on PATH. Build failed: exit code 1.

After attempt 3, Gemini hit the **free-tier input token quota** (250,000 tokens/session). The
aider summarizer failed with "cannot schedule new futures after shutdown", consuming the final
reflection slot on a garbled output. The run degraded.

### The Underlying Issue

The Dockerfile spec itself is structurally wrong for the Airflow base image:
- The official `apache/airflow` image already has pip-as-airflow configured; it doesn't allow root pip
- `RUN pip install uv` should be `RUN pip install --no-cache-dir uv` run **as airflow**, or
  better: use `pip install --constraint "..." uv` following Airflow's recommended pattern
- The correct approach for installing uv in an Airflow container is either as the `airflow`
  user with the right PATH, or using the Airflow-provided pip wrapper

This is fundamentally a **task doc authoring error** — the Dockerfile spec was not validated
against the actual base image's constraints before being embedded. The correct fix remains
issues #9 and #10.

---

## T22 vs T21 Comparison on Task 17

| | Qwen T21 | Gemini T22 |
|---|---|---|
| LLM calls | 3 | 27 |
| Image tag identified | ✅ (in reflection) | ✅ (fixed in attempt 2) |
| Got past image pull | ❌ | ✅ |
| Hit pip/USER issue | ❌ | ✅ (new failure mode) |
| Quota exhaustion | No | Yes (free tier) |
| Final failure | Image not found | pip exit code 1 + quota |

Gemini made more progress but uncovered a second layer of the same fundamental problem. Both
failures trace to the same root cause: the Dockerfile spec was not validated against the real
image before being written.

**Task 18 hard-fail — correct behavior confirmed again (two runs).**

---

## Model Comparison — T21/T22

| Metric | Gemini T22 | Qwen T21 |
|--------|------------|----------|
| Task set | Revised + infra | Revised + infra |
| Tasks 01–16 | 16/16 ✅ | 16/16 ✅ |
| Task 17 Docker | ⚠️ 27 calls, quota hit | ⚠️ 3 calls, image not found |
| Task 18 Integration | ❌ hard-fail (correct) | ❌ hard-fail (correct) |
| Root cause | Same task doc error; Gemini got further but hit pip/USER constraint + quota | Same task doc error; stopped at image pull |

**Common finding:** Both models confirm the same two upstream skill fixes are needed
(issues #9, #10). The task doc is wrong regardless of which model runs it.
