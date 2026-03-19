# Trial Set 30 — Gemini Same Regression: Missing Persistent Connection Guidance

**Date**: 2026-03-19
**Log**: `run-20260319-115120.log` (49 KB, 32 seconds)
**Model**: Gemini 3.1 Flash Lite (via Gemini API)
**Task set**: Same as T29 (regenerated post-Chat 7)
**LLM calls**: 6
**Result**: **2 ✅, hard-stop at task 3 — identical root cause to T29**

---

## Per-Task Results

| # | Task | Result | Notes |
|---|------|--------|-------|
| 01 | Settings | ✅ | Clean |
| 02 | UUID Store | ✅ | Multi-connection pattern — passes because `tmp_path` fixture masks it |
| 03 | Base Record Extractor | ❌ hard-stop | `uuid_store.filter_new()` → new `:memory:` conn → `OperationalError: no such table: seen_uuids` |
| 04–19 | — | not reached | |

---

## Root Cause: Identical to T29

Gemini independently wrote the same multi-connection pattern as Qwen:

```python
def filter_new(self, uuid_hexes):
    with sqlite3.connect(self.db_path) as conn:  # new connection each call
        cursor = conn.execute("SELECT uuid_hex FROM seen_uuids")
```

This is the natural SQLite pattern both models default to when the task doc lacks the
explicit "hold a persistent `self._conn`" instruction. The task doc in this regeneration
omitted that guidance despite the rule existing in the skill's `python-pytest.md`.

The UUIDStore tests pass because the `store` fixture uses `tmp_path` (file-backed SQLite),
where separate connections to the same file share the same database. The failure surfaces
in task 3's `test_base.py` which uses the conftest `uuid_store` fixture — if that fixture
provides a `:memory:` path, each `sqlite3.connect(":memory:")` creates an independent
empty database with no `seen_uuids` table.

---

## Key Difference from T29: Runner Behavior

In T29 (Qwen), aider exhausted all 3 reflections trying to fix the error, triggering the
"degraded and continue" path. The run continued through all 19 tasks with 9 degraded.

In T30 (Gemini), aider exited cleanly (exit 0) without exhausting reflections, but the
runner's independent test verification caught the failure. This triggered the "tests
failing but aider reported success" hard-stop at task 3. The run ended immediately.

Both outcomes are correct runner behavior for their respective conditions. The underlying
bug is identical.

---

## Confirmation: Both Models Default to Multi-Connection

This is now confirmed across both models on independent runs against the same task set:

| Trial | Model | UUIDStore Pattern | UUIDStore Tests | Base Extractor |
|-------|-------|-------------------|-----------------|----------------|
| T29 | Qwen 30B | `with sqlite3.connect(self.db_path)` per method | ✅ (tmp_path masks it) | ❌ cascade |
| T30 | Gemini Flash Lite | `with sqlite3.connect(self.db_path)` per method | ✅ (tmp_path masks it) | ❌ hard-stop |

The multi-connection pattern is what both models produce by default for SQLite. Without
explicit "hold a persistent connection" guidance in the task doc, the wrong pattern is
the expected outcome — not an anomaly.

---

## Structural Fix Required

Text-based guidance in skill files is insufficient — Claude Code's compliance with the
`:memory:` pairing rule is non-deterministic across regenerations. The fix must be
structural: eliminate the `:memory:` trap at the scaffold level so the wrong UUIDStore
pattern cannot cascade.

Two options identified in T29:
1. Conftest `uuid_store` fixture always uses `tmp_path` (file-backed), never `:memory:`
2. Stub design that fails against multi-connection pattern during Layer 2 validation

Option 1 is simpler and eliminates the trap entirely. The `:memory:` optimization saves
negligible time and has now caused failures in T23, T29, and T30.
