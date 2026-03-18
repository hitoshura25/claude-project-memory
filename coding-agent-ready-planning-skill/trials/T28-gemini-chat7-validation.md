# Trial Set 28 — Gemini Chat 7 Validation (test-by-reference + Dockerfile scaffold)

**Date**: 2026-03-18
**Log**: `run-20260318-165238.log` (1.1 MB)
**Model**: Gemini 3.1 Flash Lite Preview (via LM Studio)
**Task set**: Same as T27 (regenerated post-Chat 7)
**LLM calls**: 26
**Result**: **17/19 — 17 ✅, 1 ❌ (Docker), 1 not reached**

---

## Per-Task Results

| # | Task | Result | Notes |
|---|------|--------|-------|
| 01 | Settings | ✅ | Clean |
| 02 | UUID Store | ✅ | Clean |
| 03 | Base Record Extractor | ✅ | Clean |
| 04 | Google Drive Client | ✅ | Clean |
| 05 | MinIO Writer | ✅ | Clean |
| 06 | RabbitMQ Publisher | ✅ | Clean |
| 07 | Steps Extractor | ✅ | E501 hit but resolved within reflection budget |
| 08 | Blood Glucose | ✅ | Clean |
| 09 | HRV | ✅ | Clean |
| 10 | Heart Rate | ✅ | Clean |
| 11 | Sleep | ✅ | Clean |
| 12 | Active Calories | ✅ | Clean |
| 13 | Distance | ✅ | Clean |
| 14 | Total Calories | ✅ | Clean |
| 15 | O2 Saturation | ✅ | Clean |
| 16 | Exercise Session | ✅ | Clean |
| 17 | Wire DAG | ✅ | **Test reference-by-path validated** — no phantom imports |
| 18 | Docker Deployment | ❌ | Container exit(1) — missing `AIRFLOW__WEBSERVER__SECRET_KEY` |
| 19 | Integration Tests | — | Not reached |

---

## Chat 7 Change Validation

### Test reference-by-path: ✅ Validated

17/17 service tasks passed cleanly with zero reflections exhausted. Gemini's most
efficient run — 26 LLM calls for 17 tasks (1.5 calls/task average). The wiring task
passed cleanly, confirming the on-disk test had no phantom imports.

### Dockerfile as scaffold: ✅ Partially validated

Same as T27 — model correctly left Dockerfile untouched, created only compose files.
Docker image built from cached scaffold. Smoke test failed on same missing env var.

---

## Task 18 Root Cause — Identical to T27

Missing `AIRFLOW__WEBSERVER__SECRET_KEY` in the test compose. Airflow container
exits immediately with code 1. Both models faithfully reproduced the task doc's
compose spec, which omitted this required env var.

See T27 analysis for full root cause and proposed fix.

---

## E501 Surface — Same as T27, Different Outcome

Gemini hit 36 E501 errors across the same files as Qwen (extractors, uuid_store,
google_drive_client). Unlike Qwen (which exhausted reflections on 3 tasks), Gemini
resolved all E501 errors within its reflection budget.

This confirms the E501 surface is a consistent task doc deficiency — both models
encounter it — but Gemini handles it more efficiently. Addressing the root cause
(SQL constants + Avro schema formatting guidance in extractor task docs) would
eliminate the E501 surface for both models.

---

## Model Efficiency Comparison (T27 vs T28)

| Metric | T27 (Qwen) | T28 (Gemini) |
|--------|-----------|-------------|
| LLM calls | 39 | 26 |
| Duration | ~13 min | ~7 min |
| Reflections exhausted | 3 tasks | 0 tasks |
| E501 errors | same surface | same surface |
| E501 outcome | 3 ⚠️ | all resolved |
| Service tasks (1–17) | 14✅ 3⚠️ | 17✅ |
| Docker task (18) | ❌ | ❌ |

Gemini remains the more efficient model at ~1.5 calls/task. Qwen is competitive
but burns extra reflections on lint issues that Gemini resolves in fewer attempts.
