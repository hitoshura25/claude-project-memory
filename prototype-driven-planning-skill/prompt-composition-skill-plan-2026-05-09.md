# Prompt Composition Skill — Extract Prompt Generation from the Pipeline

**Status:** PROPOSED — not yet implemented. Plan written 2026-05-09 after a
design discussion in conversation that explored extracting prompt
generation from the implementation skill into its own skill, motivated
by two concerns: (a) prompts are currently entangled with pipeline
state and cannot be inspected or used independently; (b) the user
wants the option to feed individual task prompts to executors outside
the LangGraph pipeline (Claude Code, Aider, Gemini CLI, etc.) for
debugging or for cases where pipeline orchestration is overkill.

**Owning skill:** new `prototype-driven-prompt-composition`. Coordinated
changes to `prototype-driven-implementation`. No changes to
`prototype-driven-planning`, `prototype-driven-roadmap`, or
`prototype-driven-task-decomposition`.

**Validation:** new T17 trial against `airflow-gdrive-ingestion`,
exercising both consumption paths (manual + pipeline) of the
generated prompts.

**Revisions log:**
- Initial draft: 2026-05-09 morning.
- 2026-05-09 (post-discussion): six open-implementation questions
  resolved and folded back into the design. Audit-copy mechanism
  removed (D5 simplified). Project name + description removed from
  the preamble (D9 added; what was the conditional-preamble idea is
  rejected — preamble stays uniform across all tasks). Phase A
  reads canonical prompt from disk like every other task, instead
  of consulting tasks.json directly (D10 added). Inlineable
  extensions derived from task file paths instead of separate
  detection (D11 added). Open-questions section retained for items
  still genuinely open at implementation time.

---

## Why this exists

The implementation skill currently bundles three concerns:

1. **Prompt composition.** Reading tasks.json, inlining roadmap
   scenarios, formatting Gherkin behaviors, applying retry/error context
   — produces the markdown the executor consumes.
2. **Pipeline orchestration.** LangGraph state machine, retry/escalate,
   verification, executor dispatch.
3. **Scaffold execution + handoff.** Phase A, the conversation-time
   bootstrap.

Concerns (2) and (3) are genuinely tied to "running tasks at scale";
concern (1) is a deterministic transformation of static inputs
(tasks.json + roadmap.json) and is independent of how those prompts
are subsequently executed. Today's `compose_prompt.py` node lives
inside the LangGraph pipeline and pulls its inputs partly from
PipelineState (current task id, retry count, executor tier, log file
paths) — so prompts cannot be generated, inspected, or consumed
without first standing up the entire pipeline.

Three concrete consequences of this entanglement:

- **No inspection step.** The user can't review what the executor will
  see for a given task before running the pipeline. Prompts only
  materialize on disk during pipeline execution, in
  `logs/prompts/<task-id>_t<tier>_r<retry>.md`. Debugging "why did this
  task fail" requires running the pipeline at least once to even see
  the prompt.
- **No portability.** Users who want to hand a single task to Claude
  Code (e.g., to manually finish a stuck pipeline, or to use Claude's
  native tools for a tricky debugging session) cannot. The prompt logic
  is locked inside `nodes/compose_prompt.py.template` which only runs
  inside the LangGraph state machine.
- **No optionality on executors.** Anything that wants to consume the
  decomposition's output has to also consume the LangGraph pipeline.
  Lighter-weight executors or shell-based workflows are blocked by the
  pipeline's setup overhead.

Splitting prompt composition into its own skill removes all three
constraints. The new skill is a pure transformation — tasks.json +
roadmap.json → one markdown file per task, written to
`tasks/<feature>/prompts/<task-id>.md`. The implementation skill's
pipeline reads those files at runtime instead of composing them. Manual
consumers read the same files and feed them to whatever executor they
prefer.

---

## Architectural decisions

### D1. New skill: `prototype-driven-prompt-composition`

A fourth skill in the chain, sitting between decomposition and
implementation:

```
/prototype-plan <feature>          → design doc
/prototype-roadmap <feature>       → roadmap.json + components.json
/prototype-task-decompose <doc>    → tasks.json
/prototype-compose-prompts <feat>  → prompts/<task-id>.md     ← NEW
/prototype-implement <feature>     → pipelines/<feature>/
```

**Inputs:**
- `tasks/<feature>/tasks.json` (decomposition output)
- `tasks/<feature>/task_schema.py` (for validation)
- `docs/roadmap/<feature>/roadmap.json` (for scenario inlining)

The design doc is **not** an input. The composition skill no longer
needs project name or description (see D9), so the only structural
artifacts it consumes are the JSON outputs of upstream skills.

