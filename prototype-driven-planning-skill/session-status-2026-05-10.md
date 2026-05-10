# Session Status — 2026-05-10

> **Purpose:** Crisp handoff for the next session continuing the
> prompt-composition skill refactor. Read this after `README.md`.
> Supersedes any earlier dated session-status files.

## TL;DR

Step 1 of `prompt-composition-skill-plan-2026-05-09.md` landed: the
new `prototype-driven-prompt-composition` skill is built and the
`/prototype-compose-prompts` slash command is wired up. The first
task of the next session is to **smoke-test the skill end-to-end on
the host** (the chat sandbox can't do this — it needs the project
filesystem and pydantic). After the smoke test passes and the user
reviews 2-3 of the generated prompt files, proceed to step 2
(implementation-skill changes).

## What landed in this session

### New skill: `prototype-driven-prompt-composition`

Location: `~/claude-devtools/skills/prototype-driven-prompt-composition/`

Files:
- `SKILL.md` — three-phase user-facing flow (Inputs → Generation
  → Validation); STOP-summary at end of Phase 1 before generation
  begins
- `scripts/compose_prompts.py` (~32 KB) — standalone Python (no
  LangGraph dep); imports the project-shipped `task_schema.py` for
  validation; reads `tasks.json` + `roadmap.json`; writes one
  prompt file per task to `tasks/<feature>/prompts/<task-id>.md`
- `references/preamble.md` — verbatim universal preamble extracted
  from the implementation skill's old
  `compose_prompt.py.template`. **The `# Project: <name>` heading
  and description block are removed per plan D9** — uniform
  preamble across all task types, no conditional logic.
- `references/prompt-template.md` — canonical section structure
  documented as the format contract for downstream consumers
- `references/log-conventions.md` — the `logs/lint/<task-id>/` and
  `logs/tests/<task-id>/` per-attempt-file convention; filename
  format is `attempt-N-tierM.txt`; "highest N is most recent" rule
- `references/dependency-handling.md` — Option A (paths-not-inlined)
  rationale + deferred A+ option notes for trial follow-up

### Slash command: `/prototype-compose-prompts`

Location: `~/claude-devtools/commands/prototype-compose-prompts.md`

Standard one-line shape mirroring the other prototype-driven
commands (e.g., `prototype-task-decompose.md`).

### Sandbox helper test

The script's pure helper functions were sandbox-tested against mock
data shaped like the real schema:

- 67 assertions covering inlineable-extension derivation, scenario
  rendering (functional + security; prescribed evidence-kind),
  dependency listing (paths only, no code blocks), section assembly,
  required-marker validation, D9 (no `# Project:` heading), D10
  (scaffold tasks get a prompt)
- All 67 pass

What the sandbox test does NOT cover (needs host execution):
- Pydantic deserialization against the real `tasks.json` and
  `task_schema.py` (uses real schema field names, validators)
- Path resolution from arbitrary CWD via the schema's
  `_PROJECT_ROOT` inference
- End-to-end I/O: precondition check, `mkdir(exist_ok=False)`,
  atomic write, Phase 3 reading-back validation

## What the next session does first

### 1. Smoke-test the skill end-to-end on the host

```bash
cd ~/health-data-ai-platform
# Clean slate if a prior run left a prompts directory
rm -rf tasks/airflow-gdrive-ingestion/prompts
# Run the script
uv run --with pydantic python ~/claude-devtools/skills/prototype-driven-prompt-composition/scripts/compose_prompts.py airflow-gdrive-ingestion
```

**Expected output:**

- `[compose_prompts] Project root: /Users/vinayakmenon/health-data-ai-platform`
- `[compose_prompts] Tasks directory: /Users/vinayakmenon/health-data-ai-platform/tasks/airflow-gdrive-ingestion`
- `[compose_prompts] tasks.json loaded: 12 tasks`
- `[compose_prompts] Inlineable extensions: ` followed by the actual
  extensions present in `task.files[].path` (likely `.py`, `.toml`,
  `.txt`, `.yml` — derived from task file paths per D11)
- Phase 1 STOP-summary block listing inputs found, extensions, 12
  tasks, ~33 citations
