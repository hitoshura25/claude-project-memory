# Phase 1: Extraction & Data-Flow Mapping

Detailed guidance for the first phase of the roadmap skill. Read this
before running Phase 1.

The goal of Phase 1 is to produce a user-approved `components.json` —
the authoritative registry Phase 2 consumes. Everything else in this
phase serves that goal: the precondition check ensures the input is
parseable; the component extraction captures what's there; the
data-flow derivation informs OWASP category selection; the user review
catches mistakes before they propagate into `roadmap.json`.

---

## Precondition check

Before parsing anything, confirm the design doc's structure. The check
is structural — section names must match exactly. This skill does not
inspect section content to judge whether the planning skill did its
job; that's the planning skill's Phase 3 Open Questions Triage
responsibility.

### Required sections

- `## Architecture Overview` — with an `### Components` subsection
  beneath it.
- `## Tooling` — with a `### Security Tooling` subsection beneath it.
- `## Deferred Decisions` — this is the post-triage section name from
  the planning skill.

### Blockers

If any of the following is true, stop and explain to the user:

- Missing `## Architecture Overview` or its `### Components` subsection.
  → The design doc isn't the output of the prototype-driven-planning
  skill, or it predates the template that enforces Architecture
  Overview. The roadmap skill can't proceed.
- Missing `## Tooling` → `### Security Tooling` subsection.
  → The design doc predates the Part C security-tooling expansion
  (2026-04-23). Suggest re-running the planning skill's Phase 2 to
  populate the section, or manually adding it before proceeding.
- Present `## Open Questions` section (instead of, or in addition to,
  `## Deferred Decisions`).
  → The design doc predates the Part A Open Questions Triage expansion.
  Suggest re-running the planning skill's Phase 3 triage step before
  proceeding; the roadmap skill won't consume an untriaged design doc.

When stopping, cite the specific section that's missing or wrong and
point the user at the upstream skill step that produces it. Do not
fabricate the missing sections or proceed with a partial roadmap.

---

## Parsing components

