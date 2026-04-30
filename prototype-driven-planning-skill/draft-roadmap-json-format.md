# roadmap.json Format

The per-component content artifact for a feature's roadmap. Holds
purpose paragraphs, prototype evidence, scenarios (Gherkin), out-of-scope
items, and dependency rationales. Joined to `components.json` (the
registry) by component slug.

Written by Phase 2; validated by Phase 3. Every field and section is
required unless explicitly marked optional. The Pydantic schema in
`roadmap_schema.py` enforces this structure; deviations are not
cosmetic, they break downstream consumption.

`components.json` is the authoritative registry of components for a
feature (see `components-json-format.md`). The component slug appears
in both files; if the slug sets disagree, the `roadmap.json` slugs are
flagged and `components.json` wins. The same applies to `depends_on`
parity, OWASP id parity, and array order.

---

## Location

`docs/roadmap/<feature>/roadmap.json` — in the same directory as
`components.json`, `components_schema.py`, and `roadmap_schema.py`.

One file per feature. All component content lives in this single
file's `components` array, in the same order as `components.json`.

Component slugs follow the rules in `phase-1-extraction.md` §
"Slug generation rules" and must match `components.json`. Example
derivations spanning different project types:

| Component name | Slug | Domain |
|---|---|---|
| Google Drive Downloader | `drive-downloader` | data pipeline |
| SQLite Parser | `sqlite-parser` | data pipeline |
| MinIO Uploader | `minio-uploader` | data pipeline |
| RabbitMQ Publisher | `rabbitmq-publisher` | data pipeline |
| User Authentication Service | `auth-service` | web service |
| Payment Webhook Handler | `payment-webhook` | web service |
| Order Status Screen | `order-screen` | mobile app |
| Biometric Login View | `biometric-login` | mobile app |
| CSV Validator Library | `csv-validator` | shared library |
| Terraform Module | `terraform-module` | infrastructure |

---

## Schema

The Pydantic schema in `roadmap_schema.py` is the source of truth for
field shapes and validation rules. Top-level structure:

```json
{
  "schema_version": "1.0",
  "feature": "<feature-name>",
  "components": [
    {
      "slug": "<component-slug>",
      "purpose": "<one paragraph>",
      "prototype_evidence": [...],
      "functional_scenarios": [...],
      "security_scenarios": [...],
      "out_of_scope": [...],
      "out_of_scope_reason": null,
      "dependencies": [...],
      "dependencies_reason": null
    }
  ]
}
```

Per-component content shape:

```json
{
  "slug": "<component-slug>",
  "purpose": "<paragraph: what this component does within the feature; scope and boundaries; do not duplicate the design doc>",
  "prototype_evidence": [
    {
      "path": "<prototype-relative path>",
      "note": "<one-line note on what this file demonstrates>",
      "lines": "23-31"
    }
  ],
  "functional_scenarios": [
    {
      "name": "<short scenario name>",
      "given": "<precondition in the component's domain>",
      "when": "<the triggering action or input>",
      "then": "<the observable outcome>",
      "verified_by": "<test path | tool invocation | named manual check>",
      "evidence_kind": "prototype"
    }
  ],
  "security_scenarios": [
    {
      "name": "<short scenario name>",
      "owasp_id": "ASVS V5.1.3",
      "owasp_category_label": "Input Validation",
      "performed_by": "<component-slug>",
      "given": "<threat precondition: an input reaches this component>",
      "when": "<the adversarial or edge-case action>",
      "then": "<the component's defensive response>",
      "verified_by": "<test | tool | review artifact>",
      "evidence_kind": "prototype"
    }
  ],
  "out_of_scope": [
    {
      "concern": "<what's not this component's responsibility>",
      "owner": "<other-component-slug>",
      "reason": "<optional: why excluded>"
    }
  ],
  "out_of_scope_reason": null,
  "dependencies": [
    {
      "slug": "<other-component-slug>",
      "rationale": "<one-line: why this component depends on it, in production terms>"
    }
  ],
  "dependencies_reason": null
}
```

---

## Top-level field reference

| Key | Type | Required | Notes |
|-----|------|----------|-------|
| `schema_version` | string | yes | Currently `"1.0"`. Validator accepts `1.x`. |
| `feature` | string | yes | Kebab-case slug. Must match `components.json`'s `feature`. |
| `components` | array | yes | Non-empty array of component-content entries. Same order and same slug set as `components.json`. |

## Per-component field reference

