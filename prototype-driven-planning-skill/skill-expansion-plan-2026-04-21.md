# Skill Expansion Plan — Closed Open Questions, New Roadmap Skill, Prototype Security Tooling

> **Date:** 2026-04-21
> **Scope:** `prototype-driven-planning` skill (modify); new `prototype-driven-roadmap` skill (create); memory repo (update)
> **Driver:** User-requested additions. Two motivating observations from prior runs:
> (a) open questions surfacing during task-decomposition were ambiguities that
> should have been closed during planning, and (b) the design doc's single
> monolithic Security Posture section does not provide per-component security
> grounding that downstream phases can consume.
> **Criterion:** Least non-deterministic. Cuts over additions where possible.
> Schema strictness only where lossy prose has already caused a real bug;
> markdown-plus-validator elsewhere.

---

## 1. What we're changing and why

Three problems this expansion addresses:

1. **Open Questions survive into task decomposition.** The current
   `prototype-driven-planning` skill's Phase 3 produces a design doc whose
   "Open Questions" section is allowed to contain genuinely unresolved items.
   When the downstream `prototype-driven-task-decomposition` skill runs, it
   hits these as ambiguities and surfaces them as numbered questions to the
   user — effectively relitigating planning decisions at task-writing time.
   The planning skill should either resolve these items (via user decision)
   or loop back to Phase 2 to extend the prototype when a question is a
   feasibility question. Nothing unresolved should ship in the design doc
   that a task-decomposer would need to ask about.

