# R01 — First Roadmap-Skill Trial; ID-Set Drift Class and Cross-Component Misplacement Surfaced

> **Date:** 2026-04-26
> **Skill:** prototype-driven-roadmap (first trial against a real design doc)
> **Target:** health-data-ai-platform (`docs/design/airflow-gdrive-ingestion-2026-04-24.md`)
> **Outcome:** Roadmap directory generated cleanly under existing rules. Two failure-mode classes surfaced in review and fixed same-day before R02. Skill changes landed in `validate_roadmap.py`, `roadmap-item-template.md`, `components-yml-format.md`, `phase-1-extraction.md`, `phase-2-generation.md`, `SKILL.md`.

## Context

This was the first real trial of the `prototype-driven-roadmap` skill after
the design pass on 2026-04-24. The skill was invoked against the signed-off
design doc for the Airflow Google Drive ingestion feature. The run produced
five files in `docs/roadmap/airflow-gdrive-ingestion/`: `components.yml` plus
one roadmap markdown file per component (`drive-downloader.md`,
`sqlite-parser.md`, `amqp-publisher.md`, `airflow-dag.md`).

## Observations during the run

### Observation 1 — Output passed all existing structural validator rules

Every existing rule held:
- `components.yml` parsed; all top-level fields present; `design_doc_path`
  and `prototype_path` resolved; the four components matched the design
  doc's Architecture Overview exactly.
- All four roadmap files had complete frontmatter, all six required
  sections, valid Gherkin (Given/When/Then/Verified-by) on every scenario,
  format-valid OWASP IDs in every security scenario heading, frontmatter
  `depends_on` matching prose `## Dependencies` bullets, no orphan files,
  no missing components.
- Slug derivations were stable and reasonable. The dependency graph was
  acyclic and matched the pipeline shape.
- Judgment-vs-observation discipline propagated correctly from the planning
  skill: scenarios verified by future tests carry "implementation-phase
  check" or "Prescribed (not validated)" markers; scenarios verified by
  prototype tests cite specific files and line ranges.

### Observation 2 — A misclaimed "ID inconsistency" finding in initial review (self-correction)

The first review of this output claimed "cross-file ASVS ID inconsistency"
between `components.yml` and the per-file scenarios. On closer comparison
this was not true — all four files had their `components.yml`
`owasp_categories` lists matching the IDs cited in the file's security
scenario headings exactly. The reviewer (this assistant) had conflated two
distinct concerns and labeled one as the bug it wasn't.

The actual concern, when separated cleanly, was about *category placement
at component boundaries* (Observation 3), not ID drift between files. The
self-correction is preserved here because the original mis-statement led
directly to closing the structural ID-drift gap (Observation 4), which is
a real and useful fix even though the specific drift didn't happen this
time.

### Observation 3 — Cross-component category misplacement (parser V8.1.1)

The parser's `## Security Scenarios` includes an ASVS V8.1.1 (Data
Protection) scenario about temp-directory permissions for the extracted
SQLite database file. The scenario's Given/When clauses describe the
extraction step:

```
**Given** the parse_and_publish task calling tempfile.mkdtemp(prefix="hc_db_")
and extracting health_connect_export.db into it
**When** zipfile.ZipFile.extract(SQLITE_FILENAME, extract_dir) writes the file
```

But this work happens in the orchestrator (`parse_and_publish` task in the
DAG), not in the parser module. The parser's source code in
`src/parsers/sqlite_parser.py` receives a `db_path` and queries it; it
doesn't choose where the DB lives or what permissions the temp dir has.

The category is correctly chosen for a real concern (PII at rest in temp
files). It's misplaced onto the file of a component that *consumes* the
result rather than the file of the component that *creates* the
condition.

### Observation 4 — Validator gap on registry-vs-scenario ID parity

While reviewing the output, it became clear that even though IDs matched
across `components.yml` and the per-file scenarios in this run, the
validator never actually checked this. A drift between
`registry: [V9.2.1]` and `scenarios: [V9.2.2]` would have passed because
both are valid ASVS format. The format check (existing) and the parity
check (missing) are different rules; the validator only had the first.

This is the structural cousin of Observation 3 — a fragility where a real
bug class is mechanically preventable but not currently prevented.

## Root cause analysis

