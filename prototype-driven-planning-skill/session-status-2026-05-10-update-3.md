# Session Status — 2026-05-10 (update 3)

Picking up from `session-status-2026-05-10-update-2.md`. This update
captures a significant architectural insight that emerged from running
the generated task-01 prompt against three different executors
(Pi+Gemma, Pi+Qwen, Claude Code) and observing a consistent failure
pattern across all of them.

## What this session accomplished

### Validated the prompt-composition skill structural fix works

The skill changes from update 2 (script-as-implementation, no
source/non-source filter, line-anchored preamble matcher, thin SKILL.md
invoker) all hold. Three independent executor runs (Pi+Gemma 27B, Pi+Qwen
30B Coder, Claude Code via Claude Sonnet 4.6) all consumed the
generated prompts cleanly without complaining about format.

### Discovered an architectural problem in the decomposition skill

All three executors hit a consistent failure mode on task-01:
**`tests/conftest.py` was written without the `all_records` fixture
the prompt explicitly required.** Claude Code additionally dropped
`apache-airflow[celery]==2.10.5` from requirements.txt.

The root cause is the same in both cases: the decomposition skill
produces `files[].description` fields that combine two contradictory
instructions in a single bullet:

> "Module-scoped `all_records` fixture calling `extract_all(sample_db_path)`
> once per module. **Mirror prototypes/airflow-gdrive-ingestion/tests/
> conftest.py exactly.**"

The prototype only has `sample_db_path`. "Mirror exactly" and
"include `all_records`" are contradictory. Three different models
with very different capability levels all resolved the contradiction
the same way: drop the explicit requirement, mirror the prototype.

The same pattern fired for requirements.txt:

> "Pinned direct dependencies: apache-airflow[celery]==2.10.5,
> [list]. Copy from prototypes/airflow-gdrive-ingestion/
> requirements.txt."

The prototype omits `apache-airflow[celery]==2.10.5` (it's in the
base image). The prompt asks for it explicitly. Qwen included it
(followed the list); Claude Code dropped it (followed "copy from").
Both readings are defensible.

### The insight the user named

After seeing three executors fail on the same prompt in the same way,
Vinayak observed:

> "The biggest win I see in all of these workflows is the prototype,
> as it actually is supposed to be something working and referenced.
> Everything else after, may be too much planning based on what we've
> seen with never getting a consistently followed code based on the
> plan."

The framing this opened up:

- The roadmap skill's BDD-style scenarios are at the right level — they
  describe observable behaviors grounded in the prototype, not
  implementation strategies.
- The decomposition skill is encoding the *same information* a second
  time in prose form (`task.files[].description` paragraphs that
  re-state what the prototype already shows and what the roadmap
  scenarios already constrain).
- That second encoding is where the contradictions get introduced.
- LLM nondeterminism means we will never get consistent output from
  detailed prose instructions; the only stable reference is the
  prototype itself.

The proposal: rethink the decomposition output to drop or radically
simplify the per-file `description` paragraph. Replace with:

- `intent` (stub | test | implementation) — already implicit in
  `task_type` + `stub` fields
- `prototype_reference` — path to the prototype file the executor
  should base its output on
- (Behavior contract stays in roadmap scenarios, already inlined into
  prompts under `## Behaviors to Verify`)

The LLM gets three non-contradictory sources of truth:
- *What behaviors to verify*: roadmap scenarios in the prompt
- *How to structure the file*: prototype reference (read this file)
- *What kind of file*: intent field

The current `description` paragraph collapses to either empty or a
one-line out-of-scope note (e.g., "magic-bytes guard — covered by
task-06").

## What was tested this session

Three end-to-end runs against `tasks/airflow-gdrive-ingestion/
prompts/task-01.md`:

### Run 1: Pi + Gemma 27B (LMStudio MLX)

- Setup: Pi 0.74.0, LMStudio with Gemma, custom Pi provider extension
  pointing at `http://localhost:1234/v1`.
- Result: Crashed mid-write during `docker-compose.yml` generation.
  LMStudio "Model has crashed without additional information."
  Probably OOM or context-window overflow.
- Diagnosis: Infrastructure failure, not prompt failure. Gemma was
  following the prompt correctly up to the crash.

### Run 2: Pi + Qwen 3 Coder 30B Q4 (LMStudio MLX)

- Setup: same Pi + LMStudio, swapped to Qwen.
- Result: Completed all 9 files. All four acceptance criteria passed
  per Qwen's self-verification (`ruff check` exits 0 via
  `pipx run ruff`, `pytest` exits 5, packages importable).
