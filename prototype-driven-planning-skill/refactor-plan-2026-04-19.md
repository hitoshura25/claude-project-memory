# Refactor Plan — Required `test_command` Schema Field

> **Date:** 2026-04-19
> **Driver:** T14 post-mortem. 16/17 passed; task-16 (integration test) failed
> because the Docker-compose-wrapped test command was embedded in the task
> description prose but never made it into `TASK_TEST_COMMANDS`. The plain
> `uv run pytest tests/test_integration.py -x` was used instead, and the
> tests fixture-failed because Docker services were never started.
> **Criterion:** Promote fields to the schema only when the pipeline
> mechanically uses them and their absence has caused a real bug.

---

## 1. The bug in one paragraph

The decomposer wrote the correct Docker-wrapped test command into task-16's
`description` field. The Phase 2 pipeline generator populates `config.py`'s
`TASK_TEST_COMMANDS` dict from "per-task test command derivation" — but that
derivation ignores the task description's prose and just uses a generic
`<test-runner> <test-file> -x` pattern. The wrapped command never reached the
pipeline. Tests ran without Docker services; fixture setup hard-failed by
design; task-16 failed all 4 attempts despite Claude correctly diagnosing
the cause on T1-R1 ("the tests must hard-fail, not skip — no changes needed").

Structural issue: free-form prose is a lossy transport between decomposer
and generator. The generator has no way to know when a task has a
non-default test command and no field to read it from if it did.

## 2. What's changing and why

### 2.1 Schema: add required `test_command: str` to `Task`

Every task specifies the exact command that verifies its output beyond lint.
No defaults, no `None`. Scaffold tasks included.

```python
test_command: str = Field(
    description="Shell command the pipeline runs as the test gate for "
                "this task. For test tasks: runs the tests (expected to "
                "fail with stub errors from expected_test_failure_modes). "
                "For implementation tasks with paired tests: runs those "
                "tests. For wiring tasks: a syntax/semantic check (e.g., "
                "python -c 'import ast; ast.parse(...)'). For infra "
                "tasks: a build/config check (e.g., docker build, docker "
                "compose config). For scaffold tasks: the test runner "
                "accepting 'no tests collected' as success (e.g., "
                "'uv run pytest tests/ -x || [ $? -eq 5 ]'). "
                "Integration/e2e tests wrap the test runner with service "
                "lifecycle (docker compose up --wait / down)."
)

@model_validator(mode="after")
def validate_test_command_non_empty(self) -> "Task":
    """Every task must have a non-empty test_command. Lint alone is
    insufficient — syntactically valid but functionally broken code
    passes lint (known failure class from T07 integration tests and
    T09 task-15 wiring)."""
    if not self.test_command or not self.test_command.strip():
        raise ValueError(
            f"Task '{self.id}' has empty test_command. Every task must "
            f"specify how its output is verified beyond lint. See "
            f"task-writing-guide.md § 'Task test_command' for patterns "
            f"by task type."
        )
    return self
```

Plus a light integration-lifecycle heuristic:

```python
@model_validator(mode="after")
def validate_integration_test_lifecycle(self) -> "Task":
    """Integration/e2e test tasks whose descriptions reference external
    services should wrap the test runner in a service lifecycle.
    Heuristic check; false negatives favored over false positives."""
    if self.task_type != TaskType.TEST:
        return self
    has_int_or_e2e = any(
        t.test_type in ("integration", "e2e") for t in self.tests
    )
    if not has_int_or_e2e:
        return self

    desc_lower = self.description.lower()
    needs_lifecycle = (
        "docker" in desc_lower
        or "compose" in desc_lower
        or "container" in desc_lower
    )
    cmd_lower = self.test_command.lower()
    has_lifecycle = (
        ("up" in cmd_lower and "down" in cmd_lower)
        or "testcontainers" in cmd_lower
    )
    if needs_lifecycle and not has_lifecycle:
        raise ValueError(
            f"Test task '{self.id}' has integration/e2e tests and its "
            f"description references external services, but "
            f"test_command does not wrap a service lifecycle (expected "
            f"'up' and 'down' verbs, or 'testcontainers'). See "
            f"task-writing-guide.md § 'Integration test_command "
            f"pattern'."
        )
    return self
```