**Output:** `tasks/<feature>/prompts/<task-id>.md` — one self-contained
prompt per task. Every task in `tasks.json` gets a prompt file,
including scaffold tasks (D10).

**Output-directory precondition.** Mirrors the pipeline-existence
precondition added in the Phase A/B refactor: if
`tasks/<feature>/prompts/` already exists when the skill is invoked,
stop and ask the user to remove it. The user is responsible for knowing
when prompts need regeneration (after decomposition or roadmap
changes); the skill enforces "regenerate cleanly or not at all" rather
than implementing staleness detection.

### D2. Prompts are plain markdown, not JSON

The format question — markdown vs JSON — was settled by execution-side
constraints. Every executor (Aider via `--message-file`, Claude CLI
via `-p`/stdin, Gemini CLI similarly) consumes a string. None parse
JSON natively as "the prompt." Storing prompts as JSON would require a
render step in two places (composition skill writes JSON + renders
markdown for inspection; pipeline reads JSON + renders markdown for
the executor) without enabling validation that decomposition's
existing validators don't already provide.

Prompts are markdown files. The format mirrors the current
`compose_prompt.py.template` output structure. Section markers
(`## Objective`, `## Files to Create / Modify`, `## Acceptance
Criteria`, etc.) are stable and grep-able for downstream tools that
want to extract specific fields.

### D3. Validation: existence + section-marker presence only

The new skill validates only:

1. Every task in `tasks.json` has a corresponding `prompts/<task-id>.md`
   file.
2. Every prompt file is non-empty.
3. Every prompt file contains the canonical section markers
   (`## Objective`, `## Files to Create / Modify`,
   `## Acceptance Criteria`).

Anything deeper (every cited scenario actually inlined, every
dependency path corresponds to a real task file, prompt content
matches task spec) is delegated to the decomposition validator,
which already enforces these as part of its schema. Prompts derived
from valid decomposition output are correct by construction.

The implementation skill's `check_preconditions` node gains a check:
the `prompts/` directory exists and contains `<task-id>.md` for every
task in tasks.json (no scaffold exemption — D10). If any prompt is
missing, exit with: "Prompts not generated. Run
`/prototype-compose-prompts <feature>` first." Same fail-fast shape
as the existing scaffold-marker check.

### D4. Dependencies referenced by path; no inlining (initial cut)

The current pipeline inlines dependency file content as text into
each prompt — `_inline_dependencies` reads each dependency task's
files from disk and embeds them under a `## Dependencies` section.
This works at pipeline runtime because earlier tasks have run and
their files exist on disk; it does NOT work for pre-generated
prompts, because at composition time most dependency files don't
exist yet.

Three options were considered:

- **A: Reference dependencies by path; consumer reads them.**
  Prompt names dependency files; whatever runs the prompt reads the
  files itself.
- **A+: A, with optional pipeline-side enrichment.**
  Pre-generated prompts on disk reference paths only; the pipeline
  reads dependency files fresh at execution time and prepends a
  transient `## Dependency Snapshots` block before invoking the
  executor.
- **B: Inline dependency content as text at composition time.**
  Same as today, but using static descriptions of what the
  dependency *should* expose. Adds schema fields, defeats simplicity.

**Decision: Option A for the first cut.** Prompts name dependency
files by path under a `## Dependencies` section; no pre-injection
anywhere. If trials show local models or executors flailing on
dependency lookups, A+ becomes the targeted fix. Starting simpler
preserves option value.

Aider compatibility note: Aider's `--read <path>` flag handles the
dependency-on-disk case. The pipeline can build the `--read` list
from the prompt's `## Dependencies` paths section without enriching
the prompt itself.

### D5. Retry/error context: per-attempt log subfolder, prompt references the folder

The current prompt embeds retry context dynamically (changes per
attempt). For pre-generated prompts to handle this, the convention
moves into the filesystem.

**Log convention:**

```
logs/
├── lint/<task-id>/
│   ├── attempt-1-tier0.txt
│   ├── attempt-2-tier0.txt
│   └── attempt-3-tier1.txt    # tier escalation visible in filename
└── tests/<task-id>/
    └── attempt-N-tierM.txt    # same shape
```

**Prompt language (canonical, baked into every prompt):**

```markdown
## Previous Attempts

If this task has been attempted before, error logs will be in:

- `logs/lint/<task-id>/` — lint errors per attempt
- `logs/tests/<task-id>/` — test errors per attempt

Filenames are `attempt-N-tierM.txt` (highest N is most recent). Read
the most recent file in each directory if any exist. If a directory is
empty or missing, this is your first attempt.
```

