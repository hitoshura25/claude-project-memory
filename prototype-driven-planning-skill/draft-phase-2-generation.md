# Phase 2: Generation

Detailed guidance for the second phase of the roadmap skill. Read this
before running Phase 2, alongside `roadmap-json-format.md` for the
file shape.

The goal of Phase 2 is to produce `roadmap.json` — one JSON object
covering every component registered in `components.json`, filled with
prototype-grounded functional scenarios and data-flow-scoped security
scenarios.

---

## Reading `components.json`

Phase 2's primary input is `docs/roadmap/<feature>/components.json`,
not the design doc. The registry captures the user's amendments from
Phase 1; re-deriving components from the design doc would lose those
amendments.

Parse the JSON. For each entry in `components`, you have:

- `slug` — the component identifier
- `name` — the display name
- `depends_on` — the structural dependency slugs (array order conveys
  topological ordering)
- `owasp_categories` — the approved OWASP requirement IDs

You still need the design doc and the prototype to fill each
component's content (purpose paragraph, prototype evidence, scenario
derivation). Read those alongside the registry.

The schema file `components_schema.py` is also in the roadmap
directory; you don't need to read it as content, but its presence is
required for validation.

---

## Handling prior-run artifacts

If `docs/roadmap/<feature>/roadmap.json` already exists from a previous
Phase 2 run, ask the user before overwriting:

- **Overwrite** — regenerate `roadmap.json` from scratch. Loses any
  hand-edits. Use when the user wants a clean regeneration.
- **Merge** — load the existing `roadmap.json`, regenerate only the
  components in `components.json` whose slug isn't already in the
  loaded `roadmap.json`'s `components` array, and write back the
  combined result. Preserves existing entries. Use when the user has
  amended `components.json` (added a component) and wants to generate
  only the new one.
- **Abort** — stop. Use when the user didn't expect prior artifacts and
  wants to investigate.

`components.json` itself is never overwritten by Phase 2; it's
Phase 1's output. `components_schema.py` and `roadmap_schema.py` are
also not modified by Phase 2 — they're either already present (from
Phase 1 / a prior Phase 2) or copied in from this skill's `scripts/`
directory at the start of Phase 2.

---

## Schema files in the roadmap directory

Before generating content, ensure both schema files are in the
roadmap directory:

- `components_schema.py` — copied from this skill's `scripts/` during
  Phase 1; should already be present.
- `roadmap_schema.py` — copied from this skill's `scripts/` at the
  start of Phase 2.

Both are project artifacts: downstream skills import from these
copies, and the validator at Phase 3 imports from these copies.
Source-of-truth lives in this skill's `scripts/`; project copies are
pinned snapshots. If either file is missing, copy it before
generating content.

---

## Generating `roadmap.json`

The output is a single JSON file: `docs/roadmap/<feature>/roadmap.json`.
It contains a top-level object with `schema_version`, `feature`, and
`components` (an array, one entry per registered slug, in the same
order as `components.json`).

For each component, generate a content entry per the structure in
`references/roadmap-json-format.md`. The format doc specifies the
schema; this section covers the content choices within each field.

### Top-level fields

```json
{
  "schema_version": "1.0",
  "feature": "<from components.json>",
  "components": [...]
}
```

Copy `feature` verbatim from `components.json`. Use
`schema_version: "1.0"` (current version).

### Per-component entry skeleton

```json
{
  "slug": "<from components.json>",
  "purpose": "<paragraph>",
  "prototype_evidence": [...],
  "functional_scenarios": [...],
  "security_scenarios": [...],
  "out_of_scope": [...],
  "out_of_scope_reason": null,
  "dependencies": [...],
  "dependencies_reason": null
}
```

Copy `slug` verbatim from `components.json`. Generate the rest per
the rules below.

### Purpose paragraph

One paragraph as a single string. Derive from the design doc's
`**Responsibility**` bullet for this component, extended if the
prototype evidence or production considerations add non-obvious scope
or boundary information.

