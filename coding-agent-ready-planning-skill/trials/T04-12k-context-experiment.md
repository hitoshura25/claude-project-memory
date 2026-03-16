# Trial Set 4 — 12k Context Experiment

**Date**: 2026-03-04 afternoon
**Log**: `run-20260304-150619.log`
**Model**: Qwen 3 Coder 30B Q4
**Context**: 12,000 tokens (reduced from 32k to test if smaller window helps)
**Result**: Crashed at task 9 (HeartRateExtractor) — earlier than task 17-18 in prior runs

---

## Analysis

**Failure mode**: Metal GPU OOM — `[metal::malloc] Resource limit (499000) exceeded` — a
hard segfault, not a summarizer spiral.

**Root cause — KV cache sizing**: MLX pre-allocates a fixed GPU memory block sized to hold
exactly N token positions. With 12k that block is ~3x smaller than with 32k. Task 9 required
6 reflection loops; by reflection 6 the live conversation had grown to 24 messages. The KV
cache must hold both prompt AND generated output simultaneously — when generated output drove
the total past ~12k mid-generation, the Metal allocator segfaulted.

---

## Key Learning

**Context length floor established: Do not reduce context length below 32k for Qwen 30B on this task set.** MLX pre-allocates a fixed GPU KV cache; reducing to 12k causes Metal GPU OOM segfaults mid-run, strictly worse than the summarizer spiral seen at 32k.
