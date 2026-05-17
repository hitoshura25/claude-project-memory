# Prototype-Driven Planning Skills — Project Context

> **Purpose**: Persistent memory across chat sessions for the prototype-driven
> skill set (planning → roadmap → task decomposition → prompt composition → implementation).
>
> **Skill locations**:
> - `~/claude-devtools/skills/prototype-driven-planning/`
> - `~/claude-devtools/skills/prototype-driven-roadmap/`
> - `~/claude-devtools/skills/prototype-driven-task-decomposition/`
> - `~/claude-devtools/skills/prototype-driven-prompt-composition/`
> - `~/claude-devtools/skills/prototype-driven-implementation/`
>
> **Commands**:
> - `/prototype-plan <feature>` → planning skill
> - `/prototype-roadmap <feature>` → roadmap skill
> - `/prototype-task-decompose <design-doc>` → decomposition skill
> - `/prototype-compose-prompts <feature>` → prompt-composition skill
> - `/prototype-implement <feature>` → implementation skill
>
> **Test project**: `~/health-data-ai-platform` (airflow Google Drive ingestion)

---

## Conversation-Start Protocol

Read these files in order:
1. **This file** — orientation, standings, open issues
2. **`LEARNINGS.md`** — distilled principles (always relevant)
3. **`trials/_SUMMARY.md`** — scoreboard
4. **Most recent dated session-status file** if one exists at the top of the
   memory repo (e.g. `session-status-YYYY-MM-DD.md`). These capture mid-stream
   handoff context — what was done in the last session, what's pending, what
   to verify before continuing. They live alongside plan docs and supersede
   each other; only the most recent one matters.

Load on-demand only when needed:
- `references/architecture-rationale.md`
- `references/stack-reference.md`
- `gemini_conversation.txt` (historical)
- `trials/_INDEX.md`
- `trials/T<NN>-*.md` — pipeline trials (T01–T14)
- `trials/P<NN>-*.md` — planning-skill iterations (P01–P03, P05)
- `trials/R<NN>-*.md` — roadmap-skill trials and rebuilds (R01, R02-prep, R02, R03)
- `trials/D<NN>-*.md` — decomposition-skill iterations (D01, D02)
- `refactor-plan-2026-04-17.md` — T13 refactor (landed in T14)
- `refactor-plan-2026-04-19.md` — T14 refactor (landed same day)
- `skill-expansion-plan-2026-04-21.md` — historical reference; all parts landed
- `decomposition-roadmap-refactor-plan-2026-05-02.md` — **Active plan**
  for the decomposition refactor. Three coordinated changes (roadmap skill,
  implementation skill, decomposition skill) producing the full
  deduplication benefit. Acceptance trials: R03 → D01 → T15.
- `decomposition-roadmap-refactor-plan-2026-04-26.md` — Superseded
  2026-05-02. Preserved for historical context (2026-04-27 sequencing
  pivot, embed-vs-script debate that dissolved when roadmap output
  became JSON).
- `planning-project-setup-component-plan-2026-04-27.md` — Project Setup
  component plan (landed 2026-04-27; validates in P05)
- `asvs-5-migration-plan-2026-04-30.md` — OWASP spec migration plan
  (landed 2026-04-30)
- `phase-a-scaffold-split-plan-2026-05-07.md` — **Active plan**
  for splitting scaffold execution out of the LangGraph pipeline
  (Phase A in conversation; Phase B in pipeline) and replacing the
  static bootstrap lookup with research-at-runtime. Skill changes
  landed 2026-05-07; T16 validates end-to-end.
- `prompt-composition-skill-plan-2026-05-09.md` — **Active plan** for
  extracting prompt generation into its own skill. Step 1 (build the
  new skill) landed 2026-05-10; steps 2–5 (implementation-skill
  changes, slash command, README update, T17 trial) pending. The
  slash command + this README update landed alongside step 1.
- `observability-and-citations-plan-2026-05-14.md` — Landed
  2026-05-14 (all 8 steps). Adds Phase 1 Observability-Friendly Tech
  Selection, Source Citations with `accessed <YYYY-MM-DD>`, Phase 2
  Telemetry + Performance Measurement validation steps, Phase 3
  External-source label + References section, 3 new SKILL.md
  principles. Post-P06 fixes landed 2026-05-15 → 2026-05-16 (Plan A:
  web-research discipline; Plan B: downstream-skill references
  removed). Plan doc is historical; new work for this skill lives in
  new plan docs.

---

## Current State (2026-05-16)

