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
- `references/architecture-rationale.md` — why prototype-first, multi-model design, tool selection
- `references/stack-reference.md` — tool versions, configs, CLI flags, doc links
- `gemini_conversation.txt` — raw Gemini consultation transcript (historical)
- `trials/_INDEX.md` — structured tags per trial (find trials by failure pattern)
- `trials/T<NN>-*.md` — individual pipeline trial detail (T01–T14, implementation skill)
- `trials/P<NN>-*.md` — individual planning-skill iteration detail (P01–P03)
- `refactor-plan-2026-04-17.md` — T13 refactor plan (landed in T14)
- `refactor-plan-2026-04-19.md` — T14 refactor plan (landed same day; validates in T15)
- `skill-expansion-plan-2026-04-21.md` — expansion plan. All parts
  landed (Parts A + C on 2026-04-23, Part B on 2026-04-24). Historical
  reference only.

---

## Current State (2026-04-24)

### Built and Validated

**prototype-driven-planning** — 3 phases (Discovery → Tracer Bullet → Design Doc)
with mandatory pauses. Major expansion landed 2026-04-23 after a
three-iteration refinement arc (P01–P03):

- **Phase 2** now includes prototype security-tooling validation (dep
  scan, secrets scan, SAST) with a Surface Coverage Check that forces
  multi-tool selection for prototypes carrying multiple surfaces
  (Dockerfile, compose, IaC, shell). Security findings are handled via
  a severity-indexed policy and a 5-option Mitigation Ladder — Critical
  findings block, all severities attempt fixes before deferral,
  environmental risk assessments are proposals to the user rather than
  unilateral decisions.
- **Phase 2** also includes Scope-Removal Triage, forcing model-initiated
  removals of approved Phase 1 items through a three-bucket classification
  (User-confirmed / Requires user decision / Must be validated) with a
  mandatory STOP-report bullet.
- **Phase 3** has a new Open Questions Triage step before the final STOP.
  Every open item goes through two diagnostics (difference test AND
  assertion test) and is classified into three buckets (Resolved by user
  decision / Requires prototype extension / Deferred to implementation).
  The `## Open Questions` section in the design-doc template was renamed
  `## Deferred Decisions` with a hard rule: no feasibility questions
  allowed.
- **Phase 3** Writing Quality section now has a **Judgment vs. Observation**
  subsection with explicit labeling rules for behavioral claims (`Not
  observed — based on inference`) and prescriptions (`Prescribed (not
  validated)`).
- **Design-doc template** now has a `## Scope Deferrals from Phase 1`
  section separating user-approved out-of-scope items from
  prototype-design-choice limitations. Silence is not an allowed outcome
  — the section reads `None — all Phase 1 scope was validated` when
  empty.

**prototype-driven-task-decomposition** — 3 phases (Analysis → Task Generation →
Validation/Output). Produces `tasks/<feature>/tasks.json` with strict TDD
pairing and per-task `test_command` enforced by PydanticAI schema validators.

**prototype-driven-implementation** — LangGraph pipeline with templated stable
files and verbatim `test_command` copy from the schema. Scaffold verification
runs bootstrap + lint-tool check + the scaffold's own test_command.

### Planning Skill P01–P03 Iteration Arc (2026-04-23)

Three skill-development trials against
`~/health-data-ai-platform/docs/design/airflow-google-drive-ingestion-*.md`.
Full detail in `trials/P01`, `P02`, `P03`. Summary:

