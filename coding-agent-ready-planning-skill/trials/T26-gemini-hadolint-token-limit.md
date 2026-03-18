# Trial Set 26 — Gemini hadolint DL3013 + Token Limit

**Date**: 2026-03-17
**Log**: `run-20260317-215429.log`
**Model**: Gemini 3.1 Flash Lite Preview (via LM Studio)
**Task set**: Same as T25 (regenerated post-T24)
**Result**: **16/18 ✅, Task 17 ⚠️ (Docker), Task 18 not reached**

---

## Per-Task Results

| Task | Result | Notes |
|------|--------|-------|
| 01 UUIDStore | ✅ | T23 fix confirmed on Gemini too |
| 02 BaseRecordExtractor | ✅ | Clean |
| 03 GoogleDriveClient | ✅ | Clean |
| 04 MinIO Writer | ✅ | **T24 fixture interaction fix confirmed on Gemini** |
| 05 RabbitMQ Publisher | ✅ | Clean |
| 06–15 Extractors (10) | ✅ | All 10 clean |
| 16 Wire DAG | ✅ | Clean |
| 17 Docker Deployment | ⚠️ | hadolint DL3013 + token limit — see below |
| 18 Integration Tests | ⏭ | Not reached |

---

## Task 17 Root Cause — hadolint DL3013 + Token Limit

Gemini's failure is a different manifestation of the same upstream issue as T25:

1. Gemini wrote the Dockerfile **correctly** — unpinned versions matching spec
2. All three files (Dockerfile, production compose, test compose) applied cleanly
3. **hadolint fired DL3013** — "Pin versions in pip"
4. **Gemini hit token limit** trying to respond: `Output tokens: ~0 of 65,536`
5. No fix applied — smoke test ran against the original Dockerfile
6. Docker image **built successfully** (unpinned versions resolve fine)
7. Container **exited with code 1** — Airflow standalone crashed on startup

The container exit(1) is likely an Airflow startup issue (DAG import error,
missing env var, or SQLite path problem) — not directly related to the
hadolint/pinning issue. However, because Gemini couldn't respond after the
token limit, the run was effectively dead.

---

## Key Differences from T25 (Qwen)

| Aspect | T25 (Qwen) | T26 (Gemini) |
|--------|------------|---------------|
| First attempt | Correct (unpinned) | Correct (unpinned) |
| hadolint DL3013 | Fired | Fired |
| Reflection behavior | Fabricated pinned versions | Hit token limit (0 output tokens) |
| Build outcome | Failed (`boto3==1.29.150` nonexistent) | Succeeded (unpinned resolved) |
| Container outcome | N/A (build failed) | Built but exited(1) |

Both models wrote correct Dockerfiles on the first attempt. The failure is
entirely in the reflection cycle triggered by hadolint DL3013 on unpinned deps.

---

## Fix

Same as T25 — Issue #13: `stacks/infra.md` Step 2 updated to pin versions
via `pip freeze` during Claude Code's authoring step. The task doc the small
model receives will have verified pinned versions, so DL3013 never fires.
