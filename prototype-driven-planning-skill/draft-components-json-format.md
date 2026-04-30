# components.json Format

The authoritative registry of components for a feature's roadmap.
Written by Phase 1 after user approval; read by Phase 2 to generate
`roadmap.json`; cross-checked by Phase 3 validation.

The file exists because Phase 1's output otherwise lives only in the
conversation. If a session hits its context limit mid-generation or
the user resumes in a new conversation, Phase 2 needs a parseable
handoff artifact rather than a re-derivation from the design doc
(which would lose the user's amendments from Phase 1's STOP).

`components.json` carries the structural skeleton: which components
exist, their display names, their structural dependencies, and their
OWASP categories. The flesh — purpose paragraphs, prototype evidence,
scenarios, out-of-scope, dependency rationales — lives in
`roadmap.json` (see `roadmap-json-format.md`). Component slug is the
foreign key joining the two files.

---

## Location

`docs/roadmap/<feature>/components.json` — in the same directory as
`roadmap.json`, `components_schema.py`, and `roadmap_schema.py`.

---

## Schema

The Pydantic schema in `components_schema.py` is the source of truth
for field shapes and validation rules. The structure is:

```json
{
  "schema_version": "1.0",
  "feature": "<feature-name>",
  "design_doc_path": "docs/design/<feature>-<YYYY-MM-DD>.md",
  "prototype_path": "prototypes/<feature>/",
  "components": [
    {
      "slug": "<kebab-case-slug>",
      "name": "<Human-Readable Display Name>",
      "depends_on": ["<slug>", "<slug>"],
      "owasp_categories": ["<requirement-id>", "<requirement-id>"]
    },
    {
      "slug": "<another-slug>",
      "name": "<...>",
      "depends_on": [],
      "owasp_categories": []
    }
  ]
}
```

---

## Field reference

### Top-level fields

| Key | Type | Required | Notes |
|-----|------|----------|-------|
| `schema_version` | string | yes | Currently `"1.0"`. The validator accepts the `1.x` range; future breaking changes bump the major version. |
| `feature` | string | yes | The feature name slug. Must match the directory name under `docs/roadmap/` and the `feature` field in `roadmap.json`. Kebab-case. |
| `design_doc_path` | string | yes | Path from project root to the signed-off design doc. The validator resolves it under the project root and fails if the file doesn't exist. |
| `prototype_path` | string | yes | Path from project root to the prototype directory. Resolved and existence-checked the same way. |
| `components` | array | yes | Non-empty array of component entries. One entry per component in the design doc's `### Components` subsection. The array is in topological dependency order — each component's `depends_on` entries appear earlier in the array than the component itself. |

### Component entry fields

| Key | Type | Required | Notes |
|-----|------|----------|-------|
| `slug` | string | yes | Kebab-case identifier matching `^[a-z][a-z0-9-]*[a-z0-9]$`. Unique within this file. Must match the `slug` of the corresponding entry in `roadmap.json`. Generated in Phase 1; may be overridden by the user before approval. |
| `name` | string | yes | Human-readable display name. Non-empty (whitespace-only is rejected). |
| `depends_on` | array of strings | yes | Slugs of other components this one depends on. May be empty (`[]`). Every entry must be a slug registered in this same file. No self-references. No forward references (component A cannot depend on a component listed later in the array). The empty array is required when the component has no dependencies — omitting the field is a schema error. |
| `owasp_categories` | array of strings | yes | OWASP requirement IDs approved for this component in Phase 1. May be empty (`[]`). Same shape rule as `depends_on` — empty array required, omission is a schema error. |

---

## Dependency semantics

`depends_on` represents **structural dependencies**: this component's
code imports from or interfaces with another component's code at the
implementation level. Operational ordering — for example, "infrastructure
must be running before runtime components can execute" — is conveyed by
**array order alone**, with `depends_on` left empty.

A component listed earlier in the array but not in any later component's
`depends_on` is an upstream operational precondition. A component named
in another's `depends_on` is a code-level dependency that the
implementing pipeline will inline as context.

Example: `project-setup` is the first component in the array but is
typically not in any runtime component's `depends_on`, because runtime
code doesn't import from project setup — it operates inside the
infrastructure project setup provides. Array order conveys that
project-setup runs first; `depends_on` would be inappropriate.

---

## Validation rules

The validator (`scripts/validate_roadmap.py`) loads `components.json`
against `components_schema.py` and runs cross-file checks against
`roadmap.json`.

**Per-file rules enforced by `components_schema.py`:**

1. The file parses as valid JSON and matches the `Components` model shape.
2. `schema_version` matches the pattern `<n>.<n>`; the validator
   additionally requires the value to be in the `1.x` range.
3. `feature` matches the kebab-case slug pattern.
4. `design_doc_path` and `prototype_path` are non-empty strings (path
   existence is a cross-file check; see below).
