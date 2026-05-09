# T15 — Pipeline Run: Bootstrap Cascade Surfaces Phase A/B Need

**Date**: 2026-05-07
**Skill**: prototype-driven-implementation
**Target**: airflow-gdrive-ingestion (post-D02 regenerated decomposition + pipeline)
**Result**: ❌ Both attempts blocked at task-01 on bootstrap. Surfaced
the architectural issues that motivated the 2026-05-07 Phase A/B
refactor. Validation deferred to T16 (post-refactor).

> T15 was meant to be the end-to-end validation of the three-skill
> decomposition refactor (R03 → D01 → D02 → T15). It instead surfaced
> a deeper architectural issue: bootstrap as a pipeline task is the
> wrong shape for environmental failures. T16 supersedes T15; the
> refactor that T16 validates is documented in
> `phase-a-scaffold-split-plan-2026-05-07.md`.

## What ran

Two attempts, same day:

| Run | Timestamp | Final scoreboard |
|---|---|---|
| 1 | 2026-05-07 11:33:18 | 1 failed (task-01) / 1 skipped / 10 not_run |
| 2 | 2026-05-07 15:54:10 | 1 failed (task-01) / 1 skipped / 10 not_run |

Both runs successfully created the scaffold files (`requirements.txt`,
`Dockerfile`, `docker-compose.yml`, `ruff.toml`, package `__init__.py`
files, `tests/conftest.py`). The scaffold marker file existed on disk.
Both runs failed at the bootstrap step inside `verify_task`.

## What failed

`SCAFFOLD_BOOTSTRAP_CMD` failed every attempt (4 total: 3 at tier 0 in
run 1, 2 more across tier 0 and tier 1 in run 2):

```
ERROR: Ignored the following versions that require a different python version:
  2.10.0 Requires-Python ~=3.8,<3.13;
  ... (every Airflow 2.10.x version)
```

Root cause: `apache-airflow[celery]==2.10.5` requires Python `<3.13`.
The host's `python3` is 3.14 (visible in `.venv/lib/python3.14/`).
The bootstrap command `python3 -m venv .venv && .venv/bin/pip install
... apache-airflow[celery]==2.10.5 ... pydantic==2.11.9` inherited
the host's `python3` for the venv and pip resolution failed.

## What the executors tried

**Run 1 (Gemini tier 0, 3 retries):** Identical failure each retry.
Gemini's reasoning at line 642 (run log) was *"I will proceed with
creating the files... and then investigate further if errors recur"* —
it didn't iterate after recurrence. No tier-1 escalation completed;
pipeline terminated at `mark_failed`.

**Run 2 (Gemini tier 0 → Claude tier 1):**
- Tier 0 retry 0–2: same Python-version error each time.
- Tier 1 retry 0: Claude CLI invocation timed out at 300s.
- Tier 1 retry 1: **Claude correctly diagnosed the issue and edited
  `config.py`** to remove `pydantic==2.11.9` (and several other
  Python-3.14-incompatible pins) from `SCAFFOLD_BOOTSTRAP_CMD`,
  reporting:

  > The fix was removing `pydantic==2.11.9` from `SCAFFOLD_BOOTSTRAP_CMD`
  > in `config.py` — pydantic 2.x depends on `pydantic-core` (a Rust
  > extension via PyO3 0.24.1) which fails to build on Python 3.14
  > since PyO3 only supports up to Python 3.13. The scaffold conftest
  > doesn't use pydantic, so it's safe to exclude from the local
  > bootstrap.

  But `verify_task` then re-ran the bootstrap and got the **same
  failure** with the same command string. The pipeline process had
  already imported `config.py` at startup; the on-disk edit didn't
  take effect.

Pipeline marked task-01 failed; cascaded skips on the 11 dependents.

## Three architectural issues surfaced

The conversation that followed worked through three conjoined
questions. The answers landed as a single coordinated refactor.

### Q1: Does decomposition need bootstrap validation?

No — the gap belongs to the implementation skill. Decomposition
authors task-01's *files* (the scaffold's `requirements.txt`,
Dockerfile, etc.); it doesn't author the bootstrap *command*. The
bootstrap command is a function of the host environment (which
Python is on PATH, which package manager is available) and the
project's runtime pin — both of which are implementation-skill
concerns at Phase 1 time.