The canonical prompt at `tasks/<feature>/prompts/<task-id>.md` is
**read directly by every consumer** — pipeline, manual Claude Code
session, Aider invocation — and **never copied or modified**. The
canonical file is the single artifact for "what the executor was
told"; since its contents don't change between attempts, an audit
copy per attempt would just duplicate the same bytes N times. The
attempt-to-attempt difference lives in the lint and test log files
(per-attempt by design).

The pipeline's run log already records which prompt path was passed
to which executor on which attempt — that's enough forensic record
for "what was sent on attempt 3" since the answer is always "the
canonical file at this path."

**Deferred enrichment: explicit current-attempt signal.** An earlier
draft considered the pipeline writing a `.current-attempt` marker or
setting an environment variable so the executor doesn't have to guess
"highest N." Deferred for the first cut — the filename encodes the
attempt and tier explicitly, and modern executors should be able to
parse `attempt-3-tier1.txt > attempt-2-tier0.txt`. If trials show
models confused by attempt-history reasoning, add the explicit
current-attempt signal as a targeted fix.

### D6. Roadmap-scenario inlining moves to composition time

Today, `compose_prompt._inline_roadmap_scenarios` reads `roadmap.json`
at pipeline runtime and resolves each task's scenario IDs against the
component the task cites. With pre-generated prompts, this resolution
happens once at composition time and the rendered Gherkin lives as
text in the prompt file.

This has a nice side effect: it eliminates the CWD-relative path
resolution problem D02 fixed for the implementation side. The new
skill resolves `roadmap.json` once (whatever its CWD is when
`/prototype-compose-prompts` runs is the resolution context); the
pipeline never touches `roadmap.json` again. The parallel
`_resolve_project_path` helper that lives in
`compose_prompt.py.template` can be removed in the implementation
skill once that file goes away (see D7).

### D7. Implementation skill loses `compose_prompt.py.template`

The pipeline gains a new `nodes/load_prompt.py` (LangGraph-idiomatic
separate node, per Open Q1 resolution) that runs between
`pick_next_task` and `execute_task`. It reads
`tasks/<feature>/prompts/<task-id>.md` from disk and writes the path
into `PipelineState` for `execute_task` to pass to
`agent_bridge.execute()`. No copying, no enrichment, no
substitution — just a path read.

The implementation skill's responsibilities shrink to:

- Phase 1: tooling detection, runtime-isolation research, executor
  detection (unchanged).
- Phase 2: copy templates, fill `config.py` placeholders. **No more
  `compose_prompt.py.template` substitution.** Two placeholders that
  step substituted (`{{PROJECT_NAME}}`, `{{PROJECT_DESCRIPTION}}`)
  are removed entirely (D9), not relocated. `{{INLINEABLE_EXTENSIONS}}`
  is also removed — it becomes derived data in the composition skill
  (D11).
- Phase 3: validation, scaffold execution, handoff (mostly unchanged;
  smoke test simplifies; Phase A reads from prompts dir per D10).

The implementation skill no longer holds the prompt template. Single
source of truth for the prompt structure moves to the new skill's
`references/prompt-template.md`.

### D8. Pipeline errors hard if prompts are missing

The implementation skill's `check_preconditions` node (added in the
Phase A/B refactor for the scaffold-complete marker) gains a second
check:

- For every task ID in `tasks.json`, verify
  `tasks/<feature>/prompts/<task-id>.md` exists. **No scaffold
  exemption** — Phase A reads the scaffold prompt from disk like
  every other consumer (D10).
- If any are missing, exit with: `Prompts not generated. Run
  /prototype-compose-prompts <feature> first.`

The pipeline does NOT auto-invoke the composition skill, does NOT
warn-and-continue, does NOT fall back to in-pipeline composition.
Clean boundary: the implementation skill is purely an orchestration
layer; if its inputs aren't ready, it tells the user and stops.

### D9. Drop project name and project description from the preamble

The current `_PROJECT_CONTEXT` preamble includes a `# Project: <name>`
heading with a one-paragraph description, substituted via
`{{PROJECT_NAME}}` and `{{PROJECT_DESCRIPTION}}` placeholders.

This block is **removed entirely**, not relocated.

The reasoning:

- The task description itself names the component being built and
  what it does — the project-level framing isn't load-bearing in
  the prompt.
- The project name is visible in the file paths the executor sees
  in the `## Files to Create / Modify` section.
- Removing the block also dissolves Open Question 3 (where to
  source the description from), which had no clean answer.
- The preamble shrinks for every task, saving prompt tokens for
  every executor invocation across every trial.

The remaining preamble blocks (Role, Test writing rules, Stub
writing rules, Coding conventions, Output format) stay uniform
across all tasks. **No per-task-type conditional logic** — every
prompt has the same preamble shape. Test rules sit unused on
implementation-task prompts; that's fine, they're cheap, and
keeping the preamble uniform keeps the composition logic dumb.