The design doc's `### Components` subsection uses a predictable shape
(from the planning skill's design-doc template):

```markdown
### Components

**<Component Name>**
- **Responsibility**: <one-sentence description>
- **Prototype evidence**: <file path(s) and line references>
- **Production considerations**: <what changes between prototype and production>

**<Another Component Name>**
- **Responsibility**: ...
- **Prototype evidence**: ...
- **Production considerations**: ...
```

Extract, for each component:

- **Name** — the bolded header (e.g., "Google Drive Downloader").
- **Responsibility** — the one-sentence responsibility from the bullet.
- **Prototype evidence** — the file references cited. These become the
  `prototype_evidence` entries in `roadmap.json`.
- **Production considerations** — not a separate roadmap section, but
  useful context for writing functional scenarios (production
  behavior the prototype may have deferred).

If the `### Components` subsection uses a different structure than the
template expects (e.g., flat paragraphs, or sub-sub-headings for each
component), adapt — but surface the deviation to the user in the
Phase 1 proposal so they can confirm the components you extracted.

---

## Slug generation rules

Every component gets a slug. The slug is:
- The `slug` value in `components.json`
- The matching `slug` value in `roadmap.json`
- The stable identifier other components reference in `depends_on`

### Algorithm

1. Take the component name.
2. Lowercase it.
3. Replace any run of whitespace with a single hyphen.
4. Strip any character that is not `[a-z0-9-]`.
5. Collapse any run of multiple hyphens into a single hyphen.
6. Strip leading and trailing hyphens.
7. If the result has more than 4 hyphen-separated words, trim to the
   most distinctive 2–4 words (typically drop generic nouns like
   "service", "component", "handler" if the remaining words still
   identify the component uniquely).
8. If the result has fewer than 2 characters or starts with a digit,
   prepend a domain hint (e.g., "svc-", "lib-") rather than shipping
   an unreadable slug.

### Worked examples

| Component name | Slug | Notes |
|---|---|---|
| Google Drive Downloader | `drive-downloader` | "google" trimmed; 2 distinctive words |
| SQLite Parser | `sqlite-parser` | direct kebab-case |
| MinIO Uploader | `minio-uploader` | direct |
| RabbitMQ Publisher | `rabbitmq-publisher` | direct |
| User Authentication & Authorization Service | `auth-service` | "&" stripped; trimmed to 2 words |
| Order Status Screen | `order-screen` | trimmed; "status" dropped |
| CSV Validator Library | `csv-validator` | "library" trimmed (domain is obvious) |
| 2FA Handler | `twofa-handler` | leading digit prefixed with spelled-out form |

### Uniqueness

After generating all slugs, check for collisions. If two components
produce the same slug, the second gets a disambiguating suffix drawn
from the component name — prefer adding a semantic suffix over a
numeric one. Example: "Metrics Publisher" and "Metrics Aggregator" both
slug to `metrics` if over-trimmed → keep them as `metrics-publisher`
and `metrics-aggregator`.

### User override

The Phase 1 proposal surfaces every generated slug next to the
component name. The user can override any slug before approving. Use
the user's override verbatim; don't try to "improve" it.

---

## Data-flow derivation

For each component, name its data flows concretely. "Concretely" means
citing specific prototype files, specific endpoints, specific queues —
not "reads input from users" but "reads the uploaded `.zip` file from
`<prototype-path>/src/handlers/upload.py`."

### The five flow kinds

Every component has zero or more of these. Omit the ones that don't
apply; do not list them as "None" for every component (that's noise).

1. **Inputs** — where data enters the component's boundary.
   - External: HTTP requests, message-queue messages, file-system
     reads, scheduled triggers, user actions (taps, clicks).
   - Internal: parameters passed from another component (name which).
   - Cite the prototype file where the input is received.

2. **Outputs** — where data leaves the component's boundary.
   - External: HTTP responses, queue publishes, file-system writes,
     database writes, stdout/stderr for CLI tools.
   - Internal: return values consumed by another component.
   - Cite the prototype file where the output is emitted.

3. **Persisted state** — anything written to a store that survives
   the component's lifecycle.
   - Database tables, object storage, local files the component
     intends to read back, cache entries with non-trivial TTL.
   - Not: ephemeral in-memory state, log lines, metrics emissions
     (those are observability, not state).

4. **Auth surfaces** — authentication or authorization decisions the
   component makes or delegates.
   - Authenticates an incoming request (validates a token, checks
     a session, verifies an API key).
   - Authenticates an outgoing request (attaches credentials to call
     an external service).
   - Authorizes an action (checks whether the authenticated principal
     can perform the operation).
   - Manages credential storage or rotation.

5. **Cross-process communication** — boundaries where the component
   communicates with another process via IPC, RPC, or message
   passing.
   - RPC calls (gRPC, thrift).
   - Message-queue publish/consume.
   - Named pipes, sockets, shared memory.
   - Distinct from "outputs" because the other side of the connection
     is a known collaborator with a protocol, not a general sink.

### Prototype-evidence rule

If the design doc lists a component behavior that the prototype didn't
actually demonstrate, flag the flow as **unobserved — per design-doc
prescription**. Do not make up data flows the prototype didn't exercise.
Examples of where this commonly happens:

- The design doc says the component "should authenticate with mTLS in
  production" but the prototype used plain HTTP. The auth surface is
  real, but unobserved. Mark it as such; it will still produce a
  security scenario, but the scenario's `evidence_kind` will be
  `"prescribed"` and its `verified_by` will name an
  implementation-phase check (not a prototype test).
- The design doc says the component "persists failure state for
  retry" but the prototype used in-memory state only. Persisted
  state is real in scope, unobserved. Same handling.

The `evidence_kind` field is set per scenario in `roadmap.json`, not
per data flow in `components.json`. Phase 1 records the unobserved
status as a note for Phase 2 to use; the registry only carries OWASP
categories, not scenario evidence labels.

---

## OWASP category mapping

For every data flow, consult the relevant reference doc:

- **Web/API/service components** → `owasp-asvs-mapping.md`
- **Mobile app components** → `owasp-masvs-mapping.md`

Each reference doc has a data-flow-to-category table. Walk each of the
component's flows through the table and collect the categories.

### Scoping rules

- **Include only what the data flow implicates.** A component with no
  auth surface doesn't get an auth category. A component with no
  outbound HTTP doesn't get a TLS category. Wholesale inclusion is
  noise.
- **Collapse duplicates.** If two flows implicate the same category,
  include the category once.
- **Prefer specific requirement IDs over category-level references.**
  `ASVS V5.1.3` beats `ASVS V5` in `owasp_categories`. The reference
  tables list the top 3–5 requirement IDs per category; pick the ones
  whose text matches the component's actual flow.
- **Cite exactly what appears in the OWASP document.** The schema
  checks the ID *format*, not whether the ID exists — but stale or
  wrong IDs are reviewer-visible errors. If the reference doc points
  at `V5.1.3` but the user's OWASP version has renumbered it, defer
  to the OWASP document and note the discrepancy to the user.

### When the mapping reference doesn't cover a flow

The reference docs are not exhaustive. If a component has a data-flow
kind the mapping doesn't cover, consult the OWASP source directly and
cite the requirement ID you find there. Surface the gap in the
Phase 1 proposal so the reference doc can be expanded in a future
iteration.

### Naming the actor for each category

For every (component, OWASP category) pair, name the *component
whose code performs the action* the category will scrutinize. This
is usually the same component the category was attached to — but not
always. A category can be a real concern that surfaces because of
*another* component's actions on data this component then consumes.

Example: temp-directory permissions for a SQLite extraction. The
parser reads the extracted file, but the orchestrator that calls the
parser is the component that creates the temp directory and chooses
its permissions. ASVS V8.1.1 (Data Protection) attaches to the
orchestrator, not the parser.

The Phase 1 proposal includes one line per (component, category)
pair naming the actor. If the actor is a different component than
the one the category is currently attached to, move the category in
`components.json`'s `owasp_categories` array before user approval.

This naming step exists because misplacement is invisible to a
reviewer scanning the file later — the security scenario reads as if
it concerns the file's component, but the action it describes lives
elsewhere. Phase 2 enforces the placement via a `performed_by` field
on every security scenario in `roadmap.json`; Phase 1 prevents the
misplacement from happening in the first place.

---

## Dependency graph

`components.json` records one `depends_on` array per component.

`depends_on` represents **structural dependencies**: this component's
code imports from or interfaces with another component's code at the
implementation level. Operational ordering — for example,
"infrastructure must be running before runtime components can execute"
— is conveyed by **array order alone**, with `depends_on` left empty.

Populate `depends_on` from the design doc's component interactions and
from obvious architectural dependencies:

- **Import-level**: component B imports a type or function from
  component A's module. B depends on A.
- **Pipeline-level**: component B consumes output component A produces.
  B depends on A.
- **Orchestration-level**: a DAG or orchestrator depends on every
  component it coordinates.

The design doc's `### Interactions` subsection is the primary source
for pipeline-level dependencies. Import-level dependencies come from
reading the prototype.

### Operational vs structural — the project-setup case

A `project-setup` component (when present) is an operational
precondition for runtime components but is typically NOT a structural
dependency. Runtime code doesn't import from project setup; it
operates inside the infrastructure project setup provides. The
schema convention:

- `project-setup` is the first component in the array.
- Runtime components have empty `depends_on` lists with respect to
  `project-setup` — array order conveys the operational precedence.
- Runtime components that depend on each other (parser depends on
  downloader output) DO list those dependencies in `depends_on`.

If a runtime component genuinely imports from `project-setup` (e.g.,
it imports a Settings class defined there), that's a structural
dependency and `project-setup` belongs in its `depends_on`. The
default for typical infrastructure-vs-runtime projects is operational
ordering only.

### Topological array order

Components in `components.json` must be in topological order — every
component's `depends_on` references appear earlier in the array than
the component itself. This makes array order convey ordering without
an extra `order` field, and the schema catches cycles naturally
(a cycle requires a forward reference, which the topological check
rejects).

The conventional ordering: infrastructure first (`project-setup`
when present), then runtime components in dependency order. Generate
the array by walking the dependency graph in topological order.

### No self-references, no cycles

A component cannot depend on itself. The schema rejects cycles
(A → B → A, A → B → C → A). If the graph would be cyclic, something
is wrong in the decomposition — the two components are really one, or
a shared dependency needs to be extracted as a third component. Loop
back to the design doc rather than forcing a cyclic roadmap.

---

## The Phase 1 proposal message

Surface the full extraction as a single structured message to the user:

```
Roadmap Extraction: <feature-name>

Precondition check: ✓
Components found: N

### <Component 1 name> → slug: <component-1-slug>
- Responsibility: <from design doc>
- Prototype evidence: <file list>
- Data flow:
  - Inputs: <concrete list>
  - Outputs: <concrete list>
  - Persisted state: <list or omit>
  - Auth surfaces: <list or omit>
  - Cross-process: <list or omit>
- Proposed OWASP categories:
  - ASVS V5.1.3 (performed by: <slug>)
  - ASVS V5.1.4 (performed by: <slug>)
  - ASVS V14.2.1 (performed by: <slug>)
- Depends on: []

### <Component 2 name> → slug: <component-2-slug>
...

Component dependency graph (structural, with array order):
  1. project-setup        (operational precondition; depends_on: [])
  2. drive-downloader     (depends_on: [])
  3. sqlite-parser        (depends_on: [drive-downloader])
  4. minio-uploader       (depends_on: [sqlite-parser])
  5. rabbitmq-publisher   (depends_on: [minio-uploader])

---
Please review:
- Component list and slugs (any you want to rename?)
- Data flows (any missing or incorrect?)
- OWASP categories (any to add or remove?)
- Dependency graph (any edges wrong? any operational-vs-structural calls to revisit?)
- Component array order (topological — does it match your mental model?)

Once approved, I'll write `docs/roadmap/<feature>/components.json`,
copy `components_schema.py` into the roadmap directory, run schema
validation, and proceed to Phase 2.
```

---

## Writing `components.json`

After user approval:

1. Create the directory if it doesn't exist:
   `docs/roadmap/<feature>/`.
2. Copy `components_schema.py` from this skill's `scripts/` directory
   into the roadmap directory. The schema becomes a project artifact;
   downstream skills and the validator import from the project copy.
3. Write `components.json` per `references/components-json-format.md`.
   Use `json.dump(data, f, indent=2)` or equivalent — `indent=2`
   matches the readability convention everyone reads fluently.
4. Run schema validation on the registry alone before Phase 2 begins.
   This catches Phase 1 mistakes (bad slug format, forward references,
   malformed OWASP IDs) before Phase 2 spends time generating content
   against a broken registry.

The full validator (`validate_roadmap.py`) requires both files, so
Phase 1's check is a registry-only schema validation:

```bash
uv run --with pydantic python -c "
import sys
sys.path.insert(0, 'docs/roadmap/<feature>')
from components_schema import Components
import json
with open('docs/roadmap/<feature>/components.json') as f:
    Components.model_validate(json.load(f))
print('components.json: schema OK')
"
```

If schema validation fails, fix the registry and re-validate before
proceeding. Common mistakes:

- **Forward reference in `depends_on`** — a component references a
  slug that appears later in the array. Reorder the array to
  topological order.
- **Bad OWASP ID format** — `ASVS 5.1.3` (missing V) or
  `ASVS V5.1` (missing patch number). Check the format rules in
  `components-json-format.md`.
- **Slug not kebab-case** — capitals, underscores, leading digit.

If Phase 1 runs successfully but the user asks to pause before
Phase 2, `components.json` and `components_schema.py` are already on
disk — a future session can resume from them.

---

## Common mistakes to avoid

- **Inventing data flows.** If the prototype's upload handler doesn't
  actually validate MIME type, don't list MIME validation as an input
  characteristic. The scenario can describe the gap as out of scope
  in `roadmap.json`, not pretend the prototype handled it.
- **Over-scoping OWASP categories.** Walking every component through
  every category produces a roadmap no reviewer reads. Scope tightly.
- **Slug collision with a real word.** `test` is a valid slug by the
  algorithm but a bad choice — it collides with pytest's `tests/`
  directory conventions and will confuse future readers. Prefer
  `test-harness`, `test-runner`, etc. The uniqueness check won't catch
  this; human judgment does.
- **Skipping the user review STOP.** The approval step is where most
  mistakes get caught. Don't write `components.json` before approval.
  Don't start writing `roadmap.json` content during Phase 1.
- **Putting `project-setup` (or other infrastructure) in runtime
  components' `depends_on` reflexively.** Operational preconditions
  are conveyed by array order; structural dependencies are imports.
  Mixing the two confuses downstream reasoning.
- **Writing `components.json` without the schema file.** The roadmap
  directory must contain both. Phase 3 validation requires the schema
  to be present; downstream skills consume it for typed access.
