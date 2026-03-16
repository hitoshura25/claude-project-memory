# Trial Set 14 — Qwen Repeat: ISE → OOM on Wire DAG

**Date**: 2026-03-12
**Model**: Qwen 3 Coder 30B (via LM Studio)
**Result**: 16/18 ✅, 1 ❌ HALTED (task 17 — Metal OOM, DAG file emptied)

---

## Analysis

Repeat run of T13 conditions. Tasks 1–16 passed cleanly. Task 17 (Wire DAG) hit a
`litellm.InternalServerError` during reflection, which bloated context with garbage output.
The resulting context size triggered a Metal GPU OOM segfault, and the DAG file was left
in a corrupted/emptied state.

This is the same ISE → context bloat → OOM pattern from T13 reflection 2, but this time
the OOM was fatal rather than recoverable.

---

## Key Learning

ISE-induced context bloat is a non-deterministic failure mode that can escalate from
recoverable (T13) to fatal (T14). The callable-body snippet fix was designed to reduce
the probability of this pattern by making the wiring task completable in fewer LLM calls,
reducing the surface area for ISE encounters.