**Observation 3** is a Phase 1 reasoning fragility. Phase 1 picked the
right OWASP category for a real concern, but answered the question "which
component does this category belong on?" by attaching it to the component
the concern is *about* (the parser, which reads the temp file) rather than
the component whose code *creates* the condition (the orchestrator, which
makes the temp dir). No structural validator can catch this — the
scenario reads as syntactically valid and the category is real. The
underlying pattern is the same as the planning-skill iterations P01–P03:
an LLM can do reasoning it has to make visible; it cannot reliably do
reasoning it can internalize and shortcut.

**Observation 4** is a structural fragility that's mechanically
preventable. The validator already checks bidirectional consistency for
`depends_on` (frontmatter ↔ prose ↔ registry). The same pattern wasn't
applied to OWASP IDs because design-time review didn't surface the
specific drift mode. R01 surfaced it (even though the bug didn't happen
in this run), so the same machinery can be extended one more axis.

## Fixes applied (skill-level, same day)

### A. Validator: ID-set parity check

`scripts/validate_roadmap.py` extended with check 17: for each roadmap
file, the set of OWASP IDs cited in `## Security Scenarios` headings must
equal the `owasp_categories` set in the matching `components.yml` entry.
IDs in the registry but not cited in any scenario, or IDs cited in
scenarios but not in the registry, are validator errors. Hard exit 1 on
mismatch.

Documented in `components-yml-format.md` (new rule 17), `SKILL.md`
(extended principle on OWASP IDs), and `roadmap-item-template.md`
(security scenario heading subsection + new anti-pattern entry).

### B3. Validator: required `**Performed by**` field on every security scenario

Every security scenario must include `**Performed by** <component-slug>`.
The validator checks:
- The field is present and non-empty (else: missing-field error).
- The slug matches the file's own `component` slug (else: misplacement
  error).
- The slug is registered in `components.yml` (else: unregistered-slug
  error).

All three are hard exit 1.

The `Performed by` field exists to force the placement decision into a
visible artifact at scenario-write time. A reviewer scanning the file
later can see immediately whether the action belongs to the file's
component; the validator confirms. If the action belongs to a different
component, the scenario belongs in that component's file.

Functional scenarios are unaffected — they still need only
Given/When/Then/Verified-by. The new key is security-only.

Documented in `roadmap-item-template.md` (new "Performed by" subsection
in Field reference, updated scenario-structure rule, updated security
scenario template block, new anti-pattern), `phase-2-generation.md`
(new bullet at top of "What makes a good security scenario," updated
example), `phase-1-extraction.md` (new "Naming the actor for each
category" subsection + updated proposal-message template), `SKILL.md`
(new Principle).

### Validator smoke-tests

The validator was tested against four synthetic cases:
1. Happy path with correct Performed-by → exit 0, summary table prints.
2. ID drift between registry and scenarios → exit 1 with both
   missing-from-scenarios and extra-from-scenarios errors.
3. Missing Performed-by line → exit 1 with missing-field error.
4. Unregistered-slug Performed-by → exit 1 with both file-mismatch and
   registry-mismatch errors.

All four passed expectations.

## Cross-cutting pattern note

The two findings share the planning-skill arc's recurring shape: each is a
case where reasoning the model *could* do correctly is not currently
*forced visible*. A1 (validator parity check) makes the registry-vs-
scenario reasoning visible to the validator. B3 (Performed-by field) makes
the actor reasoning visible to the validator and to a reviewer. In both
cases the fix is to require the model to commit to an answer in a
machine-checkable place rather than leaving the answer implicit in prose.

This is the same pattern the planning skill's P01–P03 iterations
established and that LEARNINGS.md already records.

## Action: R01 output discarded

Per user direction, the existing `docs/roadmap/airflow-gdrive-ingestion/`
directory is not patched. It will be removed by the user (`rm -rf`) and
the skill re-run as R02 against the same design doc to validate the new
structural rules end-to-end.

R01 stands as the trial that surfaced the gaps; R02 will validate the
fixes hold.

## Open items for R02

- Confirm the new validator checks (parity + Performed-by) all fire as
  hard errors when violated.
- Confirm the parser's V8.1.1 scenario ends up on `airflow-dag` (or
  wherever the model determines the actor is) rather than on
  `sqlite-parser`. This is the specific instance of the misplacement
  class that surfaced in R01.
- Confirm Phase 1's actor-naming step appears in the proposal message
  and the user has the chance to move categories before approving
  `components.yml`.
- Run validator against the regenerated output and confirm exit 0.