- Phase 2 listing 12 prompt files written under
  `tasks/airflow-gdrive-ingestion/prompts/`
- Phase 3 confirming all 12 found, all non-empty, all required
  markers present, sub-counts for behaviors / dependencies /
  security sections

**If anything fails, the most likely culprits are:**

- **AttributeError**: my `SimpleNamespace` mocks in the sandbox test
  don't match the real pydantic field names. Paste the traceback —
  it'll point at the wrong attribute. Fix is in
  `compose_prompts.py`'s helper functions (small).
- **FileNotFoundError for `task_schema.py`**: the candidate-walking
  logic in `main()` walked too few/too many parents. The script
  walks CWD + parents looking for `tasks/<feature>/task_schema.py`.
  If the user's CWD isn't a project root or one of its parents
  contains the right path, this trips.
- **Pydantic validation error**: the schema's cross-load of
  `components.json` and `roadmap.json` failed. Most likely cause: a
  citation in `tasks.json` doesn't resolve against `roadmap.json`
  (i.e., decomposition is stale; user needs to re-run
  `/prototype-task-decompose`). The error message will name the
  specific task and citation; that's a project-side fix, not a
  skill-side fix.

### 2. Manually inspect 2-3 of the generated prompts

Pick a scaffold task (`task-01`), a test task with both functional
and security citations (`task-02` or `task-04`), and an
implementation task with dependencies (`task-03` or `task-05`).

**What to verify:**

- The `# Project:` heading is **absent** (D9 — major change from
  current pipeline-composed prompts)
- The `## Behaviors to Verify (from roadmap)` section renders
  Gherkin correctly: Given/When/Then bullets, OWASP requirement
  for security scenarios, Performed-by for security scenarios,
  Evidence kind callout when `evidence_kind == "prescribed"`
- The `## Dependencies` section lists file paths with the
  `— created by \`task-NN\`` attribution; **no inlined file
  content** (no code blocks)
- The `## Previous Attempts` section is present in **every** prompt
  with the task ID substituted (e.g., `logs/lint/task-05/`)
- The preamble's section ordering matches `references/preamble.md`
  (Role → Test rules → Stub rules → Coding conventions → Output
  format)

If the structure looks right, proceed to step 2.

If you want changes (e.g., section order, wording, additional
content), tell me what to change. Edits to the new skill are cheap;
edits after step 2 lands are expensive because the implementation
skill will start consuming the prompts.

### 3. Then: step 2 of the plan

After approval of the prompt format, proceed to step 2 of
`prompt-composition-skill-plan-2026-05-09.md`:

**Implementation skill changes (eight files):**

1. **Delete** `templates/nodes/compose_prompt.py.template` —
   the entire file goes away; `load_prompt.py` replaces it.
2. **Add** `templates/nodes/load_prompt.py` — new LangGraph node
   that runs between `pick_next_task` and `execute_task`. Reads
   `tasks/<feature>/prompts/<current_task_id>.md` from disk;
   writes the path into `PipelineState`. No copying, no
   enrichment.
3. **Modify** `templates/nodes/execute_task.py` — consume the path
   `load_prompt` writes; remove any prompt-composition residue.
4. **Modify** `templates/nodes/verify_task.py` — change lint/test
   error log paths to the new convention:
   `logs/lint/<task-id>/attempt-N-tierM.txt` and
   `logs/tests/<task-id>/attempt-N-tierM.txt`. Drop the
   `task-NN_error_<time>.txt` style. `N = current_retry + 1` so
   first attempt is `attempt-1-tier0.txt`.
5. **Modify** `templates/nodes/check_preconditions.py` — add a
   check that every task ID in `tasks.json` has a corresponding
   prompt file at `tasks/<feature>/prompts/<task-id>.md` (no
   scaffold exemption). Exit with "Prompts not generated. Run
   /prototype-compose-prompts <feature> first." if any are
   missing.
6. **Modify** `templates/graph.py` — wire `load_prompt` between
   `pick_next_task` and `execute_task`. Remove `compose_prompt`
   from the graph.