Don't copy the design doc's responsibility bullet verbatim — paraphrase
so the entry reads as a self-contained description. Do cross-reference
the design doc's Architecture Overview implicitly by keeping the
vocabulary consistent (if the design doc calls it a "publisher," don't
switch to "emitter" here).

Empty / whitespace-only `purpose` is rejected by the schema.

### Prototype evidence

Array of `{path, note, lines?}` objects.

- Cite concrete paths relative to the prototype root (or the project
  root, depending on your project's convention — be consistent across
  the roadmap).
- One-line `note` per entry, describing what the file demonstrates
  *for this component*.
- Use `lines` (string like `"23-31"`) when the file is long and only
  a subset is relevant. Omit (or set to `null`) otherwise.

Example:

```json
"prototype_evidence": [
  {
    "path": "prototypes/airflow-gdrive-ingestion/dags/health_connect_ingestion.py",
    "note": "main DAG with download_zip task using sort by modifiedTime",
    "lines": "70-78"
  },
  {
    "path": "prototypes/airflow-gdrive-ingestion/Dockerfile",
    "note": "airflow user, pip install in user site-packages"
  }
]
```

Every component must have at least one prototype-evidence entry.
The schema rejects empty arrays. If a component has zero prototype
evidence, something went wrong upstream — the design doc named a
component the prototype didn't validate, which should have triggered
a Phase 2 loopback in planning. Stop and surface this rather than
writing a component entry without evidence.

### Functional scenarios

Array of Gherkin-shaped scenarios. The scenario set for a component
describes its externally observable behaviors.

```json
{
  "name": "<short scenario name>",
  "given": "<precondition in the component's domain>",
  "when": "<the triggering action or input>",
  "then": "<the observable outcome>",
  "verified_by": "<test path | tool invocation | named manual check>",
  "evidence_kind": "prototype" | "prescribed"
}
```

**What makes a good functional scenario:**

- **Derived from prototype evidence.** The prototype demonstrated this
  behavior; the scenario describes it. The `verified_by` clause names
  the test or artifact, and `evidence_kind` is `"prototype"`.
