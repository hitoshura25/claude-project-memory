# T14 — Tight Task-Doc Refactor Validated; Integration-Test Command Gap Exposed

**Date**: 2026-04-19
**Skill**: implementation
**Executors**: Aider+Qwen (local) → Gemini 2.5 Flash → Claude Sonnet 4.6
**Result**: ⚠️ 16/17 passed — task-16 failed all 4 attempts
**Log**: `~/health-data-ai-platform/pipelines/airflow-google-drive-ingestion/logs/runs/run-20260419_111117.log`

---

## Configuration

- **Executor chain** (implementation role): Aider+Qwen3 Coder 30B (local via
  LM Studio) → Gemini 2.5 Flash → Claude Sonnet 4.6
- **Executor chain** (test/scaffold roles): Gemini 2.5 Flash → Claude Sonnet 4.6
- **EXECUTOR_TIMEOUT**: 300 (held stable via templated pipeline)
- **MAX_RETRIES_PER_TASK**: 1 (held)
- **Task count**: 17 (re-decomposed with tight task-doc template)
- **Baseline**: T13 was 5/19 on the prior decomposition; T14 uses a new
  17-task decomposition with the full T13-refactor-plan applied
  (tight task-doc, JSON-only output, `expected_test_failure_modes`
  schema field, `compose_prompt.py.template` changes)

## Task Execution Summary

```
task-01    passed  scaffold        gemini(t0r0) → gemini(t0r1) → claude(t1r0)   3 attempts
task-02    passed  test            gemini(t0r0)                                  1 attempt
task-03    passed  implementation  aider→aider→gemini→gemini→claude              5 attempts
task-04    passed  test            gemini→gemini→claude                          3 attempts
task-05    passed  test            aider→aider→gemini                            3 attempts
task-06    passed  test            gemini→gemini→claude                          3 attempts
task-07    passed  implementation  aider→aider→gemini→gemini→claude→claude       6 attempts
task-08    passed  implementation  aider(t0r0)                                   1 attempt
task-09    passed  test            gemini→gemini→claude                          3 attempts
task-10    passed  implementation  aider→aider→gemini                            3 attempts
task-11    passed  test            gemini(t0r0)                                  1 attempt
task-12    passed  implementation  aider→aider→gemini                            3 attempts
task-13    passed  test            gemini→gemini                                 2 attempts
task-14    passed  implementation  aider→aider→gemini→gemini                     4 attempts
task-15    passed  implementation  aider→aider→gemini                            3 attempts
task-16    FAILED  integration     gemini→gemini→claude→claude  (4 tiers exhausted)
task-17    passed  implementation  gemini→gemini→claude                          3 attempts
```

## What Worked (T13 Refactor Validation)

- **Tight task-doc template held.** Every task.description in the
  regenerated `tasks.json` followed the Component / Component type /
  Interface / Behaviors / Expected test failure mode / Out of scope
  structure. No internal contradictions observed.
- **task-05 and task-07 passed.** These were T13's explicitly-deferred
  failures (test over-specification and fixture path bugs). The tight
  template + recomposition + T13 system-prompt tightening together
  resolved both without targeted intervention. This was unexpected —
  the refactor plan said they were out of scope — but a pleasant
  result.
- **`expected_test_failure_modes` wired correctly.** All 6 test tasks
  (task-02/04/05/06/09/11/13/16) populated the field per schema
  requirement; `verify_task` read it directly with no project-wide
  fallback. No partial-stub false-rejection observed like T12.
- **Gemini tier-0 success rate for test tasks:** task-02, task-04,
  task-05, task-06, task-09, task-11, task-13 all reached "passed" on
  Gemini. task-16 reached Claude before failing for infrastructural
  reasons (see below).
- **Aider tier-0 success:** task-08 (simple implementation) passed on
  first attempt. Most other implementation tasks needed escalation.
- **Template stability:** `EXECUTOR_TIMEOUT = 300` held (no drift from
  prior run memory — this was the point of the templating refactor).
  No lint loops from I001/F401 (AIDER_LINT_CMD fix held).

