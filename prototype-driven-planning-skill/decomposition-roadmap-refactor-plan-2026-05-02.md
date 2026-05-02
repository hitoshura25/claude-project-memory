# Plan — Refactor `prototype-driven-task-decomposition` to Consume the Roadmap

> **Status:** Proposal. Created 2026-05-02 as a fresh draft replacing
> `decomposition-roadmap-refactor-plan-2026-04-26.md`. The earlier plan
> was authored against a markdown-roadmap world; the roadmap skill's
> 2026-04-30 migration to JSON output, combined with the project-shipped-
> schema architecture (`roadmap_schema.py` is copied into each project's
> roadmap directory at Phase 3), changed enough of the design surface that
> a rewrite is cleaner than a patch.
>
> **Supersedes:** `decomposition-roadmap-refactor-plan-2026-04-26.md`
> (preserved on disk as historical context for the 2026-04-27 sequencing
> pivot and the embed-vs-script debate, both of which are resolved here).
>
> **Sequencing:** Three coordinated changes — roadmap skill (small),
> implementation skill (small), decomposition skill (the bulk of the
> work). Each change ships independently; the full benefit (no scenario
> content duplicated between roadmap and decomposition) requires all
> three. Acceptance trials: R03 → D01 → T15.

---

## 1. Where to read in (do this first)

A fresh session must load these before proposing edits.

**Memory repo (always loaded at session start by project instructions):**

- `~/claude-project-memory/prototype-driven-planning-skill/README.md`
- `~/claude-project-memory/prototype-driven-planning-skill/LEARNINGS.md`
- `~/claude-project-memory/prototype-driven-planning-skill/trials/_SUMMARY.md`

**Memory repo (load on demand for this work):**

- `~/claude-project-memory/prototype-driven-planning-skill/trials/R01-roadmap-id-parity-and-actor-misplacement.md`
- `~/claude-project-memory/prototype-driven-planning-skill/trials/R02-roadmap-spec-migration-revalidation.md`
- `~/claude-project-memory/prototype-driven-planning-skill/trials/T14-test-command-gap.md`
  (the prose-as-lossy-transport pattern this refactor is designed to
  eliminate)
- `~/claude-project-memory/prototype-driven-planning-skill/decomposition-roadmap-refactor-plan-2026-04-26.md`
  (superseded predecessor; useful for the 2026-04-27 pivot history and
  the rejected option set)

**Decomposition skill — full file reads required:**

- `~/claude-devtools/skills/prototype-driven-task-decomposition/SKILL.md`
- `~/claude-devtools/skills/prototype-driven-task-decomposition/references/analysis-guide.md`
- `~/claude-devtools/skills/prototype-driven-task-decomposition/references/task-writing-guide.md`
- `~/claude-devtools/skills/prototype-driven-task-decomposition/references/output-format.md`
- `~/claude-devtools/skills/prototype-driven-task-decomposition/scripts/task_schema.py`

**Roadmap skill — read for downstream contract and the schema being
extended:**

- `~/claude-devtools/skills/prototype-driven-roadmap/SKILL.md`
- `~/claude-devtools/skills/prototype-driven-roadmap/references/components-json-format.md`
- `~/claude-devtools/skills/prototype-driven-roadmap/references/roadmap-json-format.md`
- `~/claude-devtools/skills/prototype-driven-roadmap/references/phase-2-generation.md`
- `~/claude-devtools/skills/prototype-driven-roadmap/scripts/roadmap_schema.py`
- `~/claude-devtools/skills/prototype-driven-roadmap/scripts/components_schema.py`
- `~/claude-devtools/skills/prototype-driven-roadmap/scripts/validate_roadmap.py`

**Implementation skill — read for what the prompt composer currently
inlines and where roadmap-scenario inlining fits:**

- `~/claude-devtools/skills/prototype-driven-implementation/references/phase-2-generation.md`
- `~/claude-devtools/skills/prototype-driven-implementation/templates/nodes/compose_prompt.py.template`

**Roadmap output (canonical example of what input now looks like):**

- `~/health-data-ai-platform/docs/roadmap/airflow-gdrive-ingestion/components.json`
- `~/health-data-ai-platform/docs/roadmap/airflow-gdrive-ingestion/roadmap.json`
- `~/health-data-ai-platform/docs/roadmap/airflow-gdrive-ingestion/components_schema.py`
- `~/health-data-ai-platform/docs/roadmap/airflow-gdrive-ingestion/roadmap_schema.py`

**Design doc (still relevant — supplementary input for cross-cutting
concerns):**

- `~/health-data-ai-platform/docs/design/airflow-gdrive-ingestion-2026-04-28.md`
  (or whichever-date the current signed-off design doc is)

---

## 2. Why this refactor

The decomposition skill currently reads the design doc + prototype directly.
The roadmap skill now sits between planning and decomposition and produces
strictly better-shaped input for what the decomposer needs:

