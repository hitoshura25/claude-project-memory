# T43 — Qwen 30B: Interface Contract Comment-as-Default Regression (INVALID)

**Date**: 2026-03-23
**Model**: Qwen 3 Coder 30B (Q4, 32k context)
**Log**: `run-20260323-154502.log`
**Chat**: 9
**Verdict**: INVALID — Halted on task 1 due to task doc authoring error by the planning model

## Result

Task 1 (Settings) failed. Run halted. 0 tasks completed.

## Root Cause

The implementation plan's Interface Contract for `AirflowIngestionSettings` used **comments** instead of **actual Python default values**:

```python
# Plan's Interface Contract (WRONG)
google_drive_file_name: str          # default: "Health Connect.zip"
minio_bucket: str                    # default: "health-data"
rabbitmq_port: int                   # default: 5672
```

The scaffold stub correctly had `= "Health Connect.zip"` etc., and tests validated against the stub. But the **task doc's Interface Contract** was generated from the plan, not the stub.

Qwen read the task doc, saw the comment-only format, and "corrected" the stub — **removing** the actual defaults and replacing them with comments. The diff shows:

```diff
-    google_drive_file_name: str = "Health Connect.zip"
+    google_drive_file_name: str          # default: "Health Connect.zip"
```

This caused `test_defaults_applied` to fail with 5 `ValidationError: Field required` errors. Qwen exhausted reflections trying to understand the test failure (the error didn't mention defaults — it said "Field required").

Additionally, Qwen's reflections were confused — it generated responses about "making greetings more casual" and JavaScript code, indicating context confusion or prompt leakage from training data.

## Why This Happened

The code-grounding rule (Chat 8) said to ground **Behavior sections** in code, not plan prose. But it didn't cover **Interface Contract code blocks**. The planning model generated the Interface Contract from the plan's interface block (comments-as-defaults) instead of from the validated stub (actual defaults).

The plan-format.md "Include" list mentioned "class-level constants or attributes" but didn't say "actual default values as code."

## Skill Fix Applied

**SKILL.md Step 5**: Extended grounding rule to cover Interface Contracts AND Behavior sections. New explicit rule: "Interface Contract code blocks must be copied from the stub, not the plan." With specific wrong-vs-right example.

**plan-format.md**: Added to the "Include" list: "Actual default values as code — write `field: str = "value"`, not `field: str  # default: "value"`. The small model copies the code block literally; comments about defaults are not defaults."

## Outcome

Not a valid trial. Results reflect a planning model authoring error, not Qwen's implementation ability.