The composition skill's Phase 1 STOP-summary loses two outputs
(project name, project description). It now reports: inputs found,
inlineable extensions detected (from task file paths per D11),
task count, scenario citation count.

### D10. Phase A reads scaffold prompt from disk like every other task

Composition writes prompts for all tasks including scaffold. Phase
A's Scaffold Execution step (added in the Phase A/B refactor) is
updated to read `tasks/<feature>/prompts/task-01.md` instead of
constructing what to do from `tasks.json` directly.

This makes scaffold consistent with every other task in the system:
- Composition skill writes its prompt.
- check_preconditions verifies it exists alongside other prompts.
- Phase A consumes the same prompt the pipeline would have consumed
  if scaffold weren't a special case.

The only difference between scaffold and other tasks remains the
*executor*: scaffold runs in conversation via Claude Code, not via
the LangGraph pipeline. The prompt content, location, and lifecycle
are uniform.

This eliminates a small but real divergence in the original Phase
A/B plan, where Phase A was special-casing tasks.json reads. Now
Phase A is just-another-prompt-consumer.

### D11. Inlineable extensions derived from task.files paths

Open Question 2 resolution.

The composition skill scans `task.files[].path` across all tasks in
`tasks.json`, collects unique file extensions, and uses that set as
the inlineable-extensions list when filtering dependency paths into
the `## Dependencies` section.

This replaces the previous detection mechanism (read project lint
config, derive extensions per ecosystem). Three benefits:

- **Simpler**: no per-ecosystem detection logic.
- **More accurate**: reflects what tasks actually produce, not what
  the linter happens to be configured for.
- **Self-contained**: the composition skill's only inputs stay
  tasks.json, task_schema.py, and roadmap.json — no design-doc
  parsing, no project-config inspection.

The `{{INLINEABLE_EXTENSIONS}}` placeholder disappears entirely;
it becomes derived data, never substituted, never user-visible.

---

## What the prompt looks like

The canonical structure each generated prompt file follows. Sections
in order; later sections optional and omitted when their data is
empty.

```markdown
# Role

You are implementing a component in an existing codebase. You receive a
component spec and must produce tests and, when applicable, a stub file.
Another model will later implement the stub against your tests.

# Test writing rules

[generic rules from the current _PROJECT_CONTEXT preamble — unchanged]

# Stub writing rules

[generic rules from the current _PROJECT_CONTEXT preamble — unchanged]

# Coding conventions

[generic rules from the current _PROJECT_CONTEXT preamble — unchanged]

# Output format

[generic rules from the current _PROJECT_CONTEXT preamble — unchanged]

---

# Task: <task title>

## Objective

<task description verbatim from tasks.json>

## Files to Create / Modify

- **`<path>`** (<operation>): <description>
- ...

## Behaviors to Verify (from roadmap)

_Component: `<roadmap_component>` (resolved from roadmap.json at composition time)_

### Functional behaviors

### <name> (`<id>`)
- **Given**: ...
- **When**: ...
- **Then**: ...
- **Verified by**: `<path>`

### Security behaviors

### <name> (`<id>`)
- **OWASP requirement**: <owasp_id>
- **Performed by**: `<slug>`
- ...

## Dependencies

The following files exist on disk and contain interfaces this task
depends on. Read them before writing any code:

- `<path>` — created by `<dep_task_id>`
- `<path>` — created by `<dep_task_id>`

## Acceptance Criteria

- ...
- ...

## Security Considerations

- ...

## Previous Attempts

If this task has been attempted before, error logs will be in:

- `logs/lint/<task-id>/` — lint errors per attempt
- `logs/tests/<task-id>/` — test errors per attempt

Filenames are `attempt-N-tierM.txt` (highest N is most recent). Read
the most recent file in each directory if any exist. If a directory is
empty or missing, this is your first attempt.
```

Differences from today's pipeline-composed prompt:

- **Project name + description block removed** (D9). One fewer
  heading, one fewer paragraph, fewer prompt tokens, no upstream
  detection step.
- **Dependencies section**: lists paths only, no inlined content
  (D4).
- **Previous Attempts section**: always present, references log
  directory convention (D5). Today's "Previous Attempt"/"Previous
  Executor Attempts" header text variation disappears — single
  phrasing handles all cases.
- **Behaviors to Verify section**: rendered text instead of
  runtime-resolved (D6). Identical content; different timing.

Everything else (Role, Test/Stub/Coding/Output rules, Files,
Acceptance, Security) is unchanged from the current template.

---

## Skill changes

