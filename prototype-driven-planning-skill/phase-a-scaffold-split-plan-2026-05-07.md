# Phase A/B Scaffold Split + Runtime Isolation via Research

**Status:** PROPOSED — not yet implemented. Plan written 2026-05-07 after T15 attempts (run-20260507_113318, run-20260507_155410) blocked at task-01 on environment incompatibility (host `python3` is 3.14; pinned `apache-airflow==2.10.5` requires Python `<3.13`).

**Owning skill:** `prototype-driven-implementation`. No changes to `prototype-driven-planning`, `prototype-driven-roadmap`, or `prototype-driven-task-decomposition`.

**Validation:** T16, run end-to-end against `airflow-gdrive-ingestion`.

---

## Why this exists

Two T15 attempts both failed at task-01 with the same symptom: `pip install apache-airflow[celery]==2.10.5` errored with `Requires-Python ~=3.8,<3.13`. Three failures of the current architecture surface in this run, and the conversation that followed surfaced a fourth lesson:

1. **Bootstrap was constructed from a static lookup table** in `phase-1-analysis.md` (`pyproject.toml + uv → uv sync --dev`, `package.json + npm → npm install`, etc.) and never tested before being committed to `config.py`. The table didn't model "what runtime version does the project need?" or "is the host runtime compatible?" — only "what package manager does the language imply?"
2. **Bootstrap-failure cascade is structurally wrong.** Bootstrap failures are environmental (host wrong runtime, missing CLIs, network unreachable); the pipeline's retry/escalate/cascade logic was designed for code-quality differences. When task-01 failed, the pipeline retried with the same shell command, then cascaded 11 task skips. Claude tier-1 retry-1 *correctly diagnosed* the issue and edited `config.py` mid-run, but the change had no effect because `config.py` was already imported into the pipeline process. An executor editing pipeline config mid-run is also a class of action that doesn't belong inside the pipeline at all.
3. **Two Pythons collided silently.** The pipeline's runtime (LangGraph) and the service's runtime (Airflow) have different version constraints. The current implementation skill makes neither explicit — both were implicitly delegated to whatever `python3` resolves to on the host.
4. **Static ecosystem tables become stop-thinking instructions.** This is a recurring lesson — see LEARNINGS.md "CLI flags go stale," P01-P03's Surface Coverage Check, the OWASP version-pin issue from R02-prep. Whenever the skill writes a table of "for ecosystem X, use tool Y," the model running the skill treats the table as authoritative and skips verification. The fix is not a more accurate table; the fix is to specify the *responsibility* the model must satisfy and have it research the *realization* against the project at hand.

---

## Architectural decisions

### D1. Split scaffold execution out of the LangGraph pipeline (Phase A / Phase B)

**Phase A: scaffold execution.** Claude Code, in the same conversation that runs the implementation skill, executes task-01 plus its bootstrap interactively after pipeline generation. This uses Claude Code's native file-edit and shell tools — the same tools that built the prototype. Failures are diagnosed and fixed in the chat, not via retry/escalate cascades.

**Phase B: LangGraph pipeline.** `python run.py` executes tasks 02..N. On startup, it verifies the scaffold-complete marker exists and lint/test tools are available; if not, it stops with a clear pointer to Phase A. The pipeline's retry/escalation logic now applies only to code-quality failures, which is what it was designed for.

The boundary: Phase A's job is to put the project in a state where the pipeline's assumptions hold. The pipeline assumes a working service venv with lint/test tools available, source files importable, dependencies installed, runtime version correct. Phase A produces that state; Phase B consumes it.

### D2. Phase A runs once per pipeline-generation cycle

Implementation skill regenerates the pipeline directory only on a fresh slate — if `pipelines/<feature>/` already exists, the skill stops and asks the user to remove it. This eliminates "should I re-run scaffold?" decision-making: pipeline generation and scaffold execution are paired in the same conversation, in that order.

The user's lifecycle becomes:

1. `/prototype-implement <feature>` — generates pipeline, executes Phase A (scaffold + bootstrap + verification), writes scaffold-complete marker.
2. `python run.py` — executes Phase B (tasks 02..N).
3. As needed: re-run `python run.py`. The pipeline auto-detects where to resume from (D4).
4. If the user wants to regenerate the pipeline (e.g., because tasks changed): remove `pipelines/<feature>/` first, then re-run `/prototype-implement`.

### D3. Runtime isolation: specify the responsibility, research the realization

The skill does **not** prescribe specific tools for any ecosystem. Instead, Phase 1 specifies what the bootstrap command must accomplish:

> The bootstrap command must provision the project-pinned runtime version and install dependencies into an isolated environment, without depending on host PATH or the host's default runtime. Each ecosystem has its own conventions; the skill specifies the requirement, the model researches the realization for the project at hand.