## The Single Failure: Task-16

Task-16 is the integration test task. It had clean intent:

- `task_type: "test"`, `phase: "testing"`
- `tests[]` entries all have `test_type: "integration"`
- `expected_test_failure_modes: ["Exception"]` (pytest.fail raises
  `_pytest.outcomes.Failed`, subclass of Exception)
- `depends_on: [task-01, task-12, task-14]` (scaffold + minio + rabbitmq)

The task description specified the complete Docker-compose-wrapped test
command:

```
docker compose -f services/airflow-ingestion/deployment/services.compose.yml \
  up -d --wait --wait-timeout 120 \
  && uv run pytest services/airflow-ingestion/tests/test_integration.py -x; \
  rc=$?; docker compose -f services/airflow-ingestion/deployment/services.compose.yml \
  down -v --remove-orphans; \
  exit $rc
```

But the generated `pipelines/airflow-google-drive-ingestion/config.py`
contained:

```python
TASK_TEST_COMMANDS: dict[str, str | None] = {
    ...
    "task-16": "uv run pytest tests/test_integration.py -x",
    ...
}
INTEGRATION_TEST_TASK_IDS: set[str] = {"task-16"}
```

Plain pytest, no Docker lifecycle.

### Attempt breakdown

- **Gemini t0 r0**: Wrote the test file, but the first output wrapped it
  in a `write_file:` markdown block instead of performing a real file
  write. `ruff check` → E902 no such file. stderr showed Gemini's own
  sandbox environment was corrupting paths (`Error stating path
  localhost:5672"`, `ENAMETOOLONG`). Verify_task: lint fail, test fail
  (file didn't exist).
- **Gemini t0 r1**: Created the file this time, but imported `minio`
  SDK instead of `boto3` (contrary to the service's dependency choice),
  and had an unused `result = ` variable (F841). Some Gemini internal
  exception ("Error when talking to Gemini API", SSL/TLS bad_record_mac)
  during a middle step — Gemini recovered. Verify_task: lint fail
  (F841), test fail (import error).
- **Claude t1 r0**: Diagnosed and fixed the two issues cleanly — swapped
  `minio` for `boto3`, removed the unused variable, added
  `sys.modules.pop("pika", None)` before third-party imports so the
  conftest mock of pika doesn't affect the integration test. Lint
  passed. Test gate ran. Output: `ERROR at setup of
  test_upload_avro_round_trip` — the `pytest.fail()` in the fixture
  when MinIO is unreachable.
- **Claude t1 r1**: Correctly diagnosed the situation: *"The existing
  `tests/test_integration.py` is correct and lint-clean. The error log
  shows the expected behavior: `pytest.fail()` fires when MinIO is
  unavailable (Docker services not running). This is exactly what the
  spec requires — the tests must hard-fail, not skip. No changes are
  needed."* Made no changes. Test ran again with same "services
  unavailable" failure. Marked failed.

## Root Cause

Not in task-16's implementation. Not in the executors' capabilities.
**In Phase 2 pipeline generation.**

The implementation skill's `phase-2-generation.md` said
`TASK_TEST_COMMANDS — from Phase 1 per-task test command derivation.`
That derivation took the `test_file` from each task's `tests[]` entry
and wrapped it as `<test-runner> <test-file> -x`. It never consulted
the task's description for a more specific command.

The decomposer had written the Docker-wrapped command. It lived in prose
in `task.description`. There was no schema field named `test_command`
for Phase 2 to read it out of. Result: the command was lost in
translation.

### Secondary evidence

- `config.py._validate_docker_if_needed()` scans `TASK_TEST_COMMANDS` for
  `"docker compose"`. It found nothing (because nothing in
  TASK_TEST_COMMANDS contained "docker compose") and passed, so the
  pipeline didn't even warn about Docker not being started.
- `INTEGRATION_TEST_TASK_IDS = {"task-16"}` was set correctly — that
  field's job is to tell `verify_task` to use "tests must pass"
  semantics (not "tests must fail with stub error"). It did its job.
  But that's a verification-mode concern, orthogonal to what command
  runs.

## Decision Tree for the Fix

1. **Where should the truth about a task's test command live?**
   - Option A: in prose (status quo — failed)
   - Option B: parsed from prose in Phase 2 (fragile)
   - Option C: a dedicated schema field (chosen)
2. **Scope — test tasks only, or every task?**
   - Test tasks only leaves wiring tasks (task-15-style DAG files) and
     infrastructure tasks (task-17 Dockerfile+compose) with lint-only
     gates. Those tasks currently pass via lint even when broken.
   - Every task. Scaffold included — the scaffold task creates
     `conftest.py`, `pyproject.toml`'s `[tool.pytest]`, `tests/__init__.py`.
     A broken conftest silently passes the old bootstrap "pytest --co -q
     || true" check but causes every later test task to fail mysteriously.
     Running the test runner with "no tests collected = success" semantics
     catches it early.
3. **Validator strictness?** Non-empty required on every task. Plus a
   light integration-lifecycle heuristic (description mentions
   docker/compose/container AND test_type is integration/e2e AND command
   lacks up/down/testcontainers → raise). The heuristic is deliberately
   false-negative-prone — a task that uses an unusual compose alias
   passes; the validator's job is to catch the obvious mistake, not
   every possible one.

## Refactor Landed Same Day

See `refactor-plan-2026-04-19.md`. Summary:

- **Schema:** `test_command: str` required + two validators.
- **task-writing-guide.md:** new "Task `test_command`" section with
  per-language table and canonical integration lifecycle pattern.
- **output-format.md:** example JSON shows field on all task kinds;
  validation checklist gained item 12.
- **config.py.template:** `TASK_TEST_COMMANDS: dict[str, str]`
  (tightened from `| None`).
- **verify_task.py:** scaffold branch runs the scaffold's own
  `test_command` after bootstrap + lint-tool check. Stale
  `pytest --co -q || true` probe removed.
- **phase-1-analysis.md, phase-2-generation.md, phase-3-handoff.md,
  SKILL.md:** all updated to reflect decomposer-owned test_command
  and verbatim Phase 2 copy.
- **End-to-end validation:** the existing T14 `tasks.json` now fails
  schema validation with `Field required [test_command]` on every task
  — exactly the forced-regeneration signal intended.

## What T15 Must Validate

- Match or exceed T14's 16/17.
- Task-16 passes: Docker-compose-wrapped `test_command` starts services,
  runs tests, tears down. Services reachable during test execution.
- Task-15 and task-17 exercise their real verification commands (not
  lint-only). task-15's `test_command` should be
  `python -c 'import ast; ast.parse(...)'`. task-17's should be
  `docker build -f <Dockerfile> -t airflow-ingestion-test .`.
- Scaffold task-01's `test_command`
  (`uv run pytest tests/ -x || [ $? -eq 5 ]`) runs cleanly against the
  empty scaffold, confirming the test infrastructure is valid before
  any test file exists.

## Side Observations Not Blocking

- **Gemini's sandbox environment occasionally misinterprets prompt
  content as shell paths.** Several task-16 attempts showed stderr
  like `Error stating path localhost:5672"` — the prompt's code blocks
  referencing environment variables were being passed through some
  Gemini-side filesystem tool. This is external; not something the
  skill can fix, but worth tracking.
- **Gemini-Claude hybrid attempts succeed often.** Multiple tasks
  (task-01, task-04, task-06, task-09, task-13, task-17) escalated
  Gemini → Claude and Claude cleaned up things Gemini almost got
  right. The escalation chain is earning its keep.
- **Aider tier-0 is still marginal.** Of 6 implementation tasks where
  Aider had tier-0 access, only task-08 passed on first attempt. Aider
  reaching Gemini and then Claude was the dominant pattern. Worth
  considering whether Aider should be demoted from tier-0 for
  non-trivial implementation tasks on this kind of project.