- **P01** — First trial after Parts A + C merged. Identified two failure
  modes: (1) security tool tables read as complete specification (bandit
  picked for a project with Dockerfile + compose surfaces it couldn't
  cover), and (2) silent scope removal ("for the prototype, DB persistence
  isn't needed — remove the volume" dropped an approved Phase 1 item).
  Fixes: Surface Coverage Check, Scope-Removal Triage, two Principles
  ("Tables are starting points, not terminuses" and "Removals from
  approved Phase 1 scope are user decisions").
- **P02** — Second trial after P01 fixes landed. Surface Coverage Check
  and Scope-Removal Triage held. Review of the generated design doc
  surfaced three new failure modes: feasibility questions in Deferred
  Decisions that passed a "difference test" but failed an unstated
  "assertion test" (e.g., "boto3 upgrade is API-stable"), judgment-call
  prose indistinguishable from observation prose ("this is the correct
  behavior"), and conflation of user-approved Phase 1 deferrals with
  model-designed prototype limitations. Fixes: assertion test as a
  second triage diagnostic, new `## Scope Deferrals from Phase 1`
  design-doc section, Judgment vs. Observation Writing Quality
  subsection, new Principle ("Observation and judgment are labeled
  distinctly in the design doc").
- **P03** — Third trial after P02 fixes landed. Security findings
  handling was exercised for the first time under real CVE escalation
  (Airflow 2.9.x CVEs → user asks to extend prototype → model upgrades
  to 3.x → new Critical CVEs via `litellm` transitive dep). The model
  unilaterally finalized an environmental risk assessment ("we're not
  running litellm as a public-facing proxy"), chose between only two
  options (stay or upgrade to 1.83.0), and accepted the new Critical
  CVEs as the lesser evil without exploring pinning, downgrading, or
  exclusion. Fixes: severity-indexed Handling Findings subsection,
  Mitigation Ladder (5 options including downgrade as a first-class
  move), Environmental Risk Assessment rules (assessments are proposals
  not decisions; reachability must be addressed specifically; Critical
  assessments name a condition under which the assessment would be
  wrong), new Principle ("Security findings get severity-indexed
  handling, not blanket deferral").

**Cross-cutting meta-pattern from all three trials:** each failure mode is
a different shape of the same underlying pattern — the model does
reasoning silently and renders the output as fact-shaped prose. The
fixes each force a reasoning step into a visible artifact (tool-selection
table walkthrough, scope-change message, assertion-test confirmation,
judgment-vs-observation label, mitigation-ladder attempt log,
environmental-assessment proposal). When a new failure mode surfaces in
future trials, the diagnostic question is "what reasoning did the model
do silently that should have been visible?" — the artifact that forces
visibility is the fix.

### T14 Run (2026-04-19): 16/17 passed

Full detail in `trials/T14-test-command-gap.md`. Summary:

- All T13 refactor items landed before T14: tight task-doc template
  (Component / Component type / Interface / Behaviors / Expected failure
  mode / Out of scope), JSON-only decomposition output (no per-task `.md`),
  `expected_test_failure_modes` schema field wired through `verify_task`,
  `compose_prompt.py.template` with the T13-validated system-prompt
  tightening.
- **16/17 tasks passed.** Jump from T13's 5/19. task-05 (test over-spec)
  and task-07 (fixture path) — the T13 failures explicitly deferred as
  out of scope — both passed in T14 without targeted fixes.
- **Only task-16 (integration test) failed, all 4 attempts.** Failure
  mode was `ERROR at setup of test_upload_avro_round_trip`: the
  `pytest.fail()` call inside the fixture when MinIO is unreachable.
  Claude's T1-R1 attempt correctly diagnosed the fixture as working as
  designed.

**Root cause of the single failure:** the decomposer wrote the correct
Docker-compose-wrapped test command into task-16's `description` prose,
but the Phase 2 generator's `TASK_TEST_COMMANDS` derivation ignored
descriptions and constructed a plain `uv run pytest tests/test_integration.py
-x`. Tests ran without Docker services. Structural issue: prose is a
lossy transport between decomposer and generator.

### T14 Refactor Landed (2026-04-19)

See `refactor-plan-2026-04-19.md` for full plan.

**Decomposition skill changes:**
- Added required `test_command: str` field to `Task` schema, with
  `validate_test_command_non_empty` and
  `validate_integration_test_lifecycle` validators. Existing T14
  `tasks.json` now fails validation with "Field required" on every
  task — the expected signal to regenerate.
- `task-writing-guide.md` — new "Task `test_command`" section with
  per-task-kind × per-language table and the canonical
  integration-test lifecycle pattern (with its five rules: `--wait`
  on up, `&&` between up and test-runner, `;` before down, `rc=$?`
  + `exit $rc`, `-v --remove-orphans` on down).
- `output-format.md` — example JSON shows `test_command` on all task
  kinds including an integration example; validation checklist item
  12 added; summary table gained a Test Command column.
- `SKILL.md` — schema reference table updated; Phase 2 and Principles
  mention the new field.

**Implementation skill changes:**
- `templates/config.py.template` — `TASK_TEST_COMMANDS: dict[str, str]`
  (dropped `| None`); `_validate_docker_if_needed` comment updated.
- `templates/nodes/verify_task.py` — scaffold branch extended: after
  bootstrap + lint-tool check, run the scaffold's own `test_command`
  as the final gate. Stale pytest-availability check (`pytest --co -q
  || true`) removed from `_run_scaffold_bootstrap`. Syntax-checked
  clean.
- `references/phase-1-analysis.md` — "Per-Task Test Command Derivation"
  section replaced with "Per-Task Test Commands" that explicitly
  defers to the schema; integration-test-task detection section added;
  presentation-summary table now shows `test_command`.
- `references/phase-2-generation.md` — `TASK_TEST_COMMANDS` now
  "verbatim from `task.test_command`. No derivation, no fallback, no
  defaults." Generation Principles add an entry emphasizing this.
- `references/phase-3-handoff.md` — Config Validation gained a
  "TASK_TEST_COMMANDS completeness" check; Precondition Validation
  gained "Task ID coverage (reverse)"; What-happens list describes
  the new scaffold gate.
- `SKILL.md` — Phase 1 no longer says "Derive per-task test commands";
  Phase 3 precondition checks updated; Principles gained
  "`test_command` is the decomposer's field" and "Every task has a
  test gate".

**Not changing:**
- Pipeline templates beyond `verify_task.py` and
  `config.py.template` are untouched.
- `INTEGRATION_TEST_TASK_IDS` stays (orthogonal verification-mode
  concern).
- `GLOBAL_TEST_CMD` stays (kept for manual runs).
- Existing `expected_test_failure_modes` field and its validators are
  unchanged.

### Roadmap Skill Build Pass (2026-04-24)

`prototype-driven-roadmap` skill landed in a single build pass. Consumes
a signed-off design doc + prototype directory, produces
`docs/roadmap/<feature>/<slug>.md` — one markdown file per component
from the design doc's Architecture Overview. Each file has frontmatter,
Purpose, Prototype evidence, Functional Scenarios (Gherkin), Security
Scenarios (Gherkin with ASVS/MASVS IDs in headings), Out of Scope,
Dependencies.

**Architecture:**

- **Three phases** with STOPs: Extraction (parse design doc, derive data
  flows, map to OWASP, generate slugs, write `components.yml` after
  user approval) → Generation (write one roadmap file per
  `components.yml` entry) → Validation (run `validate_roadmap.py`,
  print summary table).
- **`components.yml` is the Phase 1 → Phase 2 handoff artifact.** A
  registry file at `docs/roadmap/<feature>/components.yml` captures
  the user-approved component set: slug, display name, depends_on
  chain, OWASP categories. Phase 2 reads it; Phase 3 validates
  bidirectional consistency between it and the per-component files.
- **No `component_type` enum.** Dropped during design rather than ship
  a taxonomy biased toward the test project (DAG, UI-screen). Slug
  identifies; display name labels; purpose paragraph describes. No
  speculative taxonomy.
- **Slug split from display name.** Frontmatter `component: <slug>`
  (stable ID) vs `name: <display>` (human text). Slugs auto-generated
  in Phase 1 from component names; user can override before approval.
- **Precondition check is structural only.** Verify design doc has
  `## Architecture Overview → ### Components`, `## Tooling → ###
  Security Tooling`, `## Deferred Decisions`. No regex heuristics over
  Deferred Decisions content — that's the planning skill's Phase 3
  triage responsibility, not this skill's.
- **Frontmatter `depends_on` is authoritative; `## Dependencies` prose
  carries rationale only.** Validator checks the two sets of slugs
  match — avoids the prose-vs-schema drift pattern that bit
  `test_command` upstream.
- **OWASP ID validation is format-level, not validity-level.** Regex
  for `ASVS V<n>.<n>.<n>` and `MASVS-<CATEGORY>-<n>` patterns; no check
  that the specific ID exists in the pinned OWASP version. Full
  validation waits for a real bug where a misspelled ID passed review.
- **MASVS reference ships thinner than ASVS.** ASVS mapping was
  informed by the airflow prototype; MASVS has no mobile trial yet
  and says so explicitly. Future mobile trial will inform revision.

**Validator (`scripts/validate_roadmap.py`):** pure stdlib + pyyaml,
runs via `uv run --with pyyaml`. Checks `components.yml` schema,
bidirectional consistency with `<slug>.md` files, frontmatter
completeness, scenario structure (all four Given/When/Then/Verified-by
lines with non-empty content), OWASP ID format in security scenarios,
dependency consistency (frontmatter ↔ prose ↔ registry), slug format
and uniqueness, cycle detection in depends_on graph. Exit 0 = PASS
with summary table; exit 1 = validation failure with line-numbered
error report; exit 2 = precondition failure (missing directory or
unparseable `components.yml`).

**Smoke-tested on three scenarios:** minimal valid happy path passes;
broken input (bad OWASP ID, missing Verified-by, frontmatter/registry
mismatch, prose/frontmatter dependency mismatch) fails with specific
line-numbered errors; 3-node cycle detected cleanly.

**Not yet trial-validated:** the first real roadmap skill run against
the airflow-gdrive-ingestion design doc is still ahead. Expect
iterations on the reference docs and validator based on what the first
trial surfaces.

### T10–T13 Arc (2026-04-16 through 2026-04-17)

Four runs on the same 19-task decomposition. Full detail in
`trials/T10-T13-tightening-arc.md`. Summary:

- **T10**: 5/19. Templating refactor held. Split-module test bug (parser
  across task-07/08 sharing test file) and mock path inconsistency
  (task-05) exposed test-writing as a coherence problem.
- **T11**: 6/19. Gemini upgrade fixed intra-file mock drift. New failure
  class: defensive-default tests that pass against partial stubs instead
  of raising NotImplementedError.
- **T12**: 2/19. Claude-as-test-writer experiment. Revealed `verify_task`
  rigidity — correct partial stub rejected by hardcoded single-pattern check.
- **T13**: 5/19. Tight system prompt + tight task-02 spec. **All 3 test tasks
  passed Gemini tier 0 retry 0.** ~55% prompt size reduction for task-02.
  Remaining failures were test over-specification (task-05) and fixture path
  resolution (task-07) — different failure class than prompt-structure
  issues; deferred.

**Key findings that drove the T13 refactor (landed in T14):**

1. System-prompt bloat confuses models more than per-task bloat.
2. Tight task-doc templates with fixed fields eliminate prompt contradictions.
3. Test over-specification is distinct from under-specification and
   doesn't get better with a more capable test-writer.
4. Partial-stub components need a structural fix (`expected_test_failure_modes`
   schema field), not more prose.
5. Dependency inlining should filter to files the task could actually import.
6. Duplicate rule blocks across prompt sections silently contradict — each
   rule belongs in exactly one section.

### Features List

1. `EXECUTORS` + `EXECUTOR_ROLES` config with type-based dispatch
2. Multi-executor dispatch via `agent_bridge.py`
3. Lint auto-fix as a post-executor step in `verify_task`
4. Executor escalation via `escalate_executor` node
5. Phase 1 live CLI research + test prompt verification
6. Phase 1 Step 1b: Aider model settings research for local models
7. Prompt composition with dependency inlining and test-task guidance
8. Enum serialization fix (`model_dump(mode="json")`)
9. Aider test file inclusion for implementation tasks
10. `AIDER_MODEL_EXTRA_ARGS` per-model config
11. Stub files in test tasks with `stub: true` schema field
12. `validate_stub_on_test_tasks_only` and `validate_stub_to_modify` validators
13. verify_task test-task logic: config-driven stub error pattern = pass, collection error = fail
14. Stub writing rules in test-task prompt composition
15. Prototype references removed — task descriptions are sole source of truth
16. Inline patterns and output field contracts in decomposition skill
17. Implementation pipeline no longer reads prototype directory or design doc
18. `AIDER_LINT_CMD` — auto-fix before check in Aider's `--lint-cmd`
19. `TeeWriter` stdout capture in `run.py` for run log completeness
20. `EXECUTOR_TIMEOUT` default reduced from 600s to 300s
21. Integration test Docker lifecycle in test commands (compose up/test/down)
22. Docker availability validation at startup when integration tests present
23. Scaffold task creates `services.compose.yml` for dependency services
24. Integration test task descriptions require exact function signatures
25. Orchestrator/wiring tasks must depend on scaffold if they import config/settings
26. Pipeline templates — stable files copied verbatim, config/compose_prompt/README generated
27. Integrated scaffold verification — marker file, bootstrap, tool checks in one verify_task pass
28. Config template with placeholders — prevents value drift from model memory
29. Language-agnostic templates — platform-specific patterns driven by config fields
30. Stub mock-import rule — stubs import third-party dependencies tests will mock
31. **Tight task-description template** (Component / Component type / Interface /
    Behaviors / Expected test failure mode / Out of scope) — landed T14
32. **`expected_test_failure_modes` schema field** wired into `verify_task` —
    enables correct handling of partial stubs. Landed T14.
33. **`compose_prompt.py.template`** — T13-validated tight system prompt
    with duplicate-rule removal and filtered dependency inlining baked in.
    Landed T14.
34. **JSON-only decomposition output** — no per-task `.md` files; summary
    table printed at decomposition time is the human-review artifact.
    Landed T14.
35. **Required `test_command` schema field** — every task specifies its
    own test gate command; populated verbatim into `TASK_TEST_COMMANDS`
    during Phase 2. Scaffold tasks included. Validators enforce non-empty
    and integration-lifecycle wrapping. Landed 2026-04-19 after T14.
36. **Scaffold test-infrastructure gate** — `verify_task` runs the
    scaffold's `test_command` after bootstrap/lint-tool checks. Catches
    broken `conftest.py`, wrong pytest config, missing pythonpath before
    any real test tasks run. Landed 2026-04-19 after T14.
37. **Open Questions Triage in Phase 3** — three-bucket classification
    with two diagnostics (difference test + assertion test). Feasibility
    questions never ship in the design doc. Landed 2026-04-23 through
    P01–P03.
38. **Prototype security-tooling validation in Phase 2** — dep scan
    (always), secrets scan (always), SAST (with Surface Coverage Check
    forcing multi-tool selection for prototypes carrying Dockerfile /
    compose / IaC / shell surfaces). Landed 2026-04-23 through P01.
39. **Severity-indexed security finding handling** — Critical findings
    block; all severities attempt fixes before deferral; Mitigation
    Ladder with 5 options (upgrade, override/pin/downgrade, exclude,
    replace, accept with compensating controls). Downgrade is a
    first-class option. Landed 2026-04-23 through P03.
40. **Environmental Risk Assessment rules** — contextual CVSS reasoning
    is a proposal to the user, never a unilateral decision. Reachability
    must be addressed specifically. Critical-severity assessments name
    a condition under which they would be wrong. Landed 2026-04-23
    through P03.
41. **Scope-Removal Triage in Phase 2** — three-bucket classification
    forcing model-initiated removals of approved Phase 1 items through
    user review. Mandatory STOP-report bullet. Landed 2026-04-23
    through P01.
42. **Scope Deferrals from Phase 1 section in design doc** — separates
    user-approved out-of-scope items from prototype-design-choice
    limitations. Landed 2026-04-23 through P02.
43. **Judgment vs. Observation labeling in design doc** — behavioral
    claims cite evidence or label as inference; prescriptions carry
    explicit "Prescribed (not validated)" label. Landed 2026-04-23
    through P02.
44. **`prototype-driven-roadmap` skill** — new sibling skill that
    consumes a signed-off design doc and produces one markdown file
    per component with BDD scenarios and OWASP-cited security
    scenarios. Three phases with STOPs; `components.yml` as the
    authoritative Phase 1 → Phase 2 handoff registry; Phase 3
    validator checks structural rules. Landed 2026-04-24.
45. **`components.yml` registry pattern** — persisted Phase 1 output
    that survives session interrupts, is parseable by Phase 2/3, and
    serves as the two-way consistency anchor for per-file
    validation. Model for future skills that need a Phase-to-Phase
    handoff beyond chat history.
46. **No speculative `component_type` enum** — taxonomy field dropped
    entirely during design discussion rather than ship values biased
    toward the test project. Principle: don't introduce fields that
    don't drive behavior yet. Informs future schema decisions.
47. **Slug vs display-name split** — roadmap frontmatter has
    `component: <slug>` (stable ID) separate from `name: <display>`
    (human label). Same pattern as database PK-vs-label separation;
    avoids the "is this the filename or the human name" ambiguity
    that hits when fields do double duty.
48. **Structural-only precondition checks across skill boundaries** —
    roadmap skill checks the design doc's section names but does not
    inspect section content for feasibility patterns. Duplicate
    checks across skills create ambiguity about which layer owns the
    responsibility; structural checks at the boundary + semantic
    checks inside each skill keeps ownership clear.
49. **OWASP mapping references per standard** — static data-flow-to-
    category tables pinned to specific OWASP versions (ASVS 4.0.3,
    MASVS 2.1.0). Curated short-lists of the top 3–5 requirement IDs
    per data-flow kind. MASVS explicitly marked thinner pending
    mobile-trial validation.
50. **Validator smoke-testing during build, not just pre-merge** —
    three scenarios (happy path, broken input variants, cycle
    detection) run against the validator before the skill was
    declared done. Cheap confidence-builder that catches parser
    bugs before the first real trial.

### Skill Expansion Plan — Complete

All parts of `skill-expansion-plan-2026-04-21.md` have landed:

- **Part A (Phase 3 Open Questions Triage)** — 2026-04-23, through the
  P01–P03 arc. Expanded beyond the original plan with the assertion
  test as a second triage diagnostic, the `## Scope Deferrals from
  Phase 1` design-doc section, and Judgment vs. Observation labeling.
- **Part C (Phase 2 security-tooling validation)** — 2026-04-23,
  through P01 and P03. Expanded with the Surface Coverage Check,
  severity-indexed finding handling, the 5-option Mitigation Ladder,
  and Environmental Risk Assessment rules.
- **Part B (`prototype-driven-roadmap` skill)** — 2026-04-24, single
  build pass. Expanded with `components.yml` as the handoff registry,
  dropped `component_type` enum, slug/display-name split, structural-
  only precondition check.

The plan doc is historical reference only at this point. New skill
expansions would live in new plan docs.

---

## Pipeline Run History

### Run 1 (2026-03-31) — Single-tier Aider + Qwen
27 tasks, all attempted. 20/31 invocations hit reflection exhaustion. Dominant
failure: I001/F401 lint loops.

### Run 2 (2026-04-01) — Aider + Gemini Flash (model roles, no CLI research)
18 tasks. Stalled at task-02. Empty stubs from oversized scaffold, enum
serialization bug, single-tier test role.

### Run 3 (2026-04-02) — Claude CLI as scaffold/test executor
Pipeline hung on task-01. Hardcoded `--allowedTools` was wrong.

### Run 4 (2026-04-03) — Full escalation: Aider+Qwen → Gemini → Claude
18 tasks, ~2.5 hours. Best run to that point — all implementation code
produced. Claude rate limited after ~1 hour. 3 Qwen repetition loops.

### Run 5 (2026-04-04) — Re-decomposed with task sizing
21 tasks. Stalled at task-02. verify_task rejected valid test task due to
ModuleNotFoundError from missing stub.

### Run 6 (2026-04-05) — First clean run: Aider+Qwen → Gemini → Claude
21 tasks, ~2h 19m. First clean 21/21 run. Post-run review found field name
drift, wrong signatures, prototype-over-prose copying.

### Run 7 (2026-04-07) — Re-decomposed with inline patterns
31 tasks. I001 lint loops on all Aider+Qwen tasks, Gemini 429 on escalation.
Led to AIDER_LINT_CMD, TeeWriter, 300s timeout.

### Run 8 (2026-04-09) — Auto-fix + TeeWriter + 300s timeout
22 tasks, ~6.9h. 19/22 passed. Timeout was still 600s due to config drift.

### Run 9 (2026-04-13) — Re-decomposed (17 tasks)
17 tasks, ~1h 47m. 8 passed, 4 degraded, 1 failed (task-13), 1 skipped,
3 not_run. Timeout still 600s (memory contamination). ruff not in dev deps.
Task-13 failed: stub missing pika import for test patching. Led to
pipeline templates refactor.

### Run 10 (2026-04-16) — Templated pipeline + Aider+Qwen → Gemini → Claude
19 tasks. 5/19. Templating refactor held (300s timeout stable). Split-file
test bug (task-07) and mock-path inconsistency (task-05) exposed
test-writing quality as a coherence problem.

### Run 11 (2026-04-16) — Newer Gemini
19 tasks. 6/19. Gemini upgrade fixed intra-file mock drift. Stubs-pass
failures surfaced (defensive defaults pass against partial stubs).

### Run 12 (2026-04-16) — Claude-as-test-writer
19 tasks. 2/19. Exposed verify_task rigidity around partial stubs.

### Run 13 (2026-04-17) — Tight system prompt + tight task-02 spec
19 tasks. 5/19. All 3 test tasks passed Gemini tier 0 r0. Remaining
failures: test over-specification (task-05), fixture path (task-07).
Led to refactor-plan-2026-04-17.

### Run 14 (2026-04-19) — Tight task-doc refactor applied
17 tasks. **16/17 passed.** Only task-16 (integration test) failed; root
cause: Docker-wrapped test command embedded in task description but
never copied into pipeline. Led to refactor-plan-2026-04-19: required
`test_command: str` schema field.

### Planning-skill iterations (P01–P03, 2026-04-23)

Three skill-development trials, not pipeline runs. See `trials/_SUMMARY.md`
planning-skill iterations section and individual P01/P02/P03 files for
detail. Summary: each iteration surfaced a distinct failure-mode class
(table-as-complete-spec + silent scope removal; feasibility-in-disguise +
judgment-as-fact + Phase-1 scope ambiguity; severity-blind handling +
environmental-assessment shortcut), and each landed skill fixes the same
day.

---

## Next Steps

- **P04 validation trial (planning skill).** Re-run planning on a new
  or regenerated feature to confirm the P01–P03 fixes hold together.
  Acceptance bar:
  - Surface Coverage Check produces multi-tool SAST selection without
    user prompting.
  - No silent scope removals; any removal goes through Scope-Removal
    Triage message and user confirmation.
  - Open Questions Triage classifies items using both diagnostics; no
    feasibility-in-disguise items survive in Deferred Decisions.
  - Design doc's Scope Deferrals from Phase 1 section is populated (or
    explicitly reads "None").
  - Judgment vs. Observation labels appear on any behavioral claim
    without prototype evidence.
  - If any security finding surfaces, it runs through the Mitigation
    Ladder (not blanket deferral). Critical findings block on user
    decision after full attempt log; environmental assessments (if any)
    are proposals not decisions.

- **T15 pipeline validation run.** Regenerate
  `tasks/airflow-google-drive-ingestion/tasks.json` under the new
  decomposition schema (which will now fail validation and force the
  decomposer to populate `test_command` on every task). Regenerate the
  pipeline. Run. Acceptance bar:
  - Match T14's 16/17 at minimum.
  - Task-16 passes (services started by Docker-wrapped `test_command`).
  - Task-15 and task-17 test_commands exercise the AST-parse and
    `docker build` commands from their acceptance criteria (not lint-only
    anymore).
  - Scaffold task-01's test_command runs cleanly against the empty
    scaffold (pytest exit 5, normalized to exit 0 by the
    `|| [ $? -eq 5 ]` suffix).

- **First roadmap-skill trial (R01 or equivalent).** Run the
  roadmap skill against
  `~/health-data-ai-platform/docs/design/airflow-gdrive-ingestion-2026-04-24.md`.
  Acceptance bar:
  - Precondition check passes (all required sections present; no
    `## Open Questions` section).
  - Phase 1 extracts the four components (drive-downloader,
    sqlite-parser, amqp-publisher, airflow-dag) with reasonable
    slugs and proposes a defensible OWASP category set per
    component grounded in the design doc's data flows.
  - `components.yml` is written after user approval and validates
    against the schema described in `components-yml-format.md`.
  - Phase 2 produces one `<slug>.md` per component with at least one
    functional scenario and at least one security scenario each,
    plus non-empty Purpose, Prototype evidence, Out of Scope,
    Dependencies.
  - Phase 3 validator exits 0 and prints the summary table.
  - File the trial record at `trials/R01-*.md`; update `_SUMMARY.md`
    and `_INDEX.md`; record any skill fixes in `LEARNINGS.md`'s
    "From Roadmap Skill" section.

- **Manual cleanup**: delete
  `~/claude-devtools/skills/prototype-driven-implementation/templates/nodes/bootstrap.py`
  (tombstone file from bootstrap merge; noted but not confirmed present).

---

## Test Run Results (session history)

### Planning Skill
- Session `f75b5f43-fd52-4138-87ad-c7c18589fa07` — First test run (2026-03-28)
- Session `a7c48f00-b614-4086-a640-b623a00f5a97` — Second test run (2026-03-28)
- P01 (2026-04-23) — First Part A + C trial
- P02 (2026-04-23) — Second Part A + C trial (design-doc review)
- P03 (2026-04-23) — Third Part A + C trial (security-finding handling)

### Decomposition Skill
- Session `6d471491-32b7-4f74-a720-8fdbf0060023` — First run (8 tasks)
- Session `b2354707-0024-45db-bb9a-7ff872e39271` — Second run (11 tasks)
- Session `64052f92-5393-4425-8286-1389124c6feb` — Third run (27 tasks)

### Implementation Skill — runs 1–14
See `trials/_SUMMARY.md` for the canonical scoreboard.

### Roadmap Skill
- Design pass (2026-04-24) — skill built and validator smoke-tested;
  no trial run against a real design doc yet.

---

## File Map

```
~/claude-project-memory/prototype-driven-planning-skill/
├── README.md                              # This file (read first)
├── LEARNINGS.md                           # Distilled principles (read second)
├── gemini_conversation.txt                # Raw Gemini consultation (historical)
├── refactor-plan-2026-04-17.md            # T13 refactor (landed in T14)
├── refactor-plan-2026-04-19.md            # T14 refactor (landed same day; validates in T15)
├── skill-expansion-plan-2026-04-21.md     # Expansion plan — all parts landed (A+C: 2026-04-23; B: 2026-04-24)
├── references/
│   ├── architecture-rationale.md
│   └── stack-reference.md
└── trials/
    ├── _SUMMARY.md                        # Scoreboard (read third) — includes planning-skill iterations section
    ├── _INDEX.md
    ├── T<NN>-<slug>.md                    # Pipeline trials (implementation skill)
    └── P<NN>-<slug>.md                    # Planning-skill iterations (2026-04-23 arc)

~/claude-devtools/skills/prototype-driven-planning/
├── SKILL.md                               # Updated 2026-04-23: Parts A+C and P01-P03 expansions
└── references/
    ├── design-doc-template.md             # Updated 2026-04-23: Scope Deferrals from Phase 1, Security Tooling, Deferred Decisions rename
    ├── phase-1-discovery.md
    ├── phase-2-prototype.md               # Updated 2026-04-23: Security Tooling Validation, Scope-Removal Triage, Mitigation Ladder, Environmental Risk Assessment
    └── phase-3-design-doc.md              # Updated 2026-04-23: Open Questions Triage, assertion test, Judgment vs. Observation

~/claude-devtools/skills/prototype-driven-task-decomposition/
├── SKILL.md                               # Updated 2026-04-19: test_command field
├── scripts/
│   └── task_schema.py                     # Updated 2026-04-19: test_command required + 2 validators
└── references/
    ├── analysis-guide.md
    ├── task-writing-guide.md              # Updated 2026-04-19: Task test_command section
    └── output-format.md                   # Updated 2026-04-19: test_command in examples + checklist

~/claude-devtools/skills/prototype-driven-implementation/
├── SKILL.md                               # Updated 2026-04-19: Phase 1/3 and Principles
├── templates/                             # Verbatim pipeline files (language-agnostic)
│   ├── run.py                             # Entry point with TeeWriter
│   ├── pipeline_state.py                  # LangGraph state TypedDicts
│   ├── graph.py                           # StateGraph, routing, pick/retry/escalate nodes
│   ├── agent_bridge.py                    # Executor dispatch, subprocess wrappers
│   ├── requirements.txt                   # langgraph, pydantic
│   ├── config.py.template                 # Updated 2026-04-19: TASK_TEST_COMMANDS: dict[str, str]
│   └── nodes/
│       ├── __init__.py
│       ├── load_tasks.py                  # Task loading, schema validation
│       ├── compose_prompt.py.template     # T13 tight system prompt with 3 placeholders
│       ├── execute_task.py                # Executor dispatch node
│       ├── verify_task.py                 # Updated 2026-04-19: scaffold runs test_command
│       └── report.py                      # Final summary
└── references/
    ├── phase-1-analysis.md                # Updated 2026-04-19: test_commands come from schema
    ├── phase-2-generation.md              # Updated 2026-04-19: TASK_TEST_COMMANDS verbatim
    ├── langgraph-patterns.md              # State machine design reference
    ├── executor-integration.md            # Executor dispatch and prompt composition
    └── phase-3-handoff.md                 # Updated 2026-04-19: reverse task-ID coverage check

~/claude-devtools/skills/prototype-driven-roadmap/
├── SKILL.md                               # Landed 2026-04-24: 3-phase contract + Principles
├── scripts/
│   └── validate_roadmap.py                # Landed 2026-04-24: bidirectional registry + per-file checks
└── references/
    ├── roadmap-item-template.md           # Per-file template (frontmatter + 6 sections)
    ├── components-yml-format.md           # Phase 1 → Phase 2 handoff registry schema
    ├── phase-1-extraction.md              # Component extraction + data-flow mapping rules
    ├── phase-2-generation.md              # Per-file writing rules
    ├── phase-3-validation.md              # Validator workflow
    ├── owasp-asvs-mapping.md              # ASVS 4.0.3 data-flow → category reference (worked example)
    └── owasp-masvs-mapping.md             # MASVS 2.1.0 reference (thinner; unvalidated pending mobile trial)

~/claude-devtools/commands/
├── prototype-plan.md
├── prototype-task-decompose.md
└── prototype-roadmap.md                   # Landed 2026-04-24
```