Phase 1 has a step that:

1. Inspects the project for existing tooling signals (lockfiles, version-pin files, build-tool config, CI workflow files, Dockerfile build steps, README setup instructions). The project's existing convention takes precedence — if the project already uses tool X, use X; do not introduce a different one.
2. If no convention exists (greenfield, scaffold-phase): searches the web for current best-practice runtime+dependency tools for the detected ecosystem. Verifies the chosen tool's invocation by running its version check.
3. Locates the runtime pin: where does this ecosystem record the project's required runtime version? Reads it from the source the project uses.
4. Constructs the bootstrap command as runtime-provision + dependency-install. Tests the constructed command in a temporary directory before committing it to `config.py`.
5. Records what was researched (sources, tool, why) so the user can challenge the choice during the Phase 1 STOP.

No ecosystem matrix in the skill. No "Python = uv" entry. The model produces project-specific tool choices each time, with research as the source. This is the same approach already adopted for CLI-flag detection (in `phase-1-analysis.md`'s "Research Non-Interactive Invocation Patterns") and for OWASP version verification.

### D4. Auto-detect resume point via per-task status persistence

Pipeline writes per-task verdicts to `logs/task_status.json` keyed by task ID. On startup, `pick_next_task` reads the file and starts from the first task that's not `passed`. Failed tasks re-run from scratch on the next invocation; `not_run` tasks are picked up; `passed` tasks are skipped.

`--start` becomes an override flag, not a required input. The default user experience is `python run.py` with no arguments.

Staleness handling kept simple per discussion: `passed` markers are honored across runs. If the user changes a task spec and wants the pipeline to re-attempt, they pass `--start <task-id>` (or delete `task_status.json`). A more sophisticated approach (hash-based invalidation) is deferred — a real bug surfacing the need would justify it.

---

## Skill changes

### `prototype-driven-implementation/SKILL.md`

Three structural changes:

1. **Phase 1 absorbs runtime-isolation research.** A new section between "Detect tooling commands" and "Identify the scaffold bootstrap command":

   > **Determine the project's runtime-isolation tooling.** The bootstrap command must provision the project-pinned runtime version and install dependencies into an isolated environment, without depending on host PATH. Inspect the project for existing tooling signals; if none exist, research current best practices for the detected ecosystem; locate the project's runtime pin from the appropriate ecosystem source; construct and test the bootstrap command before committing it to config. See `references/phase-1-analysis.md` for the detailed protocol.

   The existing static "Scaffold Bootstrap Detection" table in `phase-1-analysis.md` is removed and replaced with the research protocol described in D3.

2. **Phase 3 absorbs Phase A.** Renamed and expanded from "Validation & Handoff" to **"Validation, Scaffold Execution, and Handoff"**. Three internal sections:
   - Validation (templates, syntax, smoke test, precondition checks — as today, minus scaffold concerns).
   - **NEW: Scaffold Execution.** Read task-01 from `tasks.json`. Use Claude Code's native tools to create the files. Run the bootstrap command. Verify the runtime version matches the pin (`<runtime-cmd> --version` parsed against the pin). Run the scaffold task's `test_command` (the exit-5-tolerant pytest equivalent). Write `pipelines/<feature>/.scaffold_complete` with task ID, timestamp, and runtime version detected. If anything fails, diagnose and fix in chat — do not write the marker until everything passes.
   - Handoff. Tell the user to run `python run.py` (no `--start` needed). Document the auto-detect-resume behavior. Document `--start` as an override.

3. **Pipeline-existence precondition.** SKILL.md's "How to Start" section adds: "If `pipelines/<feature>/` already exists, stop and ask the user to remove it. Pipeline generation and scaffold execution are paired and do not overwrite an existing pipeline directory."

### `prototype-driven-implementation/references/phase-1-analysis.md`

Three changes:

1. **Remove the static bootstrap lookup table.** Delete the "Scaffold Bootstrap Detection" section's table mapping config-file → bootstrap-command. Replace with the research protocol from D3.

2. **Add a Runtime-Isolation Research section** that documents:
   - The responsibility (provision pinned runtime + isolated dependency install).
   - Detection signals (lockfiles, version-pin files, build-tool config, Dockerfile build steps, CI workflows) — described abstractly, no per-ecosystem table of file names.
   - Greenfield research procedure (web search for current best-practice tool, verify by running version check).
   - Bootstrap construction and verification (run in temp dir before committing).
   - What to record for the user (sources, tool chosen, why).

3. **Update "Per-Task Working Directory" and "Tooling Command Detection — The Critical Rule"** to remove implicit assumptions about specific tools. The existing per-ecosystem invocation table in "Tooling Command Detection" becomes a *worked example* of how a model might reason from signals to invocations, framed as "patterns observed across ecosystems" rather than "the table you should use." The Critical Rule itself stays — commands must work as isolated subprocess calls without an activated environment — but the table loses its prescriptive framing.

### `prototype-driven-implementation/references/phase-3-handoff.md`

Three changes:

1. **Add a Scaffold Execution section** between Smoke Test and Handoff Instructions. Documents what Claude Code does:
   - Read task-01.
   - Create files using native edit tools.
   - Run the bootstrap command from `config.SCAFFOLD_BOOTSTRAP_CMD`.
   - Verify runtime version matches pin (parse output of the runtime's version flag against the recorded pin).
   - Run the scaffold task's `test_command` (from `config.TASK_TEST_COMMANDS["task-01"]`).
   - Write `pipelines/<feature>/.scaffold_complete` (JSON: task_id, timestamp_iso8601, runtime_version_detected, runtime_pin).
   - On any failure: diagnose and fix interactively. Do not write the marker until all checks pass.

2. **Update Handoff Instructions** — the post-handoff "what happens" section reflects the new flow:
   - task-01 already executed; pipeline starts from task-02 by default (auto-detected from `task_status.json`, which doesn't exist yet on first run, so `pick_next_task` falls back to "first task whose dependencies are satisfied and that's not in `task_status.json` as passed").
   - `--start <task-id>` documented as override.
   - Re-running the pipeline picks up where it left off.

3. **Document the scaffold-complete marker as a precondition.** Add to "Precondition Validation": pipeline checks for `.scaffold_complete` at startup; missing marker means run Phase A first.

### `prototype-driven-implementation/templates/`

Four pipeline-side changes:

1. **`nodes/verify_task.py`**: remove the scaffold-bootstrap branch (`_run_scaffold_bootstrap`, the scaffold-marker check on first task, the bootstrap exit-code handling). Scaffold tasks no longer have special handling in `verify_task` — they don't reach `verify_task` at all (they're handled in Phase A, and once handled, their `task_status.json` entry says `passed`).

2. **`nodes/load_tasks.py` or new `nodes/check_preconditions.py`**: add a startup check that verifies `.scaffold_complete` exists and the env's lint/test tools are available. If missing, exit with a clear error pointing the user to `/prototype-implement`. Probably cleanest as a new node `check_preconditions` that runs before `pick_next_task`.

3. **`nodes/pick_next_task.py` (currently inside another file)**: read `logs/task_status.json` on each invocation. Skip tasks marked `passed`. Auto-detect start point. The `--start` flag overrides this.

4. **`nodes/verify_task.py` (continued)**: after each verdict, write/update `logs/task_status.json` with the task's status (`passed`, `failed`, `skipped`). Atomic write — temp file + rename — to handle interrupted runs.

5. **`run.py`**: keep `--start` as an override; remove any "must specify --start" warnings. Default flow has no required arguments.

---

## What stays unchanged

- **`prototype-driven-planning`**: untouched. The design doc still records prototype evidence; the prototype's Dockerfile pin still records the runtime version. Implementation Phase 1 reads the pin from there. (Or from `pyproject.toml`'s `requires-python`, or `.python-version`, or wherever the project actually records it — the model researches.)
- **`prototype-driven-roadmap`**: untouched.
- **`prototype-driven-task-decomposition`**: untouched. Task-01 still creates `requirements.txt`/Dockerfile/etc. as today. No new schema fields. No `bootstrap_command` field on tasks — the bootstrap command is implementation-skill territory because it's host-environment-specific, not task-specification.
- **The pipeline's executor dispatch, prompt composition, retry/escalation logic**: all unchanged. These were designed for code-quality failures and continue to apply only to those.

---

## Validation plan: T16

Single trial that exercises the whole change end-to-end against `airflow-gdrive-ingestion`.

**Pre-trial setup:**
1. Land all skill changes (SKILL.md, references/, templates/).
2. Remove the existing `pipelines/airflow-gdrive-ingestion/` directory (per D2's pipeline-existence precondition).

**Trial run:**

1. **Re-run implementation skill.**
   - Phase 1: Verify the model researches runtime isolation (web search expected, no static table consultation) and detects the Python pin from `prototypes/airflow-gdrive-ingestion/Dockerfile` (`apache/airflow:2.10.5-python3.11` → 3.11). Verify it constructs and tests a bootstrap command before committing. Record what tools it chose and why.
   - Phase 2: Pipeline directory generated; scaffold-bootstrap branch removed from verify_task; status file logic added to pick_next_task; precondition check exists.
   - Phase 3 Validation: smoke test passes.
   - Phase 3 Scaffold Execution: Claude Code creates service files, runs bootstrap, verifies runtime version is 3.11, runs scaffold's `test_command`, writes `.scaffold_complete`. The Python-3.13-incompatibility that blocked T15 should not occur because the bootstrap installs Python 3.11 via the chosen tool, not via the host's `python3`.
   - Phase 3 Handoff: documents `python run.py` as the next step.

2. **Run the pipeline (`python run.py`).**
   - Startup: precondition check finds `.scaffold_complete`; lint/test tools available.
   - `pick_next_task`: no `task_status.json` exists yet, so starts from task-01's first non-scaffold dependent (task-02). (Slight edge case: task-01 is in `tasks.json` but has been completed in Phase A — it should be in `task_status.json` as `passed` after Phase A writes the marker. Simplest implementation: Phase A writes a `task_status.json` entry for task-01 alongside the `.scaffold_complete` marker, so `pick_next_task` sees task-01 as passed and naturally picks task-02 as the first eligible task.)
   - Tasks 02..N execute. Verify `task_status.json` updates after each task.

3. **Validate auto-resume.** After tasks 02..N complete, re-run `python run.py`. Expected: skips all `passed` tasks, exits cleanly with "all tasks passed."

4. **Validate failure-resume.** Manually mark a mid-pipeline task as failed in `task_status.json`. Re-run `python run.py`. Expected: starts from that task; subsequent passed tasks downstream are re-evaluated against current state.

**Acceptance bar:**

- T15's blocking failure mode (Python version incompatibility surfacing as a pipeline cascade) does not occur.
- Phase A completes scaffold execution successfully without retry/escalation cascade.
- `task_status.json` accurately tracks state across runs.
- The skill's runtime-isolation step shows visible research output (URLs, tool choice rationale) — not consultation of a static table.
- Bootstrap command contains a runtime-version specifier (e.g., `--python 3.11` for uv, equivalent for whatever tool was chosen) so the host's default Python is not used.
- Pipeline completes all 12 tasks (or as many as the underlying decomposition supports — task-quality issues are out of scope for this trial).

**Out of scope for T16:**

- Validating the runtime-isolation approach against non-Python ecosystems. The skill's responsibility-not-realization framing makes this safe in principle, but actual validation requires a Node or Android or Go project trial. Capture this as a follow-up trial when such a project becomes available.
- Hash-based `task_status.json` invalidation. Deferred per D4.
- Scaffold-marker idempotency for re-runs without removing the pipeline directory. Deferred per D2 (the user removes the directory before regenerating).

---

## Open implementation questions

These are details to settle when writing the actual skill changes, not blockers for the plan:

1. **Where exactly does `pick_next_task` live?** Currently inside `verify_task.py` or `graph.py` — need to confirm by re-reading the templates. The status-file read fits naturally wherever this lives.

2. **`task_status.json` schema.** Minimal proposal: `{"<task-id>": {"status": "passed|failed|skipped", "timestamp": "<iso8601>", "executor_tier": <int>, "retries_used": <int>}}`. Schema can grow if needed.

3. **`.scaffold_complete` schema.** Minimal proposal: `{"task_id": "task-01", "timestamp": "<iso8601>", "runtime_pin": "3.11", "runtime_version_detected": "3.11.7", "bootstrap_command": "<command-as-run>"}`. Recording the bootstrap command as run is useful for diagnosing later mismatches.

4. **Exact phrasing of the runtime-isolation step.** The plan says "research at runtime"; the skill text needs to make this concrete enough that the model produces visible research output (URLs, tool name, justification) without listing tools that would defeat the purpose. Probably mirrors the existing "Research Non-Interactive Invocation Patterns" section's phrasing.

5. **Signal-list framing.** The detection-signals step needs to describe the *kinds* of signals (lockfiles, runtime-pin files, build-tool config) without naming specific files for specific ecosystems — but specific enough that the model knows what to look for. This is the trickiest framing problem in the plan. Likely answer: describe abstract categories (e.g., "lockfile: a manifest of resolved transitive dependencies pinned by version and content hash, indicating the project uses a tool that produced it"), not file globs.

---

## Memory-repo updates after T16

Regardless of T16 outcome:

- New trial file `trials/T16-<slug>.md`.
- Update `trials/_SUMMARY.md` and `_INDEX.md`.
- Update `LEARNINGS.md` with whatever generalizes from the trial — likely entries on (a) "research-at-runtime over static tables, including for ecosystem tooling," (b) the Phase A/B split as the model for separating environmental setup from task execution, (c) the auto-resume pattern, (d) any specifics about runtime-isolation tools that came up in the worked example without being prescribed by the skill.
- Mark this plan doc as superseded once T16 lands.