- Manual content review found:
  - 8 of 9 files correct.
  - `tests/conftest.py` missing `all_records` fixture.
- Diagnosis: Strong signal for prompt format working end-to-end with
  a tier-0 local model. Plus one content gap pointing at a
  decomposition-level ambiguity.

### Run 3: Claude Code (Claude Sonnet 4.6)

- Setup: `claude --dangerously-skip-permissions < task-01.md` from
  project root.
- Result: Completed all 9 files. Acceptance criteria passed via
  prototype's venv (Claude Code discovered
  `prototypes/airflow-gdrive-ingestion/.venv/bin/ruff` after the
  system ruff wasn't available).
- Manual content review found:
  - 7 of 9 files correct.
  - `tests/conftest.py` missing `all_records` fixture (same as Qwen).
  - `requirements.txt` missing `apache-airflow[celery]==2.10.5`
    (regression vs Qwen, but defensible — the prototype omits it
    deliberately since Airflow comes from the base image).
- Diagnosis: A second instance of the "explicit list vs copy from
  prototype" anti-pattern in the same prompt. Two of two strong
  models couldn't resolve it consistently.

### Cross-run conclusion

All three executor runs surface the same category of failure: the
decomposition skill is producing `task.files[].description` text
that contains contradictory instructions, and models resolve the
contradictions inconsistently. The fix is upstream in the
decomposition skill, not in the prompt-composition skill or the
executors.

## Where things stand at the close of this session

### State of skills

- `prototype-driven-planning` — stable, no changes this session.
- `prototype-driven-task-decomposition` — has the anti-pattern
  identified above. No fix made yet.
- `prototype-driven-prompt-composition` — restructured this session
  (script-as-implementation, no extension filter, thin SKILL.md).
  Changes are stable and validated by three executor runs.

### State of test project

`~/health-data-ai-platform/services/airflow-gdrive-ingestion/`
currently contains Claude Code's output from Run 3. Two known
content issues (missing `all_records` fixture, missing
`apache-airflow[celery]==2.10.5`). Whether to clean it up depends on
the next-session decision (see below).

### State of memory repo

`session-status-2026-05-10-update-2.md` documents the
prompt-composition skill refactor and its validation steps. Those
validation steps were partially run (the prompt-composition skill
changes themselves work; the snapshot test was deleted at user
request, replaced by running directly in the test project).

LEARNINGS.md was updated in update 2 with four new entries about
the SKILL.md-as-instructions trap, source/non-source filters as LLM
bait, snapshot tests catching reimplementation drift, and the
Filesystem MCP em-dash quirk.

## Next session: design a scaffolding prompt that Claude executes successfully

The goal of the next session is to take the architectural insight
above and validate it concretely. Specifically:

**Hand-write a task-01 scaffolding prompt that drops the
contradictory prose, leans on the prototype as the source of truth,
and runs through Claude Code with zero content drift from
intent.**

If that prompt works, it becomes the prototype for the redesigned
decomposition output format. If it doesn't, the diagnosis is more
nuanced than the working theory and we adjust.

### Inputs the next session needs

- The current generated `task-01.md` at
  `~/health-data-ai-platform/tasks/airflow-gdrive-ingestion/prompts/
  task-01.md` — as the baseline to compare against.
- The current `tasks.json` at
  `~/health-data-ai-platform/tasks/airflow-gdrive-ingestion/
  tasks.json` — for the structured fields (roadmap_component, files
  paths, depends_on, acceptance_criteria, test_command).
- The roadmap scenarios for `project-setup` in
  `~/health-data-ai-platform/docs/roadmap/airflow-gdrive-ingestion/
  roadmap.json` — these inline into the prompt's
  `## Behaviors to Verify` section.
- The prototype at
  `~/health-data-ai-platform/prototypes/airflow-gdrive-ingestion/` —
  the source of truth.
- The session-status updates from this skill iteration (this file
  and `session-status-2026-05-10-update-2.md`).
- LEARNINGS.md, specifically the entries about "Tests that don't
  constrain what you actually care about" and "stubs must satisfy
  the mock boundary" — these are constraints the rewritten prompt
  needs to honor.