### `prototype-driven-prompt-composition/` (new skill)

Layout:

```
~/claude-devtools/skills/prototype-driven-prompt-composition/
├── SKILL.md
├── scripts/
│   └── compose_prompts.py     # The actual generator; standalone Python script
└── references/
    ├── prompt-template.md     # Canonical prompt structure documented
    ├── log-conventions.md     # Where logs go; filename format; how prompts reference them
    └── dependency-handling.md # Why paths-not-inlined; how the pipeline enriches at runtime (deferred)
```

`SKILL.md` shape (mirrors decomposition skill):

- **Quick Reference table**: tasks.json + task_schema + roadmap.json
  → prompts/<task-id>.md
- **How to Start**: feature name from `$ARGUMENTS`, ask which feature
  if missing (scan `tasks/` subdirectories with `tasks.json` like
  the implementation skill does — Open Q5 resolution), fail fast on
  missing inputs, refuse to overwrite existing `prompts/` directory.
- **Phase 1: Inputs and Inlineable Extensions.** Validate inputs
  exist and parse cleanly. Scan `task.files[].path` across all tasks
  to collect inlineable extensions (D11). Present a STOP-summary:
  inputs found, extensions detected, task count, total scenario
  citations.
- **Phase 2: Prompt Generation.** For each task in tasks.json:
  - Render the universal preamble (Role, Test/Stub/Coding/Output
    rules) — uniform across all tasks (D9).
  - Render the task-specific section (Objective, Files, Behaviors to
    Verify, Dependencies, Acceptance, Security, Previous Attempts).
  - Resolve roadmap citations against `roadmap.json` and inline the
    Gherkin (D6).
  - List dependency file paths under `## Dependencies` — no content
    inlining (D4).
  - Always include the `## Previous Attempts` section pointing at the
    log convention (D5).
  - Write to `tasks/<feature>/prompts/<task-id>.md`.
  - Every task gets a prompt, including scaffold (D10).
- **Phase 3: Validation and Handoff.** Run the existence /
  section-marker validator (D3). Print summary: N prompts written,
  M tasks total, all files non-empty, all section markers present.
  Tell the user the next step is `/prototype-implement <feature>`
  (or manual consumption).

`scripts/compose_prompts.py`: the actual generator. Standalone Python
script (no LangGraph dependency). Imports the project's shipped
`task_schema.py` for validation. Reads tasks.json and roadmap.json.
Produces prompts. Idempotent with respect to its inputs.

`references/prompt-template.md`: documents the canonical section
order and content rules. The new source of truth for what an executor
prompt looks like.

`references/log-conventions.md`: documents the
`logs/lint/<task-id>/attempt-N-tierM.txt` and
`logs/tests/<task-id>/attempt-N-tierM.txt` convention. Documents the
filename format. Documents that prompts reference the directory, not
specific files. The implementation skill's pipeline reads this same
doc by reference (cross-skill citation, not duplication).

`references/dependency-handling.md`: documents the
paths-not-inlined decision (D4). Documents the deferred A+ option
(pipeline-side enrichment) so future trial findings can refer to it
without re-deriving the analysis.

### `prototype-driven-implementation/` (coordinated changes)

#### `SKILL.md`

Four structural changes:

1. **How to Start gains a prompts-existence precondition.** New bullet
   alongside the existing pipeline-existence and tasks.json-existence
   checks: "If `tasks/<feature>/prompts/` does not exist or is missing
   any `<task-id>.md` file for tasks in tasks.json, stop and tell the
   user to run `/prototype-compose-prompts <feature>` first." No
   scaffold exemption (D10).

2. **Phase 2 loses the compose_prompt.py.template substitution
   step.** Step 4 in the current SKILL.md ("Generate
   `nodes/compose_prompt.py` from the template") is removed. The
   three placeholders that step substituted (`{{PROJECT_NAME}}`,
   `{{PROJECT_DESCRIPTION}}`, `{{INLINEABLE_EXTENSIONS}}`) are
   removed entirely — none relocate (D9, D11).

3. **Phase 3 smoke test simplifies.** The smoke test currently
   exercises both `load_tasks_node` (schema-side path resolution) AND
   `compose_prompt._inline_roadmap_scenarios` (implementation-side
   path resolution). With the refactor, the second exercise goes
   away — the pipeline doesn't resolve roadmap paths anymore. The
   smoke test reduces to `load_tasks_node` only.

4. **Phase 3 Scaffold Execution reads from prompts dir (D10).**
   The Scaffold Execution step reads
   `tasks/<feature>/prompts/task-01.md` instead of consulting
   `tasks.json` directly. The protocol stays the same (create files,
   run bootstrap, verify runtime, run test_command, write marker);
   only the input source changes.

#### `references/phase-2-generation.md`

- **Remove "Step 3: Generate `nodes/compose_prompt.py` from its
  template"** entirely. The template file goes away (see templates
  section below).