> **Recent change (2026-05-15 → 2026-05-16): planning skill
> observability expansion + post-P06 fixes.** Two-phase work. Phase 1
> (2026-05-14): observability-and-citations expansion landed all 8
> steps of `observability-and-citations-plan-2026-05-14.md` — Phase 1
> Step 5 Observability-Friendly Tech Selection (per-candidate ×
> dimension verdicts: Strong/Adequate/Weak, with justification +
> workaround for any Adequate or Weak); Phase 1 Step 5 Source
> Citations subsection (URL + `accessed <YYYY-MM-DD>` format, three
> anti-patterns banned: "as of <date>" prose, training-data
> citations, silent omission); Phase 2 Telemetry Instrumentation
> Validation step (responsibility + applicability gate + signals +
> research protocol + demonstrated viewing path + what to capture);
> Phase 2 Performance Measurement Validation step (same structural
> shape, three project categories: UI rendering / backend latency /
> batch timing); Phase 3 External-source label as fifth element of
> Judgment vs Observation discipline (label hierarchy: Cliff edge >
> observation-with-evidence > Not observed > External > Prescribed);
> Phase 3 References section (silence-not-allowed rule); design-doc
> template updates (5-label meta-commentary, Telemetry + Performance
> subsections under `## Tooling`, References section); SKILL.md
> updates (Phase 1 Step 5 expansion fold-in, Phase 1 Step 6
> tech-selection bullet, Phase 2 new Steps 8-9 with renumbering of
> End-to-End → 10 and Cross-Cutting Research → 11, STOP report
> bullets, 3 new principles: "Tech selection is observability-checked
> before scope is approved", "Observability is prototype-validated
> before the design doc prescribes it", "External claims cite sources
> with `accessed <YYYY-MM-DD>`"). Phase 2 (2026-05-15 → 2026-05-16):
> P06 trial run against `airflow-gdrive-ingestion` exposed two
> distinct gaps the expansion didn't cover. **Gap 1**: research-shaped
> instructions elsewhere in the skill defaulted to training-data
> recall, not web search. The expansion's own steps worked because
> they spelled out the searches ecosystem-by-ecosystem; the older
> steps (Phase 1 Research, Phase 2 Cross-Cutting Research, Mitigation
> Ladder) used the word "research" without naming tools. Concrete
> failure: P06 ran Trivy, formed verdicts on fix availability from
> Trivy output alone, treated HIGH findings without a Trivy-surfaced
> fix as "unresolvable" until user prompted to search. Same
> silent-recall behavior likely operating across all research steps,
> not security-specific. **Gap 2**: skill files contained stale
> references to downstream skills (roadmap, task-decomposition,
> "implementation pipeline", "Phase 4", "downstream skills will try
> to run them", "downstream skills tag as non-negotiable", etc.). The
> references encoded the *reason for a rule* in terms of downstream
> consumption rather than the rule's intrinsic justification, making
> the skill non-standalone. **Fix Plan A (research discipline) — 5
> sub-edits landed**: new SKILL.md principle "Research means web
> research, not training-data recall" as cross-cutting default;
> Mitigation Ladder gains "Before declaring an option unavailable,
> search" preamble with 5 search targets (CVE ID/NVD/GHSA, package +
> CVE, GitHub issues, CHANGELOG, distro tracker); per-section
> preambles in Phase 1 Research and Phase 2 Cross-Cutting Research
> naming `web_search` and `web_fetch` explicitly; LEARNINGS.md gains
> "From P06" subsection with 4 distilled learnings (training-recall
> default, local-tool-output-as-research-boundary = same
> stop-thinking anti-pattern in a new costume, per-option search
> rule, principles→specifics cross-references reinforce discipline
> at point of use). **Fix Plan B (downstream-skill references
> removed) — 14 sub-edits landed**: every reference to downstream
> skills, downstream pipelines, downstream task decomposer, roadmap
> skill, Phase 4, etc. removed across SKILL.md and all 4 reference
> files. Where downstream-consumption rationale was load-bearing
> (Cliff edge label "why does the label matter"), replaced with
> intrinsic rationale (boundary conditions that must not be
> substituted at implementation time). Renamed "Consumability for
> Future Phases" section to "Structural Consistency". Final grep
> audit: 7 remaining `downstream` mentions, all legitimately referring
> to **downstream teams (humans)** or **downstream in time**
> (workarounds applying to later prototype build) — not downstream
> skills. The skill is now genuinely standalone; rules and rationale
> justify themselves on the skill's own terms. **Files touched**:
> `SKILL.md`, `references/phase-1-discovery.md`,
> `references/phase-2-prototype.md`,
> `references/phase-3-design-doc.md`,
> `references/design-doc-template.md`, `LEARNINGS.md`. Plan doc:
> `observability-and-citations-plan-2026-05-14.md`. P06 trial detail
> to be filed at
> `trials/P06-research-discipline-and-downstream-cleanup.md` before
> next session.

> **Recent change (2026-05-10): prompt-composition skill built.** Step 1
> of `prompt-composition-skill-plan-2026-05-09.md` landed: new
> `prototype-driven-prompt-composition` skill at
> `~/claude-devtools/skills/prototype-driven-prompt-composition/` with
> `SKILL.md`, `scripts/compose_prompts.py` (~32 KB standalone Python,
> no LangGraph dep), and four reference docs (`preamble.md` —
> verbatim universal preamble extracted from the implementation
> skill's `compose_prompt.py.template` with the project block removed
> per D9; `prompt-template.md`; `log-conventions.md`;
> `dependency-handling.md`). Slash command
> `/prototype-compose-prompts` added at
> `~/claude-devtools/commands/prototype-compose-prompts.md`. The
> script's pure helper functions were sandbox-tested (67 assertions,
> all pass) covering inlineable-extension derivation, scenario
> rendering (functional + security, prescribed evidence kind),
> dependency listing (paths only, no inlining), section assembly,
> required-marker validation, and D9 (no project block) +
> D10 (scaffold task gets a prompt) verification. End-to-end smoke
> test against the real `airflow-gdrive-ingestion` decomposition
> requires running the script on the host (uv + pydantic + project
> filesystem) and is the next session's first task. **Steps 2–5
> pending**: (2) implementation-skill changes — delete
> `nodes/compose_prompt.py.template`, add `nodes/load_prompt.py`,
> update `verify_task.py` for the new per-attempt log-folder
> convention, update `check_preconditions.py` to verify all prompt
> files exist, drop `{{ROADMAP_JSON_PATH}}` from `config.py.template`;
> (3) memory repo full update; (4) T17 trial against
> airflow-gdrive-ingestion validating both consumption paths
> (manual Claude Code on a single prompt + full pipeline run). See
> `session-status-2026-05-10.md` for the next-session handoff
> (smoke-test instructions, expected output, what to verify before
> step 2). **No implementation-skill changes yet — the pipeline still
> uses the old `compose_prompt.py.template`.** Don't run
> `/prototype-implement` against the new prompts yet; the pipeline
> won't read them.

> **Recent change (2026-05-07): Phase A/B scaffold split + research-at-runtime
> for runtime isolation.** T15 ran twice (2026-05-07 11:33 and 15:54)
> and both attempts blocked at task-01 on bootstrap. The pinned
> `apache-airflow==2.10.5` requires Python `<3.13`; the host's `python3`
> is 3.14, and the bootstrap command Phase 1 generated didn't account
> for the version mismatch. Run 2 retry-1 had Claude tier-1 correctly
> diagnose the issue and edit `config.py` mid-run, but the change had
> no effect (config was already imported into the running pipeline
> process); pipeline cascaded 11 task skips. Conversation worked
> through three conjoined questions: (Q1) does decomposition need
> bootstrap validation? (Q2) are the two Pythons — pipeline runtime
> vs. service runtime — colliding? (Q3) should scaffold move out of
> the pipeline? Answer landed on a coordinated implementation-skill
> refactor with four pieces: (D1) Phase A executes scaffold +
> bootstrap interactively in the same conversation that generated
> the pipeline; Phase B = pipeline executes tasks 02..N. (D2)
> Pipeline-existence precondition — implementation skill stops if
> `pipelines/<feature>/` already exists. (D3) Runtime-isolation
> research replaces the static ecosystem lookup table — the skill
> describes responsibilities (provision pinned runtime + isolated
> dependency install + invoke commands without host PATH) and
> signals (lockfiles, runtime-pin files, build-tool config); the
> model researches the project's actual tooling at Phase 1, verifies
> with a temp-dir test before committing. No prescriptive
> ecosystem-to-tool table. (D4) Auto-resume via `logs/task_status.json`
> — pipeline writes per-task verdicts atomically; `pick_next_task`
> reads the file and skips passed tasks; `--start` becomes an
> override. Skill changes landed: SKILL.md restructured (Phase 3
> absorbs Scaffold Execution); `phase-1-analysis.md` rewritten
> (static bootstrap lookup table removed; Runtime-Isolation Research
> protocol added); `phase-2-generation.md` updated (new
> RUNTIME_VERSION_PIN / RUNTIME_VERSION_CHECK_CMD placeholders;
> static ecosystem table reframed as project-tooling-detected);
> `phase-3-handoff.md` rewritten end-to-end (Validation / Scaffold
> Execution / Handoff sections; six-step Phase A protocol).
> Templates: new `nodes/check_preconditions.py` (verifies
> `.scaffold_complete` marker + lint/test tools at startup);
> `verify_task.py` lost its `_run_scaffold_bootstrap` branch and now
> writes per-verdict entries to `task_status.json`; `graph.py` wires
> `check_preconditions` between `load_tasks` and `pick_next_task`,
> and persists status from `mark_failed` and skip transitions;
> `load_tasks.py` merges `task_status.json` on startup;
> `pipeline_state.py` drops `bootstrap_done`; `run.py` updates help
> text for auto-resume default; `config.py.template` adds
> RUNTIME_VERSION_PIN, RUNTIME_VERSION_CHECK_CMD, removes
> SCAFFOLD_BOOTSTRAP_CMD comment about pipeline-runtime usage. All six
> edited template Python files compile clean. **No decomposition
> changes.** No planning changes. No roadmap changes. Plan doc:
> `phase-a-scaffold-split-plan-2026-05-07.md`. Validation: T16
> (pre-trial: user removes existing `pipelines/airflow-gdrive-ingestion/`
> directory; trial: full chain end-to-end against
> airflow-gdrive-ingestion).

