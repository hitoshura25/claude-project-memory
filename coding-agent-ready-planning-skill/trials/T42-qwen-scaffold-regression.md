# T42 — Qwen 30B: Scaffold Infrastructure Regression (INVALID)

**Date**: 2026-03-22
**Model**: Qwen 3 Coder 30B (Q4, 32k context)
**Log**: `run-20260322-230345.log`
**Chat**: 9
**Verdict**: INVALID — 11/11 tasks degraded due to scaffold infrastructure failures, not model performance

## Result

11⚠️ (all degraded — reflections exhausted on every task)

Run halted after task 11 with all tasks degraded.

## Root Causes (all scaffold/infrastructure, not model)

### 1. Lint script not executable + missing `./` prefix

Manifest had `"lint_cmd": "docs/plans/airflow-google-drive-ingestion-tasks/lint.sh"` (missing `./`). Shell couldn't find the script. Every task hit:

```
/bin/sh: docs/plans/airflow-google-drive-ingestion-tasks/lint.sh: No such file or directory
```

Qwen saw the lint error, couldn't fix it (infrastructure issue), and wasted all reflections.

### 2. pytest not installed — `uv sync` never ran

Independent verification failed with:

```
Using CPython 3.11.14
Creating virtual environment at: .venv
warning: No `requires-python` value found in the workspace. Defaulting to `>=3.11`.
error: Failed to spawn: `pytest`
  Caused by: No such file or directory (os error 2)
```

The scaffold step didn't run `uv sync` from the service root, so `.venv` didn't exist and pytest wasn't installed.

## Skill Fix Applied

**SKILL.md Step 3**: Replaced the single vague sentence "After setup, verify both lint and test commands pass" with a 5-step scaffold verification checklist:
1. `uv sync` + verify pytest installed
2. `chmod +x` on lint scripts
3. Verify lint works from project root (with `./` prefix)
4. Verify test command finds pytest
5. Verify manifest paths match

**SKILL.md Step 6**: Fixed infra lint manifest example — was `"docs/plans/my-tasks/infra-lint.sh"`, corrected to `"./docs/plans/my-tasks/infra-lint.sh"`.

## Outcome

Not a valid trial. Results do not reflect model performance.
