# Phase 3: Validation

Detailed guidance for the third phase of the roadmap skill. Read this
before running Phase 3, alongside `scripts/validate_roadmap.py` (the
validator itself).

The goal of Phase 3 is to confirm the roadmap output is structurally
sound and internally consistent, then present a summary for user
sign-off. Structural rules are machine-checked by the validator;
content quality is eyeballed by the user.

---

## Running the validator

```bash
uv run --with pydantic python \
  ~/claude-devtools/skills/prototype-driven-roadmap/scripts/validate_roadmap.py \
  docs/roadmap/<feature>/
```

The validator takes one positional argument: the roadmap directory.
The path may be absolute or relative-to-cwd per standard shell
convention; the validator derives the project root from the roadmap
directory's location (the layout convention is
`<project>/docs/roadmap/<feature>/`).

The validator:

1. Loads `components.json` and `roadmap.json` from the roadmap
   directory.
2. Loads `components_schema.py` and `roadmap_schema.py` from the same
   directory (the project's shipped copies).
3. Runs per-file schema validation (per-field rules, per-component
   invariants).
4. Runs cross-file invariants that span both JSON files.
5. Writes a human-readable report to stdout and exits 0 on success,
   non-zero on any failure.

### Exit codes

- `0` — all checks passed.
- `1` — one or more checks failed; details in the stdout report.
- `2` — the directory doesn't exist, a required file is missing, or
  a schema file failed to import (this is a precondition failure, not
  a validation failure; fix the input before re-running).

### What the validator checks

The full check list is in `references/components-json-format.md` and
`references/roadmap-json-format.md`. Summarized:

**Per-file schema validation (Pydantic):**

- Both files parse as valid JSON matching their respective schemas.
- `schema_version` is `<n>.<n>` and in the `1.x` range.
- All required fields present; non-empty strings where required;
  enum values within the allowed set.
- Slug format kebab-case; uniqueness within each file.
- `depends_on` resolves to registered slugs; no self-references; no
  cycles; topological array order in `components.json`.
- OWASP id format `ASVS V<n>.<n>.<n>` or `MASVS-<CAT>-<n>`.
- Every component has at least one `prototype_evidence` entry.
- Every scenario has all Gherkin fields, all non-empty, with non-
  placeholder `verified_by`.
- Every security scenario's `performed_by` matches the enclosing
  component's slug (R01 fix made structural).
- Out-of-scope and dependencies completeness: either non-empty array
  or explicit reason; mutually exclusive.

**Cross-file invariants (validator script):**

- `feature` matches between files.
- Component slug set matches between files.
- Component array order matches between files.
- `depends_on` parity (registry array ↔ roadmap rationales).
- OWASP id parity (registry `owasp_categories` ↔ roadmap scenario
  `owasp_id` set).
- Every security scenario's `performed_by` is a registered slug.
- Every `out_of_scope.owner` (when set) is a registered slug.
- `design_doc_path` and `prototype_path` resolve under the project
  root.

---

## Acting on validator output

### Exit 0

Proceed to the summary step.

### Exit 1 (validation failures)

The validator prints a numbered error report. Each error cites:
- The file and (where applicable) the component slug, scenario name,
  or field path.
- The specific rule that failed.
- What was found vs. what was expected.

Errors accumulate — the validator runs all per-file and cross-file
checks before reporting, so a roadmap with three issues surfaces all
three on one run rather than one at a time.

Fix the specific files called out. Do not:

- **Modify the schemas to pass.** The structural rules are intentional;
  bypassing them defeats the purpose. The schemas were earned over
  multiple trials (R01–R04); each rule encodes a real failure mode.
- **Regenerate the whole roadmap to fix one component.** Validator
  reports are scoped to specific components; fixes should be too.
- **Suppress errors you don't understand.** Ask the user if an error
  is unclear rather than guessing.

Re-run the validator after fixes. Iterate until exit 0.

### Exit 2 (precondition failure)

`components.json`, `roadmap.json`, `components_schema.py`, or
`roadmap_schema.py` is missing; or a schema file failed to import; or
the directory doesn't exist.

Common causes:
- Phase 1 didn't complete and `components.json` was never written.
- Phase 2 didn't complete and `roadmap.json` was never written.
- The schema files weren't copied into the roadmap directory at
  Phase 1 / Phase 2. Copy them from this skill's `scripts/` directory
  and re-run.

This is not a validation failure; it's a precondition. Loop back to
the appropriate phase rather than trying to patch the registry by
hand.

---

## The summary table

After a clean validator run, the validator prints a markdown-style
summary table:

```
Roadmap Validation: airflow-gdrive-ingestion — PASS

| Component | Functional | Security | OWASP categories |
|-----------|-----------:|---------:|------------------|
| project-setup | 1 | 2 | ASVS V2.10.4, ASVS V14.2.1 |
| drive-downloader | 1 | 3 | ASVS V2.10.4, ASVS V9.2.1, ASVS V12.4.2 |
| sqlite-parser | 5 | 3 | ASVS V5.1.3, V5.1.4, V8.3.4 |

Output directory: /path/to/project/docs/roadmap/airflow-gdrive-ingestion
```

The table shows:

- **Component** — the slug.
- **Functional** — count of `functional_scenarios` entries for the
  component.
- **Security** — count of `security_scenarios` entries for the
  component.
- **OWASP categories** — the OWASP IDs from `components.json`'s
  `owasp_categories` for the component, comma-separated.

The counts let the user eyeball whether any component is under- or
over-specified. A component with 0 security scenarios when its
`owasp_categories` is non-empty would have triggered a cross-file ID
parity error before reaching this table — but the counts let the user
notice patterns the validator can't (one component overwhelmingly
larger than the others, for instance).

