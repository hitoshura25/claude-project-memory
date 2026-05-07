# D02 — Decomposition Skill: CWD-Relative Path Resolution Bug

**Date**: 2026-05-06
**Skill**: prototype-driven-task-decomposition (primary), prototype-driven-implementation (parallel fix)
**Target**: airflow-gdrive-ingestion (T15 first attempt)
**Result**: ⚠️ Schema-side path-resolution bug surfaced at first runtime;
fix landed in upstream skills; T15 blocked until user regenerates
decomposition + pipeline from fixed skills.

## What surfaced

T15 first attempt: user ran `python run.py` from
`pipelines/airflow-gdrive-ingestion/` (the natural directory for a
generated pipeline). `load_tasks_node` invoked
`TaskDecomposition.model_validate_json(...)`, which fired
`validate_roadmap_component_registered` → `_load_roadmap_schemas(...)` →
`Path(self.components_json_path).parent.resolve()`. With CWD set to
the pipeline directory, the relative path
`docs/roadmap/airflow-gdrive-ingestion/components.json` resolved to
`<pipeline-dir>/docs/roadmap/...` — the wrong place. The schema raised
`FileNotFoundError` before the pipeline could reach any executor.

Root cause: schema-side path resolution implicitly depended on
`Path.cwd()` matching the project root. The contract on
`components_json_path` and `roadmap_json_path` was already documented
as *"path from project root"*, but the resolver wasn't honoring that
contract — `Path(p).resolve()` resolves against CWD when `p` is
relative. The runtime caller's CWD was never the project root.

## Why earlier validation didn't catch this