5. `components` is a non-empty array.
6. Every component entry has all four required fields.
7. Every `slug` matches `^[a-z][a-z0-9-]*[a-z0-9]$` (kebab-case;
   starts with letter; ends with letter or digit; no trailing hyphens).
8. Every `slug` is unique within the file.
9. Every entry in any `depends_on` list is a slug registered in this
   same file.
10. No component depends on itself.
11. The array is in topological order: every component's `depends_on`
    references appear at lower array indices than the component itself.
    This catches cycles naturally — a cycle requires at least one
    forward reference, which the topological check rejects.
12. Every `owasp_categories` entry matches one of:
    - `ASVS V<major>.<minor>.<patch>` (e.g., `ASVS V5.1.3`)
    - `MASVS-<CATEGORY>-<num>` (e.g., `MASVS-STORAGE-1`)

**Cross-file rules enforced by `validate_roadmap.py`:**

13. `design_doc_path` resolves to an existing file under the project root.
14. `prototype_path` resolves to an existing directory under the project root.
15. `feature` matches `roadmap.json`'s `feature` field.
16. The set of component slugs matches `roadmap.json`'s component slugs.
17. The component array order matches `roadmap.json`'s component array order.
18. For each component, `depends_on` matches the slug set of the
    corresponding `dependencies` array in `roadmap.json`. Drift between
    the two files is a validator error.
19. For each component, `owasp_categories` exactly matches the set of
    `owasp_id` values cited by that component's security scenarios in
    `roadmap.json`. IDs registered but not cited, or cited but not
    registered, are validator errors. The registry is authoritative;
    scenarios derive from it.

---

## Example

```json
{
  "schema_version": "1.0",
  "feature": "airflow-gdrive-ingestion",
  "design_doc_path": "docs/design/airflow-gdrive-ingestion-2026-04-28.md",
  "prototype_path": "prototypes/airflow-gdrive-ingestion/",
  "components": [
    {
      "slug": "project-setup",
      "name": "Project Setup",
      "depends_on": [],
      "owasp_categories": ["ASVS V2.10.4", "ASVS V14.2.1"]
    },
    {
      "slug": "drive-downloader",
      "name": "Google Drive Downloader",
      "depends_on": [],
      "owasp_categories": ["ASVS V2.10.4", "ASVS V9.2.1", "ASVS V12.4.2"]
    },
    {
      "slug": "sqlite-parser",
      "name": "SQLite Parser",
      "depends_on": ["drive-downloader"],
      "owasp_categories": ["ASVS V5.1.3", "ASVS V5.1.4", "ASVS V12.2.1"]
    },
    {
      "slug": "minio-uploader",
      "name": "MinIO Uploader",
      "depends_on": ["sqlite-parser"],
      "owasp_categories": ["ASVS V8.1.1", "ASVS V9.1.1", "ASVS V12.3.1"]
    },
    {
      "slug": "rabbitmq-publisher",
      "name": "RabbitMQ Publisher",
      "depends_on": ["minio-uploader"],
      "owasp_categories": ["ASVS V2.10.4", "ASVS V8.3.4", "ASVS V9.1.1"]
    }
  ]
}
```

In this example, `project-setup` is first in the array (operational
precondition for everything else) but no runtime component lists it
in `depends_on` — runtime code doesn't structurally depend on
project-setup; it just runs inside the infrastructure project-setup
provides. Conversely, `sqlite-parser` lists `drive-downloader` in
`depends_on` because the parser code consumes the downloader's
output structure.

---

## Why this shape

- **Flat array, not a nested tree.** `depends_on` references are by
  slug, not by nesting. This keeps the JSON readable and makes it easy
  for the model to generate: one entry per component, no recursion.
- **Array order is meaningful.** Topological order is enforced by the
  schema. Array index conveys ordering without an extra `order: 1`
  field, and the validator catches cycles + out-of-order entries with
  one rule.
- **`owasp_categories` as strings, not structured objects.** The
  category identifier is what the validator and downstream consumers
  care about. The human-readable category label (e.g., "Input
  Validation") lives in `roadmap.json`'s scenarios as
  `owasp_category_label`. Keeping this file lean makes diffs readable.
- **No `data_flow` field.** The data-flow derivation is Phase 1's
  reasoning, not Phase 2's input. Once the OWASP categories are
  picked, the data flow has served its purpose — it informed the
  category selection, which is what Phase 2 needs. Recording the flow
  here would duplicate content that belongs in `roadmap.json`'s
  prototype evidence and scenario details.
- **No `purpose` or `prototype_evidence` fields.** Those live in
  `roadmap.json`. `components.json` is a registry, not a content
  store.
- **Each file standalone-validatable.** `components_schema.py` enforces
  every per-file rule with no reference to `roadmap.json`. The
  cross-file checks live in `validate_roadmap.py` and require both
  files. This separation makes it possible to run schema validation
  on `components.json` at the end of Phase 1 — before Phase 2 has
  produced `roadmap.json` — to catch registry-level errors early.