### Approach for the next session

The next session should follow this rough arc:

1. **Read the current generated `task-01.md`** to anchor on what the
   prompt-composition skill currently produces. Note especially the
   `## Files to Create / Modify` section — that's where the
   contradictory bullets live.

2. **Hand-write a replacement prompt** for the same scaffolding
   scope. Constraints:
   - Drop the prose `description` paragraph entirely from each file
     bullet, or reduce it to one short clause.
   - Add explicit `prototype_reference: <path>` for each file that
     has a prototype counterpart.
   - Keep `## Behaviors to Verify` (roadmap scenarios) unchanged —
     that's the BDD contract.
   - Keep `## Acceptance Criteria` unchanged.
   - Keep the universal preamble unchanged.
   - The prompt should be self-contained enough that an executor
     reading the prototype reference can produce the file correctly
     without ambiguity.

3. **Run that hand-written prompt against Claude Code** (the
   strongest reference executor). Clean up `services/
   airflow-gdrive-ingestion/` before each run.

4. **Manually verify the generated content** against the prompt's
   intent — not just acceptance criteria, but content-level checks:
   - Does conftest.py have both `sample_db_path` and `all_records`?
   - Does requirements.txt have `apache-airflow[celery]==2.10.5`?
   - Do the other 7 files match prototype + prompt's intent?

5. **Iterate.** If the first attempt has content drift, adjust the
   hand-written prompt (more or less prototype reference framing,
   different field structure, etc.) and rerun. The goal is to
   converge on the minimum prompt structure that produces correct
   output reliably.

6. **Once it works against Claude Code**, retry against Pi+Qwen to
   confirm the redesigned format works across tier levels.

7. **Document the resulting prompt structure** as the spec for the
   decomposition skill rewrite. The structure of the prompt is the
   structure the decomposition skill should produce.

### Stretch goal for next session

If the hand-written prompt approach validates, sketch what the
`tasks.json` schema would look like under the new design. Likely
candidates to remove or simplify:

- `task.files[].description` — collapse to optional one-clause field
  or remove entirely.
- `task.files[].stub` — keep, drives executor behavior.
- Add `task.files[].prototype_reference` as a structured field the
  composition script knows to inline into the prompt.
- Possibly: `task.description` paragraph — collapse to a slug or
  one-line summary, since the per-file detail moved to the
  prototype references.

This is the "medium scope" rewrite proposal — replace prose
`description` with structured `intent + prototype_reference`. Hold
off on the "large scope" rewrite (collapse the task to a tuple of
schema fields with no prose at all) until medium is validated.

### What NOT to do in the next session

- Don't change the prompt-composition skill's script. The script is
  fine — it faithfully composes what the decomposition gives it.
- Don't change the planning skill. The roadmap output is at the
  right level (BDD scenarios grounded in prototype).
- Don't re-implement the decomposition skill yet. Validate the
  prompt structure first; the decomposition rewrite follows from
  whatever structure works.

## Open items carried forward (unchanged from update 2)

- Step 2 of `prompt-composition-skill-plan-2026-05-09.md` (the
  implementation-skill changes) is still pending. Holding until the
  decomposition rethink stabilizes — implementation skill changes
  that consume the current prompt format would be invalidated by a
  decomposition rewrite.
- T10/T17 validation runs deferred for the same reason.
- Aider+Qwen tier-0 value reassessment — Pi+Qwen looks like a viable
  alternative based on this session's runs. Worth tracking but not
  blocking.
- MCP memory server — still designed, still not built. Not blocking.

## Key insight summary (for LEARNINGS.md propagation)

**The prototype is the only stable reference in the prototype-driven
chain.** Roadmap scenarios are derived from prototype behavior;
prompts are derived from scenarios + prototype references; tests
verify prototype behavior. Every level of derivation introduces an
opportunity for LLM-generated content to drift from the prototype.
The decomposition skill's `task.files[].description` field is one
such derivation layer where drift has been observed across three
independent executor runs.

The architectural principle that follows: **when prototype and prose
might conflict, the prototype wins, and prose should be minimized to
reduce conflict opportunities.** The minimum prose is what's needed
to point the executor at the right prototype file and tell it what
kind of output to produce.

This insight belongs in LEARNINGS.md once the next session validates
that a prototype-reference-driven prompt structure actually works in
practice.