| Key | Type | Required | Notes |
|-----|------|----------|-------|
| `slug` | string | yes | Kebab-case identifier matching the same component's `slug` in `components.json`. Unique within `roadmap.json`. |
| `purpose` | string | yes | One paragraph explaining what this component does within the feature, with scope and boundaries. Do not duplicate the design doc — focus on what a reader needs to understand this entry standalone. Non-empty (whitespace-only is rejected). |
| `prototype_evidence` | array | yes | At least one entry. See "Prototype evidence" below. |
| `functional_scenarios` | array | optional (default `[]`) | Functional Gherkin scenarios. May be empty if the component is purely security-focused. |
| `security_scenarios` | array | optional (default `[]`) | Security Gherkin scenarios with OWASP IDs and Performed-by fields. May be empty if the component has no implicated security categories. |
| `out_of_scope` | array | optional (default `[]`) | Out-of-scope concerns. Mutually exclusive with `out_of_scope_reason` (see "Out-of-scope completeness"). |
| `out_of_scope_reason` | string or null | optional | Single explanation when `out_of_scope` is empty. |
| `dependencies` | array | optional (default `[]`) | Dependency rationales. Mutually exclusive with `dependencies_reason`. |
| `dependencies_reason` | string or null | optional | Single explanation when `dependencies` is empty. |

---

## Prototype evidence

Every component must cite at least one prototype-evidence entry.
Components without prototype evidence indicate either (1) a design-doc
component the prototype didn't actually validate (which should have been
caught in planning's Phase 2 loopback) or (2) a mapping error during
Phase 1 of this skill. Either way, stop and fix before proceeding.

Each entry:

| Key | Type | Required | Notes |
|-----|------|----------|-------|
| `path` | string | yes | Path relative to the prototype directory or project root, depending on convention. Non-empty. |
| `note` | string | yes | One-line description of what this file demonstrates for this component. Non-empty. |
| `lines` | string or null | optional | Line range like `"23-31"`. Used when only part of the file is relevant. May be omitted or `null`. |

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

---

## Scenario structure

Both functional and security scenarios are Gherkin-shaped (Given /
When / Then / Verified-by). Security scenarios add Performed-by and
the OWASP requirement id. Every scenario also declares an
`evidence_kind` indicating whether the verifier is a prototype
artifact or an implementation-phase prescription.

### Common scenario fields

Every scenario (functional or security) carries these fields:

| Key | Type | Required | Notes |
|-----|------|----------|-------|
| `name` | string | yes | Short scenario name; reads as the scenario summary. Non-empty. |
| `given` | string | yes | Precondition. Non-empty. |
| `when` | string | yes | Triggering action or input. Non-empty. |
| `then` | string | yes | Observable outcome. Non-empty. |
| `verified_by` | string | yes | Concrete artifact: test file path, tool invocation, or named manual check. **Empty / "TBD" / "<unknown>" / "N/A" / "TODO" are rejected.** A scenario that cannot name its verifier is a principle or aspiration, not a scenario. |
| `evidence_kind` | enum | yes | One of `"prototype"` (the verifier exists in the prototype) or `"prescribed"` (the verifier will be created during implementation; the design doc requires the behavior). See "Evidence kind" below. |

### Security scenario additional fields

| Key | Type | Required | Notes |
|-----|------|----------|-------|
| `owasp_id` | string | yes | OWASP requirement identifier. Matches `ASVS V<n>.<n>.<n>` (e.g., `ASVS V5.1.3`) or `MASVS-<CAT>-<n>` (e.g., `MASVS-STORAGE-1`). |
| `owasp_category_label` | string | yes | Human-readable category label, e.g., `"Input Validation"`, `"Data Storage"`. Should match the category name in `owasp-asvs-mapping.md` or `owasp-masvs-mapping.md` for consistency, but the validator only checks non-empty. |
| `performed_by` | string | yes | The slug of the component whose code performs the action this scenario describes. **Must equal the enclosing component's own slug.** See "Performed by" below. |

---

## Evidence kind

Every scenario declares whether its verifier is observed or prescribed:

- **`"prototype"`** — the verifier exists and runs against the prototype.
  The behavior is observed.
- **`"prescribed"`** — the verifier will be created during implementation.
  The behavior is required by the design doc but not yet validated.

This replaces the prose convention of "Prescribed (not validated)"
labels in scenarios. Making it a structured field forces every scenario
to commit to one or the other and lets the validator and downstream
skills reason about prototype-validated vs. design-prescribed behaviors
without parsing scenario prose.

A scenario marked `"prototype"` whose `verified_by` doesn't actually
exist in the prototype is a content error a human reviewer must catch
during Phase 3 review. The schema enforces the field is set and the
verifier is non-placeholder, but it cannot run the verifier itself.

---

## Performed by

Every security scenario must declare which component's code performs
the action the scenario describes:

```json
"performed_by": "<component-slug>"
```