7. **Modify** `templates/pipeline_state.py` — `current_prompt_path`
   stays (already there); the writer changes from `compose_prompt`
   to `load_prompt`. The retry-context state fields
   (`current_lint_error_path`, `current_test_error_path`) can be
   removed — the prompt's `## Previous Attempts` section references
   the log directories by convention, not by injected path.
8. **Modify** `templates/config.py.template` — remove the
   `{{ROADMAP_JSON_PATH}}` placeholder and the `ROADMAP_JSON_PATH`
   variable; pipeline doesn't read roadmap.json at runtime
   anymore (composition inlined the scenarios).

**Implementation skill SKILL.md and reference doc changes:**

- `SKILL.md`: How to Start gains prompts-existence precondition
  bullet (no scaffold exemption); Phase 2 step 4 (compose_prompt
  template substitution) removed; Phase 3 smoke test simplifies
  (no more `compose_prompt._inline_roadmap_scenarios` exercise);
  Phase 3 Scaffold Execution reads from prompts dir per D10.
- `references/phase-2-generation.md`: remove "Generate
  `nodes/compose_prompt.py`" step entirely; remove
  `{{ROADMAP_JSON_PATH}}` from placeholder table; update Output
  Structure file list to remove `nodes/compose_prompt.py` and add
  `nodes/load_prompt.py`.
- `references/phase-3-handoff.md`: update Smoke Test (drop
  `_inline_roadmap_scenarios` exercise); update Precondition
  Validation (add prompts-existence check); update Scaffold
  Execution (Step 1 reads `prompts/task-01.md`).

After step 2, write the slash command (already done — step 3 is
already complete), update memory README again with step 2's results,
stage T17 trial slot, run T17.

## Open implementation questions for step 2

(Items genuinely open at implementation time, not blockers for
proceeding):

1. **Where does load logic live?** Plan says separate
   `nodes/load_prompt.py` (LangGraph-idiomatic). Keep that
   decision unless step 2 reveals a reason to inline it into
   `execute_task.py`.
2. **`load_prompt` existence check**: `check_preconditions` is
   the authoritative check at startup. `load_prompt` runs
   per-task; it can either trust precondition (raise
   FileNotFoundError naturally if file deleted mid-run) or
   re-check with a friendlier error. Default: trust the
   precondition.

## Files written this session

```
~/claude-devtools/skills/prototype-driven-prompt-composition/SKILL.md
~/claude-devtools/skills/prototype-driven-prompt-composition/scripts/compose_prompts.py
~/claude-devtools/skills/prototype-driven-prompt-composition/references/preamble.md
~/claude-devtools/skills/prototype-driven-prompt-composition/references/prompt-template.md
~/claude-devtools/skills/prototype-driven-prompt-composition/references/log-conventions.md
~/claude-devtools/skills/prototype-driven-prompt-composition/references/dependency-handling.md
~/claude-devtools/commands/prototype-compose-prompts.md
~/claude-project-memory/prototype-driven-planning-skill/prompt-composition-skill-plan-2026-05-09.md  (revised in-session)
~/claude-project-memory/prototype-driven-planning-skill/README.md  (updated for new skill)
~/claude-project-memory/prototype-driven-planning-skill/session-status-2026-05-10.md  (this file)
```

No implementation skill files modified. No project-side files
modified. Manual `git add -A && git commit && git push` required
from the user's local terminal — Claude can't push from the
sandbox.

## Anti-patterns to avoid in the next session

- **Don't run `/prototype-implement` against the new prompts yet.**
  The pipeline still reads its prompts via the old
  `compose_prompt.py.template` until step 2 lands. Running the
  implementation skill before step 2 will produce pipeline files
  that ignore the new `prompts/` directory entirely.
- **Don't cite the deferred enrichment options as fixes for early
  trial failures.** D4's A+ option (pipeline-side dependency
  enrichment) and D5's explicit current-attempt signal are
  deliberately deferred. If T17 surfaces problems, those become
  candidate fixes — not before.
- **Don't fold the smoke test results into the README's Recent
  Change block.** The README's recent-change entries record what
  *landed in the skill*; smoke test outcomes go in T17 trial notes
  or in a follow-up session-status file. Keep the boundary clean
  so future sessions can find each kind of information where they
  expect it.
