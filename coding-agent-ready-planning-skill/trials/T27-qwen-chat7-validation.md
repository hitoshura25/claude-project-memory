# Trial Set 27 — Qwen Chat 7 Validation (test-by-reference + Dockerfile scaffold)

**Date**: 2026-03-18
**Log**: `run-20260318-163040.log` (1.1 MB)
**Model**: Qwen 3 Coder 30B (via LM Studio)
**Task set**: Regenerated post-Chat 7 (test reference-by-path + Dockerfile as scaffold)
**LLM calls**: 39
**Result**: **17/19 — 14 ✅, 3 ⚠️, 1 ❌ (Docker), 1 not reached**

---

## Per-Task Results

| # | Task | Result | Notes |
|---|------|--------|-------|
| 01 | Settings | ✅ | Clean |
| 02 | UUID Store | ✅ | SQL constants used correctly; initial E501 on first attempt, fixed in reflection |
| 03 | Base Record Extractor | ✅ | Clean |
| 04 | Google Drive Client | ✅ | E501 on first attempt (101 chars), fixed |
| 05 | MinIO Writer | ✅ | Clean |
| 06 | RabbitMQ Publisher | ✅ | E501 on first attempt (93 chars), fixed |
| 07 | Steps Extractor | ⚠️ | Reflections exhausted — Avro schema dict + inline SQL f-string both over 88 chars |
| 08 | Blood Glucose | ✅ | Clean |
| 09 | HRV | ✅ | Clean |
| 10 | Heart Rate | ⚠️ | Reflections exhausted — same Avro schema + SQL pattern |
| 11 | Sleep | ✅ | Clean |
| 12 | Active Calories | ✅ | Clean |
| 13 | Distance | ✅ | Clean |
| 14 | Total Calories | ✅ | Clean |
| 15 | O2 Saturation | ⚠️ | Reflections exhausted — same pattern |
| 16 | Exercise Session | ✅ | Clean |
| 17 | Wire DAG | ✅ | **Test reference-by-path validated** — no phantom imports |
| 18 | Docker Deployment | ❌ | Container exit(1) — missing `AIRFLOW__WEBSERVER__SECRET_KEY` |
| 19 | Integration Tests | — | Not reached |

---

## Chat 7 Change Validation

### Test reference-by-path: ✅ Validated

All 17 service tasks passed tests correctly. The wiring task (17) passed cleanly with
the on-disk `test_dag.py` — no phantom import bug. The T23/T24/T27-class divergence
that caused the previous regeneration's wiring test to have bogus shallow-path imports
is eliminated.

### Dockerfile as scaffold: ✅ Partially validated

The model correctly left the Dockerfile untouched and created only compose files. The
Docker image built successfully (all layers CACHED from scaffold). No hadolint issues,
no fabricated versions, no wrong tags. The T21/T22/T25/T26 failure class is eliminated.

The smoke test failure is a different issue — see below.

---

## Task 18 Root Cause — Missing Airflow Secret Key

Both compose files were created correctly and pass `docker compose config`. The Docker
image built successfully. MinIO and RabbitMQ started and became healthy. But the Airflow
container exited with code 1 immediately after starting.

**Root cause:** The test compose is missing `AIRFLOW__WEBSERVER__SECRET_KEY`. Airflow 2.9's
`standalone` command requires this env var to initialize the webserver. Without it, the
process crashes on startup.

This is a **task doc content gap** — the compose spec in the task doc didn't include
this required env var, so the model faithfully reproduced the spec without it. Both Qwen
(T27) and Gemini (T28) hit the same failure.

**Not a model regression.** The model did exactly what the task doc specified. The fix
is either:
1. Add the env var to the task doc's compose spec (platform-specific fix)
2. Add a skill-level rule that Claude Code must verify the service starts successfully
   in the scaffold test compose before finalizing the deployment task doc

---

## E501 Lint Pattern — Addressable Task Doc Deficiency

Three tasks (07, 10, 15) exhausted reflections on E501 errors. Two distinct sources:

1. **Avro schema dict literals** — nested `{"type": "record", ...}` on single lines
   reaching 131 chars. The task doc doesn't instruct the model to break these across
   multiple lines.

2. **Inline SQL f-strings** — `f"SELECT ... FROM {self.table_name} WHERE hex(uuid) IN ({placeholders})"`
   reaching 112 chars. The SQL constants pattern from Chat 5 is documented for UUIDStore
   but not applied to extractor tasks.

The UUID Store task doc (02) has explicit SQL constants guidance and the model followed it
correctly. The extractor task docs (07–16) lack this guidance, leaving the model to inline
SQL and schemas, which reliably exceeds 88 chars.

**Gemini (T28) hit the same E501 surface** (36 E501 errors across the same files) but
resolved all of them within its reflection budget. This is a model capability difference
— Gemini is more efficient at line-breaking — but the E501 surface itself is an upstream
task doc deficiency that should be addressed.

**Proposed fix:** Extend the SQL constants pattern to all tasks that use SQL, and add a
long-literal formatting rule (break nested dicts/schemas across lines) to `writing-guide.md`.

---

## Summarizer Failures (Secondary)

Two `summarizer unexpectedly failed for all models` events during the run. These are
aider's context summarization failing when context grows large — not a task doc issue.
The model continued normally after each failure.
