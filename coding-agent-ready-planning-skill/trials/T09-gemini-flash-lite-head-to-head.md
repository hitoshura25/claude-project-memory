# Trial Set 9 — Gemini 2.0 Flash Lite Head-to-Head

**Date**: 2026-03-10 afternoon
**Model**: `gemini/gemini-2.0-flash-lite-preview` (Gemini API)
**Result**: 12/13 ✅, 1 degraded ⚠️ (task 13), halted at task 14 ❌

---

## Per-Task Results

| Task | Qwen T7 | Codestral T8 | Gemini T9 | Notes |
|------|---------|--------------|-----------|-------|
| 01 Settings | ⚠️ | ⚠️ | ✅ | Gemini: LazySettings proxy with @cached_property, self-diagnosed |
| 02–05 | ✅ | mixed | ✅ | |
| 06 UUIDStore | ⚠️ | ✅ | ✅ | Gemini: self._conn persistent connection |
| 07–11 | ✅ | mixed | ✅ | |
| 12 Airflow DAG | ⚠️ | ⚠️ | ✅ | Gemini: first model to pass — but added hallucinated import |
| 13 ActiveCaloriesExtractor | ❌ | ⚠️ | ⚠️ | Gemini: correct impl; cascaded from hallucinated DAG import |
| 14–18 | NOT RUN | mixed | NOT RUN | |

---

## Root Cause Analysis

**Task 12 — Gemini passed but hallucinated**: Added `from plugins.extractors.sleep_session_extractor
import SleepSessionExtractor` — a module that doesn't exist. Task 12's test suite passed
(count was 5 including the hallucinated class). Surfaced at task 13 full-suite collection.

**Root cause of all T6-T9 cascades**: Every extractor task had an inline `Modify: dags/...`
step and `test_dag.py` in its `test_command`. When the DAG task degraded, all downstream
extractors failed their gates regardless of their own correctness. This is a structural plan
problem, not a model capability problem.

---

## Key Insight

This trial confirmed the cascade isolation fix was the highest-priority item. Also established
Gemini as the strongest model on the task set at this point, with the caveat of hallucinated
imports needing to be addressed.