### 2.2 `task-writing-guide.md` additions

New major section: **Task `test_command`**.

Subsections:

1. **Why every task needs one.** Lint gates don't catch functional bugs.
   Every task has *something* to verify; if it's not tests, it's a syntax
   check or build check. This was the silent failure mode in T07 (DAG
   wiring passed lint with broken signatures) and T14 (integration test
   ran without services).

2. **Pattern by task-type × phase × language.** A lookup table:

   | Task kind | Python | TypeScript | Go |
   |---|---|---|---|
   | scaffold | `uv run pytest tests/ -x \|\| [ $? -eq 5 ]` | `npx jest --passWithNoTests` | `go test ./... (noop if no tests)` |
   | test (unit) | `uv run pytest <test-file> -x` | `npx jest <test-file>` | `go test <package>` |
   | test (integration) | lifecycle wrapper around pytest | lifecycle wrapper around jest | lifecycle wrapper around go test |
   | impl (with paired tests) | same as paired test task | same as paired test task | same as paired test task |
   | impl (wiring) | `python -c 'import ast; ast.parse(open("<file>").read())'` | `npx tsc --noEmit <file>` | `go build <package>` |
   | impl (infra: Dockerfile) | `docker build -f <Dockerfile> -t <image>-test .` | same | same |
   | impl (infra: compose only) | `docker compose -f <file> config` | same | same |

3. **Canonical integration-test lifecycle pattern.** The wrapped shell
   idiom with its five rules:
   - `up` must block until healthy (`--wait` on Docker Compose v2)
   - `&&` between up and test-runner (short-circuit)
   - `;` between test-runner and down (teardown always runs)
   - `rc=$?` before teardown; `exit $rc` at end
   - `-v` and `--remove-orphans` on down (prevent state leak)

   Example block (pattern, not prescriptive):
   ```
   <service-up-cmd> \
     && <test-runner-cmd>; \
     rc=$?; <service-down-cmd>; \
     exit $rc
   ```

4. **How `test_command` relates to `expected_test_failure_modes`.** The
   command runs the test; the `expected_test_failure_modes` field tells
   the pipeline what successful-stub output looks like. They work
   together for test tasks.

### 2.3 `output-format.md` updates

