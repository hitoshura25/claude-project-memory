# T10–T13 — Prompt & Spec Tightening Arc

> Four runs on the same 19-task decomposition (airflow-google-drive-ingestion),
> between 2026-04-16 and 2026-04-17. Consolidated into a single arc because
> the trials share a common storyline: shrinking the prompt and tightening the
> task spec until test-writing quality is reliably solved.

---

## T10 — 2026-04-16 — Post-templating-refactor validation

**Decomposition:** 19 tasks.
**Outcome:** 4 passed + 1 degraded + 2 failed + 12 not_run.
**Executors:** Aider+Qwen → Gemini Flash → Claude Sonnet (all tiers active).

### Context entering T10

Post-T09 skill changes: stub mock-import rule added, pipeline templates
refactor complete, `EXECUTOR_TIMEOUT` = 300s, `MAX_RETRIES_PER_TASK` = 1,
bootstrap merged into scaffold verification.

### What worked

Scaffold verification caught Gemini's broken `pyproject.toml` at task-01 and
correctly escalated to Claude, who fixed it. Timeout held at 300s. No I001
lint loops. No memory-driven config drift.

### Failure mode A — split-module test file (task-07)

Parser decomposed into two tasks that both touch `tests/test_parser.py`:

- task-06 (test task for parser infrastructure — `_parse_zip`, header parsing)
- task-07 (infrastructure impl) — writes production code for parts of parser
- task-08 (extractor impl) — writes production code for remaining parser functions

The test file has cases exercising BOTH what task-07 implements AND what
task-08 implements. The test gate runs the whole file, so task-07 can never
pass — tests call `_parse_blood_glucose` etc. which it's forbidden to
implement (belongs to task-08).

All 6 attempts failed with the same error: tests from the task-08 slice of
functionality trying to exercise unimplemented code in task-07.

### Failure mode B — mock path inconsistency (task-05)

Gemini-written tests for `drive_downloader` had two different mock target
paths in the same file:

- Some tests patched `plugins.drive_downloader.service_account.Credentials`
- Others patched `plugins.drive_downloader.Credentials` directly

Claude's test-task attempt dutifully exposed BOTH import styles in the stub
to satisfy both tests. But task-05 (the implementation task) could only
import one style — whichever it chose, roughly half the tests failed.

### Key finding

**Test-writing quality is coherence work**, not generation work. Coherence
across mocked imports, fixture paths, and assertion specifics requires
maintaining a consistent mental model across dozens of test cases.
Gemini Flash produces tests that individually look correct but collectively
drift.

---

## T11 — 2026-04-16 — Gemini version upgrade

**Decomposition:** same 19 tasks.
**Outcome:** 5 passed + 1 degraded + rest not_run. Similar shape to T10.
**Change from T10:** Gemini CLI updated (newer version).

### What changed

Gemini's intra-file consistency improved noticeably. The mock-inconsistency
class of bug (T10 task-05) disappeared — Gemini kept mock paths consistent
within a single test file.

### What didn't change