2. **No per-component roadmap exists between design doc and tasks.** The
   current workflow goes from design doc (prose, narrative, cross-cutting)
   directly to `tasks.json` (flat list of fine-grained implementation
   tasks). The design doc is the wrong shape for consumption by a task
   decomposer — it's structured around concerns (architecture, data model,
   security, deployment) rather than around components. The decomposer
   has to digest the whole doc and re-fan-out to components. A per-component
   roadmap in between narrows the design doc's contract to one component
   at a time in a scannable, testable form (BDD/Gherkin with Verified-by
   clauses), and gives the future task-decomposition skill a natural input
   shape to consume per-component (eventual refactor — not part of this
   plan's scope, but the roadmap skill is designed with that in mind).

3. **Security is cross-cutting prose, not per-component testable scenarios.**
   The current design doc's Security Posture section describes auth,
   input validation, data sensitivity, and known risks as a single
   narrative. It does not map to specific components, cite specific
   OWASP requirements, or produce verifiable scenarios. Per-component
   roadmap items with Security Scenarios grounded in data-flow-scoped
   ASVS/MASVS give implementation teams concrete security checks rather
   than generic advice. And the prototype itself doesn't validate that
   the security tooling (dep scanner, secrets scanner, SAST) actually
   works in the project's ecosystem — which means the design doc is free
   to prescribe tools the toolchain may not support.

---

## 2. Changes by skill

### 2.1 Planning skill (`prototype-driven-planning`) — Part A + Part C

**Part A: Close open questions before Phase 3 ends.**

`SKILL.md`:

- Phase 3 gains a Step 2 (before the existing final STOP): **Open Questions
  triage.** Content and rules in §3 below.
- Phase 3 Step 3 (was Step 2): present design doc for review. Unchanged
  except it runs after triage is complete.
- Phase 2 ↔ Phase 3 loopback becomes explicit. The Principles section gains:
  "The prototype is immutable *after design-doc sign-off*, not before.
  Looping back from Phase 3 to Phase 2 to resolve a feasibility question
  is the correct move, not a workflow failure."
- Principles section gains: "No feasibility question ships in the design
  doc. If the doc would need to speculate about something, that's a Phase 2
  loopback, not a Deferred Decision."

`references/phase-3-design-doc.md`:

- New section "Open Questions Triage" after "Generating the Doc",
  before "Writing Quality". Specifies the triage workflow and the three
  buckets (Resolved by user decision / Requires prototype extension /
  Deferred to implementation).
- The existing "Open Questions" paragraph in section-by-section guidance
  (currently reads "A good design doc admits what it doesn't know rather
  than papering over uncertainty.") is rewritten to reflect the new rule.

`references/design-doc-template.md`:

- Section renamed: `## Open Questions` → `## Deferred Decisions`.
- Intro text rewritten: "Items explicitly out of the planning horizon
  for this feature. Nothing here may be a feasibility question — those
  require prototype validation. Items here are implementation-phase
  decisions (e.g., SLO tuning, dashboard choice) or operational decisions
  that do not affect the design."

**Part C: Prototype security-tooling validation.**

`references/phase-2-prototype.md`:

- New subsection "Security Tooling Validation" inserted under
  "Toolchain Validation", after "Dockerfile (Conditional)" and before
  "End-to-End Validation". Content in §4 below.
- Existing "Security-by-Design" subsection under "Cross-Cutting Research"
  gets a cross-reference back to the security-tooling validation — the
  prototype now validates that the tooling works; cross-cutting research
  focuses on what the tooling should *find* per the design.

`references/design-doc-template.md`:

- New subsection `### Security Tooling` added to the existing `## Tooling`
  section, after `### Bootstrap` and before `### Notes`. Fields listed in
  §4 below.
- No other `## Tooling` subsections change.

`SKILL.md`:

- Phase 2 Step 2 (Toolchain Validation) gains a new step 7 (after Dockerfile,
  before the existing step 8/End-to-End Validation) pointing to the new
  reference-doc section.

### 2.2 New skill (`prototype-driven-roadmap`) — Part B

Full directory layout:

```
~/claude-devtools/skills/prototype-driven-roadmap/
├── SKILL.md
├── scripts/
│   └── validate_roadmap.py       # Validator: frontmatter + Gherkin structure
└── references/
    ├── phase-1-extraction.md     # Component extraction + data-flow mapping
    ├── phase-2-generation.md     # Roadmap file writing
    ├── phase-3-validation.md     # Cross-reference and schema checks
    ├── roadmap-item-template.md  # The per-component markdown template
    ├── owasp-asvs-mapping.md     # Data-flow → ASVS category reference
    └── owasp-masvs-mapping.md    # Data-flow → MASVS category reference
```

New command at `~/claude-devtools/commands/prototype-roadmap.md`.

Input: a signed-off design doc at `docs/design/<feature>-<date>.md` and
the prototype at `prototypes/<feature>/`. (Signed-off means the user has
completed Phase 3 of the planning skill, including the open-questions
triage; no Deferred Decisions contain feasibility questions.)

Output: `docs/roadmap/<feature>/<component>.md`, one markdown file per
component identified in the design doc's Architecture Overview.

Always required after planning. The skill is part of the standard
workflow, not opt-in.

Phases detailed in §5 below.

### 2.3 Memory repo updates

`README.md`:

- Skill locations section gains
  `~/claude-devtools/skills/prototype-driven-roadmap/` (new).
- Commands section gains `/prototype-roadmap <feature>`.
- Conversation-Start Protocol gains a pointer to this plan doc while it's
  active (read on-demand), then removed once the plan lands and
  `README.md` itself captures the new state.
- File Map gains the new skill's directory tree.
- Current State section gains an entry for this expansion once it lands.

`LEARNINGS.md`:

- "From Planning Skill" section gains two entries:
  - "No feasibility question ships in the design doc" — the Part A rule.
  - "Security tooling must be prototype-validated before the design doc
    prescribes it" — the Part C rule.
- New top-level section "From Roadmap Skill" is added once that skill
  has at least one trial run. Initially omitted.

`trials/_INDEX.md`:

- New tag added to glossary: `design-doc-unresolved-question` — design
  doc shipped with an open question that the task-decomposer had to
  relitigate. Applied retroactively if we see it in existing trials.
  (Not applied now; tag is reserved for future use.)

### 2.4 Task decomposition skill — *no changes in this expansion*

The `prototype-driven-task-decomposition` skill keeps reading the design
doc as today. A future refactor may teach it to read per-component
roadmap files instead, narrowing each task-decomposition pass to one
component. That future refactor is out of scope for this plan. The
roadmap skill is designed so that eventual refactor is a clean substitution
(roadmap files have all the information a per-component decomposer would
need), but the current decomposer continues to work unchanged.

---

## 3. Open Questions triage (Part A detail)

### 3.1 When triage runs

Phase 3 Step 1 generates the design doc as today. Before presenting the
doc as final, the model runs Phase 3 Step 2 (triage). The user sees
the doc only after triage is complete.

### 3.2 The three buckets

For every item the model would have placed in Open Questions (under the
old template) or Deferred Decisions (under the new template), it classifies
into one of:

- **Resolved by user decision.** The question is a choice between known
  alternatives (library X vs Y, naming convention A vs B, scope boundary
  include-or-exclude). The model asks the user, records the decision
  into the appropriate design-doc section, and removes the item from
  the triage output. **The Deferred Decisions section does not carry
  this item forward.**

- **Requires prototype extension.** The question is a feasibility
  question — "does library X actually support Y?", "what does API Z
  return in edge case W?", "can we actually authenticate against
  service S?". The model proposes a prototype extension: which file(s)
  to add, what would be observed, what would change in the design doc
  once observed. The user approves or adjusts the proposal; the flow
  returns to Phase 2; the prototype is extended; Phase 3 re-runs with
  the extended prototype as input.

- **Deferred to implementation.** The question is genuinely outside
  the design horizon — "what monitoring dashboard do we put this on?",
  "what's our target p99 latency?", "which rotation schedule for the
  service account key?". These carry forward in the design doc's
  Deferred Decisions section. **A Deferred Decision must be
  accompanied by a one-sentence rationale explaining why it's not a
  design-time concern.**

### 3.3 The no-feasibility rule

A Deferred Decision must not be a feasibility question. If the model is
tempted to write "Can we use library X for this?" or "Does the SDK
handle case Y?" in Deferred Decisions, that's a signal to classify the
item as "Requires prototype extension" instead.

The difference test:

- **Feasibility question** — the answer changes what the design doc
  would say. "Does X work?" is feasibility: if the answer is yes, one
  design; if no, a different one.
- **Implementation decision** — the answer is orthogonal to the design
  doc's architecture. "What's our p99 SLO?" does not change the
  architecture; the system is the same either way.

If in doubt, classify as feasibility. Small prototype extensions are
cheap; post-hoc design rework is not.

### 3.4 The triage output

Before the design doc is presented for review, the model surfaces
triage results in a structured message:

```
Open Questions Triage: <feature-name>

Found N open questions during design-doc generation. Classified:

### Need your decision (M)
1. <question> — options: <A, B>. Recommendation: <A because …>
2. <question> — …

### Need prototype extension (P)
1. <question> — proposed extension: <files to add>, <what will be
   observed>. Expected design-doc impact: <section X will change
   from … to …>.

### Deferred to implementation (Q)
1. <question> — rationale: <one-sentence reason this is not a design
   concern>.

---
Proceed by:
- Answering the M decisions above
- Approving or adjusting the P prototype extensions
- Confirming the Q deferrals
```

User responds; model acts:

- For "Need your decision" items: write the decision into the relevant
  design-doc section, remove from Deferred Decisions.
- For "Need prototype extension" items: loop to Phase 2 Step 1/2/3
  (core code / toolchain / end-to-end) for the proposed extension,
  update the prototype README with what was observed, regenerate the
  design doc in Phase 3.
- For "Deferred to implementation" items: keep in Deferred Decisions
  with the confirmed rationale.

Only then does Phase 3 Step 3 (present design doc for review) run.

### 3.5 Loopback discipline

The prototype is immutable *after design-doc sign-off*, not before.
During Phase 2 ↔ Phase 3 loopbacks, the prototype may be extended freely.
The Principles section of `SKILL.md` gains this clarification.

The existing rule that the prototype is a reference artifact still
holds; what changes is the phase at which "reference artifact" starts.
It's when the user confirms the design doc in Phase 3 Step 3, not at
the end of Phase 2.

---

## 4. Security-tooling prototype validation (Part C detail)

### 4.1 What gets validated

Three classes of tooling, always in this order:

**Dependency scanning — always required.** The ecosystem-standard tool
for detecting known vulnerabilities in declared dependencies.

| Ecosystem | Tool | Notes |
|-----------|------|-------|
| Python (uv/pip) | `pip-audit` | `uv run pip-audit` or equivalent; respects `pyproject.toml` / `uv.lock` |
| Python (poetry) | `pip-audit` | Works against poetry-exported requirements too |
| Node | `npm audit` or `pnpm audit` | Match project's package manager |
| Rust | `cargo audit` | Requires `cargo install cargo-audit` first |
| Go | `govulncheck` | `go install golang.org/x/vuln/cmd/govulncheck@latest` |
| Gradle (Android/JVM) | OWASP Dependency-Check | `./gradlew dependencyCheckAnalyze` with plugin |
| Maven | OWASP Dependency-Check | Maven plugin |

**Secrets scanning — always required.** Scans the prototype directory
(and its history, for git-tracked prototypes) for leaked credentials.

| Tool | Notes |
|------|-------|
| `gitleaks` | Default. Runs against directory. Low false-positive rate. |
| `trufflehog` | Alternative with more aggressive detection |

Choose `gitleaks` unless the ecosystem has a clear reason to use something
else.

**SAST — conditional.** Run only if the ecosystem has a clear default
static-analysis tool that integrates cleanly with the project's toolchain.

| Ecosystem | Tool | Notes |
|-----------|------|-------|
| Python | `bandit` | Checks for common security issues in Python |
| JavaScript/TypeScript | `semgrep` with `p/javascript` ruleset | Or `p/typescript` |
| Kotlin/Android | `detekt` with security ruleset, or Android Lint's security checks | |
| Rust | skip — less standardized | |
| Go | skip — `gosec` exists but has high noise | |

If SAST is skipped, the design doc's Security Tooling subsection
explicitly records "SAST: Not applicable — <one-sentence reason>".
Skipping requires a reason, not silence.

### 4.2 What "validated" means

For each of the three classes (subject to SAST conditionality):

1. Install the tool using the ecosystem's standard installation path
   (e.g., `uv add --dev pip-audit` for Python; `brew install gitleaks`
   or equivalent for platform tools).
2. Run the tool against the prototype directory or its dependencies.
3. Confirm the tool produces useful output (findings or a clean "no
   issues" result). A tool that crashes or produces unusable output
   fails validation.
4. Capture the exact command that ran.

### 4.3 What to capture for the design doc

The `## Tooling` section of the design doc gains a new subsection:

```markdown
### Security Tooling

- **Dependency scanner**: <tool + version, e.g., pip-audit 2.7.x>
- **Dependency scan command**: <exact command, runnable from service root>
- **Secrets scanner**: <tool + version, e.g., gitleaks 8.x>
- **Secrets scan command**: <exact command>
- **SAST tool**: <tool + version> or "Not applicable — <reason>"
- **SAST command**: <exact command> or "N/A"
- **Notes**: <anything surprising discovered during prototype validation>
```

The field structure mirrors the existing Lint / Test / Bootstrap
subsections. Field names are fixed so downstream skills parse them
reliably.

### 4.4 What "pure-library feature" looks like

For a feature whose prototype is a pure in-memory library (no external
inputs, no new declared dependencies, no file I/O beyond the test
fixtures), dep scan and secrets scan still run — they're cheap. SAST is
likely skipped. The subsection is not omitted; all three lines are
populated, with SAST reading "Not applicable — pure-in-memory library
with no untrusted inputs."

### 4.5 Tool install cost

For ecosystems where the tool isn't typically pre-installed, the
prototype's Toolchain notes (in the prototype's README.md) record the
install command. This is in addition to the design-doc subsection.
Downstream teams using the output of this skill should be able to
reproduce the tooling setup without guessing.

### 4.6 Skip conditions

There are no skip conditions for dependency and secrets scanning. These
always run. SAST may be skipped if:

- The ecosystem lacks a standardized default (Rust, Go as of writing).
- The project uses a language not covered by any freely available SAST
  tool.
- The feature is trivially small (<50 lines) and running SAST would
  produce zero findings with near-certainty.

Each skip is recorded with reason in the design-doc subsection.

---

## 5. Roadmap skill (Part B detail)

### 5.1 Phases

**Phase 1: Component extraction & data-flow mapping.**

1. Read the signed-off design doc. Parse the Architecture Overview's
   "Components" subsection into a list: name, responsibility,
   prototype-evidence file, production considerations.
2. Parse the design doc's Tooling section to understand what security
   tooling is available in the prototype.
3. For each component, derive its data flow: inputs (where data enters),
   outputs (where data leaves), persisted state, auth surfaces,
   cross-process communication. This is a mapping exercise — the model
   names each input/output concretely, referencing prototype files.
4. Map data flows to OWASP categories. Use `references/owasp-asvs-mapping.md`
   (web/API/service components) or `references/owasp-masvs-mapping.md`
   (mobile app components) to identify which categories are implicated
   by each component's data flow. Include only categories the data flow
   actually implicates — no wholesale inclusion.
5. Surface the proposed mapping to the user: component list × data-flow
   summary × proposed OWASP categories.
6. **STOP.** User reviews and adjusts before Phase 2.

**Phase 2: Roadmap item generation.**

For each component, write `docs/roadmap/<feature>/<component>.md` using
the template in `references/roadmap-item-template.md` (detailed in §5.3
below). Fill:

- Frontmatter (component name, type, feature, design_doc_path,
  prototype_path, depends_on list).
- Purpose (one-paragraph narrative).
- Prototype evidence (file references).
- Functional Scenarios in Gherkin form.
- Security Scenarios in Gherkin form, one per implicated OWASP category,
  each citing its requirement ID.
- Out of Scope.
- Dependencies (other roadmap items this one depends on).

**Phase 3: Cross-reference validation.**

1. Run the validator script (`scripts/validate_roadmap.py`) against
   the produced files. The script checks:
   - Frontmatter present with required fields.
   - Every `### Scenario:` block has Given / When / Then / Verified by.
   - Every security scenario has an OWASP requirement ID in its title
     (e.g., `ASVS V5.1.3` or `MASVS-STORAGE-1`).
   - Every `Verified by` clause has a non-empty value.
   - Every `depends_on` reference points to a roadmap file that exists.
   - `design_doc_path` and `prototype_path` resolve to real files/directories.
2. Print a summary table to the conversation: component × functional
   scenario count × security scenario count × OWASP categories covered.
3. **STOP.** User reviews the summary. Any feedback triggers edits to
   specific roadmap files; re-validate after edits.

### 5.2 File naming

- Output directory: `docs/roadmap/<feature-name>/`
- One file per component: `<component-slug>.md`
- Slug rule: lowercase, hyphens for spaces, 2–4 words. Example: a
  component named "Google Drive downloader" becomes `drive-downloader.md`.

This matches the existing `docs/design/<feature>-<date>.md` pattern
(feature-scoped directory) and `tasks/<feature>/tasks.json` (feature-scoped
directory for downstream consumption).

### 5.3 The roadmap-item template

```markdown
---
component: <component-name>
component_type: <ingestor | parser | publisher | DAG | orchestrator | scaffold | UI-screen | service | library | infrastructure>
feature: <feature-name>
design_doc_path: docs/design/<feature>-<date>.md
prototype_path: prototypes/<feature>/
depends_on: [<other-component-slug>, ...]
---

# Roadmap: <Component Name>

## Purpose

<One paragraph: what this component does within the feature. Cross-references
the design doc's Architecture Overview but does not duplicate it.>

## Prototype evidence

- `<file1>` — <what it demonstrates about this component>
- `<file2>` — <what it demonstrates about this component>

## Functional Scenarios

### Scenario: <short name>

**Given** <precondition>
**When** <action>
**Then** <observable outcome>
**Verified by** <automated test | tool output | named manual check>

### Scenario: <short name>

**Given** …
**When** …
**Then** …
**Verified by** …

## Security Scenarios

Derived from data-flow-scoped OWASP ASVS/MASVS. Each scenario cites the
requirement it addresses.

### Scenario: <short name> (ASVS V5.1.3 — Input Validation)

**Given** <threat precondition>
**When** <attacker or adversarial action>
**Then** <system's defensive response>
**Verified by** <test | tool | review>

### Scenario: <short name> (MASVS-STORAGE-1 — Data storage)

**Given** …
**When** …
**Then** …
**Verified by** …

## Out of Scope

- <Concern this component is not responsible for>. Owned by <other-component>.
- <Concern explicitly outside the feature>.

## Dependencies

- `<other-component-slug>.md` — <one-line: why this component depends on it>
```

### 5.4 The validator script

`scripts/validate_roadmap.py`. Pure-Python, no dependencies beyond stdlib
(plus `pyyaml` for frontmatter, which is pip-installable or available via
`uv run --with pyyaml`).

Inputs: path to `docs/roadmap/<feature>/`.

Checks:

1. Every `.md` file in the directory has valid YAML frontmatter with
   required keys: `component`, `component_type`, `feature`,
   `design_doc_path`, `prototype_path`, `depends_on` (may be empty list).
2. `design_doc_path` resolves to an existing file.
3. `prototype_path` resolves to an existing directory.
4. For each `depends_on` entry, `<entry>.md` exists in the same directory.
5. Every `### Scenario:` block is followed by lines containing `**Given**`,
   `**When**`, `**Then**`, `**Verified by**`. Order doesn't matter, all
   four must appear before the next scenario heading or section heading.
6. Every `Verified by` clause has non-empty text after the bold marker.
7. Every scenario under `## Security Scenarios` has an OWASP requirement
   ID in parentheses in the heading. Requirement ID matches one of:
   - `ASVS V<major>.<minor>.<patch>` (e.g., `ASVS V5.1.3`)
   - `MASVS-<CATEGORY>-<num>` (e.g., `MASVS-STORAGE-1`)
8. No two roadmap files have the same `component` frontmatter value.

Exit 0 on success; exit non-zero with a line-numbered error report on
failure.

### 5.5 The OWASP mapping references

`references/owasp-asvs-mapping.md` and `references/owasp-masvs-mapping.md`
are static mapping tables. Pinned to specific OWASP versions (ASVS 4.0.3
and MASVS 2.x as of writing) so requirement IDs stay stable.

Structure for each:

- Version pinned in the top matter (e.g., `ASVS 4.0.3`).
- A data-flow-to-category table: for each data-flow kind (reads untrusted
  input, authenticates a user, stores credentials, writes to persistent
  store, makes outbound HTTP, communicates cross-process, etc.), list
  the ASVS/MASVS categories typically implicated and the top 3–5
  requirement IDs within each.
- A worked example: given a concrete component's data flow, show the
  produced security scenarios.

This is a reference artifact, not an exhaustive OWASP export. If the
model finds a data flow not covered by the mapping, it's expected to
consult the OWASP source directly and cite the requirement ID it finds.

### 5.6 Schema strictness — starting point

Starting position: markdown + validator script. The validator enforces
structural discipline without a Pydantic schema in the middle.

The reasoning matches the LEARNINGS.md rule: "Promote fields to the schema
only when the pipeline mechanically uses them and their absence has
caused a real bug." No pipeline currently consumes roadmap files
mechanically. The consumer is a model (and eventually, the task-decomposer
after a future refactor). A model can read markdown; a validator script
enforces the structure.

If a future task-decomposer refactor hits a "prose is lossy" moment with
roadmap files (analogous to T14's `test_command` bug), we promote the
relevant field to a schema at that time. Speculative promotion is
explicitly avoided.

### 5.7 Precondition check

The roadmap skill's Phase 1 must confirm the design doc is parseable
before proceeding:

- The file at `docs/design/<feature>-<date>.md` exists.
- The file has a `## Architecture Overview` section with an `### Components`
  subsection.
- The file has a `## Tooling` section with `### Security Tooling`
  subsection (added by the Part C changes above).
- The file does not have a `## Open Questions` section (renamed to
  `## Deferred Decisions` under the Part A changes), and its
  Deferred Decisions section does not contain items whose text matches
  feasibility-question patterns (starting with "Can we…", "Does the
  library support…", etc.). This is a heuristic; any match prompts the
  user for confirmation before proceeding.

If any precondition fails, the skill stops with an explicit error
message and does not produce partial output.

---

## 6. Migration / validation plan

### Step 1: Write this plan to the memory repo.

Path: `~/claude-project-memory/prototype-driven-planning-skill/skill-expansion-plan-2026-04-21.md`.

Also update the memory repo's `README.md` — add a pointer to this file
in the Conversation-Start Protocol's on-demand list. Pointer removed
after the plan lands and `README.md` itself captures the new state.

**Pause.** User reviews the plan doc. Adjustments applied before Step 2.

### Step 2: Part C — Phase 2 security-tooling extension.

Smallest scope. Lands first so both Part A (triage) and Part B (roadmap)
can rely on the design doc having a Security Tooling subsection.

Changes:
- `~/claude-devtools/skills/prototype-driven-planning/references/phase-2-prototype.md` —
  add Security Tooling Validation subsection.
- `~/claude-devtools/skills/prototype-driven-planning/references/design-doc-template.md` —
  add `### Security Tooling` subsection under `## Tooling`.
- `~/claude-devtools/skills/prototype-driven-planning/SKILL.md` —
  Phase 2 Step 2 gains Security Tooling step pointer.

Validation:
- [ ] Re-read the planning skill end-to-end; no internal contradictions
      between phase-2-prototype.md and design-doc-template.md.
- [ ] Dry-run on the health-data-ai-platform's existing Airflow prototype:
      confirm pip-audit, gitleaks, and bandit all run cleanly against
      `prototypes/airflow-google-drive-ingestion/` (or the closest
      analog in the project).

### Step 3: Part A — Planning skill triage.

Changes:
- `~/claude-devtools/skills/prototype-driven-planning/SKILL.md` —
  Phase 3 Step 2 (Open Questions Triage) added; Step 3 is the existing
  final STOP. Principles section gains two entries (no feasibility in
  design doc; prototype immutable only after sign-off).
- `~/claude-devtools/skills/prototype-driven-planning/references/phase-3-design-doc.md` —
  new "Open Questions Triage" section; existing Open Questions paragraph
  rewritten.
- `~/claude-devtools/skills/prototype-driven-planning/references/design-doc-template.md` —
  section renamed Open Questions → Deferred Decisions; intro rewritten.

Validation:
- [ ] Walk through a hypothetical plan for a small feature end-to-end;
      confirm the triage step produces the structured output format;
      confirm the loopback path from Phase 3 → Phase 2 is clear.
- [ ] Confirm no stale references to "Open Questions" remain in the
      planning skill (grep across all its reference docs).

### Step 4: Part B — New roadmap skill.

Create the full directory layout, SKILL.md, reference docs, validator
script, and OWASP mappings. Also create the `/prototype-roadmap`
command doc.

Validation:
- [ ] Run the validator script against a hand-written valid roadmap
      file; confirm exit 0.
- [ ] Run it against intentionally broken roadmap files (missing
      frontmatter, missing Verified-by, bad OWASP ID); confirm exit
      non-zero with line numbers.
- [ ] Dry-run the roadmap skill on the existing
      airflow-google-drive-ingestion design doc: confirm Phase 1
      extracts a reasonable component list with data-flow mappings,
      confirm Phase 2 produces one file per component, confirm Phase 3
      validates cleanly.

### Step 5: End-to-end trial (T15 or next available).

Target: a small new feature added to the health-data-ai-platform, or
re-plan an existing one. Criterion:
- Planning phase 3 ends with zero unresolved feasibility questions in
  the design doc.
- Roadmap skill produces per-component files with BDD scenarios and
  OWASP-cited security scenarios.
- Validator passes on the produced files.

Trial record filed at `~/claude-project-memory/prototype-driven-planning-skill/trials/T<NN>-<slug>.md`;
summary added to `trials/_SUMMARY.md` and `trials/_INDEX.md`.

### Step 6: Memory repo update.

- `README.md` updated to reflect new skill (Skill locations, Commands,
  File Map). Current State gains a section describing this expansion.
- `LEARNINGS.md` gains the two new planning-skill entries listed in §2.3.
- Plan doc (this file) gets a "LANDED" marker at the top once validation
  passes.

### Step 7: Commits.

User commits both repos locally:
```
cd ~/claude-devtools && git add -A && git commit && git push
cd ~/claude-project-memory && git add -A && git commit && git push
```

---

## 7. Out of scope for this expansion

- **Teaching the task-decomposition skill to consume roadmap files.**
  That refactor is a follow-up. The roadmap skill is designed so that
  refactor is clean, but the current decomposer continues to read the
  design doc as today.
- **Automated enforcement of data-flow → OWASP mapping.** The mappings
  are reference tables the model consults. A future skill revision could
  validate that the mappings in produced roadmaps are consistent with
  the reference — but not now.
- **Runtime security (DAST, pentest, fuzzing).** The prototype-validated
  security tooling is limited to static analysis, dep scanning, and
  secrets scanning. Runtime security belongs in implementation-phase
  tooling.
- **Changes to the prototype-driven-implementation skill.** This
  expansion does not touch the pipeline generator. Roadmap files are
  consumed by humans and (eventually) the decomposer; the pipeline
  runtime still reads `tasks.json`.
- **Security scenarios that require cross-component reasoning.** The
  roadmap's security scenarios are scoped to one component's data flow.
  Scenarios that span multiple components (e.g., "user input from
  component A reaches database in component C without component B
  sanitizing it") are not modeled here. Cross-component security is
  design-doc-level and lives in the Security Posture section.

---

## 8. Open questions — resolved

- **Planning skill vs. separate roadmap skill.** Decided: **two skills.**
  Planning closes open questions; roadmap is a separate skill. Reasoning:
  planning's existing 3-phase loop is tuned; adding more phases dilutes
  each phase's discipline. Roadmap has its own schema/validator concern
  and will eventually be consumed by a different downstream skill, so a
  clean boundary pays off. Also matches existing project precedent of
  narrow, single-purpose skills.

- **Roadmap granularity.** Decided: **one file per component.** Each
  component in the design doc's Architecture Overview becomes one
  roadmap file. Maps naturally to eventual per-component task
  decomposition. Alternative (one file per user-visible capability) was
  rejected because capabilities often span multiple components and the
  file would become the wrong unit for downstream consumption.

- **OWASP scope depth.** Decided: **relevant ASVS/MASVS sections only,
  scoped by data flow.** Include only the categories a component's
  actual data flow implicates. Wholesale checklist inclusion creates
  noise; curated short-list hand-wavers what "curated" means. Data-flow
  scoping is mechanical: the mapping reference tells you which
  categories apply to which data-flow kind.

- **Roadmap generation always or opt-in.** Decided: **always required.**
  Part of the standard workflow after design-doc sign-off. The roadmap
  gets skipped only if the feature has no components (impossible under
  the current design-doc template, which requires an Architecture
  Overview). If a feature is genuinely too small for per-component
  decomposition (one component total), the roadmap produces one file;
  the overhead is small.

- **Roadmap schema discipline — how strict.** Decided: **markdown +
  validator script (B1).** Matches the "promote to schema when a real
  bug forces it" rule. The consumer is a model, which reads markdown
  fine; the validator enforces structure. Pydantic upgrade (B2) is
  deferred until a concrete consumer and a concrete bug force it.

- **Security tooling mandatory vs. conditional.** Decided: **dep scan +
  secrets scan always mandatory; SAST conditional on ecosystem.** Both
  always run regardless of feature type. SAST runs when the ecosystem
  has a clear default (Python → bandit, JS/TS → semgrep, Android/JVM →
  detekt); otherwise skipped with explicit reason recorded in the
  design doc's Security Tooling subsection.

---

## 9. Open questions — deferred (not resolved, not blocking)

- **OWASP version revs.** ASVS 5.0 is in draft as of this writing.
  The mapping references pin to 4.0.3. When 5.0 ships, the reference
  docs rev; requirement IDs may renumber. Deferred because it doesn't
  block this expansion and the OWASP rev schedule is out of our control.

- **Roadmap updates after tasks are underway.** If task decomposition
  or implementation reveals that a roadmap scenario was wrong or
  incomplete, what's the update flow? For now: manual edit to the
  roadmap file, re-run validator. No formal change-tracking mechanism.
  May revisit if we see this pattern repeatedly.

- **Multi-feature roadmap aggregation.** Some projects will have
  multiple features with overlapping components. We don't address this
  now; each feature gets its own `docs/roadmap/<feature>/` directory.
  Cross-feature component reuse is a future concern.

---

## 10. Summary

- Planning skill's Phase 3 gains an Open Questions triage step that
  closes feasibility questions (via prototype extension) or decisions
  (via user input) before the design doc is considered final. Section
  renamed to Deferred Decisions with a hard rule: no feasibility
  questions allowed.
- Planning skill's Phase 2 gains a Security Tooling Validation step
  that runs dep scan (always), secrets scan (always), and SAST
  (conditionally by ecosystem) against the prototype. The design doc's
  Tooling section gains a Security Tooling subsection matching the
  existing field structure.
- New sibling skill `prototype-driven-roadmap` consumes the signed-off
  design doc and produces one markdown file per component at
  `docs/roadmap/<feature>/<component>.md`. Each file has BDD Functional
  Scenarios and data-flow-scoped Security Scenarios citing ASVS/MASVS
  requirement IDs. A validator script enforces structural discipline.
- Memory repo's README, LEARNINGS, and trial index updated to reflect
  the new skill and the new planning-phase structure.

Net additions: one new skill, one new Phase 3 step, one new Phase 2
step, one new design-doc template subsection, two new planning-skill
principles. Nothing existing is deleted. The task-decomposition and
implementation skills are not touched.
