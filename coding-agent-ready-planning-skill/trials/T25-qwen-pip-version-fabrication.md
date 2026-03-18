# Trial Set 25 — Qwen Pip Version Fabrication

**Date**: 2026-03-17
**Log**: `run-20260317-181145.log`
**Model**: Qwen 3 Coder 30B (via LM Studio)
**Task set**: Regenerated post-T24 (fixture-patterns.md + interaction rules applied)
**Result**: **16/18 ✅, Task 17 ⚠️ (Docker), Task 18 not reached**

---

## Per-Task Results

| Task | Result | Notes |
|------|--------|-------|
| 01 UUIDStore | ✅ | T23 `:memory:` fix confirmed — test uses `tmp_path` only |
| 02 BaseRecordExtractor | ✅ | Clean |
| 03 GoogleDriveClient | ✅ | Clean |
| 04 MinIO Writer | ✅ | **T24 fixture interaction fix confirmed** — no `mock_fastavro_writer` in body assertion test |
| 05 RabbitMQ Publisher | ✅ | Clean |
| 06–15 Extractors (10) | ✅ | All 10 clean |
| 16 Wire DAG | ✅ | Clean — import integrity, callable bodies |
| 17 Docker Deployment | ⚠️ | Fabricated pinned versions — see below |
| 18 Integration Tests | ⏭ | Not reached |

---

## Task 17 Root Cause — Fabricated Pinned Versions

The task doc spec uses unpinned versions (`pip install fastavro boto3 pika ...`),
which is what Claude Code's `docker build` verification confirmed works.

Qwen's **first attempt** correctly wrote unpinned versions matching the spec.
The initial build succeeded. But hadolint fired DL3013 ("Pin versions in pip"),
triggering a reflection cycle where Qwen added fabricated pinned versions:

- `boto3==1.29.150` — does not exist (boto3 jumped from 1.29.7 to 1.33.0)
- `fastavro==1.9.5` — exists but not the version resolved by the base image
- `pika==1.3.2` — exists
- `structlog==23.1.0` — exists

The Docker build failed on `boto3==1.29.150` — pip could not find that version.

---

## Root Cause Chain

1. Task doc Dockerfile spec uses unpinned versions (correct per skill guidance at the time)
2. Qwen writes unpinned → build succeeds → hadolint fires DL3013 warning
3. Qwen's reflection interprets DL3013 as requiring pinned versions
4. Qwen fabricates version numbers from training data (not from `pip freeze`)
5. `boto3==1.29.150` doesn't exist → build fails → reflections exhausted

---

## Same Root Cause as T26

Both T25 (Qwen) and T26 (Gemini) fail on the same upstream issue: the task doc
spec has unpinned pip dependencies, hadolint DL3013 fires, and the model's
reflection attempt makes it worse (Qwen fabricates versions; Gemini hits token limit).

---

## Fix Applied

**Issue #13**: `stacks/infra.md` Step 2 rewritten — "Write a draft Dockerfile,
build it, and pin versions." Claude Code must:
1. Build with unpinned versions first
2. Run `docker run --rm test-build-verify pip freeze` to capture resolved versions
3. Pin the resolved versions in the Dockerfile
4. Rebuild to confirm
5. Run hadolint — DL3013 should not fire with pinned versions

This moves version pinning to Claude Code's authoring step (Step 3), so the
task doc the small model receives already has verified pinned versions.