- **Remove `{{ROADMAP_JSON_PATH}}` placeholder** from the config
  placeholder table. The pipeline doesn't read roadmap.json directly
  anymore; roadmap content is inlined into prompts at composition
  time (D6).
- **Update the Output Structure file list** to remove
  `nodes/compose_prompt.py` and add `nodes/load_prompt.py`. Add a
  brief note that the pipeline reads prompts from
  `tasks/<feature>/prompts/<task-id>.md` at runtime.

#### `references/phase-3-handoff.md`

- **Update Smoke Test section** per the SKILL.md change above —
  remove the `compose_prompt._inline_roadmap_scenarios` exercise,
  keep the `load_tasks_node` exercise.
- **Update Precondition Validation** to add the prompts-existence
  check (every task in tasks.json has a corresponding prompt file
  in `tasks/<feature>/prompts/`).
- **Update Scaffold Execution section** per D10 — Step 1 reads
  `tasks/<feature>/prompts/task-01.md` (not tasks.json directly);
  Steps 2–6 stay the same.

#### `templates/`

Pipeline-side changes:

1. **Delete `templates/nodes/compose_prompt.py.template`.** Replaced
   by a new `templates/nodes/load_prompt.py` (verbatim template, no
   placeholders) per Open Q1 resolution.

2. **Add `templates/nodes/load_prompt.py`.** New LangGraph node that
   runs between `pick_next_task` and `execute_task`. Reads the
   canonical prompt at
   `<TASKS_DIR>/prompts/<current_task_id>.md`,
   verifies it exists (defense in depth — `check_preconditions` is
   the authoritative check), writes the path into `PipelineState`
   for `execute_task` to consume.

3. **Modify `templates/nodes/execute_task.py`.** Remove any
   prompt-composition logic that may have crept in; consume the
   path written by `load_prompt`. No copying.

4. **Modify `templates/nodes/verify_task.py`.** Update lint and test
   error log paths to follow the new convention:
   `logs/lint/<task-id>/attempt-N-tierM.txt` and
   `logs/tests/<task-id>/attempt-N-tierM.txt`. The current code
   writes to `logs/lint/task-NN_error_<time>.txt` style — the new
   convention puts each task in its own subdirectory and uses the
   attempt+tier in the filename rather than a timestamp.

5. **Modify `templates/nodes/check_preconditions.py`.** Add a check
   that every task ID in tasks.json has a corresponding prompt file
   at `tasks/<feature>/prompts/<task-id>.md` (no scaffold exemption,
   D10). If any are missing, exit with the
   "run /prototype-compose-prompts" pointer.

6. **Modify `templates/graph.py`.** Wire `load_prompt` between
   `pick_next_task` and `execute_task`.

7. **Modify `templates/pipeline_state.py`.** `current_prompt_path`
   stays in `PipelineState` (already there); the node that writes it
   changes from `compose_prompt` to `load_prompt`. The
   retry/escalation-context state fields
   (`current_lint_error_path`, `current_test_error_path`) can be
   removed — prompts reference log directories by convention now,
   not by absolute paths injected into state.

8. **Modify `templates/config.py.template`.** Remove the
   `{{ROADMAP_JSON_PATH}}` placeholder and the `ROADMAP_JSON_PATH`
   variable — no longer used by the pipeline (roadmap content is
   inlined at composition time).

### Memory repo (`~/claude-project-memory/prototype-driven-planning-skill/`)

After implementation:

- New trial file `trials/T17-<slug>.md` documenting the validation
  trial (outline below).
- Update `trials/_SUMMARY.md` and `_INDEX.md`.
- Update `README.md`'s skill list to include the new skill, update
  the file map, update the conversation-start protocol.
- Update `LEARNINGS.md` with whatever generalizes from the trial —
  likely entries on (a) prompt composition as a separable concern
  from orchestration, (b) the "log conventions over runtime context"
  pattern, (c) the "uniform preamble over conditional logic"
  pattern, (d) any specifics about the dependency-handling
  decision if the trial validates or invalidates the simplest-first
  approach.
- Mark this plan doc as superseded once T17 lands.

---

## What stays unchanged

- **`prototype-driven-planning`**: untouched.
- **`prototype-driven-roadmap`**: untouched.
- **`prototype-driven-task-decomposition`**: untouched. tasks.json
  schema is unchanged. The CWD-relative-path-resolution helper added
  in D02 (`_resolve_project_path` in `task_schema.py`) stays — it's
  still needed for the schema's own validators that resolve
  `components_json_path` and `roadmap_json_path`.
