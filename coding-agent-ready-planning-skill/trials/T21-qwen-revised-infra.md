# Trial Set 21 — Qwen on Revised Task Set with Infra Support

**Date**: 2026-03-16
**Log**: `run-20260316-112706.log` (385 KB)
**Model**: Qwen 3 Coder 30B (via LM Studio)
**Result**: **16/18 ✅, 1 degraded ⚠️ (task 17 Docker), 1 hard-fail ❌ (task 18 — services unavailable)**

---

## Root Cause Analysis

**Task 17 Docker — Wrong Airflow image tag in task doc spec**: The task doc specified
`apache/airflow:2.9-python3.11` but this tag doesn't exist — the correct tag is
`2.9.0-python3.11`. This is a **task doc authoring error** — Qwen correctly diagnosed the
issue in reflection but couldn't override the spec it was given.

**Task 18 Integration — Hard-fail (correct)**: Services unavailable. Runner correctly
identified this via `service_check_commands` and hard-failed. This is expected behaviour.

---

## Significance

First trial with infrastructure (Docker/compose) task support. The Docker task failure
confirmed that the Dockerfile spec needs upstream validation — the image tag must be
verified to exist before being embedded in the task doc. Led to open issues #9 and #10.
