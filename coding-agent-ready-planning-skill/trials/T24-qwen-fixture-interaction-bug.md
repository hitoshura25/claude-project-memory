# Trial Set 24 — Qwen Fixture Interaction Bug

**Date**: 2026-03-17
**Log**: `run-20260317-102208.log`
**Model**: Qwen 3 Coder 30B (via LM Studio)
**Task set**: Regenerated post-T23 (`:memory:` fix applied)
**Result**: **3/18 (1 ⚠️, 2 ✅) — stalled on Task 04 (MinIO Writer)**

---

## Per-Task Results

| Task | Result | Notes |
|------|--------|-------|
| 01 UUIDStore | ⚠️ | Reflections exhausted but tests pass — T23 `:memory:` fix confirmed (no `:memory:` fixture in test) |
| 02 BaseRecordExtractor | ✅ | Clean |
| 03 GoogleDriveClient | ✅ | Clean |
| 04 MinIO Writer | ❌ stalled | Logically impossible test — see below |
| 05–18 | not reached | |

---

## Task 04 Root Cause — Capture Mock / Assertion Contradiction

The test `test_avro_body_non_empty` uses **both** `mock_s3_client` and `mock_fastavro_writer`:

```python
def test_avro_body_non_empty(mock_s3_client, mock_fastavro_writer):
    writer.upload_avro(records, schema, ...)
    body = mock_s3_client["captured_body"]()
    assert len(body) > 0  # always fails
```

The `mock_fastavro_writer` fixture patches `fastavro.writer` with a side_effect that
captures `(fo, schema, records)` but **never writes bytes to `fo`**. The implementation
correctly does `fastavro.writer(buffer, schema, records)` → `buffer.read()` →
`put_object(Body=avro_bytes)`, but the mock intercepts the call and the buffer stays
empty. So `Body=b""` and `assert len(body) > 0` always fails.

**This is a test authoring error, not a model error.** Qwen's implementation is correct.
The test is logically impossible to pass — the capture mock prevents the behavior the
assertion checks.

---

## Root Cause Analysis — Same Class as T23

Both T23 and T24 are **Claude Code test-authoring errors** caused by LLM non-determinism:

| Trial | Bug | Pattern |
|-------|-----|--------|
| T23 | `:memory:` fixture without persistent connection Behavior warning | Fixture creates constraint; task doc doesn't warn about it |
| T24 | Capture mock combined with assertion on captured function's output | Mock blocks the side effect the assertion checks |

Both are instances of: **Claude Code generates complex fixture/test interactions from
scratch each regeneration, and sometimes the interactions are logically contradictory.**

In T15/T18 (clean sweeps), Claude Code happened to write compatible fixture/test
combinations. In T23/T24, it didn't. Pure non-determinism — no skill file change
caused the regression.

---

## Fix Applied

**Fixture Patterns reference file** (`references/stacks/fixture-patterns.md`) — new file.

Categorizes all mock fixtures into three behavioral patterns (Capture Mock, Client Mock,
Stateful Fake) with explicit rules about what tests can and cannot assert with each:

- **Capture mock**: CAN assert on captured args. CANNOT assert on output side effects.
- **Client mock**: CAN assert on call patterns/kwargs. CANNOT assert on return values.
- **Stateful fake**: CAN assert on actual outcomes. MUST respect backend constraints.

**Fixture Interaction Rules** prevent the T24 class of bug:
- Rule 1: Capture mocks block downstream side effects — do not assert on them
- Rule 2: Client mocks return MagicMocks — set return_value explicitly if needed
- Rule 3: Stateful fakes have real constraints — respect `:memory:` semantics

**SKILL.md** updated: Step 3 references fixture-patterns.md for conftest setup;
Step 3b adds fixture interaction rule check before writing tests.

**python-pytest.md** updated: External Dependency Mock Fixtures section replaced with
pattern summary table + pointer to fixture-patterns.md. Technology-specific traps
(pika is_closed, fastavro positional) remain inline.

---

## Degenerate Output Loop (Secondary)

Same pattern as T23: after exhausting reflections, Qwen entered a repetition collapse
(infinite "Looking at my files again, I see that there's a mismatch..."). LM Studio
log shows conversation grew to 26 messages, model reloaded once, client disconnected
while model was still processing prompt at 68.4%.

---

## LM Studio Log Summary

- 2 model loads (initial + reload after 26-msg context bloat)
- 14 completions total
- Tasks 1–3: conversation grew 8→12→16→20 messages (normal)
- Task 4: grew to 26 messages, model reload at 10:29:53, client disconnect at 10:30:11
