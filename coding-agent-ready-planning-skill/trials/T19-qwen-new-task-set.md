# Trial Set 19 — Qwen on New Task Set

**Date**: 2026-03-15
**Log**: `run-20260315-140047.log` (337 KB)
**Model**: Qwen 3 Coder 30B (via LM Studio)
**Result**: **17/19 ✅, 2 degraded ⚠️ (tasks 06, 18), 1 skipped ⏭ (task 19)**

---

## Analysis

Root causes of degradation:

1. **Task 06 — Qwen `is_closed` mock trap**: Qwen's pika RabbitMQ implementation checked
   `connection.is_closed` but the mock didn't properly simulate the pika connection lifecycle.
   The `is_closed` property on `BlockingConnection` returns a boolean based on internal state,
   but `MagicMock` auto-creates it as a callable. Fix needed in `python-pytest.md`.

2. **Task 18 — empty `test_command` → global fallback cascade**: The Docker task had no
   `test_command` specified, causing the runner to fall back to the global test suite. This
   picked up failures from other tasks. Fix needed in `run-tasks-template.sh` — every task
   must have a `test_command` or the runner must skip verification rather than run the full suite.

Task 19 (integration test) correctly skipped — services unavailable.

---

## Skill Changes Triggered

- `references/stacks/python-pytest.md`: pika `is_closed` mock trap fix
- `run-tasks-template.sh`: Redesign — per-task `lint_cmd` override; no global-suite fallback
