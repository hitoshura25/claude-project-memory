# R03 — Roadmap Skill: Scenario `id` Field Validation

**Date**: 2026-05-02
**Skill**: prototype-driven-roadmap
**Target**: airflow-gdrive-ingestion (existing design doc, regenerate
`roadmap.json` against the rebuilt schema)
**Result**: ✅ Clean sweep — validates step 1 of the three-skill
decomposition refactor (`decomposition-roadmap-refactor-plan-2026-05-02.md`)

## What was tested

Step 1 of three coordinated changes per the 2026-05-02 refactor plan:
the roadmap skill gains a required, kebab-case, unique-within-component
`id` field on every functional and security scenario. The field provides
a stable handle for downstream skills (decomposition cites it;
implementation pipeline inlines from it) that won't break if a scenario
is reworded on regeneration.

Schema additions to `roadmap_schema.py`:

- `id: str` field added to both `FunctionalScenario` and `SecurityScenario`.
- Per-field validator: `^[a-z][a-z0-9-]*[a-z0-9]$` regex (matches the
  same kebab-case rule used by component slugs).
- Component-level model validator
  `scenario_ids_unique_within_component`: rejects duplicate IDs across
  the union of `functional_scenarios` and `security_scenarios` within a
  component. Cross-component duplicates are fine — `(slug, id)` is the
  global key, not `id` alone.

Reference doc updates:

- `references/roadmap-json-format.md`: `id` field added to both scenario
  field-reference tables; new "Scenario IDs" subsection covering format,
  the within-component uniqueness rule, and the regenerate-preserves-IDs
  guidance; JSON example updated; validation rules list extended.
- `references/phase-2-generation.md`: new subsection on writing scenario
  IDs (derive kebab-case from `name` for first generation; preserve
  existing IDs on regeneration unless the scenario is substantively
  restructured).

## Acceptance bar

| Criterion | Result |
|---|---|
| Updated `roadmap_schema.py` accepts `id` on both scenario kinds | ✅ |
| Format validator enforces kebab-case `^[a-z][a-z0-9-]*[a-z0-9]$` | ✅ |
| `scenario_ids_unique_within_component` validator fires on duplicates | ✅ |
| Schema smoke-tested against happy path + 6 edge cases | ✅ — all 7 cases produce expected outcomes |
| Regenerated `roadmap.json` has `id` on every scenario | ✅ — 33 scenarios across 5 components |
| All IDs match kebab-case format | ✅ |
| No duplicate IDs within any component | ✅ |
| Project-shipped `roadmap_schema.py` updated; `components_schema.py` re-shipped unchanged | ✅ |

## Structural verification

**Scenario id population per component (regenerated roadmap.json):**

| Component | Functional scenarios | Security scenarios | Total |
|---|---|---|---|
| project-setup | 3 | 3 | 6 |
| drive-downloader | 3 | 3 | 6 |
| sqlite-parser | 5 | 3 | 8 |
| minio-uploader | 4 | 3 | 7 |
| rabbitmq-publisher | 3 | 3 | 6 |
| **Total** | **18** | **15** | **33** |

**ID format check**: every id matches `^[a-z][a-z0-9-]*[a-z0-9]$`.
Spot examples:

- `selects-newest-zip-by-modified-time` (drive-downloader functional)
- `extracts-11-record-types-from-sample-db` (sqlite-parser functional)
- `idempotency-key-stable-across-retries` (minio-uploader functional)
- `mkstemp-uses-restrictive-permissions` (drive-downloader security)
- `sql-queries-use-only-hardcoded-identifiers` (sqlite-parser security)
- `routing-key-encodes-health-category-pii` (rabbitmq-publisher security)

**Within-component uniqueness**: confirmed by inspection of each
component's scenario list. No id appears more than once in any
component. Some natural cross-component overlap (e.g., `v5.0.0-12.2.1`
TLS-related scenarios appear under both drive-downloader and
minio-uploader, but with distinct ids: `drive-api-enforces-https` vs.
`minio-connection-must-use-tls`) — exactly the intended pattern.

**Cross-component check**: no scenario id is shared across two
components. This isn't required (the schema only enforces
within-component uniqueness) but the IDs ended up globally unique
anyway, because they encode component-specific behaviors.

## Schema smoke tests

Validated against 7 cases before regeneration:

1. Happy path: minimal valid scenario with `id` field — accepts.
2. Missing `id`: rejects with required-field error.
3. Empty string `id`: rejects on format regex.
4. Uppercase `id` (`Selects-Newest-Zip`): rejects on format regex.
5. Trailing hyphen (`selects-newest-zip-`): rejects on format regex.
6. Duplicate id within one component (same id in `functional_scenarios`
   and `security_scenarios` of one component): rejects on
   `scenario_ids_unique_within_component`.
7. Same id in two different components: accepts (cross-component
   duplicates are allowed by design).

All 7 cases produce the expected outcome. The schema is ready for
production use.

## Failure modes surfaced

None. The `id` field landed cleanly. The hardest design question —
whether to enforce within-component uniqueness vs. global uniqueness —
was settled before implementation: within-component, because the
component slug is already part of the citation key downstream
(`roadmap_component` + `roadmap_*_scenarios` together).

## Skill changes

All landed 2026-05-02:

- `~/claude-devtools/skills/prototype-driven-roadmap/scripts/roadmap_schema.py`
- `~/claude-devtools/skills/prototype-driven-roadmap/references/roadmap-json-format.md`
- `~/claude-devtools/skills/prototype-driven-roadmap/references/phase-2-generation.md`

Project-shipped schemas re-copied at
`~/health-data-ai-platform/docs/roadmap/airflow-gdrive-ingestion/`.

## Implications

- R03 unblocks D01 (decomposition skill regeneration against the new
  roadmap output).
- R03 also unblocks step 2 of the refactor (implementation skill's
  `compose_prompt.py.template` gains `_inline_roadmap_scenarios`),
  though that change is exercised end-to-end by T15, not in any
  standalone trial.
- Existing `tasks/airflow-google-drive-ingestion/tasks.json` (T14
  output) is now invalid against the post-refactor decomposition
  schema — D01 regenerates from scratch.
- The within-component uniqueness rule, combined with the
  `(roadmap_component, scenario_id)` pair as the citation key in
  decomposition, gives the chain a clean lookup discipline:
  decomposition cites pairs; implementation pipeline resolves pairs
  via direct dict lookup; ambiguity is mechanically impossible.

## Cross-cutting pattern note

This trial doesn't surface a new failure mode, but it cements a
pattern that's been recurring across the skill chain:

- T14: prose was a lossy transport between decomposer and pipeline →
  promote `test_command` to a schema field with a validator.
- R02-prep: prose was claiming verification ("as of <date>") that
  hadn't happened → promote spec data to a JSON file with
  `verified_at` / `verified_against` fields.
- R03: prose-paraphrased scenario content was the only handle
  decomposition had on roadmap behaviors → promote scenarios to
  citable IDs with a downstream resolution step.

The pattern holds: when downstream consumers need stable handles on
upstream content, prose paraphrase is a leaky abstraction, and a typed
identifier with a validator is the structural fix. Each application of
the pattern is small; together they form the skill chain's spine.