D01's smoke tests against the schema all ran from the project root
(implicit via the validation harness's CWD). The decomposition skill's
own validator passes there because CWD happens to equal the inferred
project root — schema and CWD agree by coincidence. The pipeline
runtime is the first caller whose CWD differs from project root.

The implementation skill's Phase 3 had a `python -m py_compile` step,
which validates syntax but doesn't execute import-time validators. It
also had a "schema import check" but that step only imported the
schema class — it didn't invoke `model_validate_json` against
`tasks.json`, which is what fires the cross-file validators that
contain the bug.

## Pattern surfaced

`cwd-relative-path-resolution`. New tag. The shape: skill A produces
an artifact with documented project-relative paths; skill B (or B's
output) consumes the artifact from a CWD that isn't the project root;
A's path-resolution code uses `Path(p).resolve()` (CWD-implicit) when
the contract requires resolving against an explicit project root.

This is a recurrence-class of the broader "implicit-context bites at
runtime" failure family (compare T02's enum-as-object serialization,
T08's config-value drift). The structural fix, as in those cases, is
to make the dependency explicit at the data-flow boundary —
`_resolve_project_path` instead of `Path.resolve()`.

## Fix

Three changes, all in upstream skills (no project-side patches per the
"don't make changes to health-data-ai-platform" directive):

### 1. `task_schema.py` (decomposition skill)

Added `_PROJECT_ROOT` constant inferred from the schema's installed
location (`Path(__file__).resolve().parent.parent.parent`,
i.e., three `.parent` hops: file → feature dir → tasks/ → project
root) and a `_resolve_project_path(p: str) -> Path` helper that
returns absolute paths unchanged and resolves relative paths against
`_PROJECT_ROOT`. Replaced four call sites:

- `_load_roadmap_schemas`: `components_dir = Path(p).parent.resolve()`
  → `_resolve_project_path(p).parent` (×2)
- `validate_roadmap_component_registered`:
  `Path(self.components_json_path).resolve()` → `_resolve_project_path(...)`
- `validate_roadmap_scenarios_resolve`:
  `Path(self.roadmap_json_path).resolve()` → `_resolve_project_path(...)`

Updated the `components_json_path` and `roadmap_json_path` field
descriptions to make the resolution rule explicit ("Absolute paths
are also accepted; relative paths are resolved against the project
root inferred from task_schema.py's installed location").

### 2. `compose_prompt.py.template` (implementation skill)

The pipeline already had a CWD-correct guard inline in `_load_roadmap`
(`if not roadmap_path.is_absolute(): roadmap_path = config.PROJECT_ROOT / roadmap_path`).
Hoisted that guard into a `_resolve_project_path(p: str) -> Path`
helper with the same name and shape as the schema's, but sourcing root
from `config.PROJECT_ROOT` instead of `__file__`. The two helpers
share name + shape; their roots differ because each has access to a
different concrete answer. Pattern is greppable across the codebase.

### 3. `phase-3-handoff.md` + `SKILL.md` (implementation skill)

Added a "Smoke Test" section to `phase-3-handoff.md` between Syntax
Check and Precondition Validation. It runs from the pipeline directory
(critical — same CWD as `python run.py`) and exercises:

- `load_tasks_node({...})` — transitively runs every schema-side path
  validator, catching schema-side regressions of this exact bug class.
- `compose_prompt._inline_roadmap_scenarios(first_cited_task)` —
  exercises the implementation-side `_resolve_project_path`. Skipped
  with a note if no tasks have citations.

The previous "Schema import check" step in Precondition Validation is
now informational — it's strictly weaker than the smoke test (imports
the class but doesn't validate against `tasks.json`). Renumbered the
Phase 3 step list in SKILL.md to add the smoke test as step 3,
demoting precondition validation to step 4 and run instructions to
step 5.

## Why two helpers, not one

The two skills can't share a runtime import — each must produce a
self-contained project artifact. The schema infers project root from
`__file__`; the implementation pipeline reads `config.PROJECT_ROOT`
(set explicitly at Phase 2 generation time). Different sources, same
shape. Named identically (`_resolve_project_path`) so a future reader
or `grep` finds both implementations of the pattern.

The alternative — having `compose_prompt` import `PROJECT_ROOT` from
the schema instead of using `config.PROJECT_ROOT` — was considered and
rejected. It would couple the implementation pipeline's path-handling
to a transitive dependency for no gain; `config.PROJECT_ROOT` is the
explicit contract and should stay the source of truth on that side.

## Acceptance bar

| Criterion | Result |
|---|---|
| Schema-side `_resolve_project_path` helper added | ✅ |
| Four call sites in `task_schema.py` use the helper | ✅ |
| Field-description prose makes the resolution rule explicit | ✅ |
| Implementation-side `_resolve_project_path` helper added (template) | ✅ |
| Inline absolute/relative guard in `_load_roadmap` replaced | ✅ |
| Smoke test added to phase-3-handoff.md | ✅ |
| Phase 3 step list in SKILL.md renumbered | ✅ |
| Two helpers share name + shape; sources differ | ✅ |
| **Project-side artifacts (`task_schema.py`, regenerated pipeline) unchanged** | ✅ — per directive, all changes are skill-side; user regenerates from fixed skills |

## Implications

- **T15 is blocked** until the user regenerates decomposition (which
  reships the project's `task_schema.py` from the fixed skill source)
  and regenerates the pipeline (which produces a `compose_prompt.py`
  with the new helper).
- **R03 / D01 are still valid trials.** The decomposition output
  (`tasks.json`) didn't change shape — only the validator logic did.
  The same `tasks.json` that D01 produced will validate cleanly under
  the fixed schema, *if* validated from the project root or from any
  other CWD.
- **Smoke test is a permanent guard.** Future skill changes that touch
  path resolution in either `task_schema.py` or `compose_prompt.py`
  surface during Phase 3 instead of at first pipeline run. The smoke
  test exercises both implementations of the `_resolve_project_path`
  pattern from the same CWD as runtime, which is the only context
  where this bug class is observable.

## Cross-cutting pattern note

D02 fits the broader memory-repo arc cleanly:

- T14: prose was lossy transport between decomposer and pipeline →
  promote `test_command` to typed schema field.
- R02-prep: prose claimed verification that hadn't happened →
  promote spec data to JSON file with provenance fields.
- R03: prose-paraphrased scenarios were the only handle → promote to
  citable IDs.
- D01: implicit boundary inference → explicit roadmap consumption.
- **D02: implicit CWD dependence in path resolution → explicit project-
  root-anchored helper.**

The pattern: when something behaves correctly in some contexts and
fails in others, the structural fix is to remove the implicit
dependence on context (CWD, prose transport, paraphrase, training-data
recall). Each fix is a small local change; the cumulative effect is a
codebase whose contracts hold regardless of caller context.

The "force visibility" pattern from P01–P03 still applies, just at a
different level: making the project-root dependency a named helper
makes the contract visible at every call site, which means future
readers and future Claudes can tell at a glance whether a piece of
path-handling code honors the contract or punts on it.

## Trial-earned principle

> **Path resolution must name its anchor.** When a skill output
> documents paths as "relative to project root," the resolver must
> resolve against an explicit project root, not against `Path.cwd()`.
> CWD-implicit resolution works in some contexts (e.g., validation
> from project root) and silently fails in others (e.g., pipeline
> runtime from a subdirectory). The structural fix is a named helper
> at every resolution site that takes its anchor explicitly. Skills
> that produce path-bearing artifacts ship a helper with their output;
> skills that consume those artifacts use the producer's helper, or
> implement a same-named helper sourcing the anchor from their own
> config.

Adds to LEARNINGS.md when it next gets a refresh.