| What decomposition needs | Where it lives today | Where it should live after refactor |
|---|---|---|
| Component boundaries | Inferred from design doc Architecture Overview prose | `components.json` registry (authoritative slug + name + deps + OWASP cats) |
| Per-component dependency graph | Inferred from design doc + prototype reading | `components.json` `depends_on` (validated, acyclic, slug-based) |
| Testable behaviors per component | Paraphrased from design doc + prototype into `Behaviors to test:` prose in each task | Cited by stable scenario `id` against `roadmap.json`'s `functional_scenarios[]`; pipeline inlines Given/When/Then content at prompt time |
| Security concerns per component | Paraphrased from design doc Security Posture into `security_considerations` prose | Cited by stable scenario `id` against `roadmap.json`'s `security_scenarios[]`; pipeline inlines content at prompt time. Freeform `security_considerations` stays as escape hatch for task-specific concerns the roadmap didn't surface. |
| Out-of-scope boundaries per component | Inferred or omitted | `out_of_scope` per component in `roadmap.json` (explicit) |
| Cross-cutting tooling / data model | Design doc | Design doc (unchanged — roadmap doesn't replace this) |

The refactor's purpose is to **stop reinventing component identification,
dependency mapping, and scenario enumeration** when the roadmap skill already
produced authoritative answers. Three failure classes the refactor closes:

- **Component-boundary drift between roadmap and decomposition.** If the
  decomposer re-derives boundaries from the design doc, it can land on a
  different set than the roadmap (different splits, different names,
  different deps). Downstream artifacts that reference the roadmap (security
  scenarios, Performed-by slugs) then disagree with task-level component
  boundaries silently.
- **Scenario content duplication and drift.** Today, decomposition
  paraphrases scenario behavior into the task description's `Behaviors to
  test:` section. The roadmap is the human-reviewed source; the paraphrase
  is what the implementing model sees. They can drift — and almost certainly
  do, because Phase 2 of decomposition rewords whatever it reads. Removing
  the paraphrase entirely (citation only; pipeline inlines from
  `roadmap.json`) makes the roadmap the single source of truth for scenario
  content.
- **No machine-checkable mapping of task → roadmap content.** Today, "this
  task implements scenario X" is implicit in prose; the validator can't
  confirm it. With explicit citation fields (`roadmap_component`,
  `roadmap_functional_scenarios`, `roadmap_security_scenarios`) the validator
  confirms every citation resolves; missing or stale roadmap content surfaces
  immediately.

---

## 3. The skill-boundary principle this refactor enforces

Three credible options for how decomposition reads roadmap output. **Decision
already made: option C (consume project-shipped output, no internal
imports).**

**Option A — Decomposition imports roadmap-skill internals.** Cross-skill
import of `roadmap_schema.py` from the roadmap skill's source tree.

*Rejected because:* couples the two skills' release cycles. A change to
the roadmap skill's schema can break decomposition silently or force
synchronized updates. Violates the principle of "skill output as the
boundary."

**Option B — Decomposition embeds its own copy of the roadmap-file
parser.** As the previous plan (2026-04-26) proposed, copy the parsing
logic into `task_schema.py` so decomposition is fully self-contained.

*Rejected because:* under JSON output, parsing reduces to
`json.load()` — there is essentially nothing to copy. The "parser drift"
problem the embed approach solved doesn't exist with structured JSON.
Embedding a Pydantic model just to parse JSON is duplication for its
own sake.

**Option C — Decomposition imports the project-shipped schemas (chosen).**
At Phase 3, the roadmap skill already copies `roadmap_schema.py` and
`components_schema.py` into the project's roadmap directory.
Decomposition imports from those project-shipped copies. The skills
share the schema *file* via the project's filesystem; neither reaches
into the other's source tree.

*Why option C:* it matches a pattern already in use. The implementation
pipeline already imports `task_schema.py` from the project's tasks
directory at runtime — same pattern, different schema. The decomposition
skill adopts the same pattern for its upstream input. The boundary
between skills is the *project artifact*, not the skill's source code.

**This means decomposition outputs only the mapping it creates — task →
component, task → scenarios — and never duplicates content that already
lives in the roadmap.** If decomposition needs information the roadmap
output doesn't carry, that's a signal to extend the roadmap skill, not
to copy content into the task description.

---

## 4. The three coordinated changes

This refactor is structurally three changes to three skills. Each is
small individually; coordination produces the full benefit (no scenario
content duplicated between roadmap and decomposition; pipeline gets
richer per-task context than current paraphrased prose).

### 4.1 Roadmap skill: stable per-scenario `id` field

**Why.** Decomposition tasks need a stable identifier to cite scenarios
they implement. Citing by `name` is brittle (regenerating the roadmap
may reword scenario names; cited tasks break silently). Citing by
`owasp_id` works only for security scenarios and creates ambiguity if
a component grows two scenarios under one OWASP ID. A dedicated `id`
field — required, kebab-case slug, unique within a component, written
by the model in Phase 2 — is the most stable identifier and works
symmetrically for both functional and security scenarios.

**Schema change.** Add `id: str` to `FunctionalScenario` and
`SecurityScenario` in `roadmap_schema.py`:

```python
id: str = Field(
    description="Stable, kebab-case identifier for this scenario, "
                "unique within the enclosing component. Written by "
                "the Phase 2 generating model alongside the scenario "
                "name. Used by downstream skills (decomposition, "
                "implementation) to cite the scenario without being "
                "fragile to name rewording on roadmap regeneration."
)
```

**Validators added:**

- **`scenario_id_format`** (per-scenario field validator). Match
  `^[a-z][a-z0-9-]*[a-z0-9]$` — same kebab-case rule as component slugs.
- **`scenario_ids_unique_within_component`** (component-level model
  validator). All `id` values across both `functional_scenarios` and
  `security_scenarios` of one component must be unique. Cross-component
  duplicates are fine — the component slug + scenario id together form
  the global key. Reusing IDs within a component would defeat the
  citation key.

**Phase 2 generation guidance update.** The generating model writes both
`name` and `id`. The reference doc spells out the rule: derive `id` as a
kebab-case slug from `name` *for the first generation*; on regeneration,
preserve existing IDs unless the scenario itself is being substantially
restructured. The model's hand on this — not a script's — because the
generating model is the one that knows whether a reworded scenario is
"the same scenario, reworded" or "a new scenario replacing an old one."

**`name` is still required and stays.** `name` is the human-readable
summary; `id` is the machine-readable handle. Both are useful for
different audiences (reviewers read `name`, validators check `id`).

**Migration of existing roadmap output.** R02 output predates the `id`
field. R03 regenerates against the rebuilt schema. The model assigns
fresh IDs from current scenario names. No content changes; just a new
field per scenario.

### 4.2 Implementation skill: scenario inlining in `compose_prompt`

**Why.** Decomposition citation alone isn't enough — the implementing
model needs the scenario *content* (Given/When/Then) at prompt time.
Today the prompt composer inlines dependency files (per-task
`depends_on` chain). It doesn't yet inline roadmap scenarios. Adding
this is a natural extension of the existing inlining pattern.

**Template change.** `compose_prompt.py.template` gains a new helper
parallel to `_inline_dependencies`:

```python
def _inline_roadmap_scenarios(task: dict) -> str:
    """Read roadmap.json and inline cited scenarios as a structured
    'Behaviors to Test' section.

    Cited via task.roadmap_component + task.roadmap_functional_scenarios
    + task.roadmap_security_scenarios. Resolves each (component, id) pair
    against roadmap.json and renders the Gherkin content into the prompt.
    """
```

Resolution rule: for each scenario id in `roadmap_functional_scenarios`
or `roadmap_security_scenarios`, look up the scenario in `roadmap.json`
under the task's `roadmap_component`; render `name`, `given`, `when`,
`then`, `verified_by`, and (for security scenarios) `owasp_id` into a
structured prompt section.

**New placeholder.** `compose_prompt.py.template` gains
`{{ROADMAP_JSON_PATH}}` — set in Phase 2 of the implementation skill to
the project-relative path of `roadmap.json` (typically
`docs/roadmap/<feature>/roadmap.json`). The template-substitution table
in the implementation skill's `phase-2-generation.md` gains this
placeholder.

**Prompt assembly order.** `_inline_roadmap_scenarios` runs before
`_inline_dependencies`. Scenarios describe *what* the task implements;
dependencies describe *what code it builds on*. Scenarios first matches
how a developer reads a spec.

**Failure mode.** If `roadmap.json` isn't readable or a cited scenario
id doesn't resolve, the prompt composer fails loudly with a clear error
naming the task id and the unresolved citation. This catches drift
between decomposition output and roadmap content that survived
decomposition's own validation (rare — usually means roadmap was
regenerated after decomposition without re-validating). Fail-loud at
prompt-compose time is the right place; a silent prompt with missing
content would burn executor budget on a task with no actual spec.

**Scaffold and infrastructure tasks.** Per §4.3, scaffold tasks
reference `project-setup` as their `roadmap_component` but typically
don't cite scenarios (project-setup's scenarios are about toolchain
validation, not code behavior). The inliner handles empty scenario
lists gracefully — no section rendered if both lists are empty.

### 4.3 Decomposition skill: schema, description template, validator

**Schema additions to `Task`:**

```python
roadmap_component: str = Field(
    description="The slug of the roadmap component this task belongs to. "
                "Must match a slug in components.json. Every task — "
                "including scaffold and infrastructure tasks — declares "
                "a component. Scaffold tasks reference 'project-setup'."
)

roadmap_functional_scenarios: list[str] = Field(
    default_factory=list,
    description="Stable scenario IDs from this task's roadmap_component's "
                "functional_scenarios in roadmap.json. The implementing "
                "pipeline inlines the cited scenarios' Given/When/Then "
                "content at prompt time. Empty for tasks without "
                "behavioral scenarios (typically scaffold and pure "
                "infrastructure tasks)."
)

roadmap_security_scenarios: list[str] = Field(
    default_factory=list,
    description="Stable scenario IDs from this task's roadmap_component's "
                "security_scenarios in roadmap.json. The implementing "
                "pipeline inlines the cited scenarios' Given/When/Then + "
                "owasp_id content at prompt time. Empty for tasks without "
                "security scenarios."
)
```

**Schema additions to `TaskDecomposition`:**

```python
components_json_path: str = Field(
    description="Path from project root to the components.json file "
                "produced by the roadmap skill (typically "
                "'docs/roadmap/<feature>/components.json'). The "
                "decomposition validator loads this file to confirm "
                "every task's roadmap_component slug is registered."
)

roadmap_json_path: str = Field(
    description="Path from project root to the roadmap.json file "
                "produced by the roadmap skill (typically "
                "'docs/roadmap/<feature>/roadmap.json'). The "
                "decomposition validator loads this file to confirm "
                "every cited scenario id resolves."
)
```

Two separate path fields, not one directory path. Independent existence
checks; clearer error messages naming exactly which file is missing or
malformed.

**Validators added:**

- **`validate_roadmap_component_registered`** (decomposition-level
  model validator). Load `components.json` via `components_schema.py`
  imported from the project-shipped copy; confirm every task's
  `roadmap_component` slug appears in `components.json`'s `components[]`.

- **`validate_roadmap_scenarios_resolve`** (decomposition-level model
  validator). Load `roadmap.json` via `roadmap_schema.py`; for each task,
  confirm every `roadmap_functional_scenarios[i]` matches a scenario `id`
  in the task's `roadmap_component`'s `functional_scenarios`, and every
  `roadmap_security_scenarios[i]` matches a scenario `id` in the same
  component's `security_scenarios`. Cross-component citations (citing a
  scenario id from a different component) are rejected.

- **`validate_roadmap_scenarios_required_for_test_tasks`** (per-task
  model validator). Test tasks and implementation tasks with `tests`
  must have non-empty `roadmap_functional_scenarios` OR non-empty
  `roadmap_security_scenarios`. A test task with no roadmap citations
  is suspect — either the scenario is missing from the roadmap (fix
  upstream) or the test task shouldn't exist. Scaffold, wiring,
  infrastructure tasks may have empty scenario lists.

**Description template change.** The current template (in
`task-writing-guide.md`) has a `Behaviors to test:` bullet section.
**Remove this section entirely.** The pipeline inlines scenario
content from `roadmap.json` directly. The task description still
includes:

- `Component:` — names the component, classifies as test or
  implementation task
- `Component type:` — declarative config / pure stub / partial stub /
  etc.
- `Interface:` — type signatures
- `Expected test failure mode:` — exception types for stubbed methods
- `Out of scope:` — refusal-to-implement boundary

The structured citation fields replace prose paraphrase; the
implementing model gets richer content from `roadmap.json` than from
the previous one-liner-per-bullet paraphrase.

**`security_considerations` field stays.** Existing field, freeform
prose. Unchanged. Now serves only as escape hatch for task-specific
concerns the roadmap didn't surface (specific library version CVE,
implementation-detail concern that emerged during decomposition).
Most security concerns shift to `roadmap_security_scenarios` citation.

**`prototype_references` field is not reintroduced.** Already removed
from the pipeline; this refactor doesn't bring it back. The roadmap's
`prototype_evidence[]` per component is the new home for prototype
pattern callouts; if implementing models need prototype patterns, they
come through the existing dependency-inlining mechanism (the prototype
files themselves are referenced via `depends_on` and `files[]`
operation='create' from prototype directory) or via the Phase 1
research the planning skill already does.

---

## 5. Phase-by-phase changes (decomposition skill)

### 5.1 Phase 1 — Analysis

**Inputs change.** Today the skill reads design doc + prototype. After
the refactor it reads:

- `docs/roadmap/<feature>/components.json` — authoritative component
  registry. **Required input.** Skill stops with a clear error if
  missing.
- `docs/roadmap/<feature>/roadmap.json` — authoritative scenarios,
  out-of-scope, dependencies per component. **Required.**
- `docs/roadmap/<feature>/components_schema.py` — Pydantic schema for
  loading `components.json`. **Required.** Imported by the validator.
- `docs/roadmap/<feature>/roadmap_schema.py` — Pydantic schema for
  loading `roadmap.json`. **Required.** Imported by the validator.
- `docs/design/<feature>-<date>.md` — for cross-cutting sections only:
  Data Model, Tooling, Containerization, Deployment Strategy,
  cross-cutting Deferred Decisions, Security Posture (cross-cutting
  policies). **Required.**
- `prototypes/<feature>/` — same as today. The decomposer still
  inventories the prototype to extract inline patterns for task
  descriptions. **Required.**

**Component identification becomes a registry read, not an inference.**
The old "Identify component boundaries" step from `analysis-guide.md`
becomes "Load `components.json` and confirm component count, slugs, and
dep graph match the per-component presence in `roadmap.json`." The
decomposer does not propose its own boundaries; if the registry's
component set is wrong, the user fixes the roadmap and re-runs
decomposition.

**Behavior enumeration becomes a scenario read.** For each component,
read `roadmap.json`'s entry: `functional_scenarios[]`,
`security_scenarios[]`. These are the scenario IDs available for
citation by tasks. The decomposer doesn't paraphrase them — it cites
their IDs.

**The decomposer's freedom is now scoped.** It still decides:

- Whether each component splits into multiple tasks (still using the
  Task Sizing thresholds — cyclomatic complexity, line counts, fan-out)
- The TDD pair structure (which test task pairs with which
  implementation task)
- Which scenarios from the component each task is responsible for
- Which inline patterns to extract from the prototype (for files
  inlined via `depends_on`)
- The exact `test_command` shell invocation per task
- Field-name contracts at task boundaries (still needed —
  `components.json` doesn't capture data-flow field names within a
  component's internals)
- Open questions that aren't answerable from the roadmap (e.g.,
  "split this large parser into 2 tasks or 3?")

**The Phase 1 proposal message changes.** The numbered-questions
pattern stays. The "proposed component breakdown" section becomes
"component registry as loaded from `components.json`" with the slugs,
names, and deps shown back to the user verbatim. The user has nothing
to approve about the boundaries themselves — they're already approved.
The user reviews:

- Per-component task count proposal (1 task? 2 tasks? a TDD pair?)
- Phase assignments per task
- Per-task scenario assignments (which scenario IDs from the component
  each task implements)
- Open questions specific to decomposition (not architecture)

### 5.2 Phase 2 — Task Generation

**Each task gets `roadmap_component` set.** The decomposer assigns this
based on which component the task implements. The validator catches
typos against `components.json`.

**Test tasks and implementation-with-tests tasks get
`roadmap_functional_scenarios` and/or `roadmap_security_scenarios`
populated.** The decomposer chooses which scenario IDs from the
component each task is responsible for. Most tasks list 2–5 scenarios.
A "happy path" test task might list every functional scenario from one
component; a "security tests" task might list the security scenarios.

**Task descriptions follow the updated template** (no `Behaviors to
test:` section; structured citations carry that content). The
implementing model gets the Given/When/Then text via prompt-time
inlining from `roadmap.json`, not via paraphrase in the task
description.

**Existing task description sections stay** — `Component`, `Component
type`, `Interface`, `Expected test failure mode`, `Out of scope`.
These describe task-level information the roadmap doesn't carry
(stub structure, exception types, refusal boundary scoped to this
task).

### 5.3 Phase 3 — Validation and Output

**`tasks/<feature>/` directory still gets `tasks.json` + `task_schema.py`.**
That hasn't changed.

**The validator now needs `components.json` and `roadmap.json` available
at validation time, plus their schemas.** Validation logic:

1. Load `components.json` via the project-shipped `components_schema.py`.
   Fail loudly if either is missing or malformed.
2. Load `roadmap.json` via the project-shipped `roadmap_schema.py`.
   Same.
3. Run all per-task validators (existing + new).
4. Run all decomposition-level validators (existing + new).

The decomposition skill's own `task_schema.py` does not embed roadmap
parsing logic. It imports the project-shipped roadmap schemas at
validation time. Schema files are imported by adding the project's
roadmap directory to `sys.path` at validator entry — same pattern the
implementation pipeline uses to import `task_schema.py` from
`<project>/tasks/<feature>/`.

**Summary table gets new columns.** `Roadmap Component` and `Scenarios`
useful to a reviewer scanning whether each task is doing what its
component expects. Drop the existing `Files` count column to make
room (file count is visible in the JSON).

| ID | Title | Type | Phase | Component | Scenarios | Test Command |
|---|---|---|---|---|---|---|

---

## 6. Reference doc updates

### 6.1 Roadmap skill — `references/roadmap-json-format.md`

- Add `id` field to the FunctionalScenario and SecurityScenario field
  reference tables.
- Add a new subsection "Scenario IDs" explaining the slug rule, the
  uniqueness-within-component invariant, and the regenerate-preserves-
  IDs guidance.
- Update the JSON example under "Schema" to include `id` on both
  scenario kinds.
- Update the "Validation rules" list to include the new
  `scenario_ids_unique_within_component` rule and the format check.

### 6.2 Roadmap skill — `references/phase-2-generation.md`

- Add a subsection on writing scenario IDs: derive kebab-case from
  `name` for first generation; preserve existing IDs on regeneration
  unless the scenario is being substantively restructured.
- Update example output snippets to include `id` on every scenario.

### 6.3 Implementation skill — `references/phase-2-generation.md`

- Add `{{ROADMAP_JSON_PATH}}` to the placeholder substitution table for
  `compose_prompt.py.template`.
- Add a brief subsection under "Generation Principles" noting that
  scenario inlining is parallel to dependency inlining and reads from
  `roadmap.json` at prompt-compose time.

### 6.4 Implementation skill — `templates/nodes/compose_prompt.py.template`

- Add `_inline_roadmap_scenarios` helper.
- Wire it into `_build_prompt` between the task objective and the
  files section.
- Add `{{ROADMAP_JSON_PATH}}` placeholder for the path constant the
  helper reads.
- Update the docstring at top to mention scenario inlining alongside
  dependency inlining.

### 6.5 Decomposition skill — `references/analysis-guide.md`

- **Replace** "Reading the Design Doc" section: roadmap output is now
  the primary input; design doc is supplementary for cross-cutting
  concerns only.
- **Replace** "Identifying Component Boundaries" with "Loading the
  Component Registry" — the decomposer reads boundaries from
  `components.json`, doesn't infer them.
- **Add** "Reading per-component scenarios" subsection explaining the
  `roadmap.json` shape and which fields the decomposer reads.
- **Update** "Mapping Dependencies" — cross-component deps are
  pre-computed in `components.json`. Inter-task deps within a component
  are still the decomposer's responsibility.
- **Update** the proposal-message format: components shown verbatim
  from registry; new "Component → tasks → scenarios" mapping
  subsection.

### 6.6 Decomposition skill — `references/task-writing-guide.md`

- **Add** "Roadmap-Driven Task Authoring" section near the top,
  before "The Self-Containment Rule", explaining the citation
  fields and how the pipeline inlines scenario content.
- **Update** "Task Description Template" — remove the `Behaviors to
  test:` section. Update the example tasks to show the citation
  fields instead.
- **Update** "Writing Security Considerations" — most concerns now
  move to `roadmap_security_scenarios`. The freeform field stays for
  decomposition-specific concerns. Add an example showing both.
- **Update** the example TDD pair to include `roadmap_component`,
  `roadmap_functional_scenarios`, and (on the implementation task)
  `roadmap_security_scenarios`. Show the description without the
  removed `Behaviors to test:` section.
- **Keep** Task Sizing rules as-is.
- **Keep** `test_command` rules as-is.

### 6.7 Decomposition skill — `references/output-format.md`

- **Update** the summary table example to include the new columns
  (Component, Scenarios, drop Files).
- **Update** the validation checklist to add:
  - Every task's `roadmap_component` matches a slug in
    `components.json`.
  - Every test task and every implementation task with tests has
    non-empty `roadmap_functional_scenarios` OR `roadmap_security_scenarios`.
  - Every cited scenario `id` matches a scenario in the matching
    component's `functional_scenarios` or `security_scenarios` in
    `roadmap.json` (per kind — functional citations resolve against
    functional scenarios only, security against security only).
  - `components_json_path` and `roadmap_json_path` are present and
    resolve to existing files at validation time.
- **Update** the JSON example to include the new fields on tasks of
  each type.
- **Add** an "Integration with the Roadmap" subsection explaining the
  read-only relationship: decomposition consumes the roadmap; never
  modifies `components.json` or `roadmap.json`.

### 6.8 Decomposition skill — `SKILL.md`

- **Update** "Quick Reference" table: input now includes the roadmap
  directory.
- **Update** "How to Start" to confirm both the roadmap directory and
  the design doc exist before proceeding.
- **Update** Phase 1 step 1 to read the roadmap first; demote
  design-doc reading to step 2 with explicit scoping.
- **Update** Phase 1 step 3 ("Identify component boundaries") to
  "Load `components.json` and confirm registry presence."
- **Add** Principle: "Component boundaries come from the roadmap."
- **Add** Principle: "Scenario content lives in the roadmap; tasks
  cite by ID; the pipeline inlines content at prompt time."
- **Update** the schema reference table to include the three new task
  fields and the two new top-level fields.

---

## 7. Validator implementation notes

### 7.1 Importing the project-shipped schemas

At validator entry, add the project's roadmap directory to `sys.path`
and import `components_schema` and `roadmap_schema` from there. Pattern:

```python
import sys
from pathlib import Path

def _load_roadmap_schemas(components_json_path: str, roadmap_json_path: str):
    # The schemas live alongside the JSON files in the same directory.
    components_dir = Path(components_json_path).parent.resolve()
    if str(components_dir) not in sys.path:
        sys.path.insert(0, str(components_dir))
    from components_schema import Components
    from roadmap_schema import Roadmap
    return Components, Roadmap
```

This is the same pattern the implementation pipeline uses to import
`task_schema.py` from `<project>/tasks/<feature>/`. No cross-skill
imports; no embedded copies.

If the schemas are missing from the project's roadmap directory (e.g.,
the user copied JSON files between projects without the schemas), the
validator fails with a clear pointer: "schema file not found at
`<path>` — re-run the roadmap skill to regenerate the project-shipped
schemas."

### 7.2 Error message tone

Match the existing schema's error tone: name the field, name the
failing value, suggest the fix. Example:

```
Task 'task-04' has roadmap_component='drive-loader' but no slug
'drive-loader' is registered in
docs/roadmap/airflow-gdrive-ingestion/components.json. Did you mean
'drive-downloader'?
```

```
Task 'task-07' cites roadmap_functional_scenarios=['locates-zip-by-name']
under roadmap_component='sqlite-parser', but no scenario with id
'locates-zip-by-name' is registered in sqlite-parser's
functional_scenarios in roadmap.json. The id 'locates-zip-by-name'
does exist in component 'drive-downloader' — did you mean to set
roadmap_component to 'drive-downloader'?
```

The "Did you mean" hint can use a simple Levenshtein nearest-neighbor
against registered slugs and IDs; nice-to-have, not required for D01.

### 7.3 Validator invocation

Phase 3 runs the schema validators against `tasks.json` (existing
behavior, extended with new fields). The `validate_roadmap_*`
decomposition-level validators load `components.json` and
`roadmap.json` once and run their cross-checks. No separate validator
script — the existing pattern of "schema validators do everything" is
preserved.

This differs from the previous plan (2026-04-26), which proposed a
separate `validate_decomposition.py` script paralleling the roadmap
skill's validator. That separation made sense when the roadmap skill
shipped markdown files needing cross-skill parser logic. With JSON
output and project-shipped schemas, the cross-skill checks become
straightforward Pydantic-validator calls; no need for a separate
script.

---

## 8. Migration of existing output

### 8.1 Existing roadmap output

R02 output predates the scenario `id` field. R03 regenerates against
the rebuilt schema. The model assigns fresh kebab-case IDs from current
scenario names. No content changes; just a new field per scenario.

This is a one-time regeneration. Subsequent regenerations of the same
feature (Phase 2 reruns) preserve existing IDs unless a scenario is
substantively restructured.

### 8.2 Existing decomposition output

The existing `tasks/airflow-google-drive-ingestion/tasks.json` (from
T14) will fail validation under the new schema (missing
`roadmap_component`, `components_json_path`, `roadmap_json_path`).

**Decision: do not migrate. Regenerate.** Same pattern as the
`test_command` field landing in T14 — the existing JSON was
deliberately broken by the schema change to force regeneration. D01
regenerates `tasks.json` from scratch under the new schema.

The path forward:

1. Roadmap skill change lands. Schema gains `id` field. R03 trial
   validates: regenerate `roadmap.json` for airflow-gdrive-ingestion;
   check `id` field is present, kebab-case, unique within each
   component, stable across a second regeneration.
2. Implementation skill change lands. `compose_prompt.py.template`
   gains scenario inliner. T15 trial later validates the full chain.
3. Decomposition skill change lands. D01 regenerates
   `tasks.json` against R03's roadmap output.
4. T15 runs the pipeline against D01's tasks; confirms the inlined
   scenarios produce useful executor prompts.

### 8.3 Feature-name slug update

The decomposition output today lives at
`tasks/airflow-google-drive-ingestion/`. The roadmap skill uses
`airflow-gdrive-ingestion`. D01 outputs to
`tasks/airflow-gdrive-ingestion/`. The old directory can be deleted
manually after D01 confirms the new directory has everything.

---

## 9. Risks and how to handle them

### 9.1 Risk: scenario `id` regeneration drift

**Symptom.** The roadmap skill regenerates scenarios with different IDs
than the previous run, breaking decomposition's citations.

**Mitigation.** Phase 2 generation guidance instructs the model: on
regeneration, preserve existing IDs unless the scenario is substantively
restructured. The roadmap-skill validator can't enforce this directly —
it has no diff against the previous run. But the decomposition validator
catches it: a citation fails to resolve, the user sees the failure, and
either updates the citation or fixes the upstream regeneration.

For tighter enforcement, a future iteration could add a `scenario_ids.lock`
file (like a manifest) that the validator cross-checks against. Out of
scope for this refactor; surface as a follow-up if D01 hits this in
practice.

### 9.2 Risk: scenario citation lookup fails at prompt-compose time

**Symptom.** The decomposition validator passes, but the pipeline's
prompt composer can't resolve a scenario id (e.g., roadmap was
regenerated after decomposition without re-validating).

**Mitigation.** `_inline_roadmap_scenarios` fails loudly with a clear
error naming the task id and the unresolved citation. Better than a
silent prompt with missing content (which would burn executor budget on
a task with no actual spec). The fix is to re-run decomposition against
the new roadmap output.

### 9.3 Risk: `roadmap_component` placement awkward for cross-cutting tasks

**Status:** Already resolved upstream. The planning skill's project-setup
component (landed 2026-04-27, validated in P05) means scaffold tasks
reference `roadmap_component: "project-setup"` and validate cleanly.
For features that extend an existing service (no Project Setup
component), scaffold tasks don't exist.

### 9.4 Risk: `roadmap_security_scenarios` ID-based lookups lose specificity

**Symptom.** A component grows two security scenarios under the same
OWASP ID. With the new schema, each has a unique `id` field, so this
isn't a problem at the citation layer. But could ID generation produce
near-identical IDs that confuse a reviewer?

**Mitigation.** The model writing scenario `id` should follow the same
naming discipline as other fields — distinct, descriptive, kebab-case.
The roadmap skill's validator enforces uniqueness within a component;
near-duplicates would be caught at schema time. Reviewer concern beyond
that is the same as for any other identifier scheme.

### 9.5 Risk: pipeline doesn't know about the new fields

**Symptom.** A pipeline deployed before the implementation-skill change
sees `roadmap_component` etc. in `tasks.json` but ignores them.

**Mitigation.** The fields are additive; ignoring them keeps existing
behavior. The pipeline's `compose_prompt.py.template` change is what
*activates* the inlining — without it, the fields are metadata. This
means the three changes can land in any order without breaking the
in-between states. Full benefit requires all three; partial benefit
follows monotonically from each.

If a pipeline's `compose_prompt.py.template` predates the inlining
change but its `tasks.json` has citation fields, the prompts will look
like the old (paraphrased) prompts — but the task description no
longer has `Behaviors to test:` either, so the executor sees less
information than before. This is the broken-in-between-state to avoid:
**land the implementation-skill change before regenerating any
project's pipeline against decomposition output that omits `Behaviors
to test:`.**

### 9.6 Risk: refactoring decomposition mid-flight on the test project

**Symptom.** The R03 roadmap output is fresh; the design doc is
current; a new decomposition under the new schema is the next thing to
run. If the refactor lands but the validator has bugs, D01 fails for
refactor reasons, not decomposition reasons, making it hard to
evaluate.

**Mitigation.** Smoke-test the schema validators against synthetic
inputs *before* running D01 on real data. Same pattern as the roadmap
skill's validator smoke tests — happy path, missing-field,
mismatched-slug, mismatched-scenario-id, malformed schemas. Document
the smoke-test procedure in D01's trial record.

---

## 10. Acceptance trials

### 10.1 R03 (revived; retargeted)

R03 was previously queued as a Project Setup component validation
trial. R02-rerun (2026-05-01) implicitly exercised that flow, so R03's
original purpose is satisfied. R03 is **revived with a new purpose:**
validate the scenario `id` field addition end-to-end.

- **Trial code:** R03.
- **Target:** `~/health-data-ai-platform/`, feature
  `airflow-gdrive-ingestion`.
- **Inputs:**
  - Existing R02 `roadmap.json` and `components.json` (regenerate from
    the same design doc).
- **Acceptance bar:**
  - Updated `roadmap_schema.py` accepts `id` on FunctionalScenario and
    SecurityScenario.
  - Validator enforces format (kebab-case) and uniqueness within a
    component.
  - Regenerated `roadmap.json` has `id` on every scenario; IDs are
    kebab-case; no duplicates within any component.
  - A second regeneration preserves existing IDs (manual diff check
    against the first regeneration's output).
  - Project-shipped `roadmap_schema.py` includes the new field;
    project-shipped `components_schema.py` is unchanged but is
    re-shipped as part of Phase 3.
- **File at:** `trials/R03-roadmap-scenario-id-field.md`.

### 10.2 D01

After R03 lands and the decomposition refactor lands, regenerate the
decomposition.

- **Trial code:** D01 (D for decomposition; first decomposition-skill
  iteration trial).
- **Target:** `~/health-data-ai-platform/`, feature
  `airflow-gdrive-ingestion`.
- **Inputs:**
  - `docs/roadmap/airflow-gdrive-ingestion/` (post-R03)
  - `docs/design/airflow-gdrive-ingestion-<latest>.md`
  - `prototypes/airflow-gdrive-ingestion/`
- **Output target:** `tasks/airflow-gdrive-ingestion/` (note: feature
  name updated from `airflow-google-drive-ingestion` per the roadmap
  skill's slug; old path can be deleted manually).
- **Acceptance bar:**
  - Decomposition skill loads `components.json` and `roadmap.json`
    via project-shipped schemas without error.
  - Phase 1 proposal shows the components verbatim from the registry —
    expected to be five (project-setup, drive-downloader, sqlite-parser,
    minio-uploader, rabbitmq-publisher); no boundary inference.
  - Generated `tasks.json` validates against the new schema with no
    errors.
  - Every task has `roadmap_component` set to one of the registered
    slugs. Scaffold tasks reference `project-setup`.
  - Every test task and every implementation task with tests has
    non-empty `roadmap_functional_scenarios` OR
    `roadmap_security_scenarios`.
  - Every cited scenario `id` resolves against `roadmap.json`.
  - Validator smoke tests pass on five synthetic cases.
  - Summary table renders with new columns.
  - Task descriptions follow the updated template (no `Behaviors to
    test:` section).
- **File at:** `trials/D01-decomposition-roadmap-integration.md`.

### 10.3 T15

After D01 lands, run the implementation pipeline.

- **Trial code:** T15.
- **Target:** Same feature; pipeline regenerated for the new
  decomposition output.
- **Acceptance bar:**
  - Pipeline imports the new `task_schema.py` cleanly.
  - `compose_prompt.py` inlines roadmap scenarios for tasks with
    citations; prompts are visually correct (manual spot-check of two
    task prompts in `logs/prompts/`).
  - Executor sees richer Given/When/Then content than the previous
    paraphrased prose; this is observable in prompt files.
  - End-to-end pipeline run completes (existing T01–T14 acceptance bar
    still applies).
- **File at:** `trials/T15-roadmap-driven-pipeline.md`.

---

## 11. Implementation order

A fresh session should do this work in this sequence so each step is
reviewable in isolation:

1. **Roadmap skill changes first** (smallest blast radius; unblocks
   everything else).
   - Update `roadmap_schema.py`: add `id` field, validators.
   - Update `references/roadmap-json-format.md` and
     `references/phase-2-generation.md`.
   - R03 trial: regenerate airflow-gdrive-ingestion roadmap; verify
     IDs, uniqueness, regeneration-stability.
   - File R03 trial record. Update memory repo (`_INDEX.md`,
     `_SUMMARY.md`, `README.md`).

2. **Implementation skill changes second** (small but unblocks D01's
   full benefit).
   - Update `templates/nodes/compose_prompt.py.template`: add
     `_inline_roadmap_scenarios`; add `{{ROADMAP_JSON_PATH}}`
     placeholder; wire into `_build_prompt`.
   - Update `references/phase-2-generation.md`: add the placeholder
     to the substitution table.
   - No trial yet; this change is exercised by T15 after D01.

3. **Decomposition skill changes third** (the bulk of the work).
   - Update `task_schema.py`: add the three task fields, two top-level
     fields, four new validators.
   - Smoke-test the validators against synthetic inputs.
   - Update `references/analysis-guide.md`,
     `references/task-writing-guide.md`,
     `references/output-format.md`, `SKILL.md`.

4. **D01 trial.** Regenerate decomposition; verify acceptance bar.
   File trial record; update memory repo.

5. **T15 trial.** Run pipeline against D01's tasks. Verify scenario
   inlining works end-to-end. File trial record; update memory repo.

6. **Memory repo updates throughout.** Each trial gets a record.
   `LEARNINGS.md` "From Decomposition Skill" subsection gains entries
   for the design choices made here. `README.md` "Current State" gets
   updates after each step. `LEARNINGS.md` may also gain a
   "From Implementation Skill" entry about the inlining pattern's
   parallel to dependency inlining.

7. **(Manual)** User commits and pushes both repos after each step.

---

## 12. What this plan deliberately doesn't change

- **The roadmap skill's structure beyond the `id` field addition.** No
  changes to component-level schema, validation rules, or Phase 1/2/3
  flow. Just a new field on scenarios.
- **The decomposition skill's TDD discipline.** Strict TDD pairing,
  stub discipline, `test_command` rules, `expected_test_failure_modes`
  semantics — all unchanged.
- **The implementation skill's pipeline architecture.** Templates stay
  templates; LangGraph state machine is untouched; executor chain
  unchanged. Just a new prompt-composition helper.
- **The `description` template's other sections.** `Component`,
  `Component type`, `Interface`, `Expected test failure mode`, `Out
  of scope` all stay. Only `Behaviors to test:` is removed.
- **`security_considerations` field.** Stays as freeform escape hatch.
- **`prototype_references` field.** Stays removed.
- **Output directory layout.** `tasks/<feature>/` with `tasks.json`
  and `task_schema.py`. No new files.
- **The "no per-task .md files" rule.** Reviewers read the summary
  table at decomposition time and the JSON for detail.

---

## 13. One open question to settle in D01's trial record

Per-component decomposition (decompose component-by-component instead
of feature-as-a-whole) is left explicitly out of scope for this
refactor. The schema change in §4.3 sets it up as a *future
possibility* — once every task declares its component, the decomposer
could in principle process one component at a time, presenting the
user with one component's tasks before moving to the next.

The open question for D01's trial record: does feature-as-a-whole
decomposition show signs of scaling problems on realistic features?
If yes, per-component decomposition becomes a separate plan with its
own design space. If not, `roadmap_component` stays metadata for now.

The principle to surface in the answer: **least non-determinism, least
drift.** Per-component decomposition would require multiple decomposer
invocations with shared context, coordination of cross-component task
IDs, and merge logic — each a new failure surface. The bar for
adopting it should be a real scaling problem, not a hypothetical one.
