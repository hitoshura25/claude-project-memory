# Trial Set 23 — Qwen :memory: Trap Regression

**Date**: 2026-03-16
**Logs**: `run-20260316-205929.log` (197 KB), `run-20260316-205930.log` (196 KB, duplicate), `run-20260316-211230.log` (52 KB)
**Model**: Qwen 3 Coder 30B (via LM Studio)
**Task set**: Regenerated post-Chat 6 (Docker image verification fix)
**Result**: **0/18 — stalled on Task 01 (UUIDStore) in both attempts**

---

## What Happened

Both runs failed identically on Task 01 (UUIDStore). Neither progressed past the first task.

### Attempt 1 (run-20260316-205929 + 205930)

Two aider instances launched 1 second apart (duplicate launch). Both attempted Task 01.

1. Qwen wrote a correct-looking UUIDStore with SQL constants, `_init_db()` in `__init__`,
   and batch chunking for the IN-clause limit.
2. **Critical error**: Used `sqlite3.connect(self.db_path)` inside each method (new connection
   per call) rather than holding a persistent `self._conn`.
3. Test fixture `mem_store` passes `":memory:"` — each new `connect(":memory:")` creates a
   fresh empty database, so `filter_new` gets "no such table: seen_uuids".
4. Two reflection attempts failed to identify the root cause.
5. Qwen entered a **degenerate output loop** — infinite repetitions of
   `"# Create placeholders for the IN clause"` until context exhaustion.

### Attempt 2 (run-20260316-211230)

Same failure sequence. Same "no such table" error. Degenerate output loop at end —
infinite `"middle of the middle of the middle..."` until context exhaustion.

---

## Root Cause

**Latent test-authoring regression, not caused by Chat 6 skill changes.**

The test file written by Claude Code during this regeneration included a `mem_store` fixture
using `":memory:"`. The task doc's Behavior section did NOT include the mandatory persistent
connection instruction: *"Must hold a persistent `self._conn` connection opened in `__init__`
— do not open a new connection per method call."*

The `:memory:` trap is documented in `python-pytest.md` § "SQLite Trap Patterns / Trap 1",
which says to include the persistent connection warning "in every task doc's `## Behavior`
section whenever SQLite is used." However, no enforcement mechanism existed to ensure Claude
Code actually adds this warning when it writes a `:memory:` fixture. The skill said to do it,
but didn't make it a paired requirement.

**Why this didn't happen in T15/T18 (clean sweeps):** Previous regenerations likely used only
`tmp_path`-based fixtures for UUIDStore tests. File-backed SQLite works correctly even with
separate connections per method. The `:memory:` fixture is the new element this regeneration
introduced — Claude Code added it for speed but omitted the matching Behavior warning.

---

## Fix Applied

**Mandatory test-authoring rule added to `python-pytest.md` § Trap 1:**

If any test fixture passes `":memory:"` to a SQLite-backed class, the task doc's `## Behavior`
section **must** include the persistent connection instruction. The `:memory:` fixture and the
Behavior warning are a matched pair — writing one without the other is now explicitly prohibited.

A verification step was also added: after writing a test file with a `:memory:` fixture,
confirm the task doc's Behavior section contains the persistent connection rule before
proceeding.

---

## Degenerate Output Loop (Secondary Issue)

Both runs ended with Qwen entering a repetition collapse — infinitely repeating the same
token sequence until context exhaustion. This is a model-level behavior under context pressure
(after failed reflections fill the context). The `--timeout` flag may not be cutting through
the streaming output effectively. This is not addressable through task doc improvements but
is worth monitoring — it means a task failure on Qwen doesn't just fail, it hangs.

---

## Duplicate Launch (run-20260316-205929 + 205930)

Two log files started within 1 second, both ~196 KB, both attempting Task 01. This suggests
an accidental double-launch of the runner script. Not a skill issue — operational.