The right fix isn't a new schema field or validator on decomposition.
It's that the implementation skill's Phase 1 must:
1. Detect the project's runtime version pin (from Dockerfile,
   `pyproject.toml`, `.python-version`, etc.).
2. Choose a runtime-isolation tool that can provision that pinned
   version, not assume host-default Python is acceptable.
3. Test the constructed bootstrap command in a temp dir before
   committing it to `config.py`.

### Q2: Are the two Pythons colliding?

Yes — the pipeline's Python (3.14, runs LangGraph) and the service's
Python (3.11, would run Airflow) are different and must stay
different. The pre-2026-05-07 implementation skill made neither pin
explicit; both were implicitly delegated to whatever `python3`
resolves to on the host. The bug isn't the pipeline's Python being
3.14 — that's fine, LangGraph runs there. The bug is the pipeline
using `python3 -m venv` to create the *service's* venv, which
inherited 3.14 instead of getting 3.11.

The fix is that the service's bootstrap explicitly requests its pinned
runtime version. The tool used to do this is project-specific (uv for
this project; would be different for Node, JVM, Go); the pattern is
ecosystem-agnostic.

### Q3: Should scaffold move out of the pipeline?

Yes. Three converging reasons:

1. **Bootstrap-failure cascade is structurally wrong.** Environmental
   failures shouldn't trigger code-quality retry/escalation logic.
   Run 2 retry-1 burned an executor escalation cycle on a host
   Python version mismatch — no executor can fix that.

2. **Mid-run config edits don't take effect.** The case where the
   executor *correctly diagnoses* the problem and tries to fix it
   produces a new bug class: `config.py` is imported once at startup,
   so an executor's edit lands on disk but not in memory. The
   structural fix is to move bootstrap-changing decisions out of the
   pipeline runtime entirely — into the conversation that generates
   the pipeline.

3. **Skill arc has been pulling scaffold out of regular-task land
   for several trials.** P05 (Project Setup component), T14 (scaffold
   gets its own `test_command`), D01 (scaffold-aware citation rules)
   — each acknowledged scaffold's structural difference from a TDD
   pair. T15's failure was the final argument for finishing the
   separation: scaffold execution moves entirely into Phase 3 of the
   implementation skill, run by Claude Code in conversation. Phase B
   (`python run.py`) executes tasks 02..N only.

## Pattern surfaced

`environmental-vs-code-failure-recovery-mismatch`. New tag. The shape:
a uniform recovery loop (retry-with-same-input → escalate-to-stronger-
executor → cascade-skip) is applied to a class of failures whose
recovery requires a different kind of intervention (interactive
diagnosis with the user, environmental fix, configuration regeneration).
The structural fix is to detect the failure class earlier and route it
to the appropriate recovery path — in T15's case, by removing the
class of failure from the pipeline's scope altogether.

This generalizes a lesson visible across earlier trials but not named
until now: T03's Claude CLI hang (input-source mismatch, not code
issue), T05's verify_task stub gap (semantic mismatch, not retryable),
T08's split-module test bug (test-spec issue, not implementation issue).
Each recurrence loop wasted retries because retries don't help when
the failure class is wrong.

## Refactor

The Phase A/B refactor landed on 2026-05-07. Skill changes:

- **SKILL.md** restructured: Phase 3 now contains "Validation, Scaffold
  Execution, and Handoff" — the Scaffold Execution section is Phase A
  of the user-facing two-phase model. Pipeline-existence precondition
  added.
- **`references/phase-1-analysis.md`**: static bootstrap lookup table
  removed. Runtime-Isolation Research protocol added — describes
  responsibility (provision pinned runtime + isolated install +
  invoke without host PATH) and signals (lockfiles, runtime-pin
  files, build-tool config); the model researches the project's
  actual tooling and verifies with a temp-dir test before committing.
- **`references/phase-2-generation.md`**: two new placeholders
  (RUNTIME_VERSION_PIN, RUNTIME_VERSION_CHECK_CMD); ecosystem table
  reframed as project-tooling-detected rather than prescriptive;
  `check_preconditions.py` added to the template-files list.
- **`references/phase-3-handoff.md`**: rewritten end-to-end with
  Validation / Scaffold Execution / Handoff sections; six-step Phase
  A protocol (read task-01 → create files → run bootstrap → verify
  runtime version → run scaffold's test_command → write
  scaffold-complete marker + initial task_status.json).

