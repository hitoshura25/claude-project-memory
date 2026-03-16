# Trial Set 16 — Codestral Final Confirmation

**Date**: 2026-03-14
**Log**: `run-20260314-123454.log` (halted at task 7)
**Model**: Codestral 22B v0.1 (via LM Studio)
**Result**: 2/7 ✅, 1 ❌ task 3 edit format failure cascading to all downstream extractors.

---

## Analysis

**Codestral disqualified — third and final confirmation** (after T8 and T11).

Task 3 (BaseRecordExtractor) hit an edit format failure — Codestral produced prose + command
output instead of conforming to aider's edit format. This cascaded to all downstream
extractor tasks that depended on the base class.

The same model-level behaviours observed in T8 and T11 persisted:
- Edit format failures under pressure
- Test file corruption when stuck
- Lint spiral loops consuming all reflections

These are fundamental model behaviours, not addressable through task doc improvements.

---

## Outcome

**Codestral 22B permanently disqualified.** No further trials planned.

| Trial | Result | Key Failure |
|-------|--------|-------------|
| T8 | 5/18 ✅, 13 ⚠️ | Test file corruption, lint spirals |
| T11 | 7/17 ✅, 9 ⚠️ | Lint spirals, edit format failures, test corruption |
| T16 | 2/7 ✅, 1 ❌ | Edit format failure cascade from task 3 |
