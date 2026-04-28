# Plan — Refactor `prototype-driven-task-decomposition` to Consume the Roadmap

> **Status:** Proposal. Implementation paused 2026-04-27 mid-design when an
> upstream omission surfaced (see "Sequencing update" below). Pick up from
> this file in a fresh session after P05 and R03 have validated the upstream
> work. Re-read the current state pointers in §1 before touching any skill
> file.
>
> **Created:** 2026-04-26 (after R02 validated the roadmap-skill fixes from R01).
>
> **Sequencing:** Originally "after R02 cleanup, before T15." Updated
> 2026-04-27 to "after P05 (planning-skill project-setup component
> validates) and R03 (roadmap re-runs against the amended design doc with
> project-setup as a registered component)." The §9.1 awkwardness that
> blocked clean implementation is resolved by that upstream work — see
> `planning-project-setup-component-plan-2026-04-27.md`. Acceptance trial
> for this refactor remains "D01" — see §10.

---

## Sequencing update (2026-04-27)

This plan was paused 2026-04-27 when implementing it surfaced an upstream
omission. The required `roadmap_component` field on every task forced
scaffold tasks to declare a component, but the existing roadmap had no
scaffold component to reference. Three options for handling that:
special-case scaffold in the schema validator (virtual slug), allow
`roadmap_component: null`, or fix the omission upstream.

The upstream fix landed instead. The planning skill now requires a
project-setup decision (greenfield vs extending) at Phase 1 and emits a
Project Setup component as the first entry in `### Components` for
greenfield features. See
`planning-project-setup-component-plan-2026-04-27.md` for the full plan
and rationale.

After that lands and is validated:

- **P05** — re-run planning skill on the airflow-gdrive feature (or
  amend the existing design doc) so the design doc gains a Project
  Setup component.
- **R03** — re-run the roadmap skill against the amended design doc.
  `components.yml` gains a `project-setup` entry; a new
  `project-setup.md` file is generated.
- **Then resume this plan.** The §9.1 awkwardness is resolved (no
  special cases needed); §4.1's `roadmap_component` field validates
  cleanly against the registry like any other slug. The body below is
  unchanged from the 2026-04-26 draft except for the targeted notes
  marked "2026-04-27 update" in §4.1, §7.3, and the R02 reference
  list, which reflect the new sequence.

---

## 1. Where to read in (do this first)

A fresh session must load these before proposing edits. The constraints they
encode are non-obvious — skipping them produces an incoherent refactor.

**Memory repo (always loaded at session start by project instructions):**

- `~/claude-project-memory/prototype-driven-planning-skill/README.md`
- `~/claude-project-memory/prototype-driven-planning-skill/LEARNINGS.md`
- `~/claude-project-memory/prototype-driven-planning-skill/trials/_SUMMARY.md`

**Memory repo (load on demand for this work):**

- `~/claude-project-memory/prototype-driven-planning-skill/trials/R01-roadmap-id-parity-and-actor-misplacement.md`
- `~/claude-project-memory/prototype-driven-planning-skill/trials/T14-test-command-gap.md`
  (the prose-as-lossy-transport pattern this refactor needs to avoid
  recreating)
- `~/claude-project-memory/prototype-driven-planning-skill/planning-project-setup-component-plan-2026-04-27.md`
  (the upstream work that resolves §9.1)

**Decomposition skill — full file reads required:**

- `~/claude-devtools/skills/prototype-driven-task-decomposition/SKILL.md`
- `~/claude-devtools/skills/prototype-driven-task-decomposition/references/analysis-guide.md`
- `~/claude-devtools/skills/prototype-driven-task-decomposition/references/task-writing-guide.md`
- `~/claude-devtools/skills/prototype-driven-task-decomposition/references/output-format.md`
- `~/claude-devtools/skills/prototype-driven-task-decomposition/scripts/task_schema.py`

**Roadmap skill — read for downstream contract:**

- `~/claude-devtools/skills/prototype-driven-roadmap/SKILL.md`
- `~/claude-devtools/skills/prototype-driven-roadmap/references/components-yml-format.md`
- `~/claude-devtools/skills/prototype-driven-roadmap/references/roadmap-item-template.md`
- `~/claude-devtools/skills/prototype-driven-roadmap/scripts/validate_roadmap.py`

**Roadmap output (treat as canonical example of what input now looks like):**

- `~/health-data-ai-platform/docs/roadmap/airflow-gdrive-ingestion/components.yml`
- `~/health-data-ai-platform/docs/roadmap/airflow-gdrive-ingestion/project-setup.md`
  (added by R03 after the project-setup work; file present once R03 has run)