- Add `test_command` to the structure example for each example task.
- Add validation checklist item: "Every task has a non-empty `test_command`."
- Update the summary table columns to include `test_command` (abbreviated —
  just enough for the reviewer to see when it's non-default).

### 2.4 `task_schema.py`

See 2.1. Add the field, its validator, and the integration-lifecycle
validator.

### 2.5 `phase-2-generation.md` updates

Clarify `TASK_TEST_COMMANDS` generation:

- **Source:** `task.test_command` verbatim. No derivation, no fallback,
  no defaults. If the schema validated, the field is present and
  non-empty.
- **Population:** for each task T in `tasks.json`, set
  `TASK_TEST_COMMANDS[T.id] = T.test_command`.

Remove the old vague guidance ("from Phase 1 per-task test command
derivation").

Drop `None` as a valid value for any task. Update config template comments.

### 2.6 `config.py.template` and `_run_scaffold_bootstrap`

- `TASK_TEST_COMMANDS: dict[str, str]` (no more `| None`).
- `_run_scaffold_bootstrap` keeps bootstrap-run + lint-tool-check.
  Drops the test-runner-availability check (`pytest --co -q || true`) —
  scaffold's test-runner check now happens via the normal test-gate path
  with the scaffold's real `test_command`. One fewer mechanism.

### 2.7 `verify_task.py`

**Scaffold branch:** after `_run_scaffold_bootstrap` succeeds (bootstrap +
lint-tool), run the scaffold's `test_command` like any other task's test
gate. If the command succeeds (exit 0), scaffold task passes. If it fails,
scaffold fails.

Critical detail: scaffold's test_command for Python is
`uv run pytest tests/ -x || [ $? -eq 5 ]`. Exit code 5 means "no tests
collected." The `|| [ $? -eq 5 ]` suffix makes that exit 0. If conftest
has a syntax error or the test dir structure is broken, pytest returns
a different non-zero exit and the scaffold fails.

**Non-scaffold branch:** unchanged (already runs `test_cmd` from
`TASK_TEST_COMMANDS`).

## 3. What's NOT changing

- `INTEGRATION_TEST_TASK_IDS` stays. Separate semantic (verification-
  mode selection: "tests must pass" vs. "tests must fail with expected
  stub error"). Still populated from Phase 1 detection.
- `GLOBAL_TEST_CMD` stays. Not used in normal per-task flow but kept
  for manual runs.
- Task template in `task-writing-guide.md` (Component / Component type /
  etc.) stays. Only addition: guidance to populate the schema field
  alongside the prose.
- Pipeline templates beyond `verify_task.py` and `config.py.template`
  are untouched.
- `expected_test_failure_modes` already exists and works.

## 4. Migration / validation plan

**Step 1: Plan file (this document). Done.**

**Step 2: Decomposition skill updates.**

- `scripts/task_schema.py`: add `test_command` field + two validators.
- `references/task-writing-guide.md`: add "Task `test_command`" section.
- `references/output-format.md`: update example tasks and validation checklist.
- `SKILL.md`: mention `test_command` in schema reference table and in
  Phase 2 generation bullets.

Validate: regenerate `tasks/airflow-google-drive-ingestion/tasks.json`.
Check every task has non-empty `test_command`; task-16's includes the
Docker-compose lifecycle wrapper; scaffold task-01's is the
`pytest ... || [ $? -eq 5 ]` form.

**Step 3: Implementation skill updates.**

- `templates/config.py.template`: `TASK_TEST_COMMANDS` type annotation
  drops `| None`; `_validate_docker_if_needed` comment updated.
- `templates/nodes/verify_task.py`: scaffold branch extended to run
  `test_command` after bootstrap. Drop the pytest-availability check
  from `_run_scaffold_bootstrap`.
- `references/phase-2-generation.md`: `TASK_TEST_COMMANDS` now verbatim
  from `task.test_command`.
- `SKILL.md`: Phase 1 no longer mentions "derive per-task test commands"
  (the decomposer owns this); Phase 2 mentions direct copy from schema
  field.

Validate: regenerate pipeline for airflow-google-drive-ingestion.
`pipelines/airflow-google-drive-ingestion/config.py` should show:
- task-01: scaffold pytest with exit-5 acceptance
- task-16: Docker-compose-wrapped command
- every other task: the plain pytest command from their description

**Step 4: T15 pipeline run.**

Full run. Acceptance bar: match T14's 16/17, plus task-16 passing
(services started, tests pass). task-15 and task-17 test_commands should
now exercise the acceptance-criterion commands (ast.parse + docker build)
and pass.

**Step 5: Commit.** User runs `git add -A && git commit && git push` in
both repos.

## 5. Out of scope

- Rewriting `INTEGRATION_TEST_TASK_IDS` to derive from
  `test_type in ("integration", "e2e")`. Possible future cleanup;
  independent from this refactor.
- Changing `expected_test_failure_modes` semantic. Works as-is.
- Task over-specification guardrails (T13 task-05 class). Separate
  refactor.

## 6. Open questions — resolved

- **Field naming: `test_command` vs. `verify_command`.** Decided:
  `test_command`. Already the terminology in LEARNINGS.md and existing
  config; no rename value.
- **Scaffold task exception vs. universal field.** Decided: universal
  field; scaffold populates with the exit-5-tolerant pytest command.
  Catches broken conftest/fixture setup as a bonus; no special-casing
  in the schema.
- **Docker lifecycle: template file vs. documented pattern.** Decided:
  documented pattern in task-writing-guide.md, not a separate script
  file. Script files would create a second artifact to sync; pattern
  keeps single source of truth in `tasks.json`.
- **Integration-lifecycle validator.** Decided: include it. Light
  heuristic (description mentions docker/compose/container AND test_type
  is integration/e2e AND command lacks "up"/"down" or "testcontainers")
  → raise. False-negative prone by design.

## 7. Summary

One schema field. One pipeline-template tweak to verify_task. One
reference-doc section. Validators catch the T14 failure class at
decomposition time. Scaffold tasks get a real test-infrastructure
check for free.

Net-reductive on ambiguity, minimal additions to the schema.