- **The pipeline's executor dispatch, retry/escalation, scaffold
  execution (Phase A/B), runtime-isolation research, auto-resume
  logic**: all unchanged. These concerns are orthogonal to where
  prompts come from. Phase A's *input source* changes per D10 (reads
  from prompts dir), but the protocol within Phase A is unchanged.
- **The prompt structure itself**: mostly unchanged. Same Role
  framing, same rules, same Gherkin-format scenario inlining, same
  task-specific sections. Only differences: project block removed
  (D9), Dependencies section lists paths instead of content (D4),
  Previous Attempts section format changed (D5), composition
  timing changed (D6).

---

## Validation plan: T17

Single trial that exercises the whole change end-to-end, validating
both consumption paths.

**Pre-trial setup:**
1. Land all skill changes (new skill, implementation-skill updates).
2. Remove the existing `pipelines/airflow-gdrive-ingestion/` directory
   (per the implementation skill's pipeline-existence precondition).
3. Confirm `tasks/airflow-gdrive-ingestion/tasks.json` is valid
   against the current schema (no schema changes in this refactor;
   should pass unchanged).

**Trial run:**

1. **Run the prompt-composition skill.**
   - `/prototype-compose-prompts airflow-gdrive-ingestion`
   - Phase 1: validates inputs, derives inlineable extensions from
     task file paths, presents STOP-summary.
   - Phase 2: generates one prompt per task in
     `tasks/airflow-gdrive-ingestion/prompts/`.
   - Phase 3: validates output, prints summary.
   - **Acceptance**: 13 prompt files written (matching the 13 tasks
     in the airflow-gdrive-ingestion decomposition, including
     scaffold task-01). Each contains all canonical section
     markers. Each is non-empty and parses cleanly as markdown.
     Project block absent from every prompt (D9 verification).

2. **Manually inspect 2-3 prompts.**
   - Pick one scaffold task, one test task, one implementation task.
   - Verify each section renders correctly: roadmap scenarios
     inlined as Gherkin, dependencies listed by path (not content),
     Previous Attempts section present, files-to-create/modify
     correct.
   - **Acceptance**: prompts read as self-contained specs that
     could be handed to any executor without further context.

3. **Hand a single prompt to Claude Code manually.**
   - Pick a non-scaffold task (e.g., a test task or an
     implementation task with one or two dependencies).
   - Open a fresh Claude Code session, attach the prompt file, and
     ask Claude to execute it against the project.
   - **Acceptance**: Claude Code completes the task — reads
     dependency files from the listed paths, writes the expected
     output files, runs the test_command. The pipeline doesn't run
     at all in this validation arm. This proves portability.

4. **Run the pipeline (`/prototype-implement` then `python run.py`).**
   - The implementation skill generates the pipeline.
   - Phase A executes scaffold task-01 by reading
     `tasks/airflow-gdrive-ingestion/prompts/task-01.md` (D10
     verification — Phase A consumes from prompts dir, not
     tasks.json directly).
   - `check_preconditions` verifies all prompt files exist
     (including scaffold).
   - Pipeline reads prompts from disk for each task via
     `load_prompt` node, passes path to executor via `execute_task`.
   - **Acceptance**: pipeline executes the same way it did in T16.
     No regression in success rate.

5. **Validate retry behavior.**
   - If any task fails on first attempt, verify:
     - `logs/lint/<task-id>/attempt-1-tier0.txt` and/or
       `logs/tests/<task-id>/attempt-1-tier0.txt` are written.
     - On retry, the executor sees the prompt's Previous Attempts
       section pointing at those directories.
     - The retry attempt produces `attempt-2-tier0.txt` (and
       eventually `attempt-N-tier1.txt` after escalation).
   - **Acceptance**: log convention works end-to-end; executors
     successfully read previous-attempt files based on prompt
     instructions.

**Acceptance bar:**

- All 13 prompts generated cleanly with canonical structure.
- No prompt contains a `# Project: ...` heading or project
  description (D9 verification).
- Phase A reads from `prompts/task-01.md` (D10 verification — check
  the conversation transcript).
- Manual Claude Code consumption of one prompt works without
  pipeline involvement (proves portability).
- Pipeline run completes at least as well as T16 — no regression
  from removing `compose_prompt.py` from the pipeline.
- Per-attempt log convention works: filenames carry attempt+tier,
  prompts reference the directory, executors find the files on
  retry.
- No leakage between consumption paths — manual run doesn't write
  to `logs/`, pipeline run doesn't modify canonical prompts.

**Out of scope for T17:**

- Pipeline-side dependency enrichment (the deferred A+ option from
  D4). If trials show local models flailing on dependency lookups,
  this becomes a follow-up.
- Explicit current-attempt signal beyond filename (deferred per
  D5). If trials show models confused by attempt-history reasoning,
  follow-up adds an `.current-attempt` marker or env var.
- Validating against non-Python projects. Same shape as T16's
  out-of-scope: future trial when a Node/Android/Go project becomes
  available.

---

## Resolved during planning (was: Open Implementation Questions)

Six questions were raised in the initial plan draft. All have been
resolved:

1. **Where does load logic go in the pipeline?** Resolved:
   separate `nodes/load_prompt.py` between `pick_next_task` and
   `execute_task` (LangGraph-idiomatic).

2. **How does the composition skill detect inlineable file
   extensions?** Resolved: derive from `task.files[].path` extensions
   across all tasks in tasks.json (D11). No project-config inspection.

3. **Project description source.** Resolved by elimination: project
   description is removed from the preamble entirely (D9), so no
   source detection is needed.

4. **Audit-trail copy timing.** Resolved by elimination: no audit
   copies are made (D5). Pipeline reads canonical prompt directly;
   the run log records which path was passed to which executor.

5. **`feature_name` extraction.** Resolved: same approach as the
   implementation skill — `$ARGUMENTS` wins; if empty, scan
   `tasks/` subdirectories containing `tasks.json` and ask the
   user.

6. **Conflict between project context and tasks without context.**
   Resolved by elimination: project block removed entirely (D9), so
   the conflict doesn't exist. Test/Stub/Coding/Output rules stay
   uniform across all tasks; they're cheap and keeping the preamble
   uniform avoids per-task-type conditional logic.

## Genuinely open at implementation time

Items that remain to settle when actually writing the code:

1. **Roadmap.json discovery.** The composition skill needs to find
   `roadmap.json`. Options: (a) read `tasks.json`'s
   `roadmap_json_path` field (already required by schema, points to
   the file decomposition consumed); (b) follow a convention like
   `docs/roadmap/<feature>/roadmap.json`. Option (a) is more robust
   — same file decomposition validated against, no convention
   drift. Probably (a).

2. **Universal-preamble file location.** The actual prose of the
   universal preamble (Role, Test rules, Stub rules, Coding
   conventions, Output format) needs to live somewhere in the
   composition skill. Two options: (a) embedded as a string
   constant in `compose_prompts.py`; (b) a separate file
   (`references/preamble.md`) that the script reads. Option (b) is
   cleaner — the prose can be reviewed and edited as a markdown
   document rather than buried in Python.

3. **Whether `load_prompt` checks for prompt existence.**
   `check_preconditions` does the authoritative check at startup.
   `load_prompt` runs per task and could either (a) trust the
   precondition and fail loudly with FileNotFoundError if the file
   was deleted mid-run, or (b) re-check and produce a friendlier
   error message. Probably (a) — keep the node logic simple,
   FileNotFoundError is already self-explanatory in this context.

---

## Sequencing

The plan implies the following order of work:

1. **Build the new skill.**
   - Create `~/claude-devtools/skills/prototype-driven-prompt-composition/`.
   - Write `SKILL.md`, `scripts/compose_prompts.py`, three reference
     docs, plus the universal-preamble prose file (per "Genuinely
     open" item 2).
   - Smoke-test the script against airflow-gdrive-ingestion's
     existing tasks.json + roadmap.json.

2. **Update the implementation skill.**
   - Update `SKILL.md`, `phase-2-generation.md`,
     `phase-3-handoff.md`.
   - Delete `templates/nodes/compose_prompt.py.template`.
   - Add `templates/nodes/load_prompt.py`.
   - Modify `templates/nodes/execute_task.py` (consume path from
     state).
   - Modify `templates/nodes/verify_task.py` for new log paths.
   - Modify `templates/nodes/check_preconditions.py` for prompts
     check.
   - Modify `templates/graph.py` to wire `load_prompt` in.
   - Modify `templates/pipeline_state.py` to drop the lint/test
     error path fields.
   - Modify `templates/config.py.template` to remove
     `ROADMAP_JSON_PATH`.

3. **Add the slash command.**
   - Create `~/claude-devtools/commands/prototype-compose-prompts.md`.

4. **Update memory repo.**
   - Update `README.md` skill list and file map.
   - Update conversation-start protocol if needed.
   - Stage trial slot for T17.

5. **Run T17.**
   - Pre-trial cleanup, then five-arm validation per the plan above.
   - File `trials/T17-<slug>.md`.
   - Update `_SUMMARY.md`, `_INDEX.md`.
   - Distill new principles into `LEARNINGS.md`.
   - Mark this plan superseded.