- `~/health-data-ai-platform/docs/roadmap/airflow-gdrive-ingestion/drive-downloader.md`
- `~/health-data-ai-platform/docs/roadmap/airflow-gdrive-ingestion/sqlite-parser.md`
- `~/health-data-ai-platform/docs/roadmap/airflow-gdrive-ingestion/amqp-publisher.md`
- `~/health-data-ai-platform/docs/roadmap/airflow-gdrive-ingestion/airflow-dag.md`

**Design doc (still relevant — supplementary input):**

- `~/health-data-ai-platform/docs/design/airflow-gdrive-ingestion-<P05-date>.md`
  (or the existing `airflow-gdrive-ingestion-2026-04-24.md` amended in
  place — the P05 trial's output)

---

## 2. Why this refactor

The decomposition skill currently reads the design doc + prototype directly.
The roadmap skill now sits between planning and decomposition and produces
strictly better-shaped input for what the decomposer needs:

| What decomposition needs | Where it lives today | Where it should live after refactor |
|---|---|---|
| Component boundaries | Inferred from design doc Architecture Overview prose | `components.yml` registry (authoritative slug + name + deps + OWASP cats) |
| Per-component dependency graph | Inferred from design doc + prototype reading | `components.yml` `depends_on` (validated, acyclic, slug-based) |
| Testable behaviors per component | Inferred from design doc + prototype | `## Functional Scenarios` Gherkin per roadmap file (named, given/when/then/verified-by) |
| Security concerns per component | Inferred from design doc Security Posture prose | `## Security Scenarios` Gherkin per roadmap file (OWASP-cited, Performed-by-grounded) |
| Out-of-scope boundaries per component | Inferred or omitted | `## Out of Scope` per roadmap file (explicit) |
| Cross-cutting tooling/data-model | Design doc | Design doc (unchanged — roadmap doesn't replace this) |

The refactor's purpose is to stop reinventing component identification,
dependency mapping, and behavior enumeration when the roadmap skill already
produced authoritative answers. Two specific failure classes the refactor
prevents:

- **Component-boundary drift between roadmap and decomposition.** If the
  decomposer re-derives boundaries from the design doc, it can land on a
  different set than the roadmap (different splits, different names,
  different deps). Downstream artifacts that reference the roadmap (security
  scenarios, Performed-by slugs) then disagree with task-level component
  boundaries silently.
- **Behavior loss in translation.** Gherkin scenarios with named verifiers
  are *more* specific than the prose the decomposer would otherwise paraphrase
  from the design doc. Letting tasks cite scenarios by name keeps that
  specificity end-to-end.

---

## 3. The design question that shapes everything

Three credible options for the design-doc / roadmap split. **Decision
already made: option 3 (roadmap-augmented).** Recording the alternatives so
the rationale survives.

**Option 1 — Roadmap-only.** Decomposition reads only `components.yml` +
per-component roadmap files. Anything the decomposer needs that's not in the
roadmap gets added to the roadmap.

*Rejected because:* Data Model, Tooling, cross-cutting Deferred Decisions,
Containerization, and Deployment Strategy don't have a natural per-component
home and shouldn't get duplicated. Pushing them into the roadmap would turn
the roadmap into a duplicate of the design doc.

**Option 2 — Roadmap-primary, design-doc-supplementary.** Decomposition reads
the roadmap as the source of truth for component boundaries, scenarios, and
dependencies, and reads the design doc only for cross-cutting sections. The
decomposer never re-derives component boundaries from the design doc.

*Acceptable as a first step.* Strictly less invasive than option 3 because
it doesn't change the schema. Could be the landing point if option 3 hits
schema-design problems mid-implementation.

**Option 3 — Roadmap-augmented (chosen).** Same as option 2, plus a stronger
contract: each generated task explicitly cites the roadmap component slug
it belongs to. This makes the task → component mapping a first-class field
in the schema, which sets up "per-component decomposition" as a future
possibility (decompose component-by-component rather than feature-as-a-whole).

*Why option 3:* It's the option that matches the planning-skill arc's
recurring shape — *force the model's reasoning into a visible, machine-checkable
artifact*. A `roadmap_component` field on every task forces the decomposer to
commit to which component the task belongs to; the validator checks the slug
exists in `components.yml`. Without this, "this task implements scenario X
from the parser file" is implicit in prose; with it, it's machine-checkable.

---

## 4. Schema changes

Each schema change earns its place by closing a specific failure class. None
are speculative — they trace back to the design questions §3 settled or to
fragilities the roadmap has structural answers for.

### 4.1 New required field: `roadmap_component: str` on every task

```python
roadmap_component: str = Field(
    description="The slug of the roadmap component this task belongs to. "
                "Must match a slug in components.yml. The decomposer asserts "
                "task → component membership; the validator confirms the "
                "slug is registered."
)
```

Validators added:

- **`validate_roadmap_component_non_empty`** (per-task `model_validator`).
  Reject empty/whitespace.
- **`validate_roadmap_component_registered`** (decomposition-level
  `model_validator`). Load `components.yml` (path given by a new top-level
  `components_yml_path` field on `TaskDecomposition`) and verify every
  task's `roadmap_component` slug appears in the registry. Closes the typo
  class and the "task references a deleted component" class.

**Why required, not optional.** An optional field lets the decomposer skip
it on tasks where component membership feels unclear (scaffold, infra),
which defeats the purpose. Every task belongs to a component — even
infrastructure tasks belong to the component whose Dockerfile or compose
file they're producing. If a task genuinely doesn't belong to any
component, the decomposition is wrong; either the component is missing from
the roadmap or the task should be split.

**Edge case: scaffold tasks that touch multiple components — RESOLVED
UPSTREAM (2026-04-27 update).** This was originally listed as an
unresolved awkwardness with three escalation options. The upstream
project-setup work (see
`planning-project-setup-component-plan-2026-04-27.md`) made `project-setup`
a real registered slug in `components.yml` for greenfield features.
Scaffold tasks now use `roadmap_component: "project-setup"` and validate
cleanly against the registry like any other slug. No special-case logic
in the schema.

For features that extend an existing service (no Project Setup
component), scaffold tasks don't exist — the project's setup is already
in place. The decomposer doesn't generate them and the question doesn't
arise.

The earlier escalation options (virtual `scaffold` slug, list-typed
`roadmap_component`, `null` allowance) are no longer needed and should
be deleted from any draft schema work that started before 2026-04-27.

### 4.2 New optional field: `roadmap_scenarios: list[str]` on tasks with tests

```python
roadmap_scenarios: list[str] = Field(
    default_factory=list,
    description="Names of `### Scenario:` blocks in the matching roadmap "
                "file that this task is responsible for. The decomposer "
                "asserts which scenarios become tests; the validator "
                "confirms each name appears in the roadmap file. Empty "
                "for non-test, non-implementation-with-tests tasks "
                "(scaffold, wiring, infra)."
)
```

Validator added:

- **`validate_roadmap_scenarios_exist`** (decomposition-level). Parse the
  per-component roadmap markdown file (`docs/roadmap/<feature>/<slug>.md`),
  extract `### Scenario:` headings, and confirm every entry in
  `roadmap_scenarios` matches one. Implementation: reuse the
  `extract_scenarios` function from the roadmap skill's
  `validate_roadmap.py` — but rather than coupling the two skills via
  cross-imports, copy the parser logic into the decomposition skill's
  `task_schema.py`. The two parsers can drift independently if either
  skill changes its format; mismatches surface as validator errors.

**Why a list, not a single scenario.** A test task often covers multiple
related scenarios at once (one fixture, multiple `def test_*` functions
referencing different scenarios). A 1:1 task↔scenario field would force
splitting that don't add value.

**Why optional, not required.** Scaffold/wiring/infra tasks legitimately
have no scenarios. The validator's expectation: empty list for those
task types; non-empty for test tasks and implementation tasks with tests.
Codified as:

- **`validate_roadmap_scenarios_required_for_test_tasks`** (per-task).
  Test tasks must have non-empty `roadmap_scenarios`. Implementation tasks
  with tests must have non-empty `roadmap_scenarios` (it's the same list as
  the paired test task's). Implementation tasks without tests, scaffold,
  wiring, and infra must have empty `roadmap_scenarios`.

### 4.3 New optional field: `security_scenario_ids: list[str]` on implementation tasks

```python
security_scenario_ids: list[str] = Field(
    default_factory=list,
    description="OWASP IDs (e.g., 'ASVS V5.1.3') from the matching "
                "roadmap file's ## Security Scenarios that this task "
                "implements. Replaces freeform security_considerations "
                "for concerns that are already articulated in the roadmap. "
                "The decomposer cites by ID; the validator confirms each "
                "ID appears in the matching components.yml entry's "
                "owasp_categories."
)
```

Relationship to existing `security_considerations`:

- `security_scenario_ids` covers concerns the roadmap already articulated
  (data-flow-scoped, OWASP-cited, Performed-by-grounded).
- `security_considerations` (existing freeform field) covers task-specific
  concerns the roadmap didn't surface (e.g., a specific library version's
  CVE, an implementation-detail concern that emerged during decomposition).
- They coexist. Most concerns shift to `security_scenario_ids`; the freeform
  field stays as the escape hatch.

Validator added:

- **`validate_security_scenario_ids_match_registry`** (decomposition-level).
  For each task with `security_scenario_ids`, look up its
  `roadmap_component`'s entry in `components.yml`, and confirm every cited
  ID appears in that entry's `owasp_categories`. Closes the "task cites
  V9.2.1 but the component's roadmap entry doesn't list it" drift class —
  same shape as the roadmap skill's check 17 (ID-set parity).

**Why optional and ID-based, not full scenario references.** The roadmap's
security scenarios already have authoritative content; the task doesn't need
to restate it. Citing by ID gives the implementing model a stable lookup key
into the roadmap file and avoids prose duplication. Could promote to
`security_scenarios: list[str]` (by name, like the functional scenarios
field) if the test against R02-shaped output shows ID-only references
losing too much specificity for the implementer.

### 4.4 New top-level field on `TaskDecomposition`: `components_yml_path: str`

```python
components_yml_path: str = Field(
    description="Path to the components.yml registry produced by the "
                "roadmap skill (e.g., 'docs/roadmap/<feature>/components.yml'). "
                "The validator loads this to confirm task roadmap_component "
                "slugs are registered."
)
```

Required, no default. The decomposer must explicitly state where the registry
is. Validator confirms the file exists and parses cleanly (reuse the
roadmap skill's load logic, but copy don't import — same rationale as §4.2).

### 4.5 Renamed/clarified: `prototype_references` (already removed) stays gone

The skill already removed `prototype_references` (per memory `From Implementation
Skill` learnings: "removed prototype_references — task descriptions are sole
source of truth"). This refactor does not reintroduce it. The roadmap's
`## Prototype evidence` section is the new home for prototype-pattern callouts;
the task description still inlines exact patterns the implementing model
needs.

---

## 5. Phase-by-phase changes

### 5.1 Phase 1 — Analysis

**Inputs change.** Today the skill reads design doc + prototype. After the
refactor it reads:

- `docs/roadmap/<feature>/components.yml` — authoritative component
  registry. **Required input.** Skill stops with a clear error if missing.
- `docs/roadmap/<feature>/<slug>.md` for each component — authoritative
  scenarios, deps, out-of-scope per component. **Required.**
- `docs/design/<feature>-<date>.md` — for cross-cutting sections only:
  Data Model, Tooling, Containerization, Deployment Strategy, cross-cutting
  Deferred Decisions, Security Posture (cross-cutting policies). **Required.**
- `prototypes/<feature>/` — same as today. The decomposer still inventories
  the prototype to extract inline patterns for task descriptions. **Required.**

**Component identification becomes a registry read, not an inference.** The
old "Identify component boundaries" step from `analysis-guide.md` becomes
"Load `components.yml` and confirm component count, slugs, and dep graph
match the per-file presence check." The decomposer does not propose its own
boundaries; if the registry's component set is wrong, the user fixes the
roadmap and re-runs decomposition.

**Behavior enumeration becomes a scenario read.** For each component, parse
its roadmap file's `## Functional Scenarios` and `## Security Scenarios`.
These become the seed list for what tests the test task will write and
which security concerns the implementation task addresses.

**The decomposer's freedom is now scoped.** It still decides:

- Whether each component splits into multiple tasks (still using the §
  Task Sizing thresholds — cyclomatic complexity, line counts, fan-out)
- The TDD pair structure (which test task pairs with which implementation
  task)
- Which inline patterns to extract from the prototype
- The exact `test_command` shell invocation per task
- Field-name contracts at task boundaries (still needed — `components.yml`
  doesn't capture data-flow field names)
- Open questions that aren't answerable from the roadmap (e.g., "split this
  large parser into 2 tasks or 3?")

**The Phase 1 proposal message changes.** The numbered-questions pattern
stays, but the "proposed component breakdown" section becomes "component
registry as loaded from `components.yml`" with the slugs, names, and deps
shown back to the user verbatim. The user has nothing to approve about the
boundaries themselves — they're already approved. The user reviews:

- Per-component task count proposal (1 task? 2 tasks? a TDD pair?)
- Phase assignments per task
- Open questions specific to decomposition (not architecture)

### 5.2 Phase 2 — Task Generation

**Each task gets `roadmap_component` set.** The decomposer assigns this
based on which component the task implements. The validator catches typos
against `components.yml`.

**Test tasks and implementation-with-tests tasks get `roadmap_scenarios` set.**
List the named scenarios from the matching roadmap file that this task is
responsible for. Most tasks will list 2–5 scenarios; a "happy path" test
task might list every functional scenario from one component, while a
"security tests" test task might list the security scenarios.

**Implementation tasks with security concerns get `security_scenario_ids` set.**
Cite the OWASP IDs from the matching roadmap file. The freeform
`security_considerations` field stays as the escape hatch for task-specific
concerns.

**Task descriptions reference the roadmap, not just the design doc.** The
existing rule "task descriptions are self-contained" stays, but the
description's `Behaviors to test:` section can now name the roadmap scenarios
it implements. Example:

```
Behaviors to test:
- "Locates Health Connect.zip by exact name in Google Drive"
  (drive-downloader.md § Functional Scenarios)
- "Streams ZIP file to local temp directory using MediaIoBaseDownload"
  (drive-downloader.md § Functional Scenarios)
```

The implementing model still doesn't read the roadmap directly (per the
self-containment rule) — the decomposer extracts the relevant Given/When/Then
text into the task description's prose. The roadmap citation is for the
human reviewer's benefit. The validator only checks the structured field
(`roadmap_scenarios`), not the prose.

### 5.3 Phase 3 — Validation and Output

**`tasks/<feature>/` directory still gets `tasks.json` + `task_schema.py`.**
That hasn't changed.

**The validator now needs `components.yml` available at validation time.**
The validation script loads the registry and parses the per-component
roadmap markdown files. Two implementation choices:

- **Embed the parsing logic in `task_schema.py`.** The validator stays
  self-contained; the decomposition output directory still has everything
  it needs.
- **Reference roadmap files by path; assume they exist.** Lighter coupling
  but creates a runtime dependency on the roadmap directory not having moved.

**Choice as drafted: embed.** Reuse the planning skill's pattern of "the
validator is self-contained." The schema file copies the necessary
roadmap-parsing helpers from `validate_roadmap.py`. Validators run against
`components_yml_path` resolving to a real file (validator errors out with
exit code 2 if missing — same pattern as the roadmap skill's precondition).

> **2026-04-27 review note:** This embed-vs-import choice is being
> revisited as part of the resumed work. The user expressed a strong
> preference for single-source-of-truth over copied-parser duplication
> when this plan was reviewed in the project-setup-work session. The
> alternative on the table is a separate `scripts/validate_decomposition.py`
> that imports the roadmap skill's parser by path (mirroring the roadmap
> skill's own `scripts/validate_roadmap.py` pattern), with Phase 3
> running both validators in sequence — Pydantic schema for shape and
> per-task rules, validator script for cross-skill registry checks.
>
> The case for the script approach: `task_schema.py` stays Pydantic-only
> (no I/O, no parsing) and matches the roadmap skill's structure. The
> pipeline still imports just the schema; cross-file validation runs at
> decomposition time, not pipeline time.
>
> The case for embedding (as originally drafted): self-containment of the
> output directory; no cross-skill path dependency at validation time.
>
> Settle this question before writing code. Update §7.3, §11 step 1, and
> any references in §6.3/§6.4 once the decision is made.

**Summary table gets new columns.** `Roadmap Component` and `Scenarios` are
useful to a reviewer scanning whether each task is doing what its component
expects. Drop the existing `Files` count column to make room (file count is
visible in the JSON for reviewers who care).

| ID | Title | Type | Phase | Component | Scenarios | Test Command |
|---|---|---|---|---|---|---|

---

## 6. Reference doc updates

Each existing reference doc gets a targeted edit. Listed concretely so a
fresh session can do them in order.

### 6.1 `analysis-guide.md`

- **Replace** "Reading the Design Doc" section with "Reading the Roadmap"
  as the primary subsection; demote the design doc to a supplementary
  subsection for cross-cutting concerns only.
- **Replace** "Identifying Component Boundaries" with "Loading the
  Component Registry" — the decomposer no longer infers boundaries; it
  reads them.
- **Update** "Mapping Dependencies" — the dep graph already exists in
  `components.yml`. The decomposer walks it but doesn't construct it.
  Interface dependencies between *task A and task B within the same
  component* are still the decomposer's responsibility; cross-component
  deps are pre-computed.
- **Add** a "Reading per-component roadmap files" subsection that
  documents the parse: frontmatter (skip — already validated), Purpose
  (informs task description), Prototype evidence (informs which prototype
  files to inline patterns from), Functional Scenarios (seed for tests),
  Security Scenarios (seed for security concerns), Out of Scope (refusal
  boundaries that flow to task descriptions).
- **Update** the proposal-message format: the "Phase Breakdown" stays;
  the "Dependency Graph" stays (now derived from the registry); add a
  "Component → tasks mapping" subsection showing which tasks belong to
  which component.

### 6.2 `task-writing-guide.md`

- **Add** a new section "Roadmap-Driven Task Authoring" near the top,
  before "The Self-Containment Rule", explaining that scenarios come from
  the roadmap and how `roadmap_component` / `roadmap_scenarios` /
  `security_scenario_ids` work in practice.
- **Update** "Task Description Template" — the `Behaviors to test:`
  section now expects each behavior to cite a roadmap scenario name where
  one exists. Add an example of that style.
- **Update** "Writing Security Considerations" — most concerns now move
  to `security_scenario_ids`. The freeform field stays for
  decomposition-specific concerns. Add an example showing both.
- **Update** the example TDD pair to include `roadmap_component`,
  `roadmap_scenarios`, and (on the implementation task)
  `security_scenario_ids`.
- **Keep** Task Sizing rules as-is. The roadmap doesn't change cyclomatic
  complexity, line counts, or fan-out.
- **Keep** `test_command` rules as-is. The roadmap doesn't change test
  command derivation.

### 6.3 `output-format.md`

- **Update** the summary table example to include the new columns
  (Component, Scenarios, drop Files).
- **Update** the validation checklist (currently 12 items) to add:
  - 13. Every task's `roadmap_component` matches a slug in
    `components.yml`.
  - 14. Every test task and every implementation task with tests has
    non-empty `roadmap_scenarios`, and every entry matches a `### Scenario:`
    heading in the matching component's roadmap file.
  - 15. Every implementation task's `security_scenario_ids` (if non-empty)
    contains only OWASP IDs that appear in the matching component's
    `owasp_categories` in `components.yml`.
- **Update** the JSON example to include the new fields on at least one
  task per type.
- **Add** a brief "Integration with the Roadmap" subsection explaining the
  read-only relationship: decomposition consumes the roadmap; it never
  modifies `components.yml` or per-component files.

### 6.4 `SKILL.md`

- **Update** the "Quick Reference" table: input now includes the roadmap
  directory.
- **Update** "How to Start" to confirm both the roadmap directory and the
  design doc exist before proceeding.
- **Update** Phase 1 step 1 to read the roadmap first; demote design-doc
  reading to step 2 with explicit scoping (cross-cutting sections only).
- **Update** Phase 1 step 3 ("Identify component boundaries") to "Load
  `components.yml` and confirm registry presence."
- **Add** a Principle: "Component boundaries come from the roadmap."
- **Add** a Principle: "Tasks cite roadmap scenarios they implement; the
  validator confirms the citations resolve."
- **Update** the schema reference table to include the three new task
  fields and the new top-level field.

---

## 7. Validator implementation notes

### 7.1 Parsing the roadmap files from the schema

The schema validator needs `components.yml` plus per-component markdown.
Implementation choices:

- **YAML loading.** `pyyaml` (already a dependency for the schema). Single
  document; reject if multiple via `yaml.safe_load_all`.
- **Markdown scenario extraction.** Reuse the regex + state-machine from
  `validate_roadmap.py`'s `extract_scenarios`. Don't import; copy. The
  parsers can drift independently; mismatches surface as validator errors,
  which is the desired behavior.
- **Path resolution.** All paths in `components.yml` and `tasks.json` are
  project-relative. The validator resolves them against the current working
  directory (the decomposition skill assumes invocation from project root,
  same as the roadmap skill).

### 7.2 Error message tone

Match the existing schema's error tone: name the field, name the failing
value, suggest the fix. Example:

```
Task 'task-04' has roadmap_component='drive-loader' but no slug
'drive-loader' is registered in docs/roadmap/airflow-gdrive-ingestion/components.yml.
Did you mean 'drive-downloader'?
```

The "Did you mean" hint can use a simple Levenshtein nearest-neighbor
against registered slugs; nice-to-have, not required for D01.

### 7.3 Coupling between the two parsers

The decomposition skill's schema embeds a copy of the roadmap-file parser.
This is deliberate. Two reasons:

- **Decoupling skill versions.** The decomposition skill must work even if
  the roadmap skill's `validate_roadmap.py` evolves. Embedding the parser
  pins the format-as-of-refactor-time.
- **Self-containment of the output directory.** The pipeline imports
  `tasks/<feature>/task_schema.py` to validate task payloads at runtime.
  Cross-skill imports would force the pipeline to also know where the
  roadmap skill lives.

If the roadmap file format changes substantially, both copies of the parser
get updated. This is a known cost; it's smaller than the cost of cross-skill
import coupling.

> **2026-04-27 review note:** See the review note at the end of §5.3 above.
> The user has questioned the embed choice on single-source-of-truth
> grounds and surfaced an alternative (separate
> `scripts/validate_decomposition.py` paralleling the roadmap skill's
> `validate_roadmap.py`, with Phase 3 running both validators in
> sequence). Counter-argument from this section's original draft:
> embedding keeps `task_schema.py` self-contained for pipeline runtime
> import. Counter-counter-argument: the pipeline only ever needs the
> Pydantic schema for runtime validation, never the cross-skill registry
> checks — so a separate validator script doesn't increase pipeline
> coupling.
>
> Resolve before §11 step 1. Update this section, §5.3, §6.3, and §6.4
> consistently with the chosen approach.

---

## 8. Migration of existing decomposition output

The existing `tasks/airflow-google-drive-ingestion/tasks.json` (from T14)
will fail validation under the new schema (missing `roadmap_component`,
`roadmap_scenarios`, `components_yml_path`).

**Decision: do not migrate. Regenerate.** Same pattern as the test_command
field landing in the T14 refactor — the existing JSON was deliberately
broken by the schema change to force regeneration. The next pipeline trial
(T15 or D02) regenerates `tasks.json` from scratch under the new schema.

The R02 roadmap output is fresh and uncommitted-to-tasks-json; the path
forward is:

1. R02 roadmap output committed (already done outside this plan).
2. R03 (after the project-setup work) regenerates the roadmap with a
   `project-setup` component included. R03 output is the canonical input
   for D01.
3. This refactor lands.
4. D01 regenerates tasks against the new schema.

---

## 9. Risks and how to handle them

### 9.1 Risk: roadmap-component placement awkward for cross-cutting tasks — RESOLVED UPSTREAM

**Status:** Resolved 2026-04-27 by upstream project-setup work. Original
content preserved below for context; no action needed in this refactor
except to delete any draft schema work (virtual slugs, list-typed fields,
null allowance) that started before the resolution.

**Original symptom:** A scaffold task touches files that span every
component (top-level `pyproject.toml`, project-wide `__init__.py`,
top-level Dockerfile). Forcing a single `roadmap_component` slug feels
arbitrary.

**Resolution:** The planning skill now requires a project-setup decision
(greenfield vs extending) at Phase 1. When greenfield, the design doc's
`### Components` section includes a Project Setup component as the first
entry; the roadmap skill picks it up like any other component and writes
a `project-setup.md` file. Scaffold tasks reference
`roadmap_component: "project-setup"` and the validator confirms
registration like any other slug. No special-case logic in the schema.

For features that extend an existing service, scaffold tasks don't exist
(the project is already set up); the decomposer doesn't generate them.

The original mitigation listed three escalation options (virtual
`scaffold` slug, list-typed `roadmap_component`, null allowance). All
three are unnecessary now and should not appear in any draft schema.
See `planning-project-setup-component-plan-2026-04-27.md` for the full
upstream rationale.

### 9.2 Risk: `roadmap_scenarios` becomes prose duplication

**Symptom:** The decomposer cites scenario names but ALSO copies the
Given/When/Then text into the task description's `Behaviors to test:`
section. Now the same content exists in two places and can drift.

**Mitigation:** This is acceptable, even desirable. The roadmap is the
human-reviewable source; the task description is the implementing-model
input. They serve different audiences. The discipline is that the task
description's prose must be *consistent with* (not necessarily verbatim)
the cited scenario. The validator checks the structured field
(`roadmap_scenarios`); prose drift is a reviewer concern.

If drift becomes a real problem in D01, the next step is to add a
prose-vs-scenario consistency check — but it's a Phase 1 discipline
question, not a schema question.

### 9.3 Risk: ID-based security scenario references lose specificity

**Symptom:** A task cites `["ASVS V9.2.1"]` but the roadmap has *two*
V9.2.1 scenarios (e.g., outbound HTTPS to Google Drive *and* outbound HTTPS
to a different service). The implementing model can't tell which is being
referenced.

**Mitigation:** Switch to scenario-name references (like
`roadmap_scenarios`) if this happens. Initial implementation uses ID-based
references because the roadmap skill's R01/R02 outputs have one scenario
per ID per component. Promote when the multi-scenario-per-ID case becomes
real.

### 9.4 Risk: pipeline doesn't know about the new fields

**Symptom:** The implementation pipeline (`prototype-driven-implementation`)
imports `task_schema.py` and reads tasks. New fields would be ignored unless
the pipeline is updated to use them.

**Mitigation:** Pipeline doesn't need to use the new fields for
correctness. The validator runs at decomposition time; new fields' validity
is established before the pipeline ever sees them. The pipeline can ignore
`roadmap_component`, `roadmap_scenarios`, and `security_scenario_ids` and
still work — they're metadata that helps the human reviewer and validates
the decomposition, not runtime inputs.

If a future pipeline iteration wants to use the fields (e.g., to inline the
relevant roadmap scenarios into the executor prompt), it's a clean
opt-in addition. Don't pre-build it.

### 9.5 Risk: refactoring decomposition mid-flight on the test project

**Symptom:** The R03 roadmap output (post-project-setup) is fresh; the
design doc is current; a new decomposition under the new schema is the
next thing to run. If the refactor lands but the validator has bugs, D01
fails for refactor reasons, not decomposition reasons, making it hard to
evaluate.

**Mitigation:** Smoke-test the schema validators against synthetic inputs
*before* running D01 on real data. Same pattern as the roadmap skill's
validator smoke tests — happy path, missing-field, mismatched-slug,
mismatched-scenario-name, mismatched-OWASP-ID. Document the smoke-test
procedure in the same trial record as D01.

---

## 10. Acceptance trial: D01

After the refactor lands, the validation trial is a regenerated
decomposition against the airflow-gdrive-ingestion feature. Conventions:

- **Trial code:** D01 (D for decomposition; first decomposition-skill
  iteration trial).
- **Target:** `~/health-data-ai-platform/`, feature
  `airflow-gdrive-ingestion`.
- **Inputs:**
  - `docs/roadmap/airflow-gdrive-ingestion/` (R03 output, post-project-setup)
  - `docs/design/airflow-gdrive-ingestion-<P05-date>.md` (or amended
    in place)
  - `prototypes/airflow-gdrive-ingestion/`
- **Output target:** `tasks/airflow-gdrive-ingestion/tasks.json` and
  `task_schema.py` (note: feature name updated from
  `airflow-google-drive-ingestion` per the roadmap skill's slug; old path
  can be deleted manually).

**Acceptance bar:**

- Decomposition skill loads `components.yml` and the per-component
  roadmap files (including `project-setup.md`) without error.
- Phase 1 proposal shows the components verbatim from the registry —
  expected to be five with project-setup, name them as the registry
  presents them; no boundary inference.
- Generated `tasks.json` validates against the new schema with no errors.
- Every task has `roadmap_component` set to one of the registered slugs.
  Scaffold tasks specifically reference `project-setup`.
- Every test task and every implementation task with tests has
  non-empty `roadmap_scenarios`; every cited scenario name appears in
  the matching component's roadmap file.
- Every implementation task's `security_scenario_ids` (where non-empty)
  cites IDs that appear in the matching component's `owasp_categories`.
- Validator smoke tests pass on five synthetic cases (per §9.5).
- Summary table renders with new columns; reviewer can see at a glance
  which task belongs to which component.

**Trial record:** `~/claude-project-memory/prototype-driven-planning-skill/trials/D01-decomposition-roadmap-integration.md`,
following the same format as the existing P*, T*, R* records.

---

## 11. Implementation order

A fresh session should do this work in this sequence so each step is
reviewable in isolation:

0. **Resolve the embed-vs-script question** flagged in §5.3 and §7.3
   before writing any schema code. The two paths are not interchangeable
   and writing code first then converting is wasted effort.
1. **Update `task_schema.py` first** (or create `scripts/validate_decomposition.py`
   alongside, depending on step 0's outcome). Add the four new fields,
   the new validators, and the roadmap-file parser. Smoke-test against
   synthetic inputs (per §9.5) before any other changes.
2. **Update `analysis-guide.md`.** Phase 1's input model is the most
   visible behavioral change; document it before the SKILL.md changes that
   reference it.
3. **Update `task-writing-guide.md`.** New fields, updated examples.
4. **Update `output-format.md`.** New JSON example, new validation checklist
   items, summary table changes.
5. **Update `SKILL.md`.** Bring the top-level rules in line with the
   updated references.
6. **Memory repo updates.** New trial record D01 (placeholder; filled in
   after the trial actually runs); LEARNINGS.md "From Decomposition Skill"
   subsection gains entries for the design choices made here; README.md
   "Current State" gets a new "Decomposition Skill Refactor" subsection
   noting the schema change; Next Steps gets D01 + the eventual T15
   pipeline trial.
7. **(Manual)** User commits and pushes both repos.
8. **(Next session)** Run D01 against the airflow-gdrive-ingestion feature
   to validate the refactor works end-to-end on real data.

---

## 12. What this plan deliberately doesn't change

- **The roadmap skill.** No changes to `prototype-driven-roadmap`. R02
  proved the skill works; R03 will confirm it produces the project-setup
  component cleanly when the design doc has one. This refactor consumes
  the roadmap output.
- **The implementation skill.** No changes to
  `prototype-driven-implementation`. The new task fields are metadata; the
  pipeline ignores them. A future iteration can opt in.
- **The planning skill.** No changes from this plan. (Project-setup work
  is a separate plan: `planning-project-setup-component-plan-2026-04-27.md`.)
- **`test_command`, `expected_test_failure_modes`, `stub`, TDD pairing,
  Task Sizing.** All existing schema fields and rules survive verbatim.
- **Output directory layout.** Still `tasks/<feature>/` with `tasks.json`
  and `task_schema.py`. No new files.
- **The "no per-task .md files" rule.** Still holds. Reviewers read the
  summary table at decomposition time and the JSON for detail.

---

## 13. One open question to settle in the new session

Per-component decomposition (decompose component-by-component instead of
feature-as-a-whole) is left explicitly out of scope for this refactor. The
schema change in §4 sets it up as a *future possibility* — once every task
declares its component, the decomposer could in principle process one
component at a time, presenting the user with one component's tasks before
moving to the next. This would help with very large features.

The open question for the new session is: do we plan that as the next step
after D01, or do we keep feature-as-a-whole decomposition and let
`roadmap_component` stay metadata for now? **My instinct is the latter** —
we don't have evidence that feature-as-a-whole has scaling problems on
realistic features, and per-component decomposition would be a much bigger
refactor with its own design space. But surface this question explicitly in
D01's trial record so it's not lost.
