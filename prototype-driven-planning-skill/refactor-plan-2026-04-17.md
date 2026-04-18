# Refactor Plan — Task Doc Tightening + JSON/MD Consolidation

> **Date:** 2026-04-17
> **Scope:** `prototype-driven-task-decomposition` skill, `prototype-driven-implementation` skill
> **Driver:** T13 findings confirmed tight prompts work; make those changes systematic at the skill level.
> **Criterion:** Least non-deterministic. Prefer cuts to additions; promote fields to the schema only when the pipeline mechanically uses them or their absence has caused a real bug.

---

## 1. What we're changing and why

Three problems this refactor addresses:

1. **JSON/MD redundancy at decomposition time.** The decomposition skill
   currently emits both `tasks.json` (source of truth) and
   `task-NN-<slug>.md` files (human-readable views). They must be kept in
   sync manually. Hand-edits to `.md` are silently ignored by the pipeline.
   The .md files are derivations, not sources.

2. **Task-doc format is freeform prose.** Current `task-writing-guide.md`
   gives the decomposer guidance ("describe the component, list behaviors,
   inline patterns if needed") but no fixed structure. Result: descriptions
   drift, internal contradictions accumulate (e.g., task-02 in the T10–T13
   arc: "keep the class instantiatable" + "every method raises
   NotImplementedError"). Tight templates with fixed fields eliminate this.

3. **`verify_task` can't distinguish correct partial stubs from leaked-logic
   stubs.** Components like `pydantic-settings.BaseSettings` are partial
   stubs (declarative parts real, one method stubbed). The hardcoded
   single-pattern check fails them when pytest `-x` ordering hides the
   `NotImplementedError`. A schema field `expected_test_failure_modes`
   drives the check correctly.

---

## 2. Changes by skill

### 2.1 Decomposition skill (`prototype-driven-task-decomposition`)

**Output shape:**

Before:
```
tasks/<feature-name>/
├── tasks.json
├── task_schema.py
├── task-01-<slug>.md   ← STOP EMITTING
├── task-02-<slug>.md
└── ...
```

After:
```
tasks/<feature-name>/
├── tasks.json
└── task_schema.py
```

**Reference doc updates (`references/output-format.md`):**
- Remove all guidance about generating `.md` files
- Remove the "JSON-Markdown Sync Warning" section (no longer applicable)
- Remove the "Interrupted Generation Recovery" MD-specific recovery logic
- Simplify the Output Structure section to just JSON + schema copy
- Keep the summary table print-to-conversation step (that's the human-review
  artifact at decomposition time)

**Reference doc updates (`references/task-writing-guide.md`):**
- Add a new section: **Task Description Template**
- The template specifies a required structure for every task's `description`
  field in the JSON (see §3 below)
- Remove any prose patterns that contradict the new template
- Keep the existing stub mock-import rule and output-field-contract rule
  (those are still correct and complementary)

**Schema update (`scripts/task_schema.py`):**
- Add `expected_test_failure_modes: list[str] = []` to the `Task` model
- Semantic: for test tasks with a stubbed behavior, list the exception types
  whose presence in pytest output indicates the stub is working correctly.
  For pure stubs, this is typically `["NotImplementedError"]`. For partial
  stubs, it may be `["NotImplementedError", "ValidationError"]` or similar.
- Default is empty list. Empty list means `verify_task` falls back to the
  current `STUB_ERROR_PATTERN` config value (backward compat).
- No validator needed \u2014 a test task's acceptance criterion naturally
  references these.

**SKILL.md:**
- Update the output description to match new output shape
- Reference the task description template

### 2.2 Implementation skill (`prototype-driven-implementation`)

**New responsibility:** render per-task `.md` files from `tasks.json` during
pipeline generation.

**Reference doc updates (`references/phase-2-generation.md`):**
- Add a new step in the pipeline-generation sequence: after copying
  templates and generating the three project-specific files, the skill
  reads `tasks/<feature>/tasks.json` and writes one `task-NN-<slug>.md`
  per task to the same directory
- Specify the MD template (see §4 below)
- Each generated MD starts with a comment:
  `<!-- Generated from tasks.json \u2014 edits will be overwritten on regeneration -->`

**Template updates (`templates/nodes/compose_prompt.py`):**

The four T13-validated changes baked in:

1. `_PROJECT_CONTEXT` is the tight system prompt \u2014 generic rules only.
   The exact content is project-parametrized (project name, service root,
   import convention substituted at generation time), but the structure is:
   - Role (you're implementing a component, another model finishes it)
   - Project skeleton (one short paragraph: language, framework, test runner)
   - Test writing rules (generic)
   - Stub writing rules (generic, including the declarative-interfaces
     carve-out)
   - Coding conventions (generic, language-agnostic at the top level;
     language-specific details come from the design doc's Tooling section
     at generation time)
   - Output format (terse, no preamble)
2. No `_STUB_RULES` / `_TEST_RULES` constants \u2014 rules live only in the
   system prompt
3. System prompt placed at top with `---` separator before the per-task
   content
4. `_inline_dependencies` filtered to Python-importable files only
   (`.py`, `.toml`, `.cfg`, `.ini` for Python; parameterize per language)

**Template updates (`templates/nodes/verify_task.py`):**

Wire the `expected_test_failure_modes` field into the test-task verification:

```python
# Pseudocode, not final code:
expected_patterns = task.get("expected_test_failure_modes") or [STUB_ERROR_PATTERN]
if any(p in test_output for p in expected_patterns):
    return "passed"  # stub confirmed
```

Backward compat: when the task has no `expected_test_failure_modes`
(i.e., it's empty list, the default), fall back to the single
`STUB_ERROR_PATTERN` check \u2014 identical to current behavior.

**SKILL.md:**
- Update Phase 2 to include MD rendering as an output
- Reference the new MD template

### 2.3 Pipeline runtime

**No changes.** The runtime reads `tasks.json` today and continues to.
The addition of one new schema field is backward-compatible (optional field
with default).

---

## 3. Task description template (in JSON `description` field)

This is the format the decomposer writes into each task's `description`
string in `tasks.json`. The template is prose with required section
headings; the decomposer fills each section.

The skill should package this as a **placeholder template file** in
`references/` (or inline in `task-writing-guide.md`) that the decomposing
model copies verbatim and fills in per task. Models are reliable at
following explicit fill-in-the-blank templates \u2014 more reliable than
\"write prose covering these topics.\"

```
Component: <Name> (<test task | implementation task>). <One-sentence
purpose: what this component does and who uses it>.

Component type: <declarative config | pure stub | partial stub | behavioral
logic | orchestrator | integration | scaffold | infrastructure>. <One
sentence explaining implications for stubbing \u2014 e.g., \"No business
logic to stub \u2014 the field declarations are the contract,\" or \"Pure
stub: every method raises NotImplementedError.\" This primes the model on
how to treat the component during stub generation.>

Interface:

    <Brief type signature or class skeleton, 5\u201315 lines. Include
    exact parameter names, return types, env var mappings (if relevant),
    and which methods are stubbed.>

Behaviors to test:
- <Behavior 1: given/when/then in one sentence>
- <Behavior 2>
- ...

Expected test failure mode: <Which specific exceptions should appear in
pytest output when tests run against the stub? Name them. Example:
\"Only the validate_required_fields test raises NotImplementedError;
required-field tests raise pydantic.ValidationError (real behavior, not
stubbed).\" For pure stubs: \"All tests raise NotImplementedError.\" For
pure-implementation components: \"N/A \u2014 tests already pass against
the prior task's test spec.\">

Out of scope: <Concerns explicitly NOT in this task. Example:
\"Computed properties, environment-specific loading (dotenv, secrets
backends), validation logic beyond Pydantic's built-in required-field
checks.\" This is a refusal-to-implement boundary, not a future-work list.>
```

### Section rules

- **Component** and **Component type** are always required.
- **Interface** is required for test tasks and implementation tasks; may be
  omitted for scaffold tasks.
- **Behaviors to test** is required for test tasks; informational for
  implementation tasks (what must continue to pass).
- **Expected test failure mode** is required for test tasks that include
  stubbed behaviors.
- **Out of scope** is optional but recommended. When omitted, the task's
  dependencies and file list implicitly scope the work.

### What the template is NOT

- It is not a replacement for `acceptance_criteria` \u2014 those remain
  structured in the schema (they're scannable checklists, naturally a list).
- It is not a replacement for `tests[]` \u2014 those remain structured in
  the schema (the pipeline reads them for prompt composition).
- It is not a replacement for `files[]` \u2014 those remain structured
  (the pipeline reads file paths and operations for executor invocation).
- The template lives inside `description` prose only. Other task fields are
  untouched.

### Section fidelity vs. prose flexibility

A deliberate choice: the sections are required headings, but content
within each section is prose the decomposer writes. Rationale: the
decomposer needs freedom to express component-specific nuance (pydantic
vs. dataclass vs. typed-dict config loaders all need slightly different
language), but the *structure* is fixed to prevent drift.

Enforcement is at review time (human eyeballs the task descriptions
before running the pipeline) and at render time (the implementation skill's
MD renderer \u2014 §4 \u2014 extracts sections for display; missing sections
render as empty and are visually obvious).

---

## 4. Implementation skill's MD renderer (template)

The implementation skill's pipeline-generation step renders one
`task-NN-<slug>.md` per task from `tasks.json`. The rendered output is the
authoritative human-review format.

```markdown
<!-- Generated from tasks.json \u2014 edits will be overwritten on regeneration -->

# Task NN: <Title>

**Type**: test | implementation
**Phase**: <phase>
**Depends on**: <comma-separated task IDs, or "none">

## Description

<description verbatim from tasks.json \u2014 the sectioned template fills in here>

## Files

| Path | Operation | Description |
|------|-----------|-------------|
| `<path>` | create/modify | <description> |

## Tests

<For test tasks: "Test cases to write:">
<For implementation tasks: "Existing tests that must pass:">

| Test | File | Type |
|------|------|------|
| <description> | `<test_file>` | unit/integration/e2e |

<or "No tests for this task." if empty>

## Expected Test Failure Modes

<If task has `expected_test_failure_modes`:>
Tests are expected to fail with one of: `NotImplementedError`, `<other>`.
This is correct TDD behavior against the stub.

<Otherwise: omit this section.>

## Acceptance Criteria

- <criterion 1>
- <criterion 2>

## Security Considerations

| Concern | Mitigation |
|---------|------------|
| <concern> | <mitigation> |

<or "No security considerations for this task." if empty>
```

### Renderer responsibilities

- Read `tasks.json` via the Pydantic schema
- For each task, format one MD file using the template above
- Write to `tasks/<feature>/task-NN-<slug>.md` (same location as current
  decomposition-skill output)
- Slug derived from title: lowercase, spaces \u2192 hyphens, 3\u20134 words max
  (same rule as current decomposition skill)

### Renderer simplicity

The renderer is a pure function: `(TaskDecomposition) \u2192 list[(path, content)]`.
~80 lines of Python, no external dependencies beyond what the pipeline
already uses. It belongs in the implementation skill's Phase 2 generation
step as either a shell-out to a small Python script or inline in the
generation guidance.

---

## 5. Consolidation question: source-of-truth clarity

After this refactor:

| Artifact | Written by | Read by | Source of truth? |
|----------|-----------|---------|------------------|
| `tasks.json` | Decomposition skill | Implementation skill (pipeline gen), pipeline runtime | **Yes** |
| `task_schema.py` | Decomposition skill (copy) | Pipeline runtime (schema validation) | N/A (code, not spec) |
| `task-NN-<slug>.md` | Implementation skill (pipeline gen) | Humans | No \u2014 derived |
| Pipeline code (generated) | Implementation skill | Runtime | N/A |

**Hand-edit workflow:** Humans edit `tasks.json` directly when they need to
adjust a decomposition. Next pipeline run regenerates `.md` views from the
updated JSON. If the `.md` files get out of sync (because pipeline
regeneration hasn't happened yet), the comment at the top of each MD warns
humans not to trust them as current.

**Why this beats the alternatives:**
- **vs. JSON as only output (no MDs):** Humans still get a readable view when
  they want one, because the pipeline generates it at pipeline-creation time.
- **vs. MD as source-of-truth with frontmatter:** No custom markdown+YAML
  loader. Pydantic validation of JSON is simple and battle-tested.
- **vs. CLI-rendered MDs on demand:** No separate tool to maintain. MDs are
  always available as part of the pipeline's output directory.

---

## 6. Migration / validation plan

**Step 1: Memory repo changes (this document + learnings + readme).** Done.

**Step 2: Decomposition skill changes.**

- Update `output-format.md` \u2014 drop MD generation guidance
- Update `task-writing-guide.md` \u2014 add task description template
- Update `scripts/task_schema.py` \u2014 add `expected_test_failure_modes`
- Update `SKILL.md` \u2014 reflect new output shape

Validate: regenerate `tasks/airflow-google-drive-ingestion/tasks.json` with
the updated decomposition skill. Inspect the output:
- [ ] No `.md` files emitted
- [ ] Every task's `description` follows the template (scan for section
  headers)
- [ ] Test tasks have non-empty `expected_test_failure_modes` where stubs
  are involved
- [ ] Pydantic schema validates

**Step 3: Implementation skill changes.**

- Update `templates/nodes/compose_prompt.py` \u2014 bake T13 changes
- Update `templates/nodes/verify_task.py` \u2014 wire
  `expected_test_failure_modes`
- Update `references/phase-2-generation.md` \u2014 add MD rendering step
- Update `SKILL.md` \u2014 reference new output responsibility

Validate: regenerate the pipeline for airflow-google-drive-ingestion using
the updated implementation skill. Inspect the output:
- [ ] `task-NN-<slug>.md` files written to `tasks/<feature>/`
- [ ] Each MD starts with the \"generated from tasks.json\" comment
- [ ] `compose_prompt.py` in the generated pipeline matches T13's validated
  version (diff against the T13 hand-edited file as ground truth)

**Step 4: End-to-end trial run (T14).**

Run the pipeline on airflow-google-drive-ingestion. Acceptance bar:
- At least match T13's test-task outcomes (all 3 test tasks pass Gemini
  tier 0 retry 0)
- task-02 degraded-due-to-lint-glitch is acceptable if the actual test
  outcome is passing (transient and not caused by this refactor)
- task-05 and task-07 expected to still fail without additional intervention
  \u2014 those are test over-specification and fixture path bugs, out of
  scope for this refactor

If T14 regresses test-task outcomes vs. T13, stop and investigate before
committing skill changes.

**Step 5: Commit.** User commits both `~/claude-devtools` and
`~/claude-project-memory` locally per project convention:

```
cd ~/claude-devtools && git add -A && git commit -m \"skills: tight task-doc template, JSON/MD consolidation, verify_task expected_failure_modes\" && git push
cd ~/claude-project-memory && git add -A && git commit -m \"trials: T10\u2013T13 arc + refactor plan\" && git push
```

---

## 7. Out of scope for this refactor

These were raised during the T13 review but are deferred:

- **Test over-specification guardrails** (task-05 class of bug, T13).
  Would need either a post-test-writing verifier that checks tests don't
  assert on details absent from the spec, or explicit \"Tests may assert
  on these and only these behaviors\" constraint in test-task specs. Either
  is a separate refactor; neither is needed to validate that tight templates
  work.

- **Fixture path grounding** (task-07 class of bug, T13). The conftest
  fixture path computation assumes a specific project layout. This is a
  test-writing quality issue that likely improves with real-symbol grounding
  (Red Hat harness article's suggestion), but that's a larger addition.

- **Repository impact map artifact.** The Red Hat article advocates a
  separate impact-map artifact between planning and decomposition, with
  a human checkpoint. Our current flow has the human checkpoint at
  `tasks.json` review, which is more detailed but less scannable. A
  separate impact-map step would help catch decomposition-shape errors
  (like T10's parser split-across-tasks-with-shared-test-file bug), but
  it's a larger change than this refactor.

- **Moving conventions into the repo (CLAUDE.md).** Out of scope; the
  prototype already serves this purpose for our projects.

These are real issues. They're parked here so they don't get lost, but
pursuing them should wait until the current refactor's T14 validates.

---

## 8. Open questions (resolve before executing Step 2)

None blocking.

The only design question I surfaced during the plan \u2014 whether
`expected_test_failure_modes` should be an optional-with-default field or
required for test tasks \u2014 is resolved as **optional with default empty
list**. Reasons:

- Not every test task has stubbed behaviors. Pure-implementation tasks
  have test tasks that test real behavior; those tasks have no stub to
  raise an error against.
- Default empty list + backward-compat fallback to `STUB_ERROR_PATTERN`
  means existing `tasks.json` files validated under the new schema without
  modification.
- The decomposer populates the field when it's relevant (test task with
  stubbed behavior); the absence for other task types is meaningful.

---

## 9. Summary

- Cut the JSON/MD redundancy by moving MD rendering to the implementation
  skill; the decomposition skill's sole output becomes `tasks.json` +
  `task_schema.py`.
- Codify the tight task-doc template the T13 experiment validated, as a
  fill-in-the-blank template the decomposer follows per task.
- Add one schema field (`expected_test_failure_modes`) to fix the one
  pipeline-level bug that prose couldn't close (T12 partial-stub rejection).
- Bake the T13-validated `compose_prompt.py` changes into the implementation
  skill's templates so every generated pipeline benefits.

The refactor is net-reductive: two fewer artifacts emitted by the
decomposition skill (MD files, MD-generation recovery logic); two
constants removed from `compose_prompt.py`; one schema field added where
the pipeline mechanically uses it. Nothing added for aesthetics.
