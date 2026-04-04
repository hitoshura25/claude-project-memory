# T05 — Re-Decomposed Pipeline, verify_task Stub Gap

| Field | Value |
|-------|-------|
| **Date** | 2026-04-04 |
| **Skill** | prototype-driven-implementation |
| **Executors** | Claude CLI (test/scaffold), Aider+Qwen (implementation) |
| **Escalation** | 3-tier configured but never reached |
| **Test project** | health-data-ai-platform / airflow-google-drive-ingestion |
| **Result** | ❌ Stalled at task-02 — verify_task rejected valid test task |

---

## Setup

- 21 tasks (re-decomposed with updated task sizing — parser split into
  vital_signs_parser and activity_parser)
- Claude CLI for test and scaffold tasks
- Aider + Qwen 3 Coder for implementation tasks
- All Run 4 fixes applied: Step 1b model research, test file inclusion,
  task sizing rules

## Results

- **Tasks attempted:** 2 (task-01 scaffold, task-02 settings tests × 4 retries)
- **Tasks skipped:** 1 (task-03, depends on task-02)
- **Tasks not reached:** 18
- **Duration:** ~5 minutes

### Task-01 (Scaffold) — ✅ Passed

Claude CLI created the full scaffold: pyproject.toml with pinned deps,
conftest.py with airflow sys.modules patching and db_path fixture, all
package init files. Bootstrap ran `uv sync --dev` successfully.

### Task-02 (Write Settings Tests) — ❌ Failed (4 attempts)

Claude CLI wrote a good test file (12 well-structured tests using
monkeypatch.setenv, proper ValidationError assertions, correct env var
prefix mapping). However:

1. The test file imports `from config.settings import Settings`
2. `config/settings.py` doesn't exist yet (task-03 creates it)
3. pytest hits `ModuleNotFoundError` when collecting tests
4. `verify_task` treated this as a "collection error" and marked the task failed

On retry 2, Claude attempted a fixture-based approach (`from config.settings
import Settings as _Settings` inside a fixture) — same ModuleNotFoundError.

All 4 run logs show Claude CLI invoked but producing empty output on retries
1-3, suggesting Claude had nothing meaningful to change.

### Claude CLI Empty Output

All 4 retry logs contained only the command header with no executor output:
```
[claude] Command: claude -p --dangerously-skip-permissions
[claude] CWD: /Users/vinayakmenon/health-data-ai-platform/services/airflow-ingestion
```

This may indicate Claude CLI returning empty when there are no changes to make,
or a subprocess capture issue. Worth investigating separately.

## Root Cause

**verify_task's test-task logic conflicted with the TDD contract.** The
decomposition skill's acceptance criteria say "tests fail because config/settings.py
does not exist yet" — this is by design. But verify_task treated any
`ImportError`/`ModuleNotFoundError` in pytest output as a collection error
and marked the task failed.

The fundamental gap: test tasks had no way to import the module under test
because no stub file existed. The TDD contract assumed test failure from a
missing module is acceptable, but the verification code disagreed.

## Skill Changes Applied

Cross-cutting change across both decomposition and implementation skills:

**Decomposition skill:**
1. `stub: bool` field added to `FileChange` in `task_schema.py`
2. Test tasks now create stub files (interface-only, `NotImplementedError`
   bodies) alongside test files — ensures tests can import the module
3. Implementation tasks use `operation: modify` for stubbed files
4. `validate_stub_on_test_tasks_only` validator: only test tasks create stubs
5. `validate_stub_to_modify` validator: impl tasks must `modify` not `create`
   files that were stubbed
6. Updated `task-writing-guide.md` TDD section with stub rules and examples
7. Updated acceptance criteria: "tests fail with NotImplementedError" not
   "tests fail because module doesn't exist"

**Implementation skill:**
1. Updated `verify_task` logic in `phase-2-generation.md`:
   - `NotImplementedError` in output → pass (stubs working)
   - Collection error → fail (stub missing or malformed)
   - All tests pass → fail (stub has real logic, violating TDD separation)
2. Added stub-writing rules to test-task prompt composition
3. Updated test-writing rules: tests fail with NotImplementedError, not ImportError

## Key Learnings

- The TDD contract must be enforced consistently across decomposition (what
  tasks produce) and implementation (how tasks are verified)
- Missing stubs are not a verification problem — they're a decomposition
  problem. Fix at the source.
- Test tasks are the right place to create stubs because they have the most
  context about what interfaces the tests need
- Stub correctness (interface-only, no logic) can be enforced structurally
  via the `stub` field and at verification time (all tests pass → stub has
  real logic → fail)
- Language-agnostic design: stubs use the ecosystem's "not implemented"
  pattern (Python: `raise NotImplementedError`, JS/TS: `throw new Error`,
  Go: `panic`, etc.)
