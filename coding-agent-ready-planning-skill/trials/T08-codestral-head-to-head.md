# Trial Set 8 — Codestral 22B Head-to-Head

**Date**: 2026-03-10
**Model**: Codestral 22B v0.1
**Result**: 5/18 ✅, 13 degraded ⚠️, 0 halts

---

## Codestral-Specific Failure Modes

- Leaves `raise NotImplementedError` in method bodies (partial implementation)
- Class naming inconsistency: `MinIOWriter` vs expected `MinioWriter`
- **Edits test files when stuck** — corrupted `test_dag.py` to `assert 1 == 10` by task 18

---

## Head-to-Head vs Qwen T7

**Where Codestral beats Qwen**: Task 6 (UUIDStore) — used persistent `self._conn` correctly.
**Where Qwen beats Codestral**: Tasks 3, 4, 5, 7, 9, 11 — better naming discipline, no stubs left.

---

## Outcome

Codestral's test file corruption behavior is a model-level problem not addressable through
task doc improvements. First data point toward eventual disqualification.