The slug must:

- **Equal the enclosing component's own slug.** The entry describing
  component X holds security scenarios where X's code performs the
  action; if the action belongs to another component, the scenario
  belongs in that other component's entry.
- **Be a slug registered in `components.json`.** Typos and references
  to unregistered components are validator errors (cross-file check).

This field exists to catch a specific failure (R01 trial): a security
concern is real, but it gets attached to the entry of a component
that *consumes* the result of an action rather than the entry of the
component that *performs* the action. Without an explicit Performed-by,
this kind of misplacement is invisible to a reviewer scanning the file
— the scenario reads as if it concerns the entry's component, but the
action it describes lives elsewhere.

If the action lives in the design doc's overall security posture (for
example, a project-wide TLS policy that applies to every component)
rather than in any single component's code, it doesn't belong in any
component entry — record it in the design doc's Security Posture
section.

---

## Out-of-scope completeness

`out_of_scope` and `out_of_scope_reason` are mutually exclusive:

- **Non-empty `out_of_scope`** — the array lists explicit concerns.
  Each entry has `concern` (required), `owner` (optional slug pointing
  to the component that owns the concern), `reason` (optional text).
  When `out_of_scope` is non-empty, `out_of_scope_reason` must be
  `null`.
- **Empty `out_of_scope` with `out_of_scope_reason`** — the component
  has no out-of-scope concerns, with an explicit explanation. Example:
  `"out_of_scope_reason": "this component's scope is fully covered by
  the scenarios above"`.
- **Both present** — schema error.
- **Neither present (silence)** — schema error.

The "either content or reason" pattern exists because silence reads as
"the model didn't think about this" rather than "the model thought
about it and it's empty." Forcing one or the other makes Phase 2's
reasoning visible to a Phase 3 reviewer.

When `out_of_scope` entries name an `owner`, the validator checks
the owner slug is registered in `components.json` (cross-file check).

---

## Dependencies completeness

Same pattern as out-of-scope:

- **Non-empty `dependencies`** — array of `{slug, rationale}` entries.
  Each entry's slug must be a valid kebab-case slug; rationale must be
  non-empty. When `dependencies` is non-empty, `dependencies_reason`
  must be `null`.
- **Empty `dependencies` with `dependencies_reason`** — explicit
  explanation. Example: `"dependencies_reason": "this component has no
  dependencies on other components in this feature's roadmap"`.
- **Both present** — schema error.
- **Neither present** — schema error.

The validator also enforces (cross-file check) that the slugs in
`dependencies` exactly match the `depends_on` array in
`components.json`'s entry for the same component. Drift between the
two files is a validator error. The registry's `depends_on` is
authoritative; rationales in `roadmap.json` derive from it.

A dependency cannot reference itself — `dependencies[i].slug != component.slug`
is enforced by the schema.

---

## Validation rules

The validator (`scripts/validate_roadmap.py`) loads `roadmap.json`
against `roadmap_schema.py` and runs cross-file checks against
`components.json`.

**Per-file rules enforced by `roadmap_schema.py`:**

1. The file parses as valid JSON and matches the `Roadmap` model shape.
2. `schema_version` matches `<n>.<n>` and is in the `1.x` range.
3. `feature` is a kebab-case slug.
4. `components` is a non-empty array.
5. Every component entry has all required fields.
6. Every `slug` matches kebab-case format and is unique within
   `roadmap.json`.
7. Every `purpose` is non-empty.
8. Every component has at least one `prototype_evidence` entry; each
   entry has non-empty `path` and `note`.
9. Every functional and security scenario has all required Gherkin
   fields, all non-empty.
10. Every `verified_by` is a concrete artifact (not a placeholder).
11. Every `evidence_kind` is `"prototype"` or `"prescribed"`.
12. Every security scenario's `owasp_id` matches the ASVS or MASVS
    pattern.
13. Every security scenario's `performed_by` matches the kebab-case
    slug pattern AND equals the enclosing component's own slug
    (R01 fix made structural).
14. Out-of-scope completeness: either `out_of_scope` is non-empty
    OR `out_of_scope_reason` is set; not both, not neither.
15. Dependencies completeness: same pattern.
16. No dependency self-reference.
17. Every `out_of_scope.owner` (when present) matches the kebab-case
    slug pattern.

**Cross-file rules enforced by `validate_roadmap.py`:**

18. `feature` matches `components.json`'s `feature`.
19. The slug set matches `components.json`.
20. The component array order matches `components.json`.
21. For each component, `dependencies` slug set matches
    `components.json`'s `depends_on` array.
22. For each component, the set of `owasp_id` values cited in
    `security_scenarios` exactly matches `components.json`'s
    `owasp_categories` for the same component.
