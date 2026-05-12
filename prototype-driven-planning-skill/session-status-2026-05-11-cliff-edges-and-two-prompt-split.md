# Session Status — 2026-05-11 (cliff edges and two-prompt split)

Picks up from `session-status-2026-05-10-update-3.md`. That update
diagnosed the three-executor failure on task-01 (Pi+Gemma, Pi+Qwen,
Claude Code) as decomposition-skill prose ambiguity — `files[].description`
combined contradictory instructions ("mirror prototype exactly" + "include
X that prototype doesn't have") and models resolved the contradiction
inconsistently. The proposed fix was to drop the prose and lean on the
prototype as reference.

This session refined that direction substantially through discussion.
The conclusion: the right fix is not adding a new design-doc section,
but recognizing that **critical patterns are BDD scenarios** and the
existing roadmap is the right place to encode them — just with one more
structural field and explicit cliff-edge labeling upstream.

## The core decision

Cliff edges are observable behaviors with specific failure modes if
omitted (e.g., "omit `key_path=` from the Airflow connection URI → get
`DefaultCredentialsError`"). The planning skill already captures these
as breadcrumbs in observation-with-evidence form. They're just not
*tagged* in a way the roadmap can pick up structurally.

The change is small and additive across the chain:

1. **Planning** tags cliff-edge breadcrumbs explicitly with a
   `**Cliff edge:**` label discipline.
2. **Roadmap** adds `criticality` and `verification` fields to scenarios.
   Cliff-edge labels in the design doc produce scenarios tagged
   `criticality: cliff_edge`. Coverage check in the validator ensures
   every labeled breadcrumb produces at least one scenario.
3. **Decomposition** drops `files[].description` (the prose ambiguity
   surface). Tasks already cite scenarios by ID; the pipeline already
   inlines content. Nothing else to add.
4. **Prompt composition** splits each task into two prompts:
   - `task-NN-tests.md` — instruct the executor to write tests for the
     cited scenarios. The `verification` field on each scenario tells
     the executor what *form* the test takes (tool invocation, unit
     test, integration test, static assertion).
   - `task-NN-impl.md` — instruct the executor to make the tests pass.
     Cliff-edge scenarios are framed as non-negotiable; behavioral as
     the proven path; prescribed as security/production additions.

The two-prompt split is the answer to the test-writing vs implementation
separation discussed in update-3. It removes the "tests + stub +
implementation all in one prompt" confusion that the existing prompt
template carries (task-01's "Role" block contradicted task-01 being an
implementation task).

## Why this is the right shape

Three things this gets right that the earlier "add a Critical Patterns
section to the design doc" sketch did not:

1. **No new section to keep in sync.** Cliff-edge breadcrumbs already
   live in the design doc's existing narrative sections (Prototype
   Reference, Tooling Notes, Components production-considerations).
   Adding a label is cheaper than restructuring.
2. **The roadmap is already the BDD layer.** Critical patterns *are*
   given/when/then scenarios — the proof is that "omit `key_path=` →
   `DefaultCredentialsError`" maps cleanly to the scenario form. The
   roadmap doesn't need a new artifact; it needs richer fields on
   existing artifacts.
3. **The downstream skills (decomposition, prompt-composition) already
   have the consumption mechanism.** Decomposition cites scenarios by
   ID. Prompt-composition's script inlines scenario content at compose
   time. They just need to know the new fields exist.

Everything is additive — no skill is restructured wholesale.

## What I learned from reviewing the skills

Before writing this plan, I read the SKILL.md and key reference docs
for all four skills in the chain. Three facts changed my approach from
earlier in the session:

- **Planning already does breadcrumb-elicitation as instructed
  behavior**, not emergent behavior. The "Common failure patterns"
  guidance in `phase-2-prototype.md` tells the model to capture
  auth-pattern surprises, data-format mismatches, and toolchain
  gotchas in the prototype README. The Judgment-vs-Observation
  discipline in `phase-3-design-doc.md` then enforces that behavioral
  claims cite evidence. The cliff-edge breadcrumbs in the airflow
  design doc are the result of this — not accidents. So planning needs
  only a small labeling addition, not consultation changes.
- **Roadmap already has `evidence_kind: "prototype" | "prescribed"`** —
  two of the three criticality tiers exist. The third tier
  (`cliff_edge`) is what's missing. Adding it is a schema-field
  addition plus validator logic.
- **Decomposition already cites scenarios by ID and lets the pipeline
  inline content.** No paraphrasing. The change is purely additive
  (consume new roadmap fields) plus subtractive (drop
  `files[].description`).

The previous plan had been planning the wrong fight. The chain is
better than I assumed; the changes are smaller than I assumed.

## Per-skill changes

### Planning skill — `~/claude-devtools/skills/prototype-driven-planning/`

**Change 1: Cliff-edge labeling in `references/phase-3-design-doc.md`.**

Extend the Judgment-vs-Observation rules with a fourth label type:
**cliff-edge observation**. A cliff edge is an observation with
evidence that *additionally* names a specific failure mode if omitted.

Format:

```
**Cliff edge:** <Behavior description>. Omitting <what> causes
<specific failure>. Validated in `<prototype file>`.
```

Distinguished from:
- *Observation with evidence*: works because of X; X is the proven
  pattern but no specific failure mode for alternatives is documented.
- *Speculation labeled "Not observed"*: doesn't cite evidence.
- *Prescription labeled "Prescribed (not validated)"*: not present in
  prototype.

A cliff edge is a tested boundary condition. One side works; the
other side breaks loudly. The label exists so the roadmap skill can
mechanically identify which observations are cliff edges (vs. ordinary
observations with evidence) without re-inferring criticality from prose.

**Change 2: Cliff-edge breadcrumb capture in
`references/phase-2-prototype.md`.**

Extend the "Common failure patterns" subsection to call out the
breadcrumb pattern explicitly: when the prototype iteration encounters
"tried X, got error E, switched to Y," that's a cliff-edge candidate.
Capture in the prototype README's Toolchain Notes with the specific
error message. The Phase 3 design-doc generation step then uses these
captured breadcrumbs as the source for **Cliff edge:** labels.

**Change 3: Cliff-edge examples in `references/design-doc-template.md`
and `references/phase-3-design-doc.md`.**

Add a "Good (cliff edge labeled)" example alongside the existing
observation/speculation/prescription examples in
`phase-3-design-doc.md` § "Judgment vs. Observation." Concrete example
from airflow:

```
**Cliff edge:** Service account connection URI must include both
`key_path=<path>` (not `keyfile_path=`) and
`scope=https://www.googleapis.com/auth/drive.readonly`. Omitting
`key_path` causes `DefaultCredentialsError`; omitting `scope` causes
`HttpError 403 insufficientPermissions`. Validated in
`prototypes/airflow-gdrive-ingestion/docker-compose.yml` and DAG run
`prototype-e2e-test`.
```

**No change to:**

- Phase 1 discovery process.
- Phase 2 toolchain validation logic (security tooling, mitigation
  ladder, scope-removal triage all stay as-is).
- The overall design-doc section structure.
- The Open Questions Triage discipline.
- The Project Setup component rule.

### Roadmap skill — `~/claude-devtools/skills/prototype-driven-roadmap/`

**Change 1: Add `criticality` field to scenarios in
`scripts/roadmap_schema.py`.**

Both `FunctionalScenario` and `SecurityScenario` gain:

```python
criticality: Literal["cliff_edge", "behavioral", "prescribed"]
```

Default mapping by `evidence_kind`:
- `evidence_kind == "prototype"` and no cliff-edge label in source →
  `behavioral` (default).
- `evidence_kind == "prescribed"` → `prescribed`.
- Cliff-edge label in source → `cliff_edge` (requires explicit
  upgrade; model must read the label and tag the scenario).

The schema does not infer `cliff_edge` from `evidence_kind` alone —
that's the cross-file invariant the validator enforces in change 3.

**Change 2: Add `verification` field to scenarios.**

```python
verification: Literal["tool_invocation", "unit_test",
                       "integration_test", "static_assertion"]
```

The model selects per scenario based on how the scenario is verifiable:
- `tool_invocation`: run a tool (ruff, bandit, gitleaks, docker compose
  up --wait, pip-audit, hadolint, semgrep) and assert on exit code or
  output pattern. Used for most scaffold scenarios.
- `unit_test`: pytest function with mocks at the integration boundary.
  Used for most behavioral scenarios.
- `integration_test`: pytest function against real services (no mocks).
  Used for end-to-end scenarios.
- `static_assertion`: grep / regex / AST check against source. Used
  for security scenarios like "no hardcoded credentials in source."

Some scenarios genuinely have two reasonable forms (e.g., "use mkstemp,
not /tmp/" can be `unit_test` or `static_assertion`). The field is a
hint to the test executor, not a strict contract. When two forms work,
the model picks one and the prompt-composition includes the choice as
guidance, not mandate.

**Change 3: Cliff-edge coverage check in the validator.**

`scripts/validate_roadmap.py` gains a check: for every `**Cliff edge:**`
label in the design doc, at least one scenario in `roadmap.json` must
carry `criticality: cliff_edge` and cite the corresponding behavior in
its `given`/`when`/`then`. The check fails loudly if a labeled
breadcrumb has no scenario covering it.

The matching is structural — find `**Cliff edge:**` text in the design
doc, expect one cliff-edge scenario per label. The validator doesn't
need to understand the semantic content; it just enforces existence.

**Change 4: Generation guidance in `references/phase-2-generation.md`.**

Update phase 2 to instruct the model: when reading the design doc,
look for `**Cliff edge:**` labels and tag the resulting scenarios as
`criticality: cliff_edge`. Look at each scenario's verifiable form and
populate `verification` accordingly.

Add a "Verification field" subsection documenting the four values and
when each applies. Include the "two reasonable forms" guidance — the
field is a hint, not a contract.

**Change 5: Update `references/roadmap-json-format.md`** to document
the two new fields with examples.

**No change to:**

- Component extraction.
- OWASP machinery (categories, performed-by, ID parity checks).
- Slug generation.
- Dependency graph logic.
- Cross-file invariants beyond the new cliff-edge coverage check.
- The two-file split (`components.json` + `roadmap.json`).

### Decomposition skill — `~/claude-devtools/skills/prototype-driven-task-decomposition/`

**Change 1: Drop `description` from `FileChange` in
`scripts/task_schema.py`.**

The field is the prose-ambiguity surface that caused the three-executor
task-01 failure. Task-level structure (path, operation, stub) plus the
task's `roadmap_*` scenario citations plus the prototype path are
sufficient context. The pipeline inlines scenario content at compose
time; no per-file prose needed.

**Change 2: Remove inline prototype snippet guidance from
`references/task-writing-guide.md`.**

Currently the guide says to inline prototype snippets into task
descriptions ("the API response parsing at lines 23-31" with the
actual code embedded). Change to **path-only reference**:

```
Prototype reference: `prototypes/<feature>/<path>` — read for
working pattern. Deviate from shape only with documented reason.
Cliff-edge behaviors in cited roadmap scenarios are non-negotiable.
```

The implementing model reads the prototype file via its own filesystem
tools. Inlined snippets go stale (the prototype is immutable; tasks
may be regenerated) and reintroduce the "mirror exactly" pull that
caused the original failure.

**Change 3: Update the Task Description Template to remove the
implicit prose-paraphrase pull.**

The current template has sections Component / Component type /
Interface / Expected test failure mode / Out of scope. These are
structured slots — they stay. The change is in the prose guidance
around them: the template should not encourage paraphrasing roadmap
scenarios into the description. The structured citation
(`roadmap_functional_scenarios`, `roadmap_security_scenarios`) is the
canonical reference; the description gives the model just enough
context (component, type, interface signature, what tests should
fail with, what's out of scope).

**No change to:**

- The TDD pair enforcement (test task → impl task dependency).
- The scenario citation mechanism (already correct).
- The `test_command` field.
- The schema's structural invariants.
- The TaskDecomposition top-level fields.

### Prompt-composition skill — `~/claude-devtools/skills/prototype-driven-prompt-composition/`

**Change 1: Split prompt generation into two files per task in
`scripts/compose_prompts.py`.**

For each task in `tasks.json`, the script writes:
- `tasks/<feature>/prompts/task-NN-tests.md` — test-writing prompt.
- `tasks/<feature>/prompts/task-NN-impl.md` — implementation prompt.

Separate files (not one combined). Cleaner for hand-running through
Claude Code (paste one at a time, get one focused output). The
pipeline can consume both — running tests prompt first, implementation
prompt second.

Note: for `task_type: "test"` tasks in the current schema, the test
prompt is the only one needed (the impl prompt for the test task is
"write the stub"). For `task_type: "implementation"` tasks, the impl
prompt is the only one needed (the test prompt was the paired test
task). This is the current TDD-pair structure, just expressed in
prompt files instead of separate tasks.

A possible simplification: collapse the TDD-pair into one task with
two prompts (test prompt + impl prompt), eliminating the test/impl
task distinction in `tasks.json` entirely. Hold off on this until the
prompt-split itself validates — it's a bigger change to the
decomposition schema and worth its own iteration.

**Change 2: Inline scenarios with criticality framing in the
prompt.**

The current "Behaviors to Verify" section becomes structured by
criticality:

```markdown
## Behaviors to Verify

### Cliff edges (must hold — production breaks otherwise)
- <scenario name>
  - Given: ...
  - When: ...
  - Then: ...
  - Verification: <tool_invocation | unit_test | integration_test | static_assertion>

### Behavioral contract
- <scenario>
  - ...

### Prescribed (security/production additions not in prototype)
- <scenario>
  - ...
```

Each scenario carries its `verification` field as a hint for the test
executor (in the tests prompt) and as a reference for what the test
will be (in the impl prompt).

**Change 3: Test-writing prompt instruction set.**

The tests prompt's role block:

> You are writing tests for a component. The behaviors below describe
> what the implementation must do. For each behavior, write a test
> that verifies it. The verification field tells you what form the
> test takes:
>
> - `tool_invocation`: a script or pytest function that runs the named
>   tool and asserts on exit code or output pattern.
> - `unit_test`: a pytest function with mocks at the integration
>   boundary.
> - `integration_test`: a pytest function against real services
>   (no mocks).
> - `static_assertion`: a grep / regex / AST check against source.
>
> Cliff-edge behaviors are non-negotiable. Behavioral behaviors are
> the proven path. Prescribed behaviors are security/production
> additions. Tests must distinguish "tool ran, project is wrong" from
> "tool ran, project is right" — exit codes alone are not enough for
> all cases.

**Change 4: Implementation prompt instruction set.**

The impl prompt's role block:

> You are implementing the code that makes the tests below pass.
> Read the test file. Make every test pass without modifying the
> tests. Cliff-edge behaviors in the cited scenarios are
> non-negotiable — failing tests against cliff-edge behaviors must be
> fixed by changing the code, not the test. If a test cannot be made
> to pass without violating a security consideration or acceptance
> criterion, stop and report rather than relaxing the test.
>
> The prototype directory is a reference for working patterns and
> tooling. Use it as an example library — read files for working
> code and convention, but you are not required to mirror it
> file-for-file. Deviation is allowed where the tests permit it.

**Change 5: Regenerate the snapshot test fixtures at
`tests/expected/`.**

The current expected output is one prompt per task. The new expected
output is two prompts per task with the new structure. Regenerate
fixtures as part of validation step 8 below.

**Change 6: Update `references/preamble.md` and
`references/prompt-template.md`.**

Two separate preambles now (test rules vs impl rules) — split the
content from the current single preamble. Two templates instead of
one. `references/dependency-handling.md` and
`references/log-conventions.md` stay as-is — both apply to both
prompt types.

**No change to:**

- The deterministic-script principle (still a Python script, no
  chat-time rendering).
- The "dependencies referenced by path, not inlined" rule.
- The `## Previous Attempts` filesystem convention.
- The `--phase-1-only` confirmation flow.

### Implementation pipeline — not changing in this plan

The pipeline that consumes prompts and runs them will need to know
there are two prompts per task. That's a separate concern — sequence
it after the prompt structure is validated against Claude Code.

## Validation sequence (against the airflow project)

Each step is small enough to validate independently. If a step
produces noise, fix the upstream skill before continuing.

**Step 1: Update planning skill.** Cliff-edge labeling guidance in
the three reference docs. No regeneration of planning artifacts —
the airflow design doc gets a one-time hand-update in step 2.

**Step 2: Hand-update the airflow design doc.** Add `**Cliff edge:**`
labels to the existing observations that qualify. Concretely:

- Prototype Reference section: the `key_path=` / `scope=` paragraph.
- Tooling Notes: the `airflow-init` YAML block scalar entry; the
  connection URI field-name entry.
- Components > Project Setup > Production considerations: the "pip
  install runs as airflow user (not root)" entry.
- Components > Drive Downloader > Production considerations: the
  service account credentials path requirement.
- Components > MinIO Uploader > Production considerations: the
  `_upload_timestamp_utc` shared-capture pattern.

The hand-update is one-time. The planning skill update ensures
future runs produce these labels automatically.

**Step 3: Update roadmap skill.** Schema changes, validator coverage
check, generation guidance, format docs.

**Step 4: Run roadmap skill against updated airflow design doc.**
*First validation point.* Should produce scenarios with
`criticality: cliff_edge` for each labeled breadcrumb, scenarios
with `verification` fields for all entries, and pass validation
including the new cliff-edge coverage check.

If the produced roadmap is wrong: fix the roadmap skill, re-run. Do
not propagate noise downstream.

**Step 5: Update decomposition skill.** Drop
`FileChange.description`. Update task-writing guide. Update task
description template guidance.

**Step 6: Run decomposition skill against updated airflow roadmap.**
*Second validation point.* Should produce tasks without
`files[].description`, with citations to the new roadmap fields, and
pass schema validation.

If wrong: fix decomposition skill, re-run.

**Step 7: Update prompt-composition script.** Two-prompt split,
criticality-framed Behaviors section, separate test/impl preambles.

**Step 8: Run prompt-composition script against new tasks.json.**
*Third validation point.* Should produce paired
`task-NN-tests.md` and `task-NN-impl.md` for each task. Regenerate
snapshot fixtures.

If wrong: fix the script, re-run.

**Step 9: Hand-run task-01 prompts against Claude Code.** *The real
validation.*

- Clean `services/airflow-gdrive-ingestion/` before each run.
- Run `task-01-tests.md` first. Manually inspect produced tests.
  Does the test suite cover all scaffold cliff edges
  (`ruff-clean`, `docker-compose-config-valid`, etc.)? Are the
  verification forms reasonable (tool invocation for `ruff check`,
  not a unit test mocking ruff)?
- Run `task-01-impl.md` second. Manually inspect produced files.
  Does `tests/conftest.py` have both `sample_db_path` and
  `all_records`? Does `requirements.txt` have
  `apache-airflow[celery]==2.10.5`? Do all the scaffold cliff edges
  produced by the tests step pass?

If the new structure produces correct task-01 output: success
criterion met for this iteration.

If it doesn't: diagnose and adjust. The likely failure modes:

- Tests prompt produces wrong verification forms → tighten the
  verification-field guidance in the prompt instructions.
- Impl prompt drifts from prototype too far → strengthen the
  prototype-as-reference framing.
- Cliff-edge scenarios get dropped silently → strengthen the role
  block's "non-negotiable" language.

**Step 10: Retry task-01 against Pi+Qwen.** Confirm the new prompt
structure works for the tier-0 local model, not just Claude Code. If
Pi+Qwen produces correct output, the prompt structure is validated
across capability tiers.

**Step 11: End-to-end run from scratch.** Regenerate the airflow
project starting from the planning skill (with the cliff-edge
labeling change in place). This is the final validation — confirms
the full chain produces correct task-01 output from scratch, not
just from a hand-updated design doc.

## What we're not changing

These were considered and explicitly held off:

- **Planning consultation logic.** The breadcrumb-elicitation is
  already instructed and produces the right input. No consultation
  changes.
- **The prototype itself.** Reference artifact, immutable post-sign-off.
- **TDD pair structure in decomposition.** Already correct — test task
  produces tests + stub, implementation task fills the stub.
- **`test_command` field semantics.** The current shell-command form
  works for all task kinds.
- **OWASP machinery in the roadmap skill.** Categories, performed-by,
  ID parity all stay as-is.
- **The roadmap two-file split** (`components.json` + `roadmap.json`).
  Already validated.
- **Schema-shipped-to-project pattern.** Schemas continue to be copied
  into the project directory at generation time.
- **Combined "one task, two prompts" decomposition refactor.** Possible
  future simplification; out of scope for this iteration.
- **Implementation pipeline updates.** Sequenced after this iteration
  validates.

## Open questions to settle during drafting

These don't block writing the plan but will be decided as I write
each skill update:

1. **Cliff-edge label format.** Strictly `**Cliff edge:**` (markdown
   bold)? Or a more parseable format like `<!-- cliff-edge -->`? The
   bold form is human-readable; the comment form is mechanically
   robust. Probably the bold form unless the validator's pattern
   match proves fragile.

2. **Coverage check granularity.** Does the validator match one
   cliff-edge scenario per label, or many scenarios per label, or one
   label per scenario? Probably "at least one scenario per label,"
   with the validator listing labels that have no matching scenario.

3. **`verification` field on scaffold scenarios.** For scenarios like
   `all-services-healthy-after-compose-up`, the verification is
   `tool_invocation` but the tool is `docker compose up --wait`
   which has a real-services dependency. Is that still
   `tool_invocation`, or does it cross over into `integration_test`?
   Probably `tool_invocation` — the test form is "run the command,
   assert exit 0" regardless of whether real services are needed.
   `integration_test` reserved for pytest functions that exercise
   service interactions, not for shell commands that bring services
   up.

4. **Test-writing prompt's handling of `task_type: "test"` tasks.**
   The existing TDD pair has the test task produce tests + stub. In
   the new structure, `task-NN-tests.md` for a test task produces
   tests + stub (matching current behavior). `task-NN-impl.md` for a
   test task is empty / not generated — the test task has no
   implementation phase. For an implementation task, the reverse:
   `task-NN-impl.md` is the focus, `task-NN-tests.md` was already
   produced by the paired test task. Decide whether to generate
   empty prompts or skip generation per task type — probably skip,
   the file presence is the signal.

## Memory repo updates after this plan ships

After validation step 9 (task-01 against Claude Code) confirms the
new structure works, update:

- `README.md`: state shifts to "cliff-edge labeling + two-prompt
  split validated"; trial history adds T10 with the new structure's
  task-01 run.
- `LEARNINGS.md`: new entries about:
  - "Critical patterns are BDD scenarios; the roadmap is the right
    encoding layer."
  - "Cliff-edge labeling discipline — observations with specific
    failure-mode breadcrumbs get a structured label."
  - "Two-prompt split — test-writing and implementation as separate
    artifacts reduces interpretation ambiguity."
- `trials/T10-<slug>.md`: full trial record for the validation run.

If the validation run reveals the structure doesn't work, document
the failure mode and propose the next iteration. Don't ship the
skill changes upstream until the validation passes.

## What this session did not produce

- No skill files were modified this session. All discussion;
  changes start next session.
- No design-doc or roadmap edits to the airflow project. Those happen
  next session as part of validation step 2.
- No regenerated artifacts.

The plan is the artifact of this session. Next session executes it.
