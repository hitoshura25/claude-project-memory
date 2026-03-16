# Trial Set 17 — Gemini 3.1 Flash Lite — Second Clean Sweep

**Date**: 2026-03-14
**Log**: `run-20260314-130209.log` (1,501 lines)
**Model**: `gemini/gemini-3.1-flash-lite-preview` (Gemini API)
**Skill state**: Same as T15 — post callable-body snippet fix
**Result**: **18/18 ✅, 0 degraded** — 21 LLM calls (down from 27 in T12).

---

## Key Statistics

- Task 17 Wire DAG: **1 LLM call, 0 E501s**
- 12/18 tasks completed in exactly 1 call
- Total LLM calls: 21 (improvement from 27 in T12)

---

## Significance

Second Gemini clean sweep. Efficiency improved with the callable-body snippet fix —
fewer calls needed for the wiring task. Confirms Gemini as the reference model for
speed and reliability.
