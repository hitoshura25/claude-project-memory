# Trial 34 — Gemini Code-Grounding Rule Validation

**Date**: 2026-03-20
**Log**: `run-20260320-130537.log` (907 KB)
**Model**: Gemini 3.1 Flash Lite (via Gemini API)
**Task set**: Same as T33 (fresh regeneration with code-grounding rule)
**LLM calls**: 44
**Result**: **16 ✅, 1 ⚠️ degraded, Docker exit(1), Integration never ran**

---

## Per-Task Results

| # | Task | Result | Notes |
|---|------|--------|-------|
| 01 | Settings | ✅ | Clean |
| 02 | UUIDStore | ✅ | Clean |
| 03 | Base Extractor | ✅ | Clean |
| 04 | Google Drive Client | ✅ | **Fixed from T32** — was ⚠️ (JSONDecodeError) |
| 05 | MinIO Writer | ✅ | Clean |
| 06 | RabbitMQ Publisher | ✅ | Clean |
| 07 | Blood Glucose | ✅ | Clean |
| 08 | Heart Rate | ✅ | Clean |
| 09 | HRV | ⚠️ Degraded | `ExtractionResult.__init__() got unexpected keyword argument 'record_type'` then `uuid_filter assert 3 == 2` |
| 10 | Steps | ✅ | Clean |
| 11 | Sleep | ✅ | Clean |
| 12 | Active Calories | ✅ | Clean |
| 13 | Total Calories | ✅ | **Fixed from T32** — was ⚠️ (KeyError 'startTime') |
| 14 | Distance | ✅ | Clean |
| 15 | O2 Saturation | ✅ | Clean |
| 16 | Exercise Session | ✅ | Clean |
| 17 | DAG Assembly | ✅ | Clean |
| 18 | Docker | exit(1) | Container builds, MinIO+RabbitMQ healthy, Airflow exits(1) |
| 19 | Integration | Never ran | Log ended during Docker task |

---

## Code-Grounding Rule Impact

### Fixed from T32 (2 improvements)

- **Google Drive Client (04)**: Was ⚠️ (JSONDecodeError — model tried to JSON-parse binary bytes). Now ✅ — task doc specifies binary `"wb"` write mode.
- **Total Calories (13)**: Was ⚠️ (KeyError 'startTime' — model produced wrong dict keys). Now ✅ — task doc includes exact output dict structure grounded from test assertions.

### Remaining failure (1 degraded)

- **HRV (09)**: `ExtractionResult.__init__() got unexpected keyword argument 'record_type'`, then after reflection `uuid_filter assert 3 == 2`. Same ExtractionResult kwargs issue as Qwen. Only 1 of 10 extractors hit this — the other 9 passed clean.

---

## Docker exit(1)

Gemini wrote a production compose with `env_file: .env` and env var substitutions. Container builds from cache, MinIO+RabbitMQ healthy, but Airflow `exited (1)`. Same pattern as Qwen T33 and both models in T27/T28. Scaffold issue.

---

## Comparison to T32

| Metric | T32 (before) | T34 (after) |
|--------|-------------|-------------|
| ✅ tasks | 16 | 16 |
| ⚠️ degraded | 2 | 1 |
| LLM calls | 48 | 44 |
| Google Drive | ⚠️ | ✅ |
| Total Calories | ⚠️ | ✅ |
| HRV | ✅ | ⚠️ |
| Docker | ✅ (HTTP 200) | exit(1) |

Service task quality improved (both T32 gaps fixed), but Docker regressed and HRV is a new single-task failure on ExtractionResult kwargs.

---

## Cross-Model Comparison (T33 vs T34)

| Metric | T33 (Qwen) | T34 (Gemini) |
|--------|-----------|-------------|
| ✅ tasks | 12 | 16 |
| ⚠️ degraded | 5 | 1 |
| LLM calls | 46 | 44 |
| ExtractionResult kwargs | 2 tasks | 1 task |
| uuid_filter not applied | 3 tasks | 1 task (same as kwargs) |
| Docker | exit(1) | exit(1) |

Both models share the ExtractionResult kwargs issue (Gemini on 1 task, Qwen on 2). Both hit Docker exit(1). Gemini handles uuid_filter correctly on all tasks except HRV where it first hit the kwargs issue.