- **Or derived from design-doc prescription.** The design doc says
  production should do X; the scenario describes X. The `verified_by`
  clause names an implementation-phase check, and `evidence_kind` is
  `"prescribed"` (because the prototype didn't validate it).
- **One observable behavior per scenario.** A scenario that tries to
  describe "downloads, parses, and publishes" in one block is three
  scenarios.
- **Concrete preconditions.** "Given a file exists" is weaker than
  "Given a 500-record SQLite export at `/tmp/health-connect.db`." The
  concrete form is closer to what a test actually sets up.

**Count guidance:** most components will have 2–5 functional scenarios.
A component with 10+ scenarios is probably doing too much and should
have been decomposed further in the design doc. A component with 0
scenarios is one whose behavior isn't exercised — either drop it from
the registry, or reconsider its content scope.

**Example (data pipeline — parser component):**

```json
{
  "name": "Parses blood glucose records with unit conversion",
  "given": "a SQLite database with blood_glucose_record_table entries in mmol/L (observed at prototypes/<feature>/fixtures/sample.db)",
  "when": "parse_blood_glucose(db, limit=500) is called",
  "then": "each returned record has level_mg_dl computed as level_mmol_l * 18.01559",
  "verified_by": "prototypes/<feature>/tests/test_sqlite_parser.py::test_blood_glucose_unit_conversion",
  "evidence_kind": "prototype"
}
```

**Example (web service — auth component, prescribed behavior):**

```json
{
  "name": "Rejects requests with expired tokens",
  "given": "an incoming HTTP request with a JWT whose exp claim is in the past",
  "when": "the auth middleware processes the request",
  "then": "the response is HTTP 401 with {\"error\": \"token_expired\"}",
  "verified_by": "integration test (not in prototype scope — see design doc § Token validation)",
  "evidence_kind": "prescribed"
}
```

`verified_by` placeholders ("TBD", "<unknown>", "N/A", "TODO", or
empty) are rejected by the schema. A scenario without a real verifier
is a principle or aspiration, not a scenario. Surface it to the user
rather than committing it.

### Security scenarios

One scenario per OWASP category in `components.json`'s
`owasp_categories` array for this component. Each scenario carries:

```json
{
  "name": "<short scenario name>",
  "owasp_id": "ASVS V5.1.3",
  "owasp_category_label": "Input Validation",
  "performed_by": "<this component's slug>",
  "given": "<threat precondition: an input reaches this component>",
  "when": "<the adversarial or edge-case action>",
  "then": "<the component's defensive response>",
  "verified_by": "<test | tool | review artifact>",
  "evidence_kind": "prototype" | "prescribed"
}
```

**`owasp_id`** — the requirement identifier. Format-checked by the
schema:
- `ASVS V<major>.<minor>.<patch>` (e.g., `ASVS V5.1.3`)
- `MASVS-<CATEGORY>-<num>` (e.g., `MASVS-STORAGE-1`)

**`owasp_category_label`** — human-readable category name (e.g.,
`"Input Validation"`, `"Server Communications"`, `"Data Storage"`).
Should match the category name in `owasp-asvs-mapping.md` or
`owasp-masvs-mapping.md` for consistency. Schema only checks
non-empty.

**`performed_by`** — the slug of the component whose code performs
the action. **Must equal the enclosing component's own slug.** The
schema rejects mismatch; a scenario where the action lives elsewhere
belongs in that other component's entry.

**What makes a good security scenario:**

- **Performed-by-grounded.** The slug equals the enclosing component's
  slug. The scenario describes an action this component's code
  performs. If the action lives in another component, the scenario
  belongs in that component's entry. The schema enforces this; Phase 1
  should have prevented misplacement, but the scenario writer is the
  second line of defense.
- **Adversarial.** The Given describes the threat precondition, the
  When describes the adversarial action, the Then describes the
  defensive response. Generic scenarios ("the component handles
  auth") are not scenarios.
- **Data-flow-scoped.** The scenario targets a specific
  input/output/auth-surface/cross-process flow. If the scenario
  doesn't trace to a data flow listed in Phase 1's proposal, the
  OWASP category probably shouldn't have been approved.
- **Verifier-grounded.** The `verified_by` field names the test, tool,
  or manual-review artifact. "Security review" alone is too vague;
  "security review checklist item X" is acceptable.

**Example:**

```json
{
  "name": "Rejects OAuth tokens with invalid issuer",
  "owasp_id": "ASVS V3.5.1",
  "owasp_category_label": "Token-based Session Management",
  "performed_by": "auth-middleware",
  "given": "an incoming request with a JWT signed by a key from an untrusted issuer",
  "when": "the auth middleware validates the token",
  "then": "the request is rejected with HTTP 401 before any business logic runs",
  "verified_by": "tests/security/test_jwt_issuer_validation.py",
  "evidence_kind": "prototype"
}
```

### Out of scope

The component's explicit non-responsibilities. Two shapes:

**Non-empty `out_of_scope` array, with `out_of_scope_reason: null`:**

```json
"out_of_scope": [
  {
    "concern": "Input validation of uploaded files",
    "owner": "file-uploader",
    "reason": null
  },
  {
    "concern": "Retry policy tuning",
    "owner": null,
    "reason": "Deferred per design doc § Deferred Decisions"
  }
],
"out_of_scope_reason": null
```

Three common sources of content:

1. **Owned by another component.** Cite the owner slug. The validator
   checks the owner is a registered slug (cross-file).
2. **Deferred per design doc.** Set `reason` to the design-doc
   reference; leave `owner` as `null`.
3. **Out of feature scope.** The feature explicitly doesn't address
   this. Set `reason` to the explanation; leave `owner` as `null`.

**Empty `out_of_scope`, with explicit `out_of_scope_reason`:**

```json
"out_of_scope": [],
"out_of_scope_reason": "this component's scope is fully covered by the scenarios above"
```

Silence is not allowed. The schema rejects empty `out_of_scope` with
`out_of_scope_reason: null`, and rejects non-empty `out_of_scope` with
a non-null `out_of_scope_reason`.

### Dependencies

Same shape as out-of-scope. Two valid forms:

**Non-empty `dependencies` array, with `dependencies_reason: null`:**

```json
"dependencies": [
  {
    "slug": "drive-downloader",
    "rationale": "This component consumes the local ZIP path the downloader writes; it cannot run until the ZIP is on disk."
  },
  {
    "slug": "sqlite-parser",
    "rationale": "This component publishes the records the parser produces; it cannot run until the parse step has emitted records."
  }
],
"dependencies_reason": null
```

The slug set must match `components.json`'s `depends_on` for this
component (cross-file check). Drift between the two files is a
validator error. The registry's `depends_on` is authoritative;
rationales here add the production-terms explanation.

**Empty `dependencies`, with explicit `dependencies_reason`:**

```json
"dependencies": [],
"dependencies_reason": "this component has no dependencies on other components in this feature's roadmap"
```

This is the form to use when `components.json` has `depends_on: []`
for the component.

A dependency cannot reference itself — the schema rejects
`dependencies[i].slug == component.slug`.

---

## Writing the file

Write `roadmap.json` directly with `Filesystem:write_file` or its
environmental equivalent. Use `json.dump(data, f, indent=2,
ensure_ascii=False)` or equivalent — `indent=2` matches the
readability convention.

Generate components in the same order as `components.json`. Topological
order is enforced by the schema; the cross-file array-order check at
Phase 3 confirms parity.

After writing, do not proceed to Phase 3 automatically. The user may
want to review the file before validation. Announce that generation is
complete and offer to run Phase 3 (or wait for user request).

---

## Common mistakes to avoid

- **Narrative paragraphs pretending to be scenarios.** If a JSON
  scenario object lacks any of `name`, `given`, `when`, `then`,
  `verified_by`, `evidence_kind`, the schema rejects it. Don't try to
  smuggle prose-only descriptions through the `purpose` field; the
  scenario format is the contract.
- **Copy-pasted `verified_by` clauses.** If every scenario reads
  `verified_by: "integration test"`, the verifier isn't specific
  enough. Name the test file path, or the tool invocation, or the
  named review artifact.
- **Security scenarios that repeat functional scenarios.** The
  security scenario is adversarial. "Parses records correctly" is
  functional; "Rejects malformed records without crashing" is
  security. If the two are the same scenario, you're missing the
  adversarial angle.
- **Placeholder slug references.** Don't write
  `"slug": "<other-component-slug>"` in `dependencies`. Resolve to
  actual slugs from `components.json`.
- **Inconsistent `evidence_kind`.** A scenario whose `verified_by`
  points at a prototype test must have `evidence_kind: "prototype"`.
  A scenario whose `verified_by` describes a check that will be
  created during implementation must have `evidence_kind:
  "prescribed"`. Mismatches between the two are content errors a
  reviewer must catch — the schema enforces the field is present and
  one of the two values, but cannot verify the verifier actually
  matches the kind.
- **Fresh `components.json` every run.** Phase 2 reads the registry;
  it doesn't write one. If you find yourself editing `components.json`
  during Phase 2, you're back in Phase 1 — loop back explicitly and
  run through the user-review STOP.
- **Forgetting empty-list-with-reason for out-of-scope and
  dependencies.** Empty arrays without an explanatory reason field
  are rejected by the schema. Either populate the array or set the
  reason field; not both.
- **Misordering components in the array.** `roadmap.json`'s
  `components` array must match `components.json`'s component order.
  The cross-file check at Phase 3 surfaces drift — but it's easier
  to get right at generation time than to fix later.
