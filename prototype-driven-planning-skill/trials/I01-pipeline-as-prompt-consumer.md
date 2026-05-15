# I01 — Pipeline-as-prompt-consumer refactor

**Date:** 2026-05-14
**Skill:** prototype-driven-implementation
**Result:** ✅ Architectural refactor landed; validated by T16
**Tags:** `prompt-consumer-pipeline`, `single-source-of-truth-for-prompt-rendering`,
`prompt-mutation-eliminated`, `co-located-execution-artifacts`,
`prerequisite-validation-at-startup`, `structural-signal-chain-completed`

---

## What this iteration delivers

The implementation skill (LangGraph pipeline) previously composed prompts
at runtime from `tasks.json` + `roadmap.json` via a templated
`compose_prompt.py` node that duplicated logic from the prompt-composition
skill. This iteration removes that duplication entirely: the pipeline now
reads the pre-generated prompt files written by the
`prototype-driven-prompt-composition` skill, passes them through to
executors verbatim, and writes per-attempt error logs to the paths the
prompts already reference.

The structural change is small in code but architecturally significant:
the prompt-composition skill becomes the single source of truth for
prompt content; the pipeline becomes pure orchestration; and the
file-based contract between them is well-defined and inspectable.

This iteration is the structural counterpart to PC01 (the prompt-
composition skill's first iteration), and completes the cliff-edge
arc's signal chain: prototype breadcrumb → design-doc label (P04) →
roadmap criticality (R04) → task citation (D03) → prompt subsection
framing (PC01) → executor consumption (I01). Each layer's signal
survives intact to the next; the implementation skill no longer has
the opportunity to mutate prompt content.

## Background: why the refactor was needed

Three pressures forced the change:

**1. Stale runtime composition.** The pipeline's
`compose_prompt.py.template` had its own preamble (`_PROJECT_CONTEXT`),
scenario rendering (`_inline_roadmap_scenarios`), and dependency
inlining (`_inline_dependencies`). When the prompt-composition skill
gained the criticality grouping (PC01), the verification section
(Option B), and task-type-specialized preambles, the pipeline's
runtime composition lagged behind. Two implementations of
substantially the same logic diverged in non-obvious ways.

**2. Prompt as opaque per-attempt artifact.** The runtime composer
mutated prompts per attempt (injecting "Previous Executor Attempts"
or "Previous Attempt (Failed)" headers, embedding error log
absolute paths, varying based on `retry > 0` or `tier > 0`). The
canonical prompt never existed on disk between runs; what the
executor saw was different from what a manual reviewer could inspect.

**3. Pipeline-relative log paths.** Error logs lived at
`pipelines/<feature>/logs/lint/<task-id>_error_<timestamp>.txt`. The
prompt's `## Previous Attempts` section pointed at
`logs/lint/<task-id>/` (relative to executor CWD), so an executor
running from a non-pipeline directory (e.g., Aider with `--cd
services/<service>/`) might resolve the path to a service-internal
`logs/` directory that doesn't exist. The pipeline wrote to one
place; the executor looked in another.

The fix package addresses all three with a single architectural
shift: the pipeline does no prompt composition, reads pre-generated
files verbatim, and writes error logs to the paths those files
reference.

## What changed

### Upstream: prompt-composition skill log-path convention

Before I01 could land, the prompt-composition skill needed to settle
where error logs live. The pre-existing convention (`logs/<lint|
tests>/<task-id>/` relative to nothing in particular) had three
reasonable interpretations (project root / service root / CWD) and
no framing line to disambiguate. The fix moved logs to
`tasks/<feature>/logs/<lint|tests>/<task-id>/attempt-<N>-tier<M>.txt`
with an explicit "paths relative to the project root" framing in
every prompt's `## Previous Attempts` section.

Three benefits to this location:

1. **Orchestrator-agnostic.** The prompt-composition skill writes
   prompts to `tasks/<feature>/prompts/`; adding `logs/` as a sibling
   needs no knowledge of pipeline-skill conventions.
2. **Path-unambiguous.** Project-root-relative + explicit framing
   resolves the same regardless of executor CWD.
3. **Co-located.** `prompts/` (skill output) and `logs/` (orchestrator
   output) live under one parent; the relationship is obvious in a
   directory listing.

Implementation: 4 small edits to
`scripts/compose_prompts.py` (constant rewrite, `_previous_attempts_
section` takes `feature` param, `_build_prompt` threads it through,
`main()` passes it from `args.feature`) + substantial rewrite of
`references/log-conventions.md`.

### Code changes (templates)

**`templates/nodes/compose_prompt.py`** — new ~60-line verbatim node:
```python
def compose_prompt_node(state: PipelineState) -> dict:
    task_id = state["current_task_id"]
    prompt_path = config.PROMPTS_DIR / f"{task_id}.md"
    if not prompt_path.is_file():
        # log error pointing back to prompt-composition skill
        return {"current_prompt_path": None}
    if prompt_path.stat().st_size == 0:
        return {"current_prompt_path": None}
    return {"current_prompt_path": str(prompt_path)}
```
No mutation, no augmentation, no retry-context injection. The
prompt's own `## Previous Attempts` section is the retry-context
vehicle; the executor reads error logs from the directory the
section names.

**`templates/nodes/compose_prompt.py.template`** — tombstoned for
manual deletion. The previous file had `{{PROJECT_NAME}}`,
`{{PROJECT_DESCRIPTION}}`, and `{{INLINEABLE_EXTENSIONS}}`
placeholders; none are needed by the new node.

**`templates/nodes/verify_task.py`** — `_write_error_file` rewritten:
```python
log_subdir = (
    config.PROJECT_ROOT / "tasks" / config.FEATURE_NAME
    / "logs" / error_type / task_id
)
log_subdir.mkdir(parents=True, exist_ok=True)
filename = f"attempt-{retry + 1}-tier{executor_tier}.txt"
path = log_subdir / filename
```
All 6 call sites updated to pass `retry` and `executor_tier`. The
module docstring updated to reflect the new paths and the
pipeline-orchestration / executor-visible distinction.

**`templates/nodes/check_preconditions.py`** — added two new checks
after the existing scaffold + tooling checks:
1. `PROMPTS_DIR` is a directory
2. Every task in `state["all_tasks"]` has a `<task-id>.md` file in
   `PROMPTS_DIR` and the file is non-empty

`_fail` split into `_fail_scaffold` and `_fail_prompts` with
remediation instructions that point at the relevant skill
(implementation skill for scaffold issues, prompt-composition
skill for missing prompt files).

**`templates/config.py.template`** — three placeholder changes:
- `FEATURE_NAME = "{{FEATURE_NAME}}"` added as top-level constant
  (was previously inlined into `TASKS_DIR`)
- `PROMPTS_DIR = TASKS_DIR / "prompts"` added as computed value
- `ROADMAP_JSON_PATH = "{{ROADMAP_JSON_PATH}}"` removed entirely
  (the runtime composer is gone)

### Reference documentation

**`SKILL.md`** — five sections updated:
- Quick Reference adds `tasks/<feature>/prompts/` to inputs and
  `tasks/<feature>/logs/{lint,tests}/<task-id>/` to outputs; adds
  prerequisite skills list (decomposition + prompt-composition)
- Skill Layout removes `compose_prompt.py.template`, adds
  verbatim `compose_prompt.py`
- How to Start step list adds prompts-directory check to
  prerequisite validation
- Phase 2 step 4 replaced ("Copy `nodes/compose_prompt.py`
  verbatim" instead of "Generate from template")
- Phase 3 smoke test updated to exercise `compose_prompt_node`
  (file-presence check) instead of `_inline_roadmap_scenarios`
- Principles: new "Prompts are sourced from the prompt-composition
  skill, not composed at runtime" + 3 existing principles updated
  to remove references to runtime composition

**`references/phase-1-analysis.md`** — new "Prompt-Composition
Prerequisite" section after task-decomposition validation,
documenting that the pipeline depends on the prompt-composition
skill having run first and listing the directory + per-file checks.

**`references/phase-2-generation.md`** — Step 3 replaced. The old
section was a long block on generating `compose_prompt.py` from a
template with placeholder substitution and a discussion of why the
template existed. The new section is short: "`nodes/compose_prompt.py`
is copied verbatim. No substitution, no editing." Plus a new
"Error-log paths the pipeline writes to" subsection documenting the
file-based contract with the prompt-composition skill. Placeholder
table updated (`{{ROADMAP_JSON_PATH}}` removed; `{{FEATURE_NAME}}`
description updated).

**`references/phase-3-handoff.md`** — Smoke Test section rewritten.
The old test exercised `compose_prompt._inline_roadmap_scenarios` to
catch CWD-relative path resolution bugs in the runtime composer. The
new test exercises `compose_prompt_node` for the first non-scaffold
task, verifying the pre-generated prompt file is found and non-empty
at the expected location.

**`references/executor-integration.md`** — "Prompt Composition"
section renamed and rewritten as "Prompt Passthrough." The
old section described the runtime composer's preamble, retry
patterns, and dependency inlining. The new section describes how
the path produced by `compose_prompt_node` flows to each executor
(Aider's `--message-file`, Claude/Gemini CLI's `-p "$(cat ...)"`,
the working-directory and file-rebasing details, and the
zero-mutation retry/escalation contract).

## What this leaves untouched

The refactor's blast radius was narrowed deliberately:

- **`templates/run.py`, `templates/graph.py`, `templates/agent_bridge.py`,
  `templates/pipeline_state.py`, `templates/requirements.txt`** —
  unchanged. The state graph wiring, executor dispatch, file
  rebasing, and state schema are all compatible with the new
  compose_prompt node.
- **`templates/nodes/{execute_task,load_tasks,report}.py`** —
  unchanged. They consume `current_prompt_path` from state; the
  refactor changes what that path points to (a verbatim file
  instead of a generated one) but not the interface.
- **`templates/nodes/__init__.py`** — empty file; no imports to
  update.
- **`references/langgraph-patterns.md`** — generic state-machine
  reference, not affected by this refactor.

The non-touched files validate that the refactor was structurally
clean: it changed *what* one node does, not *how* the pipeline
holds itself together.

## Validation: T16

T16 (same day, this filename's sister record) is the first
end-to-end run against the refactored pipeline. Its findings:

**The architectural promises held:**
- `compose_prompt_node` logged identical prompt byte counts across
  retry attempts on task-03 (no mutation)
- `verify_task` wrote error logs to the new
  `tasks/<feature>/logs/<lint|tests>/<task-id>/attempt-<N>-tier<M>.txt`
  paths
- `check_preconditions` validated the prompts directory and all 13
  per-task files at startup
- Auto-resume from Phase A correctly skipped task-01
- Tier escalation triggered correctly when tier-0 exhausted retries
- No refactor-introduced bugs surfaced

**The trial still failed** at task-03, but for reasons orthogonal
to the refactor (Gemini 429 cascade, Claude tier-1 timeout, no
diagnostic capture on timeout, E902 misclassified as code-quality
failure). These are pre-existing orchestration concerns the
refactor was not intended to address. T16 documents them as
five RCs (RC-1 through RC-5) and routes them to a separate
orchestration-robustness workstream.

## Structural-signal-chain completion

The cliff-edge arc's structural enforcement chain is now end-to-end:

| Layer | Skill | Mechanism | Validator |
|-------|-------|-----------|-----------|
| 1. Prototype evidence | (manual, Phase 2 of planning) | Cliff-edge probe records | (none — Phase 2 is exploration) |
| 2. Design-doc label | prototype-driven-planning | `**Cliff edge:**` prose label | Phase 3 review (Rule 3 in Judgment vs. Observation) |
| 3. Roadmap criticality | prototype-driven-roadmap | `criticality: cliff_edge` field | `validate_roadmap.check_cross_file` (cliff-edge coverage) |
| 4. Task citation | prototype-driven-task-decomposition | `roadmap_{functional,security}_scenarios` lists | `TaskDecomposition.validate_cliff_edge_coverage` |
| 5. Prompt rendering | prototype-driven-prompt-composition | "Cliff edges (non-negotiable boundaries…)" subsection | (rendering is structural; no separate validator) |
| 6. Executor consumption | prototype-driven-implementation | `compose_prompt_node` reads prompt verbatim | `check_preconditions` (prompts present) |

Before I01, layer 6 was the weak link: the pipeline could mutate
the prompt's rendered structure between PC01's output and what the
executor saw. A model-introduced bug in `compose_prompt.py.template`,
or stale logic relative to PC01, could silently strip cliff-edge
framing. With I01, layer 6 is structurally inert: the pipeline
cannot mutate what layer 5 produced.

This is a "structural signal from prose label" pattern applied at
the consumption end of the chain. P04 introduced the structural
signal (the label); each downstream skill carries the signal in a
typed way (R04 criticality, D03 citations, PC01 grouping); I01
removes the only place the signal could have been silently stripped
before reaching the executor.

## Comparison to other terminal-stage iterations

This is the first iteration of the implementation skill since the
three-skill decomposition refactor and the cliff-edge arc landed.
Earlier implementation-skill iterations addressed individual
failure modes (T14's `test_command` schema field, T15's bootstrap
cascade and the Phase A/B scaffold split); I01 is the first that
addresses an architectural question about the skill's role in the
chain.

Two observations from this:

**1. The "consumer-only" terminal stage is a recurring pattern.**
PC01 made the prompt-composition skill consume the upstream chain's
typed output (roadmap criticality, decomposition citations) and
produce a final rendered artifact. I01 makes the implementation
skill consume PC01's artifact and produce executor-visible work.
Both skills shrank in scope as the chain matured — they now do less
because the chain does more upstream. This is healthy.

**2. The implementation skill remains the only skill that interacts
with stateful external systems** (executors, the filesystem, the
network). The five upstream skills produce typed JSON or markdown
artifacts; only the implementation skill runs code, calls executors,
and writes log files. I01 narrows that responsibility further by
removing prompt rendering from the pipeline's job description.
What remains — orchestration, executor dispatch, verification, retry,
escalation — is now distinguishable from rendering. T16's surfaced
issues (RC-1 through RC-5) are all in the residual responsibility,
not in the parts removed by I01.

## Why no project-side regeneration of the airflow pipeline

The user regenerates the project-side `pipelines/airflow-gdrive-
ingestion/` from the updated implementation skill. Per the
"upstream fixes only" project convention, no patches landed against
the existing generated pipeline files — the skill change is the
fix; regeneration carries the change to the project. The next
trial (T16) was the first run against the regenerated pipeline.

## What comes next

T16 surfaced three independent workstreams:

**Workstream A — Orchestration robustness.** Pipeline-internal,
no upstream-skill changes. Addresses RC-1 through RC-5: stream
executor stdout/stderr to log files during execution; detect
environmental failures (429, network, daemon down) at the
executor-bridge layer; distinguish "executor produced nothing"
from "executor produced wrong code" in verify_task; per-tier or
per-prompt-size timeout configuration; cosmetic fix for
`lint=✗` on skipped tasks.

**Workstream B — Executor tier reassessment.** Project-side, not
skill-side. Replace Gemini-2.5-pro on the test role with
Aider+Qwen 3 Coder 30B (LM Studio) for the airflow project.
Validates against the manual three-way comparison that ran on
task-01 and task-02 earlier this session.

**Workstream C — Retry policy reconsideration.** The current
`MAX_RETRIES_PER_TASK = 1` (effectively 4 attempts via 2 tiers ×
2 attempts) burns all 4 on environmental failures. Workstream A
makes this less of an issue; C is the wrong fix order.

Recommendation in T16: A before C. The right structural fix is to
not waste retries on environmental failures, not to compensate by
raising the budget.

I01 enables these workstreams to be discussed cleanly: with prompt
rendering out of the pipeline's responsibilities, orchestration
issues are isolated. Pre-I01, "this attempt failed" might have
meant "the runtime composer produced wrong content" or
"the executor produced wrong code" — two different failure
classes muddled together. Post-I01, the prompt is the same across
attempts (verified by the byte-count log lines), so any
attempt-to-attempt variation is in the executor or the
orchestration loop, not the rendering.

## Related records

- **T16** — first end-to-end run against the refactored pipeline;
  validates the refactor architecturally; surfaces RC-1 through
  RC-5 in the residual orchestration responsibility
- **PC01** — prompt-composition skill's first iteration trial; the
  upstream change I01 consumes
- **D03** — decomposition skill's third iteration; the
  `FileChange.description` removal that motivated dropping runtime
  composition's dependency-inlining of file descriptions
- **R04** — roadmap skill's fourth iteration; the criticality +
  verification fields that PC01 renders and I01 propagates intact
- **P04** — planning skill's fourth iteration; the `**Cliff edge:**`
  label whose structural signal completes its chain at I01
- **T15** — last pipeline run before the refactor; surfaced the
  bootstrap-as-pipeline-task wrong-shape that led to the Phase A/B
  scaffold split (which I01 builds on)

## Skill files touched

```
skills/prototype-driven-implementation/
├── SKILL.md                                        [updated]
├── templates/
│   ├── config.py.template                          [updated: FEATURE_NAME, PROMPTS_DIR, ROADMAP_JSON_PATH removed]
│   └── nodes/
│       ├── compose_prompt.py                       [NEW — verbatim node]
│       ├── compose_prompt.py.template              [tombstoned]
│       ├── verify_task.py                          [updated: new error-log paths, all 6 call sites]
│       └── check_preconditions.py                  [updated: prompts-dir checks added]
└── references/
    ├── phase-1-analysis.md                         [updated: Prompt-Composition Prerequisite section]
    ├── phase-2-generation.md                       [updated: Step 3 replaced, placeholder table updated]
    ├── phase-3-handoff.md                          [updated: Smoke Test section]
    └── executor-integration.md                     [updated: Prompt Composition → Prompt Passthrough]

skills/prototype-driven-prompt-composition/         [prerequisite changes for I01]
├── scripts/compose_prompts.py                      [updated: feature-aware previous-attempts paths]
└── references/log-conventions.md                   [updated: tasks/<feature>/logs/ layout]
```

10 files touched across two skills. No project-side artifacts
modified per the upstream-fixes-only convention; user regenerates
the airflow pipeline from the updated implementation skill.
