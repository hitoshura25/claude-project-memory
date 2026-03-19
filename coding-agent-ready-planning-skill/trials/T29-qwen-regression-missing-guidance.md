# Trial Set 29 — Qwen Regression: Missing Task Doc Guidance

**Date**: 2026-03-19
**Log**: `run-20260319-112234.log` (605 KB)
**Model**: Qwen 3 Coder 30B (via LM Studio)
**Task set**: Regenerated post-Chat 7 (test-by-ref + Dockerfile/compose scaffold + E501 rule)
**LLM calls**: 54
**Result**: **7 ✅, 1 ⚠️ (tests pass), 9 ⚠️ (degraded), 1 ❌ (Docker), 1 not reached**

> Note: A prior run attempt (two logs at 104007/104008) was a duplicate launch
> with two aider instances racing on the same files. That run is discarded.
> This is the clean single-instance rerun.

---

## Per-Task Results

| # | Task | Result | Notes |
|---|------|--------|-------|
| 01 | Settings | ✅ | Clean |
| 02 | UUID Store | ⚠️ (tests pass) | **Wrong pattern**: `with sqlite3.connect(self.db_path)` per method instead of persistent `self._conn`. Passes because tests use file-backed `tmp_path`. |
| 03 | Base Record Extractor | ⚠️ Degraded | `test_base.py` uses `uuid_store` conftest fixture (→ broken filter_new) → `OperationalError: no such table: seen_uuids` |
| 04 | Google Drive Client | ✅ | Clean |
| 05 | MinIO Writer | ✅ | Clean |
| 06 | RabbitMQ Publisher | ✅ | Clean |
| 07 | Steps Extractor | ✅ | Clean |
| 08 | Blood Glucose | ⚠️ Degraded | Cascade from task 3 |
| 09 | HRV | ⚠️ Degraded | Cascade from task 3 |
| 10 | Heart Rate | ✅ | Clean (does not call `extract_new` in its test) |
| 11 | Sleep | ⚠️ Degraded | Cascade from task 3 |
| 12 | Active Calories | ⚠️ Degraded | Cascade from task 3 |
| 13 | Distance | ⚠️ Degraded | Cascade from task 3 |
| 14 | Total Calories | ⚠️ Degraded | Cascade from task 3 |
| 15 | O2 Saturation | ⚠️ Degraded | Cascade from task 3 |
| 16 | Exercise Session | ⚠️ Degraded | Cascade from task 3 |
| 17 | Wire DAG | ✅ | Clean — import integrity + EXTRACTORS length pass |
| 18 | Docker Deployment | ❌ | Container exit(127) — likely DAG import error from corrupted extractors |
| 19 | Integration Tests | — | Not reached |

---

## Root Cause: Missing Persistent Connection Guidance in UUIDStore Task Doc

The UUIDStore task doc (02) in this regeneration did **not** include:
- "Must hold a persistent `self._conn` connection opened in `__init__`"
- SQL constants pattern (module-level constants for SQL strings)

Both rules exist in the skill (`python-pytest.md` § ":memory: trap", `writing-guide.md`
§ "SQL Constants Pattern"), but Claude Code did not apply them to this specific task doc
during regeneration. This is the same LLM non-determinism at the authoring stage that
caused the test embedding divergence (issue #14).

Without the persistent connection instruction, Qwen wrote
`with sqlite3.connect(self.db_path) as conn:` in every method — the natural SQLite pattern
but fatal with `:memory:` databases where each `connect()` call creates an independent
empty database.

---

## Cascade Mechanism

1. Task 2 (UUIDStore): Tests pass because the fixture uses `tmp_path` (file-backed).
   The wrong implementation ships to disk.
2. Task 3 (BaseRecordExtractor): Test uses `uuid_store` conftest fixture which provides
   `UUIDStore(":memory:")`. The `filter_new` method opens a new connection with no
   `seen_uuids` table → `OperationalError`.
3. Tasks 8–16: All extractor tests that call `extract_new` (which internally calls
   `uuid_store.filter_new`) hit the same error. Tasks that test `_build_records` directly
   (Steps at task 7, HeartRate at task 10) are unaffected.

---

## Why This Is a Recurring Problem

The skill has the rules. Claude Code doesn't always apply them. This is the third time
the `:memory:` trap has appeared:

- T23: `:memory:` fixture without Behavior warning → fix: pairing rule in `python-pytest.md`
- T24: Capture mock + body assertion contradiction → fix: fixture interaction rules
- T29: Pairing rule exists but Claude Code didn't include it in the task doc

The pattern is: adding rules to skill files works when Claude Code follows them, but
Claude Code's compliance is non-deterministic across regenerations. Some regenerations
apply all rules; others miss critical ones.

---

## Proposed Fix: Enforcement at Scaffold Validation

Rather than relying on Claude Code to include guidance text in task docs (which it may
or may not do), enforce the constraint at the scaffold level:

1. **Conftest fixture design**: If the `uuid_store` fixture passes `:memory:`, the
   `UUIDStore` stub should be designed so that the multi-connection pattern **fails
   against the stub itself** during Layer 2 validation. Currently the stub raises
   `NotImplementedError` which masks the connection pattern issue.

2. **Alternatively**: The `uuid_store` conftest fixture should always use `tmp_path`
   (file-backed), eliminating the `:memory:` trap entirely. The `:memory:` optimization
   is not worth the recurring authoring risk.

Both approaches shift enforcement from "Claude Code must remember to write specific
text" (unreliable) to "the scaffold design prevents the wrong pattern" (structural).

---

## Docker Exit(127)

Container exited with "command not found" (exit 127). The Dockerfile is scaffold
(untouched). The likely cause is corrupted DAG/plugin Python files from the 9 degraded
extractor tasks — Airflow fails to import the DAG module and crashes.