---

## User review and iteration

After the summary, wait for user feedback. Possible outcomes:

- **User approves.** Roadmap is complete. Mention that
  `docs/roadmap/<feature>/` is now a stable artifact — edits come
  from design-doc revisions, not ad-hoc changes.
- **User wants to edit specific component content** (e.g., refine a
  scenario, fix a `verified_by`, adjust `out_of_scope`). Make the
  edit in `roadmap.json`, re-run the validator, re-present the
  summary. Do not regenerate components the user didn't ask to change.
- **User wants to add, remove, or rename a component.** Loop back to
  Phase 1. The registry (`components.json`) is the upstream source; a
  component change should update the registry first and then flow
  forward to `roadmap.json`. Don't edit `roadmap.json` without
  updating the registry.
- **User wants to change OWASP category coverage for an existing
  component.** This is a Phase 1 concern (category approval). Loop
  back: update `components.json`'s `owasp_categories` for the
  component, regenerate that component's content in Phase 2,
  re-validate.

---

## What to do when the validator and the user disagree

If the validator passes but the user flags a content problem (a
scenario that's wrong, a missing concern), treat the user's feedback
as authoritative and fix the file. The validator checks structure, not
correctness. The user's eyeballs are the second line of defense for
content quality.

If the validator fails but the user wants to ship anyway, refuse. The
structural rules exist because structural drift has caused real bugs
upstream (see the `test_command` lineage in the decomposition skill,
and the R01 actor-misplacement finding). Explain the specific rule
and why it exists; offer to fix the problem rather than bypass the
check.

---

## Common mistakes to avoid

- **Running the validator before Phase 2 is complete.** If
  `roadmap.json` doesn't exist yet, the validator exits 2 with a
  precondition error. That's correct behavior, but it wastes a
  cycle — finish Phase 2 first.
- **Running the validator without the schema files in the roadmap
  directory.** The validator imports schemas from the project's
  shipped copies, not from this skill's `scripts/`. Phase 1 and
  Phase 2 should have copied the schemas in; if they're missing,
  copy them and re-run.
- **Ignoring the summary table.** The counts are a sanity check. A
  component with 12 functional scenarios probably has scope that
  should have been split at the design-doc level.
- **Treating cross-file errors as one-off bugs.** Cross-file errors
  (slug-set mismatch, OWASP id parity, depends_on parity) usually
  point at a Phase 1/Phase 2 mismatch. If the registry says one
  thing and the content says another, one of them is wrong; figure
  out which before patching either.
- **Skipping the STOP.** Phase 3 ends with user sign-off, not with
  the validator exiting 0. Wait for explicit approval before moving
  on or announcing completion.
