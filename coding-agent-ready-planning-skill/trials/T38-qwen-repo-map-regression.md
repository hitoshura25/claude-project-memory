# Trial 38 — Qwen Repo Map Regression

**Date**: 2026-03-21
**Log**: `run-20260321-002806.log` (304 KB)
**Model**: Qwen 3 Coder 30B (via LM Studio)
**Task set**: Same as T36/T37 (three-compose + service_compose)
**Runner change**: Replaced `--no-git` with `--no-auto-commits --no-dirty-commits --subtree-only`
**LLM calls**: 36
**Result**: **13 ✅, 2 ⚠️, run incomplete (Metal GPU OOM on task 17)**

---

## What Changed

Experiment to enable Aider's repo map so the model could see project source
code (e.g., `ExtractionResult` dataclass definition) without explicit task doc
inlining. Replaced `--no-git` with:
- `--no-auto-commits` — prevents Aider from committing
- `--no-dirty-commits` — prevents Aider from committing dirty files
- `--subtree-only` — limits repo map to the current service subtree

Aider confirmed: `Repo-map: using 1024 tokens, auto refresh`

---

## Per-Task Results

| # | Task | Result | Notes |
|---|------|--------|
| 01–08 | Settings → Heart Rate | ✅ | All clean |
| 09 | HRV | ⚠️ (warnings) | Reflections exhausted on lint, tests pass |
| 10 | Steps | ⚠️ Degraded | `uuid_filter assert 3 == 2` — didn't filter UUIDs |
| 11–15 | Sleep → O2 Saturation | ✅ | All clean |
| 16 | Exercise Session | ⚠️ Degraded | `uuid_filter assert 2 == 1` — same filtering failure |
| 17 | DAG Assembly | 💀 Metal GPU OOM | `RuntimeError: [metal::malloc] Resource limit (499000) exceeded` |
| 18–19 | Docker, Integration | Never reached | Run stopped at task 17 |

---

## Root Cause: Repo Map + Complex Task = Context Overflow

The DAG assembly task is the most complex task (imports 15 classes, large code
snippets). The additional 1024 tokens of repo map context, added to every Aider
invocation, pushed the DAG assembly task past the Metal GPU's KV cache capacity.
The model crashed with `[metal::malloc] Resource limit (499000) exceeded` —
repeated 7+ times with no recovery.

The uuid_filter regressions on Steps (10) and Exercise Session (16) suggest the
repo map also distracted the model on simpler tasks. Both passed cleanly in T36
without the repo map.

---

## Comparison: T36 (no repo map) vs T38 (repo map)

| Metric | T36 (`--no-git`) | T38 (repo map) |
|--------|-----------------|----------------|
| ✅ tasks | 18 | 13 |
| ⚠️ degraded | 1 (DAG) | 2 (Steps, ExSession) |
| GPU OOM | None | Task 17 — fatal |
| Integration | ✅ 3/3 | Never reached |
| LLM calls | 39 | 36 (incomplete) |

---

## Conclusion

Aider's repo map is counterproductive for Qwen 30B at 32k context on MLX.
The Aider FAQ warns that "weaker models get easily overwhelmed and confused by
the content of the repo map" — confirmed here. The extra context tokens both
distracted the model on simple tasks and caused fatal GPU OOM on complex ones.

**Decision**: Reverted to `--no-git`. The intermittent 1-task failures at 18/19
pass rate are the practical ceiling for this model size without repo map. Future
investigation paths:
- `--read` for specific files per task (targeted context, not blanket repo map)
- Larger context models that can absorb the repo map without OOM
- Task doc improvements to inline critical type details