23. For each security scenario, `performed_by` is a slug registered
    in `components.json`.
24. For each `out_of_scope` entry with an `owner`, the owner slug is
    registered in `components.json`.

---

## Anti-patterns the schema and validator prevent

- **Narrative-only entries.** The schema forces every assertion into a
  Gherkin scenario with a named verifier. "This component does X, Y,
  and Z" prose can't masquerade as a roadmap.
- **Unverifiable security claims.** "We handle auth correctly" is not
  a scenario. The `verified_by` field's non-placeholder rule forces
  naming what checks the claim.
- **Dependency-list drift.** Cross-file parity between `depends_on` in
  `components.json` and `dependencies` in `roadmap.json` means a
  refactor that adds a dependency can't forget one or the other. Same
  for `owasp_categories` ↔ `owasp_id` parity.
- **Wholesale OWASP inclusion.** Phase 1's data-flow scoping means
  only implicated categories make it into the registry, and the
  cross-file ID-set parity rule means scenarios cannot exceed the
  registered set without flagging.
- **Speculative scenarios.** `prototype_evidence` is required and
  non-empty. Scenarios without prototype validation must be marked
  `evidence_kind: "prescribed"` and name an implementation-phase
  verifier.
- **Ad-hoc taxonomies.** There is no `component_type` field — a label
  that doesn't drive any behavior is speculation about what categories
  future projects will need. The slug is the identifier; the name (in
  `components.json`) is the display; the `purpose` paragraph tells a
  reader what the component is.
- **Cross-component security misplacement.** The `performed_by` field
  is required and validated to equal the enclosing component's slug.
  A scenario where the action lives elsewhere triggers a schema error
  immediately, not a subtle misreading by a later reviewer.
- **OWASP ID drift between registry and scenarios.** A scenario's
  `owasp_id` field can subtly differ from the registry (V9.2.1 vs
  V9.2.2) without breaking format checks. The cross-file ID-set parity
  rule catches this; each side serves as a cross-check on the other.
- **Empty Out-of-Scope or Dependencies as silence.** The mutual-
  exclusion rule means an empty list must carry an explicit reason.
  "I didn't think about this" is rejected; "I thought about it and
  it's empty because <reason>" is accepted.
- **Placeholder verifiers.** `verified_by: "TBD"` and similar
  variants are rejected at schema time. A scenario without a real
  verifier is surfaced before the user signs off.
- **Unstructured judgment-vs-observation.** `evidence_kind` makes the
  prototype-validated vs. design-prescribed distinction structural.
  Scenarios cannot drift into "looks validated but isn't" without
  explicit `"prescribed"` labeling.

---

## Why this shape

- **One file, not one per component.** Earlier versions of the skill
  produced one markdown file per component. Reasoning across components
  required parsing a directory; the cross-file parity checks lived in
  the validator script. Consolidating into one JSON file with the
  `components` array makes the per-feature structure visible at a
  glance, eliminates filename-based slug joins, and makes the diff
  surface one file instead of N.
- **Sibling registry file.** `components.json` carries the structural
  skeleton; this file carries the content. Each is independently
  schema-validatable; cross-file invariants live in
  `validate_roadmap.py`. The split lets Phase 1 produce a complete
  artifact (`components.json`) before Phase 2 begins, which means a
  session interrupted between phases doesn't leave half-formed JSON
  on disk.
- **Mutual-exclusion patterns for `out_of_scope` and `dependencies`.**
  Empty lists with no reason are silent. Mutual exclusion forces the
  model to commit either to specific items or to an explicit reason
  why the list is empty. The reviewer reads the reason and confirms
  it; "I didn't think about it" never reaches the reviewer.
- **`evidence_kind` as a required enum.** The planning skill arc has
  consistently moved silent reasoning into structural artifacts.
  `evidence_kind` is the latest instance: it makes "is this validated
  by the prototype, or is it a design-doc requirement awaiting
  implementation?" a field every scenario commits to, replaces the
  prose convention of "Prescribed (not validated)" labels, and gives
  downstream skills a clean signal to reason about.
- **Performed-by per security scenario, not per component.** Earlier
  designs considered putting Performed-by once at the component level.
  But security scenarios within a component can describe actions the
  component performs in different sub-contexts (input validation in
  the parser; output sanitization in the publisher), so the
  per-scenario field is more honest. The schema's
  `security_performed_by_matches_self` validator forces every
  scenario to declare the same slug as the enclosing component, which
  means the field's *information* is no different from a per-component
  marker — but the *force-the-model-to-commit* property is per
  scenario, which is where the R01 misplacement actually happens.
