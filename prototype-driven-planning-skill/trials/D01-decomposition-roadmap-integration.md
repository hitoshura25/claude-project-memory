# D01 — Decomposition Skill: Roadmap Integration

**Date**: 2026-05-04
**Skill**: prototype-driven-task-decomposition
**Target**: airflow-gdrive-ingestion (regenerate decomposition against
R03's roadmap output)
**Result**: ✅ Clean sweep — validates step 3 of the three-skill
decomposition refactor (`decomposition-roadmap-refactor-plan-2026-05-02.md`)

## What was tested

Step 3 (the bulk of the refactor) per the 2026-05-02 plan: the
decomposition skill consumes the roadmap as primary input. Component
boundaries come from `components.json`; testable behaviors come from
`roadmap.json`'s scenario IDs. The decomposer's freedom narrows to
"how many tasks per component" and "which scenarios each task is
responsible for"; it no longer infers boundaries or paraphrases
scenario content.

This is the first decomposition-skill iteration trial — D for
decomposition, paralleling R for roadmap and T for implementation
pipeline.

Schema additions to `task_schema.py`:

- Three new task fields: `roadmap_component`,
  `roadmap_functional_scenarios`, `roadmap_security_scenarios`.
- Two new top-level fields on `TaskDecomposition`:
  `components_json_path`, `roadmap_json_path`.
- One per-task field validator: `roadmap_component_slug_format`
  (kebab-case regex matching the upstream component schema).
- Three new decomposition-level model validators:
  - `validate_roadmap_component_registered` — every task's
    `roadmap_component` resolves against `components.json`.
  - `validate_roadmap_scenarios_resolve` — every cited scenario id
    resolves against the task's component's scenarios in
    `roadmap.json`, per kind (functional vs. security).
  - `validate_roadmap_scenarios_required_for_test_tasks` — test tasks
    and implementation-with-tests tasks must cite at least one
    scenario.
- Four helper functions including `_load_roadmap_schemas` (imports
  the project-shipped schemas via sys.path), `_levenshtein` and
  `_nearest_neighbor` (for "Did you mean" hints in error messages),
  and `_build_unresolved_citation_error` (distinguishes wrong-field,
  wrong-component, and typo cases in error messages).

Reference doc rewrites end-to-end:

- `references/analysis-guide.md` — rewritten with roadmap as primary
  input; design doc demoted to supplementary for cross-cutting
  concerns; component boundaries read from registry, not inferred.
- `references/task-writing-guide.md` — gained "Roadmap-Driven Task
  Authoring" section; `Behaviors to test:` removed from the task
  description template; example TDD pair updated with citation
  fields; security-considerations rewritten to reflect the
  citation-first pattern.
- `references/output-format.md` — JSON example updated; validation
  rules 13–16 added; summary table reshaped (added Component +
  Scenarios columns, dropped Files column); "Integration with the
  Roadmap" subsection added.
- `SKILL.md` — Quick Reference, How to Start, Phase 1 (renamed to
  "Roadmap and Design Doc Analysis"), Phase 2 step renumbering with
  new "Cite roadmap scenarios" step, Phase 3 step 4 description,
  schema reference table (new fields + new top-level fields),
  Principles (added "Component boundaries come from the roadmap",
  "Scenario content lives in the roadmap", "The roadmap is read-only
  from here").

## Acceptance bar

| Criterion | Result |
|---|---|
| Schema smoke-tested against 8 cases (5 plan-mandated + 3 edge cases) | ✅ — all pass |
| Decomposition loads `components.json` and `roadmap.json` via project-shipped schemas | ✅ |
| Phase 1 proposal shows components verbatim from registry | ✅ — five components, no boundary inference |
| Generated `tasks.json` validates against the new schema | ✅ |
| Every task has `roadmap_component` set to a registered slug | ✅ — 13/13 tasks |
| Every test task and every implementation-with-tests task cites at least one scenario | ✅ |
| Every cited scenario id resolves against `roadmap.json` per kind | ✅ — 60/60 citations resolve |
| Summary table renders with new Component and Scenarios columns | ✅ |
| Task descriptions follow the updated template (no `Behaviors to test:` section) | ✅ — 13/13 tasks |
| Stub-import discipline preserved on every test task | ✅ |
| TDD pairing structure intact (impl tasks depend on test tasks; stubbed paths use `modify`) | ✅ |
| `test_command` rules from T14 still satisfied | ✅ — including integration test (task-13) wraps services lifecycle |

## Structural verification

**Decomposition shape**: 13 tasks across 5 components, mapping cleanly
to the roadmap's component graph.

| Component | Tasks | Test/Impl pairs | Notes |
|---|---|---|---|
| project-setup | 01, 02, 12 | None (orchestration only) | scaffold + infra + DAG wiring |
| drive-downloader | 03, 04 | 03(t) → 04(i) | clean TDD pair |
| sqlite-parser | 05, 06, 07 | 05(t) → 06(i), 05(t) → 07(i) | impl split (350 lines exceeds sizing limit) |
| minio-uploader | 08, 09, 13 | 08(t) → 09(i); 13 is integration test (no impl pair — exercises 09) | |
| rabbitmq-publisher | 10, 11 | 10(t) → 11(i) | clean TDD pair |

**Component slug resolution against components.json**: all 13 task
`roadmap_component` values match a registered slug. No drift, no
typos.

**Scenario id resolution against roadmap.json**: cross-checked all 60
citations (36 functional + 24 security) against per-component scenario
ID sets:

- Every cited functional id resolves to a scenario in the task's
  component's `functional_scenarios`.
- Every cited security id resolves to a scenario in the same
  component's `security_scenarios`.
- No cross-component citations.
- No typos.

**Test-task scenario coverage**: every test task and every
implementation-with-tests task cites ≥1 scenario:

| Task | Type | Func scenarios | Sec scenarios |
|---|---|---|---|
| 03 | test (drive-downloader) | 3 | 3 |
| 04 | impl-with-tests (drive-downloader) | 3 | 3 |
| 05 | test (sqlite-parser) | 5 | 3 |
| 06 | impl-with-tests (sqlite-parser, scalar) | 3 | 3 |
| 07 | impl-with-tests (sqlite-parser, series) | 3 | 0 |
| 08 | test (minio-uploader) | 4 | 3 |
| 09 | impl-with-tests (minio-uploader) | 4 | 3 |
| 10 | test (rabbitmq-publisher) | 3 | 3 |
| 11 | impl-with-tests (rabbitmq-publisher) | 3 | 3 |
| 13 | test (minio-uploader integration) | 2 | 0 |

Tasks 01, 02, 12 cite no scenarios — correct, scaffold/infra/wiring
tasks have no behavioral spec.

**`Behaviors to test:` removal**: confirmed absent from all 13 task
descriptions. The citation fields are now the contract; the pipeline
inlines structured Gherkin (Given/When/Then + verifier + OWASP id for
security) at prompt-compose time via the implementation skill's
`_inline_roadmap_scenarios` helper.

**Stub-import discipline preserved**: spot-checked all four test
tasks. Every stub explicitly states the module-level imports tests
mock at the boundary:

- task-03: imports `GoogleDriveHook`, `MediaIoBaseDownload`,
  `tempfile` ✓
- task-05: imports `sqlite3` ✓
- task-08: imports `Minio` ✓
- task-10: imports `pika` ✓

**TDD pairing structure intact**: all impl tasks with paired tests
depend on their test task; stubbed paths use `modify` not `create`
(e.g., task-04 modifies `drive_downloader.py` which task-03 stubbed).
Cross-task imports are declared in `depends_on` (task-12 depends on
04/07/09/11; task-09 depends on 06+07 because its stub serializes
parser output).

**`test_command` field**: every task has a non-empty command.
Integration test (task-13) wraps the service lifecycle with `docker
compose up --wait` / `... down -v --remove-orphans`, satisfying the
T14 integration-lifecycle validator. Scaffold (task-01) uses the
exit-5-tolerant pattern from T14.

## Notes worth flagging (not blockers)

**task-07 has empty `roadmap_security_scenarios` while task-06 cites
all three.** Both modify the same file (`sqlite_parser.py`). The split
is honest — task-07 only adds the two series extractors and doesn't
touch the SQL injection / magic-bytes / DatabaseError paths covered by
the security scenarios. If task-07's scope ever grows to touch
security-relevant code, the citation set will need to grow with it.
Current state is correct.

**task-12 (DAG wiring) cites no scenarios under `project-setup`.**
The DAG is genuinely orchestration-only — no scenarios in the roadmap
describe wiring behavior, only what each plugin does. The schema
allows impl-tasks-without-tests to skip citations. The verify gate is
the AST parse in `test_command`. Defensible.

## Failure modes surfaced

None. D01 is a clean sweep. The schema validators caught zero errors
on the regenerated decomposition; no new failure modes appeared during
the run; existing T14 invariants (`test_command` non-empty,
integration-lifecycle wrapping, stub on test tasks only,
implementation-depends-on-test, stub-to-modify) all hold under the
extended schema.

## Skill changes

All landed 2026-05-03 (skill side); D01 regeneration completed
2026-05-04. Ready for commit:

- `~/claude-devtools/skills/prototype-driven-task-decomposition/scripts/task_schema.py`
- `~/claude-devtools/skills/prototype-driven-task-decomposition/references/analysis-guide.md`
- `~/claude-devtools/skills/prototype-driven-task-decomposition/references/task-writing-guide.md`
- `~/claude-devtools/skills/prototype-driven-task-decomposition/references/output-format.md`
- `~/claude-devtools/skills/prototype-driven-task-decomposition/SKILL.md`

Project-shipped artifacts updated:

- `~/health-data-ai-platform/tasks/airflow-gdrive-ingestion/task_schema.py`
- `~/health-data-ai-platform/tasks/airflow-gdrive-ingestion/tasks.json`

The previous task directory at
`~/health-data-ai-platform/tasks/airflow-google-drive-ingestion/`
(T14 output) is now obsolete and can be deleted manually.

## Implications

- D01 unblocks T15 — the implementation pipeline can now be regenerated
  against the new tasks.json. Phase 2 of the implementation skill
  copies `roadmap_json_path` verbatim from tasks.json into
  `config.ROADMAP_JSON_PATH`; `compose_prompt._inline_roadmap_scenarios`
  resolves citations against roadmap.json at prompt-compose time.
- The full chain promised by the 2026-05-02 plan is now wired
  end-to-end. No further skill changes needed before T15.
- T14's `test_command` schema field continues to do exactly what it
  was designed for — the integration test (task-13) carries its
  Docker-wrapped command verbatim through to the pipeline.
- The "least non-determinism, least drift" principle held: feature-as-
  a-whole decomposition produced 13 tasks for 5 components without
  scaling problems. Per-component decomposition (the open question
  from §13 of the refactor plan) stays out of scope; `roadmap_component`
  remains metadata for now.

## Cross-cutting pattern note

D01 closes the loop on the pattern R03 cemented:

- Roadmap skill: every scenario gets a stable id (R03).
- Decomposition skill: every task cites scenario ids against its
  component (D01).
- Implementation skill: prompt composer resolves citations and
  inlines structured content (already landed; T15 validates).

Three small structural changes — one schema field per skill — replaced
the entire prose-paraphrase transport layer between roadmap and
implementing model. No information lost, no drift surface introduced,
each side independently testable. The pattern from T14 holds across
the chain: when downstream needs a stable handle on upstream content,
the structural fix is a typed identifier with a validator, not better
prose.

D01 also incidentally validates the project-shipped-schema architecture
introduced by the roadmap skill at the same time as the OWASP spec
migration: `_load_roadmap_schemas` adds the project's roadmap directory
to `sys.path` and imports `components_schema.py` and `roadmap_schema.py`
from there. No cross-skill source imports; no embedded copies. The
boundary between skills is the project artifact, exactly as
implementation-pipeline already does for `task_schema.py`. The pattern
generalizes cleanly to future skill chains.