> **Recent change (2026-05-06): D02 surfaces and fixes CWD-relative
> path resolution in the decomposition schema.** First T15 attempt
> failed at `load_tasks_node` with `FileNotFoundError`: the user ran
> `python run.py` from `pipelines/airflow-gdrive-ingestion/`, the
> schema's `Path(self.components_json_path).resolve()` calls in
> `_load_roadmap_schemas` and the cross-file validators resolved
> against the pipeline-dir CWD instead of the project root. D01
> didn't catch this because validation ran from project root —
> schema and CWD coincidentally agreed. Fix: `_PROJECT_ROOT`
> constant inferred from `__file__` location + new
> `_resolve_project_path(p) -> Path` helper in `task_schema.py`,
> replacing four `Path(p).resolve()` call sites; field-description
> prose on `components_json_path` and `roadmap_json_path` updated to
> document the resolution rule. Parallel `_resolve_project_path`
> helper in `compose_prompt.py.template` (sourced from
> `config.PROJECT_ROOT`, same name+shape as schema's), replacing
> the inline absolute/relative guard in `_load_roadmap`. Two helpers
> share name + shape so the pattern is greppable; sources differ
> because each side has access to a different concrete project-root
> answer. Phase 3 of the implementation skill gains a Smoke Test
> section in `phase-3-handoff.md` that runs from the pipeline
> directory (matching the runtime CWD) and exercises both helpers
> transitively (`load_tasks_node` for schema-side,
> `_inline_roadmap_scenarios` for implementation-side); SKILL.md
> Phase 3 step list renumbered, smoke test as step 3. **Project-side
> artifacts unchanged per directive** — user regenerates decomposition
> + pipeline from fixed skills before retrying T15. Detail:
> `trials/D02-cwd-relative-path-resolution.md`.

> **Recent change (2026-05-04): D01 trial validates the decomposition
> refactor end-to-end.** Step 3 of three per
> `decomposition-roadmap-refactor-plan-2026-05-02.md` (the bulk of the
> work, landed 2026-05-03). The user ran the regenerated decomposition
> against R03's roadmap output for airflow-gdrive-ingestion. Result:
> 13 tasks across 5 components, 60 scenario citations all resolve,
> `Behaviors to test:` section absent from every task description,
> stub-import discipline preserved on all four test tasks, T14
> invariants (test_command non-empty, integration-lifecycle wrapping,
> stub on test tasks only) all hold under the extended schema. Clean
> sweep — no new failure modes. **D01 unblocks T15 — the
> implementation pipeline can now be regenerated against the new
> tasks.json. Step 2 of the refactor (compose_prompt.py.template
> gaining `_inline_roadmap_scenarios`, landed 2026-05-03) needs no
> further work; T15 will exercise the full chain end-to-end.** Detail:
> `trials/D01-decomposition-roadmap-integration.md`. The previous task
> directory at
> `~/health-data-ai-platform/tasks/airflow-google-drive-ingestion/`
> (T14 output, invalid against the new schema) is now obsolete and can
> be deleted manually.

> **Recent change (2026-05-03 [later]): implementation skill inlines
> roadmap scenarios at prompt-compose time.** Step 2 of three per
> `decomposition-roadmap-refactor-plan-2026-05-02.md`. Template change
> in `compose_prompt.py.template`: new `_inline_roadmap_scenarios`
> helper parallel to `_inline_dependencies`, with module-level
> roadmap.json caching, separate `_format_functional_scenario` and
> `_format_security_scenario` renderers (security includes OWASP id +
> Performed-by), and explicit-`evidence_kind: prescribed` callouts.
> The helper is wired into `_build_prompt` between the Files and
> Acceptance Criteria sections under heading `## Behaviors to Verify
> (from roadmap)`. Empty citations omit the section; unresolved
> citations raise `ValueError` loudly (decomposition's validator
> should have caught them; reaching runtime means the roadmap was
> regenerated without re-running decomposition). New placeholder
> `{{ROADMAP_JSON_PATH}}` lives in `config.py.template` (alongside
> `{{PROJECT_ROOT}}` and other paths) — the compose_prompt template
> reads `config.ROADMAP_JSON_PATH` at runtime; this matches the
> existing path-handling pattern. Reference doc updates:
> `phase-2-generation.md` gained `{{ROADMAP_JSON_PATH}}` row in the
> Paths placeholder table, new "Roadmap-scenario inlining" subsection
> in Step 3 with the parallel-to-_inline_dependencies comparison
> table, updated "Why this is a template" paragraph to mention
> roadmap-scenario inlining as a stable element. Smoke-tested:
> template parses with placeholders substituted; full `_build_prompt`
> renders all sections in correct order; happy/empty/unresolved
> behaviors all fire correctly. **Step 2 doesn't have a standalone
> trial — validated end-to-end by T15 once D01 produces a
> roadmap-citing decomposition the pipeline can consume.**

> **Recent change (2026-05-03): decomposition skill consumes the
> roadmap.** Step 3 of three per
> `decomposition-roadmap-refactor-plan-2026-05-02.md` (the bulk of the
> work). Schema additions to `task_schema.py`: three new task fields
> (`roadmap_component`, `roadmap_functional_scenarios`,
> `roadmap_security_scenarios`), two new `TaskDecomposition` fields
> (`components_json_path`, `roadmap_json_path`), one per-task field
> validator (slug format), three new decomposition-level model
> validators (component-registered, scenarios-resolve, scenarios-
> required-for-test-tasks), four helper functions including
> project-shipped schema imports and Levenshtein-based "Did you mean"
> error hints. Reference docs updated end-to-end:
> `analysis-guide.md` rewritten (roadmap as primary input;
> components.json registry read; per-component scenario reading);
> `task-writing-guide.md` gained "Roadmap-Driven Task Authoring"
> section, `Behaviors to test:` removed from the description template,
> example TDD pair updated with citation fields, security-considerations
> rewritten to reflect the citation pattern; `output-format.md` gained
> the new fields in JSON example, validation rules 13–16, summary
> table reshaped (Component + Scenarios columns, Files dropped),
> "Integration with the Roadmap" subsection added; `SKILL.md` updated
> Quick Reference, How to Start, Phase 1 (now "Roadmap and Design Doc
> Analysis"), Phase 2 step renumbering with new "Cite roadmap
> scenarios" step, Phase 3 step 4 description, schema reference table
> (new fields + new top-level fields), Principles (added "Component
> boundaries come from the roadmap", "Scenario content lives in the
> roadmap", "The roadmap is read-only from here"). Schema smoke-tested
> against 8 cases (the 5 plan-mandated + 3 edge cases) — all pass.
> **Existing tasks.json files are now invalid** until regenerated
> against R03 roadmap output; D01 is the trial that will validate
> end-to-end regeneration.

> **Recent change (2026-05-02): R03 trial validates roadmap skill's
> scenario `id` field.** First of three coordinated changes per
> `decomposition-roadmap-refactor-plan-2026-05-02.md`. Schema additions
> to `roadmap_schema.py`: required `id: str` on `FunctionalScenario`
> and `SecurityScenario`; format validator (kebab-case);
> `scenario_ids_unique_within_component` model validator (rejects
> duplicates across both lists). Reference docs (`roadmap-json-format.md`,
> `phase-2-generation.md`) updated with the new field, a new "Scenario
> IDs" subsection, and Phase 2 writing guidance (preserve IDs across
> regenerations). Schema smoke-tested against 7 cases (happy + 6 edge
> cases) — all pass. R03 trial regenerated `roadmap.json` for
> airflow-gdrive-ingestion; 33 scenarios across 5 components, all
> kebab-case, unique within each component, schema-valid. Detail:
> `trials/R03-roadmap-scenario-id-field.md`.

> **Recent change (2026-05-01): R02 re-run validates the OWASP spec
> migration end-to-end.** First project trial against the rebuilt
> roadmap skill. All acceptance criteria green: JSON output,
> ASVS 5.0.0 version-baked IDs, `owasp_category_label` removed,
> validator clean with Categories Cited footer, R01 placement fix
> survives, structural rules fire correctly. Project Setup component
> (P05 work) implicitly exercised. No new failure modes; no skill
> changes required. Detail:
> `trials/R02-roadmap-spec-migration-revalidation.md`.

### Built and Validated

**prototype-driven-planning** — Major expansion landed 2026-04-23 after
the P01–P03 arc. Project Setup component addition landed 2026-04-27.
P04 (2026-04-29) added cliff-edge labeling discipline. Observability-
and-citations expansion landed 2026-05-14 (8 steps adding Phase 1
Observability-Friendly Tech Selection, source citations with
`accessed <YYYY-MM-DD>`, Phase 2 Telemetry and Performance Measurement
validation steps, Phase 3 External-source label, References section,
3 new principles). Post-P06 fixes landed 2026-05-15 → 2026-05-16:
Plan A (web-research discipline across all research-shaped steps),
Plan B (all downstream-skill references removed; skill now genuinely
standalone). Detail in the P01–P03, Project Setup, P04, and most
recent Current State sections.

**prototype-driven-task-decomposition** — Required `test_command: str`
field with two validators landed 2026-04-19 (T14). Refactor to consume
roadmap output landed 2026-05-03; D01 (2026-05-04) validated end-to-end
against R03 roadmap output. Schema gains 3 task fields + 2 top-level
fields + 4 validators. Component boundaries and behavioral scenarios
now come from the upstream roadmap; the decomposer doesn't infer them.
D02 (2026-05-06) added explicit project-root anchoring to schema-side
path resolution after the T15 first attempt surfaced a CWD-implicit
bug; `_resolve_project_path` helper now replaces four
`Path(p).resolve()` call sites in `task_schema.py`.

**prototype-driven-prompt-composition** — Built 2026-05-10 per
`prompt-composition-skill-plan-2026-05-09.md` step 1. Standalone
Python script + four reference docs. Reads `tasks.json` + `roadmap.json`,
writes one self-contained markdown prompt per task to
`tasks/<feature>/prompts/<task-id>.md`. The universal preamble
(extracted verbatim from the implementation skill's old
`compose_prompt.py.template` minus the project block) is uniform
across all tasks; dependency files are listed by path (no inlining);
retry/error context lives in `logs/lint/<task-id>/` and
`logs/tests/<task-id>/` per-attempt files; canonical prompts are
never modified after composition. Pure helper functions sandbox-tested
(67 assertions). End-to-end smoke test pending — needs host execution
against the real `airflow-gdrive-ingestion` decomposition. **Steps
2–5 pending** (implementation-skill changes, T17 trial); the pipeline
still consumes prompts via the old `compose_prompt.py.template` until
step 2 lands.

**prototype-driven-implementation** — LangGraph pipeline with
templated stable files; verbatim `test_command` copy from the schema.
T14 refactor landed 2026-04-19. D02 (2026-05-06) added a parallel
`_resolve_project_path` helper to `compose_prompt.py.template`
(replacing the inline absolute/relative guard with a named helper
that mirrors the decomposition schema's shape) and a Phase 3 Smoke
Test step that runs from the pipeline directory and exercises the
path-resolution code in both `load_tasks_node` and
`compose_prompt._inline_roadmap_scenarios` before handoff.
2026-05-07 landed the Phase A/B scaffold split: scaffold task-01 is
now executed by Claude Code in conversation as part of Phase 3
(after pipeline generation, before handoff), not by the LangGraph
pipeline. The pipeline gains a `check_preconditions` startup node
(verifies `.scaffold_complete` marker + lint/test tools), an
auto-resume mechanism via `logs/task_status.json` (pick_next_task
skips already-passed tasks), and atomic per-verdict persistence in
verify_task / mark_failed / skip transitions. Phase 1 replaces its
static bootstrap lookup table with a Runtime-Isolation Research
protocol — the model determines runtime-isolation tooling from
project signals (lockfiles, runtime-pin files, build-tool config)
or from runtime web research, locates the project's runtime
version pin, constructs the bootstrap command, and tests it in a
temp dir before committing. Two new config placeholders
(RUNTIME_VERSION_PIN, RUNTIME_VERSION_CHECK_CMD) drive Phase 3's
active-runtime-matches-pin verification. Validates in T16. **Per the
2026-05-09 prompt-composition refactor (steps 2–5 pending), the
pipeline will eventually consume pre-generated prompts via a new
`load_prompt` node and lose its `compose_prompt.py.template`
entirely — but as of 2026-05-10 that change has not landed.**

**prototype-driven-roadmap** — Three phases (Extraction → Generation
→ Validation) producing `components.json` + `roadmap.json` (post-
migration form). R01 fixes (Performed-by, ID-set parity check)
landed 2026-04-26. OWASP spec migration to ASVS 5.0.0 / MASVS 2.1.0
plus label canonicalization landed 2026-04-30. R02 re-run against
the rebuilt skill validated 2026-05-01 (clean sweep). Scenario `id`
field (required, kebab-case, unique-within-component) landed
2026-05-02 as step 1 of the three-skill decomposition refactor;
R03 (2026-05-02) validated end-to-end (33 scenarios, 5 components,
clean sweep).

### Roadmap Skill OWASP Spec Migration (2026-04-30)

Triggered by review of post-R02 skill artifacts. Two distinct issues
surfaced:

1. **Stale spec-version pin.** Reference docs were pinned to
   "ASVS 4.0.3 (last major release as of 2026-04-24)." Live verification
   confirmed ASVS 5.0.0 had been released in May 2025. The "as of"
   comment was authored without checking the source.
2. **Triple-source-of-truth for category labels.** Canonical category
   labels were stored in reference doc prose, per-scenario
   `owasp_category_label` fields, and (after the migration was
   planned) dedicated spec data files — three drift surfaces for one
   fact.

**Migration landed 2026-04-30:**

- **Spec data files** (`scripts/owasp-asvs.json`,
  `scripts/owasp-masvs.json`) ship as the single source of truth for
  pinned versions and canonical category titles, with explicit
  `verified_at` and `verified_against` provenance fields.
- **`owasp_category_label` field removed** from the roadmap.json
  schema; labels are derived at runtime from the spec data files for
  both the validator's summary footer and downstream skills.
- **ASVS IDs adopt the version-baked 5.0+ form** (`v5.0.0-1.2.5`);
  the schema regex is version-agnostic, the validator's runtime
  cross-check enforces version against the pinned spec.
- **Validator** loads spec data files at runtime (only the specs
  cited), cross-checks version + category prefix, renders a
  "Categories cited (ASVS 5.0.0):" footer with full canonical
  titles.
- **Reference docs rebuilt** for ASVS 5.0's 17-chapter structure.
  Reference docs speak abstractly about "the pinned version" — the
  pin lives only in the JSON.
- **MASVS coverage extended** with the PRIVACY control group
  (MASVS 2.1.0 added PRIVACY beyond the 7 categories of earlier
  versions).
- **6 new principles** in `LEARNINGS.md` covering live verification
  discipline, single source of truth for labels, force-visibility
  applies to verification, spec-data-stays-with-skill asymmetry,
  version-baked IDs, and the cross-cutting meta-pattern.

**Implications for prior trial output:**

- R01 and R02 output (in
  `~/health-data-ai-platform/docs/roadmap/airflow-gdrive-ingestion/`)
  used ASVS 4.0.3-form IDs and the `owasp_category_label` field. It
  is invalid against the rebuilt skill. The directory needs to be
  regenerated end-to-end.
- The decomposition-roadmap refactor plan
  (`decomposition-roadmap-refactor-plan-2026-04-26.md`) references
  the markdown output format and `components.yml`; sections §4.4,
  §5.1, §7, and §9.1 need updates before that work resumes.

**Cross-cutting pattern note:** the migration extends the
"force-visibility" pattern from P01–P03 (silent reasoning made
structural) and R01 (silent actor assumption made structural) to
the verification-of-external-standards layer. "As of <date>" prose
was claiming verification that didn't happen — same failure shape as
silent judgment, same fix shape (a typed artifact that can be
inspected and challenged: `verified_at`, `verified_against`).

### Planning Skill Project Setup Component (2026-04-27)

Surfaced during the decomposition-roadmap refactor work. The refactor
required scaffold tasks to declare a `roadmap_component`, and the
existing roadmap had no scaffold component to reference. Root-cause
analysis traced the omission to the planning skill's `### Components`
section capturing runtime/architectural components only.

**Fix landed (2026-04-27):**

- `phase-1-discovery.md` — new "Determine Project-Setup Status"
  section between Project Inventory and Identifying Integration
  Boundaries. Five greenfield triggers and three edge cases
  documented. Proposal template gains a labeled "Project setup"
  line.
- `phase-3-design-doc.md` — new "Project Setup component rule"
  subsection. When greenfield, the design doc's `### Components`
  MUST include a Project Setup entry as the first component. When
  extending, MUST NOT.
- `design-doc-template.md` — `### Components` template gains the
  Project Setup entry pattern for greenfield features. `## Tooling`
  gains a clarifying note.
- `SKILL.md` — Phase 1 step list gains the project-setup decision
  as Step 2; proposal-message description updated; Phase 3
  references the new rule.

**Validation pending:** P05 trial (see Next Steps).

### Planning Skill P01–P03 Iteration Arc (2026-04-23)

Three skill-development trials against
`~/health-data-ai-platform/docs/design/airflow-google-drive-ingestion-*.md`.
Full detail in `trials/P01`, `P02`, `P03`. Summary:

- **P01** — table-as-complete-spec + silent scope removal. Fixes:
  Surface Coverage Check, Scope-Removal Triage, two Principles.
- **P02** — feasibility-in-disguise + judgment-as-fact + Phase-1 scope
  ambiguity. Fixes: assertion test (2nd diagnostic), Scope Deferrals
  section, Judgment vs. Observation.
- **P03** — severity-blind handling + environmental-assessment
  shortcut + lesser-evil tradeoff. Fixes: severity-indexed handling,
  Mitigation Ladder (5 options including downgrade), Environmental
  Risk Assessment rules.

Cross-cutting pattern: silent reasoning made structural via visible
artifacts. The Project Setup work (2026-04-27) and the OWASP spec
migration (2026-04-30) both extend this pattern.

### Roadmap Skill Build Pass and R01/R02 (2026-04-24 → 2026-04-27)

**Build pass (2026-04-24):** original architecture used per-component
markdown files and `components.yml`, validator smoke-tested on three
scenarios.

**R01 (2026-04-26):** first real trial. Output passed all then-
existing structural rules. Review surfaced two fragility classes that
could not be caught structurally:

1. **Cross-component category misplacement.** Parser V8.1.1 scenario
   described work the orchestrator performs.
2. **Validator gap on registry-vs-scenario ID-set parity.** The
   validator format-checked OWASP IDs in registry and scenarios
   independently but never compared the sets.

Both fixes landed same day:

- Required `**Performed by** <slug>` field on every security
  scenario.
- Validator check: registry `owasp_categories` set must equal the
  set of OWASP IDs cited in security scenarios.
- Phase 1 actor-naming step in the proposal message.

**R02 (2026-04-27):** re-run on R01-fixed skill. R01 misplacement
does not repeat; structural fixes validated. **R02 output (markdown
format, ASVS 4.0.3 IDs) is now invalid against the post-migration
skill.**

**R02-prep (2026-04-30):** skill rebuild for OWASP spec migration as
described above. Not a project trial; full detail in
`trials/R02-prep-owasp-spec-migration.md`.

### T14 Run (2026-04-19): 16/17 passed; T14 Refactor Landed Same Day

Detail in `trials/T14-test-command-gap.md`. Summary:

- **16/17 tasks passed** (jump from T13's 5/19).
- **Only task-16 (integration test) failed.** Docker-compose-wrapped
  test command embedded in task description but never reached
  `TASK_TEST_COMMANDS`. Structural issue: prose is a lossy transport
  between decomposer and generator.

T14 refactor (`refactor-plan-2026-04-19.md`) landed same day:

- Decomposition: required `test_command: str` schema field with
  `validate_test_command_non_empty` and
  `validate_integration_test_lifecycle` validators.
- Implementation: `TASK_TEST_COMMANDS` populated verbatim from
  schema. Scaffold gets a real test gate (its own `test_command`
  with exit-5-tolerant pytest semantics).

Validates in T15 (next — see Next Steps).

### T10–T13 Arc (2026-04-16 through 2026-04-17)

Four runs on the same 19-task decomposition. Detail in
`trials/T10-T13-tightening-arc.md`. Summary:

- T10: 5/19. Templating refactor held; split-module test bug + mock
  path inconsistency.
- T11: 6/19. Gemini upgrade fixed mock drift; stubs-pass surfaced.
- T12: 2/19. Claude-as-test-writer; verify_task rigidity for partial
  stubs.
- T13: 5/19. Tight system prompt + tight task-02 spec; all 3 test
  tasks passed Gemini tier 0 r0. Test over-specification + fixture
  path bugs deferred to T14.

Six findings drove the T13 refactor (landed in T14): system-prompt
bloat > per-task bloat; tight task-doc templates beat freeform prose;
test over-specification is distinct from under-specification;
partial-stub components need a structural fix; dependency inlining
must filter to importable files; duplicate rule blocks across prompt
sections silently contradict.

### Features List (high-level)

Full per-feature list (1–53) preserved in git history. Recent
additions (2026-04-27 → 2026-05-10):

- **54: Project setup decision in planning Phase 1.** Binary
  greenfield-vs-extending decision with five triggers and three edge
  cases. Surfaces as a labeled answer at the top of the Phase 1
  prototype proposal.
- **55: Project Setup component in design doc (greenfield only).**
  When Phase 1 declares greenfield, the design doc's `### Components`
  MUST include a Project Setup entry as the first component. When
  extending, the component is omitted; the absence is the downstream
  signal.
- **56: Component ordering follows implementation order.** Design
  doc's `### Components` lists components in dependency-graph order
  (roots first), consistent with the roadmap skill's Phase 1 message
  ordering. Project Setup is always a root when present.
- **57: OWASP spec data files as single source of truth.**
  `scripts/owasp-asvs.json` and `scripts/owasp-masvs.json` hold pinned
  spec versions, canonical category titles, and `verified_at` /
  `verified_against` provenance. (2026-04-30)
- **58: Version-baked OWASP ID format for ASVS.** Adopted ASVS 5.0+'s
  `v<spec_version>-<chapter>.<section>.<requirement>` shape. Schema
  regex is version-agnostic; validator's runtime check enforces
  version against the pinned spec. (2026-04-30)
- **59: `owasp_category_label` field removed from schema.** Labels
  live only in spec data files; the validator's summary footer
  renders them at output time. (2026-04-30)
- **60: Roadmap output is JSON, not markdown.** `components.json` +
  `roadmap.json` replace the per-component `.md` files. Schemas ship
  into the project; spec data files stay with the skill.
- **61: `verified_at` / `verified_against` provenance pattern.**
  Spec data files carry explicit verification metadata; "as of
  <date>" prose pretending verification is now a banned anti-pattern.
  (2026-04-30)
- **62: Prompt composition extracted into its own skill.** Reads
  tasks.json + roadmap.json, writes one self-contained markdown
  prompt per task. Pipeline becomes one consumer among several;
  manual consumers (Claude Code, Aider, custom wrappers) read the
  same canonical prompts. Per-attempt log subfolder convention
  replaces in-prompt retry/error context. (2026-05-10, step 1 of
  multi-step refactor; steps 2–5 pending.)

### Skill Expansion Plan — Complete

All parts of `skill-expansion-plan-2026-04-21.md` have landed:

- Part A (Phase 3 Open Questions Triage) — 2026-04-23 (P01–P03 arc).
- Part C (Phase 2 security-tooling validation) — 2026-04-23 (P01,
  P03).
- Part B (`prototype-driven-roadmap` skill) — 2026-04-24 initial
  build, with major rebuilds in R01-era (2026-04-26) and R02-prep
  (2026-04-30).

The plan doc is historical. New skill expansions live in new plan
docs (`planning-project-setup-component-plan-2026-04-27.md`,
`asvs-5-migration-plan-2026-04-30.md`,
`prompt-composition-skill-plan-2026-05-09.md`).

---

## Next Steps

- **Smoke-test the prompt-composition skill end-to-end on the host.**
  First task of the next session. From the host (this script needs
  pydantic + the project filesystem; the chat sandbox can't run it):
  ```bash
  cd ~/health-data-ai-platform
  uv run --with pydantic python ~/claude-devtools/skills/prototype-driven-prompt-composition/scripts/compose_prompts.py airflow-gdrive-ingestion
  ```
  Expected output: Phase 1 STOP-summary listing inputs + extensions
  + 12 tasks + ~33 citations; Phase 2 writing 12 prompt files;
  Phase 3 confirming all 12 found, all non-empty, all required
  markers present. If any prompts/ directory exists from a prior
  run, delete it first
  (`rm -rf ~/health-data-ai-platform/tasks/airflow-gdrive-ingestion/prompts`).
  See `session-status-2026-05-10.md` for full detail and what to
  verify in the output.

- **Steps 2–5 of `prompt-composition-skill-plan-2026-05-09.md`.**
  After the smoke test passes and the user reviews 2-3 of the
  generated prompt files: (2) implementation-skill changes — delete
  `templates/nodes/compose_prompt.py.template`, add
  `templates/nodes/load_prompt.py`, modify `verify_task.py` to write
  to `logs/lint/<task-id>/attempt-N-tierM.txt` and the matching
  tests/ path, modify `check_preconditions.py` to verify all prompt
  files exist, modify `graph.py` to wire `load_prompt` between
  `pick_next_task` and `execute_task`, modify `pipeline_state.py`
  to drop `current_lint_error_path` / `current_test_error_path`
  (no longer needed; convention replaces injected paths), modify
  `config.py.template` to remove `{{ROADMAP_JSON_PATH}}`. Update
  SKILL.md (precondition added; Phase 2 step removed; Phase 3 smoke
  test simplifies; Scaffold Execution reads from prompts dir per
  D10), `phase-2-generation.md`, `phase-3-handoff.md`. (3) trial
  slot stage in memory repo. (4) T17 trial: pre-trial cleanup,
  five-arm validation (generate prompts, manual inspect, hand to
  Claude Code without pipeline, run pipeline, validate retry
  behavior). (5) Post-trial memory repo update — distill new
  principles, mark plan superseded.

- **T16 — validates the Phase A/B scaffold split end-to-end.**
  Pre-trial setup: user removes existing
  `pipelines/airflow-gdrive-ingestion/` directory (the
  pipeline-existence precondition requires a clean slate). Trial
  sequence: (1) re-run implementation skill against
  airflow-gdrive-ingestion's tasks.json. Phase 1 should produce
  visible runtime-isolation research output (signals consulted, tool
  chosen, runtime pin detected, bootstrap command tested in temp
  dir). Phase 3 executes scaffold task-01 + bootstrap interactively;
  the Python-3.13-incompatibility that blocked T15 should not occur
  because the bootstrap installs the project-pinned runtime via the
  chosen tool, not via the host's `python3`. Phase 3 writes
  `.scaffold_complete` and `logs/task_status.json` with task-01
  marked passed. (2) `python run.py` (no `--start` flag).
  `check_preconditions` finds the marker and tool availability;
  `pick_next_task` reads `task_status.json` and starts at task-02.
  Tasks 02..N execute. (3) Re-run `python run.py`; verify it skips
  all passed tasks and exits cleanly. Acceptance bar: T15's blocking
  failure mode (Python version incompatibility cascading) does not
  occur; Phase A completes without retry/escalation cascade;
  task_status.json accurately tracks state across runs; runtime
  isolation step shows visible research output (URLs, tool choice
  rationale) rather than table consultation; bootstrap command
  contains an explicit runtime-version specifier; pipeline completes
  all 12 tasks. **T16 may run before or after the prompt-composition
  steps 2–5; they're independent.** Out of scope: validating
  runtime-isolation against non-Python ecosystems (responsibility-
  not-realization framing makes this safe in principle; future trial
  will validate with a Node / Android / Go project). Detail in
  `trials/T16-phase-a-scaffold-split.md` once filed.

- **T15 — superseded by T16.** T15's two attempts (2026-05-07 11:33
  and 15:54) blocked at task-01 on Python version incompatibility
  and motivated the Phase A/B refactor. The end-to-end validation
  T15 was meant to perform now lives in T16's acceptance bar.

- **Three-skill refactor per
  `decomposition-roadmap-refactor-plan-2026-05-02.md` — complete on
  the skill side.** All three coordinated changes have landed and
  three have validation trials filed (R03, D01, D02). T16 is the
  final end-to-end validation (replacing T15).

- **P04 validation trial (planning skill, P01–P03 fixes).** Lower
  priority. Still on the list.

- **File P06 trial detail.** P06 ran 2026-05-15 against
  `airflow-gdrive-ingestion`; surfaced the two gaps that drove
  Plans A and B. Trial file at
  `trials/P06-research-discipline-and-downstream-cleanup.md` not yet
  written. Capture: design doc output's behavior on the gaps (model
  ran Trivy, reported HIGH as unresolvable until prompted to search;
  design doc generated with stale skill references intact); the
  conversation reasoning that landed on Plans A vs. B vs. "remove
  references entirely"; the final landing log. Lower priority — the
  fixes are in, the README and LEARNINGS.md captures the substance.

- **(Done) Manual cleanup**:
  `~/claude-devtools/skills/prototype-driven-implementation/templates/nodes/bootstrap.py`
  tombstone confirmed deleted 2026-05-04.

- **(Done) Obsolete decomposition output cleanup**:
  `~/health-data-ai-platform/tasks/airflow-google-drive-ingestion/`
  (T14 directory, invalid against the post-D01 schema) can be deleted
  manually. The current decomposition output lives at
  `~/health-data-ai-platform/tasks/airflow-gdrive-ingestion/`.

---

## Test Run Results (session history)

### Planning Skill
- Session `f75b5f43-fd52-4138-87ad-c7c18589fa07` — First test run (2026-03-28)
- Session `a7c48f00-b614-4086-a640-b623a00f5a97` — Second test run (2026-03-28)
- P01 (2026-04-23) — First Part A + C trial
- P02 (2026-04-23) — Second Part A + C trial (design-doc review)
- P03 (2026-04-23) — Third Part A + C trial (security-finding handling)
- P04 (2026-04-29) — Cliff-edge labeling discipline trial. Detail in
  `trials/P04-cliff-edge-labeling-discipline.md`.
- P05 (2026-05-01) — Project Setup component validation. Done; design doc updated to include Project Setup component as first entry.
- P06 (2026-05-15) — Post-observability-expansion trial against
  `airflow-gdrive-ingestion`. Surfaced two gaps: (1) research-shaped
  instructions elsewhere in the skill defaulted to training-data
  recall when they didn't explicitly name web search; (2) stale
  references to downstream skills throughout the skill files. Both
  gaps fixed via Plans A and B (landed 2026-05-15 → 2026-05-16). The
  expansion's own rules (live tech-selection research, web-searched
  citations) worked as designed. Trial detail to be filed at
  `trials/P06-research-discipline-and-downstream-cleanup.md`.

### Decomposition Skill
- Session `6d471491-32b7-4f74-a720-8fdbf0060023` — First run (8 tasks)
- Session `b2354707-0024-45db-bb9a-7ff872e39271` — Second run (11 tasks)
- Session `64052f92-5393-4425-8286-1389124c6feb` — Third run (27 tasks)
- D01 (2026-05-04) — First decomposition-skill iteration trial; validates roadmap consumption (step 3 of three-skill refactor). 13 tasks across 5 components, 60 scenario citations all resolve, clean sweep.
- D02 (2026-05-06) — CWD-relative path resolution surfaced at T15 first attempt. Schema-side `_resolve_project_path` helper added; parallel helper in `compose_prompt.py.template`; Phase 3 smoke test added. Project-side artifacts unchanged per directive.

### Prompt-Composition Skill
- Sandbox helper test (2026-05-10) — 67 assertions, all pass. Pure
  helper logic verified. End-to-end smoke test against the host is
  the next session's first task.

### Implementation Skill — runs 1–14
See `trials/_SUMMARY.md` for the canonical scoreboard.

### Roadmap Skill
- Design pass (2026-04-24) — skill built and validator smoke-tested.
- R01 (2026-04-26) — first real trial; structural fixes landed same
  day.
- R02 (original, 2026-04-27) — R01 fixes validated (markdown / ASVS
  4.0.3 output). Now invalid against the post-migration skill.
- R02-prep (2026-04-30) — skill rebuild for OWASP spec migration.
  Not a project trial.
- R02 re-run (2026-05-01) — first trial against rebuilt skill;
  clean sweep. Validates the OWASP spec migration end-to-end.
- R03 (2026-05-02) — retargeted to validate scenario `id` field
  addition (step 1 of 2026-05-02 three-skill refactor). Schema
  smoke-tested + airflow-gdrive-ingestion regenerated; 33 scenarios
  across 5 components, all unique within component. Clean sweep.

---

## File Map

```
~/claude-project-memory/prototype-driven-planning-skill/
├── README.md                                     # This file (read first)
├── LEARNINGS.md                                  # Distilled principles (read second)
├── gemini_conversation.txt                       # Raw Gemini consultation (historical)
├── refactor-plan-2026-04-17.md                   # T13 refactor (landed in T14)
├── refactor-plan-2026-04-19.md                   # T14 refactor (landed same day)
├── skill-expansion-plan-2026-04-21.md            # All parts landed; historical
├── decomposition-roadmap-refactor-plan-2026-04-26.md  # Paused; needs §4.4/§5.1/§7/§9.1 update for JSON output
├── planning-project-setup-component-plan-2026-04-27.md # Landed 2026-04-27
├── asvs-5-migration-plan-2026-04-30.md           # Landed 2026-04-30
├── phase-a-scaffold-split-plan-2026-05-07.md     # Active; T16 validates
├── prompt-composition-skill-plan-2026-05-09.md   # Active; step 1 landed 2026-05-10; steps 2-5 pending
├── observability-and-citations-plan-2026-05-14.md  # Landed 2026-05-14 (8 steps); post-P06 fixes landed 2026-05-15 → 2026-05-16
├── session-status-2026-05-10.md                  # Mid-stream handoff for the prompt-composition refactor
├── references/
│   ├── architecture-rationale.md
│   └── stack-reference.md
└── trials/
    ├── _SUMMARY.md                               # Scoreboard
    ├── _INDEX.md
    ├── T<NN>-<slug>.md                           # Pipeline trials
    ├── P<NN>-<slug>.md                           # Planning-skill iterations
    ├── R<NN>-<slug>.md                           # Roadmap-skill trials/rebuilds (R01, R02-prep, R02, R03)
    └── D<NN>-<slug>.md                           # Decomposition-skill iterations (D01, D02)

~/claude-devtools/skills/prototype-driven-planning/
├── SKILL.md                                      # Updated 2026-05-16 (observability expansion + post-P06 fixes)
└── references/
    ├── design-doc-template.md                    # Updated 2026-05-16 (5-label meta, Telemetry/Performance fields, References)
    ├── phase-1-discovery.md                      # Updated 2026-05-16 (Observability Tech Selection, Source Citations, web-research preamble)
    ├── phase-2-prototype.md                      # Updated 2026-05-16 (Telemetry + Performance validation, Mitigation Ladder search preamble, Cross-Cutting web-research preamble)
    └── phase-3-design-doc.md                     # Updated 2026-05-16 (External-source label, References section, downstream-skill references removed)

~/claude-devtools/skills/prototype-driven-task-decomposition/
├── SKILL.md                                      # Updated 2026-05-03 (roadmap consumption)
├── scripts/
│   └── task_schema.py                            # Updated 2026-05-06 (D02: `_resolve_project_path` helper + 4 call sites)
└── references/
    ├── analysis-guide.md                         # Rewritten 2026-05-03 (roadmap-primary)
    ├── task-writing-guide.md                     # Updated 2026-05-03 (Roadmap-Driven Task Authoring section)
    └── output-format.md                          # Updated 2026-05-03 (new fields, summary table reshape, Integration with Roadmap)

~/claude-devtools/skills/prototype-driven-prompt-composition/  # NEW 2026-05-10
├── SKILL.md                                      # Three-phase flow: Inputs → Generation → Validation
├── scripts/
│   └── compose_prompts.py                        # Standalone (no LangGraph dep); reads tasks.json + roadmap.json
└── references/
    ├── preamble.md                               # Verbatim universal preamble (project block removed per D9)
    ├── prompt-template.md                        # Canonical section structure for downstream consumers
    ├── log-conventions.md                        # logs/lint/<task-id>/attempt-N-tierM.txt convention
    └── dependency-handling.md                    # Option A (paths-not-inlined) rationale + deferred A+ notes

~/claude-devtools/skills/prototype-driven-implementation/
├── SKILL.md                                      # Updated 2026-05-07 (Phase A/B split, runtime-isolation research, no static bootstrap table)
├── templates/
│   ├── run.py                                    # Updated 2026-05-07 (auto-resume default; --start as override; bootstrap_done removed)
│   ├── pipeline_state.py                         # Updated 2026-05-07 (bootstrap_done removed from state)
│   ├── graph.py                                  # Updated 2026-05-07 (check_preconditions wired in; mark_failed/skip persist to task_status.json)
│   ├── agent_bridge.py
│   ├── requirements.txt
│   ├── config.py.template                        # Updated 2026-05-07 (RUNTIME_VERSION_PIN, RUNTIME_VERSION_CHECK_CMD added)
│   └── nodes/
│       ├── __init__.py
│       ├── load_tasks.py                         # Updated 2026-05-07 (merges task_status.json on startup)
│       ├── check_preconditions.py                # NEW 2026-05-07 (verifies .scaffold_complete + lint/test tools at startup)
│       ├── compose_prompt.py.template                # Updated 2026-05-06 (D02: `_resolve_project_path` helper hoisted from inline guard); SLATED FOR DELETION in step 2 of prompt-composition refactor
│       ├── execute_task.py
│       ├── verify_task.py                        # Updated 2026-05-07 (scaffold branch removed; persists per-verdict to task_status.json); WILL BE UPDATED in step 2 of prompt-composition refactor (per-attempt log convention)
│       └── report.py
└── references/
    ├── phase-1-analysis.md                       # Updated 2026-05-07 (static bootstrap lookup removed; Runtime-Isolation Research protocol added)
    ├── phase-2-generation.md                     # Updated 2026-05-07 (RUNTIME_VERSION_PIN/CHECK placeholders; static ecosystem table reframed; check_preconditions in template list)
    ├── langgraph-patterns.md
    ├── executor-integration.md
    └── phase-3-handoff.md                        # Rewritten 2026-05-07 (Validation/Scaffold-Execution/Handoff sections; six-step Phase A protocol)

~/claude-devtools/skills/prototype-driven-roadmap/
├── SKILL.md                                      # Major rewrite 2026-04-30 (OWASP spec migration)
├── scripts/
│   ├── components_schema.py                      # Updated 2026-04-30: version-agnostic ASVS regex
│   ├── roadmap_schema.py                         # Updated 2026-04-30: regex; owasp_category_label REMOVED
│   ├── validate_roadmap.py                       # Updated 2026-04-30: spec loading, runtime cross-checks, Categories Cited footer
│   ├── owasp-asvs.json                           # NEW 2026-04-30: ASVS 5.0.0 spec data
│   └── owasp-masvs.json                          # NEW 2026-04-30: MASVS 2.1.0 spec data
└── references/
    ├── components-json-format.md                 # Updated 2026-04-30 (replaces components-yml-format.md)
    ├── roadmap-json-format.md                    # Updated 2026-04-30 (replaces roadmap-item-template.md)
    ├── phase-1-extraction.md                     # Updated 2026-04-30
    ├── phase-2-generation.md                     # Updated 2026-04-30
    ├── phase-3-validation.md                     # Updated 2026-04-30
    ├── owasp-asvs-mapping.md                     # Rebuilt 2026-04-30 for ASVS 5.0's 17-chapter structure
    └── owasp-masvs-mapping.md                    # Updated 2026-04-30: MASVS-PRIVACY data flows added

~/claude-devtools/commands/
├── prototype-plan.md
├── prototype-roadmap.md
├── prototype-task-decompose.md
├── prototype-compose-prompts.md                  # NEW 2026-05-10
└── prototype-implement.md
```