- task-07 split-file bug identical to T10
- New failure class surfaced: Gemini writes tests that **pass instead of
  failing with NotImplementedError** (e.g., tests that use defensive default
  values, so Pydantic-style field declarations return placeholders rather
  than raising). verify_task's stub-pattern check flagged these as wrong
  (correctly — a test that passes against a stub means the stub leaked
  real logic, or the test isn't actually testing the stubbed behavior).

### Key finding

**A newer-model tier upgrade fixes some failure modes and exposes others.**
Gemini fixed cross-test consistency but introduced "over-defensive tests"
that pass when they should fail — revealing that the decomposition skill
wasn't explicit enough about what `NotImplementedError`-in-output means
as a contract.

---

## T12 — 2026-04-16 — Claude-as-test-writer experiment

**Decomposition:** same 19 tasks.
**Outcome:** Worst run of the arc. 1 passed + 1 degraded, died early.
**Change:** Gemini's test-writing role swapped for Claude Sonnet on tier 0.

### Context

With T10/T11 failures pointing to test-writing as a coherence problem, we
tried the most capable model available on the test-task tier to see if
raw capability alone solved it.

### task-02 failure — verify_task rigidity

Task-02 spec: "create stub Settings class" where Settings is a
pydantic-settings BaseSettings. Spec said to include field declarations
(real) and a `validate_required_fields()` method that raises
`NotImplementedError`.

Claude produced exactly what was asked: working Pydantic fields + one
stubbed method. Tests ran: the field-loading tests passed, the stubbed-method
test raised `NotImplementedError`.

But: `verify_task`'s test-task logic had a single hardcoded check —
**"does `STUB_ERROR_PATTERN` appear in the test output?"**. Because pytest's
`-x` flag stopped at the first failing test, and the field-loading tests
ran first (and passed), `NotImplementedError` never reached the verify
output. `verify_task` rejected a correct result.

### Claude retry-1 correctly diagnosed but couldn't proceed

Retry prompt told Claude "test failed verification, fix it." Claude read
the files, said "tests pass and files look correct, no changes needed."
Claude was right. Pipeline had no way to accept that diagnosis.

### Key finding

**Partial stubs are a real category the pipeline doesn't model.** A
component like `Settings` has:

- Declarative parts (Pydantic field declarations — not method bodies, can't
  be "stubbed")
- One or two stubbed methods with `NotImplementedError`

The hardcoded "stub error must appear in output" check works for pure stubs
but rejects partial stubs when test ordering hides the raise. This is a
pipeline-level gap that a schema field (`expected_test_failure_modes`)
would close — not a prompting problem.

### What T12 also validated

Even with Claude as the test writer, test over-specification still happened
in places. Capability alone does not fix structural gaps in the spec.

---

## T13 — 2026-04-17 — Tight prompt + tight task-02 spec

**Decomposition:** same 19 tasks, but task-02 hand-rewritten to a tight
template (Component / Component type / Interface / Behaviors / Expected
test failure mode / Out of scope).
**Outcome:** 4 passed + 1 degraded + 2 failed + 1 skipped + 11 not_run.
**Changes from T11:**

1. `_PROJECT_CONTEXT` in `compose_prompt.py` replaced with tight system
   prompt: Role + Project + Test writing rules + Stub writing rules +
   Coding conventions + Output format. Removed all project-specific
   prototype insights from the universal prompt (blood glucose math, HR
   joins, fastavro, etc. — only relevant to specific tasks, shouldn't be
   in every task's prompt).
2. Removed duplicate `_STUB_RULES` and `_TEST_RULES` constants (were
   redundant with the new system prompt).
3. System prompt placed at top with `---` separator (not embedded under a
   `## Project Context` subheading).
4. `_inline_dependencies` filtered to Python-importable files only
   (`.py`, `.toml`, `.cfg`, `.ini`) — skips `.avsc`, `.yml`, `.yaml`,
   `.json`, Dockerfiles, compose files.
5. task-02 JSON entry rewritten to tight prose format.

### Results — test tasks

**All three test tasks (02, 04, 06) passed Gemini tier 0 retry 0.**

This is the biggest improvement the arc produced. In T10/T11 these tasks
needed multiple retries or escalation. In T13 each passed on the first
Gemini attempt.

Notable: task-04 and task-06 were not hand-rewritten to the tight format.
Their JSON entries are the same verbose versions as T11. They passed
because of the system-prompt tightening alone, not the per-task spec
tightening. This tells us the system-prompt content was the larger source
of confusion; fixing that alone made the verbose per-task content workable.

### task-02 degraded (lint file-not-found glitch)

task-02 went `degraded` not `passed`, but the test gate passed cleanly.
The lint step briefly couldn't find the target files (E902 "no such file or
directory") because task-01's Claude escalation had concurrently replaced
files and task-02's Gemini attempt (which hit a 429 rate limit) raced the
filesystem. Transient. The task's actual output was correct.

### Remaining failures — different failure class

task-05 and task-07 exhausted all three executor tiers.

**task-05 — test over-specification.** Gemini-written test asserted
implementation calls with `pageSize=10` and `fields="files(id, name, size)"`.
Neither value appears in the task spec. Every implementation attempt had
to guess these exact literals and couldn't. The tests constrained the
implementation beyond what the task description specified.

**task-07 — fixture path bug.** `conftest.py`'s `SAMPLE_ZIP` fixture used
`Path(__file__).parents[3] / 'docs' / 'sample-data'` which resolves to a
non-existent path under the current project layout. Gemini moved the
fixture without recomputing the parent depth.

Neither failure is about prompt contradictions or irrelevant context. Both
are test-quality issues — the tests themselves are wrong in ways that no
downstream implementation can satisfy.

### Prompt size reduction

task-02 prompt went from ~11,500 characters in T12 to 5,099 characters in
T13 — a ~55% reduction. Content removed: prototype insights unrelated to
Settings, duplicate stub/test rules, embedded `## Project Context`
subheading noise.

### Key findings

1. **System-prompt bloat is a larger source of confusion than per-task
   bloat.** Tightening the system prompt alone made verbose per-task
   content workable. This is the most actionable finding for the
   decomposition and implementation skill refactors.

2. **Tight task-doc templates with fixed fields beat freeform prose.**
   The rewritten task-02 had zero internal contradictions; Gemini produced
   correct code on the first try. Freeform prose, even when detailed, leaves
   room for the same contradictions that plagued T10/T11.

3. **Test over-specification is a distinct failure class.** It's not fixed
   by the same interventions that fix under-specification (which is what
   T10/T11/T12 failures were). Over-specification needs explicit guardrails
   on what tests may assert — or a post-test-writing verifier that checks
   tests don't prescribe details absent from the spec.

4. **Partial-stub components need a structural fix, not more prose.**
   `verify_task`'s hardcoded single-pattern check can't distinguish correct
   partial stubs (T12 task-02) from leaked-logic stubs (T11 stubs-pass
   class). A schema field `expected_test_failure_modes` driving the check
   would close the gap.

---

## Summary — what the arc produced

**Validated:**
- Tight system prompts reduce test-task failure rates dramatically (Gemini
  went from multi-retry-or-escalation to first-attempt success on three
  test tasks)
- Tight task-doc templates with fixed fields work — task-02 tight rewrite
  eliminated all prompt contradictions
- Filtered dependency inlining removes noise (Avro schemas, compose YAML
  no longer injected into every prompt)
- Duplicate rule blocks in compose_prompt.py can be cut without loss

**Remaining failure classes to address:**
- Test over-specification (task-05 class) — tests prescribe details absent
  from spec, blocking any implementation
- Fixture path grounding (task-07 class) — tests reference paths that
  don't resolve in the layout
- Partial-stub verification (T12 task-02 class) — pipeline needs
  `expected_test_failure_modes` schema field

**Skill refactor targets** (see `refactor-plan-2026-04-17.md`):
- Decomposition skill: stop emitting `.md` files, emit JSON only
- Implementation skill (pipeline gen): render `.md` views from JSON
- Tight task-doc template specification in the decomposition skill
- Bake `compose_prompt.py` changes into implementation skill templates
- Add `expected_test_failure_modes` schema field + wire into `verify_task`