Pipeline templates:

- **`nodes/check_preconditions.py`** (new): verifies
  `.scaffold_complete` marker and `BOOTSTRAP_TOOL_CHECKS` at startup.
  Wired between `load_tasks` and `pick_next_task` in `graph.py`.
- **`nodes/verify_task.py`**: `_run_scaffold_bootstrap` and the
  scaffold branch removed entirely. Per-verdict atomic write to
  `logs/task_status.json` added at the end of each verification.
- **`nodes/load_tasks.py`**: merges `task_status.json` on startup so
  passed tasks are skipped on resume.
- **`graph.py`**: `pick_next_task` skips and `mark_failed` exhaustion
  also persist to `task_status.json`.
- **`pipeline_state.py`**: `bootstrap_done` field removed from state.
- **`run.py`**: auto-resume documented as default; `--start` reframed
  as override (force-mark earlier tasks passed).
- **`config.py.template`**: RUNTIME_VERSION_PIN and
  RUNTIME_VERSION_CHECK_CMD placeholders added; comment on
  `SCAFFOLD_BOOTSTRAP_CMD` clarifies it's run by Phase 3, not the
  pipeline.

No decomposition skill changes. No planning skill changes. No roadmap
skill changes. The full plan is documented in
`phase-a-scaffold-split-plan-2026-05-07.md`.

## Acceptance bar (for T15 itself)

T15 has no positive acceptance bar — both attempts failed at task-01
and the trial's value is the architectural issues it surfaced rather
than the pipeline run itself. The acceptance bar for the refactor T15
motivated lives in T16:

| Criterion (deferred to T16) | Trial |
|---|---|
| T15's blocking failure mode (host runtime mismatch cascading) does not occur | T16 |
| Phase A completes scaffold + bootstrap without retry/escalation cascade | T16 |
| `task_status.json` accurately tracks state across runs | T16 |
| Runtime-isolation step shows visible research output (URLs, tool rationale), not table consultation | T16 |
| Bootstrap command contains explicit runtime-version specifier | T16 |
| Pipeline (Phase B) completes all tasks 02..N | T16 |

## Implications

- **T15 supersedes nothing.** R03, D01, D02 remain validated trials —
  the decomposition + roadmap output was schema-clean and the
  schema-side path resolution worked correctly. T15's failure was at
  the implementation skill's Phase 1 bootstrap construction, not at
  any layer T15 was meant to validate.
- **T16 is the deferred end-to-end validation.** Pre-trial: user
  removes the existing `pipelines/airflow-gdrive-ingestion/`
  directory (per the new pipeline-existence precondition).
- **The 2026-05-02 three-skill refactor's end-to-end validation
  effectively shifts to T16.** R03 → D01 → D02 → T16 is the new
  acceptance chain; T15 was an aborted attempt that surfaced
  prerequisite work.

## Cross-cutting pattern note

T15 fits the broader memory-repo arc cleanly:

- T14: prose was lossy transport between decomposer and pipeline →
  promote `test_command` to typed schema field.
- R02-prep: prose claimed verification that hadn't happened →
  promote spec data to JSON file with provenance.
- D02: implicit CWD dependence in path resolution → explicit
  project-root-anchored helper.
- **T15: implicit host-runtime dependence in bootstrap construction →
  explicit project-pinned runtime, researched and verified at
  Phase 1.**

Each fix is a small local change that removes a context-implicit
dependency. The cumulative effect is a skill set whose contracts hold
regardless of where the caller starts from — host Python version,
CWD, prose-paraphrased intent, training-data recall.

The "force visibility" pattern (P01–P03 origin) extends one more
level: the runtime-isolation research output is the visible artifact
that replaces silent table consultation. A model running the skill
must produce evidence (signals consulted, tool chosen, URLs read,
temp-dir test result) before the bootstrap command lands in
`config.py`. The user reviews that evidence at the Phase 1 STOP
before any pipeline file is written.

## Trial-earned principles

Already documented in LEARNINGS.md (2026-05-07 update):

- Static ecosystem-to-tool tables are stop-thinking instructions.
- Environmental and code-quality failures need different recovery paths.
- Long-running processes don't see edits to imported config.
- Auto-resume via persisted per-task state is the right default.
- Pair pipeline generation with one-shot scaffold execution.
