# Prototype-Driven Planning Skills — Project Context

> **Purpose**: Persistent memory across chat sessions for the prototype-driven
> skill set (planning → task decomposition → implementation).
>
> **Skill locations**:
> - `~/claude-devtools/skills/prototype-driven-planning/`
> - `~/claude-devtools/skills/prototype-driven-task-decomposition/`
> - `~/claude-devtools/skills/prototype-driven-implementation/`
> - `~/claude-devtools/skills/prototype-driven-roadmap/`
>
> **Commands**:
> - `/prototype-plan <feature>` → planning skill
> - `/prototype-task-decompose <design-doc>` → decomposition skill
> - `/prototype-implement <feature>` → implementation skill
> - `/prototype-roadmap <feature>` → roadmap skill
>
> **Test project**: `~/health-data-ai-platform` (airflow Google Drive ingestion)

---

## Conversation-Start Protocol

Read these files in order:
1. **This file** — orientation, standings, open issues
2. **`LEARNINGS.md`** — distilled principles (always relevant)
3. **`trials/_SUMMARY.md`** — scoreboard

Load on-demand only when needed:
- `references/architecture-rationale.md`
- `references/stack-reference.md`
- `gemini_conversation.txt` (historical)
- `trials/_INDEX.md`
- `trials/T<NN>-*.md` — pipeline trials (T01–T14)
- `trials/P<NN>-*.md` — planning-skill iterations (P01–P03, P05)
- `trials/R<NN>-*.md` — roadmap-skill trials and rebuilds (R01, R02-prep, R02, R03)
- `trials/D<NN>-*.md` — decomposition-skill iterations (D01)
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

---

## Current State (2026-05-04)

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
the P01–P03 arc. Project Setup component addition landed 2026-04-27
(validates in P05). Detail in the P01–P03 and Project Setup sections
below.

**prototype-driven-task-decomposition** — Required `test_command: str`
field with two validators landed 2026-04-19 (T14). Refactor to consume
roadmap output landed 2026-05-03; D01 (2026-05-04) validated end-to-end
against R03 roadmap output. Schema gains 3 task fields + 2 top-level
fields + 4 validators. Component boundaries and behavioral scenarios
now come from the upstream roadmap; the decomposer doesn't infer them.

**prototype-driven-implementation** — LangGraph pipeline with
templated stable files; verbatim `test_command` copy from the schema;
scaffold verification runs bootstrap + lint-tool check + the
scaffold's own test_command. T14 refactor landed 2026-04-19.

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
additions (2026-04-27 → 2026-04-30):

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
`asvs-5-migration-plan-2026-04-30.md`).

---

## Next Steps

- **T15 — top of queue.** Run the implementation pipeline against
  D01's regenerated tasks.json. Acceptance: pipeline imports the new
  `task_schema.py` cleanly; `compose_prompt.py` inlines roadmap
  scenarios for tasks with citations (manual spot-check of two task
  prompts in `logs/prompts/`); executor sees richer Given/When/Then
  content than the previous paraphrased prose; end-to-end pipeline
  run completes (existing T01–T14 acceptance bar still applies).
  Detail in `trials/T15-roadmap-driven-pipeline.md` once filed.

- **Three-skill refactor per
  `decomposition-roadmap-refactor-plan-2026-05-02.md` — complete on
  the skill side.** All three coordinated changes have landed and two
  have validation trials filed (R03, D01). T15 is the final
  end-to-end validation.

- **P04 validation trial (planning skill, P01–P03 fixes).** Lower
  priority. Still on the list.

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
- P05 (2026-05-01) — Project Setup component validation. Done; design doc updated to include Project Setup component as first entry.

### Decomposition Skill
- Session `6d471491-32b7-4f74-a720-8fdbf0060023` — First run (8 tasks)
- Session `b2354707-0024-45db-bb9a-7ff872e39271` — Second run (11 tasks)
- Session `64052f92-5393-4425-8286-1389124c6feb` — Third run (27 tasks)
- D01 (2026-05-04) — First decomposition-skill iteration trial; validates roadmap consumption (step 3 of three-skill refactor). 13 tasks across 5 components, 60 scenario citations all resolve, clean sweep.

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
├── references/
│   ├── architecture-rationale.md
│   └── stack-reference.md
└── trials/
    ├── _SUMMARY.md                               # Scoreboard
    ├── _INDEX.md
    ├── T<NN>-<slug>.md                           # Pipeline trials
    ├── P<NN>-<slug>.md                           # Planning-skill iterations
    ├── R<NN>-<slug>.md                           # Roadmap-skill trials/rebuilds (R01, R02-prep, R02, R03)
    └── D<NN>-<slug>.md                           # Decomposition-skill iterations (D01)

~/claude-devtools/skills/prototype-driven-planning/
├── SKILL.md                                      # Updated 2026-04-27
└── references/
    ├── design-doc-template.md
    ├── phase-1-discovery.md
    ├── phase-2-prototype.md                      # Updated 2026-04-23
    └── phase-3-design-doc.md                     # Updated 2026-04-27

~/claude-devtools/skills/prototype-driven-task-decomposition/
├── SKILL.md                                      # Updated 2026-05-03 (roadmap consumption)
├── scripts/
│   └── task_schema.py                            # Updated 2026-05-03 (roadmap citation fields + 4 new validators)
└── references/
    ├── analysis-guide.md                         # Rewritten 2026-05-03 (roadmap-primary)
    ├── task-writing-guide.md                     # Updated 2026-05-03 (Roadmap-Driven Task Authoring section)
    └── output-format.md                          # Updated 2026-05-03 (new fields, summary table reshape, Integration with Roadmap)

~/claude-devtools/skills/prototype-driven-implementation/
├── SKILL.md                                      # Updated 2026-04-19
├── templates/
│   ├── run.py
│   ├── pipeline_state.py
│   ├── graph.py
│   ├── agent_bridge.py
│   ├── requirements.txt
│   ├── config.py.template                        # Updated 2026-05-03 (ROADMAP_JSON_PATH)
│   └── nodes/
│       ├── __init__.py
│       ├── load_tasks.py
│       ├── compose_prompt.py.template                # Updated 2026-05-03 (_inline_roadmap_scenarios)
│       ├── execute_task.py
│       ├── verify_task.py                        # Updated 2026-04-19
│       └── report.py
└── references/
    ├── phase-1-analysis.md                       # Updated 2026-04-19
    ├── phase-2-generation.md                     # Updated 2026-05-03 (roadmap-scenario inlining)
    ├── langgraph-patterns.md
    ├── executor-integration.md
    └── phase-3-handoff.md                        # Updated 2026-04-19

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
├── prototype-task-decompose.md
└── prototype-roadmap.md
```
