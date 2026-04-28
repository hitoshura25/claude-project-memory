# Plan — Add Project Setup Decision and Component to the Planning Skill

> **Status:** Proposal. Not yet implemented. Pick up from this file in a fresh
> session if needed. Re-read the current state pointers in §1 before touching
> any skill file.
>
> **Created:** 2026-04-27 (after R02 validated the roadmap-skill fixes from
> R01, while drafting the decomposition-roadmap refactor).
>
> **Sequencing:** Surfaced *during* the decomposition-roadmap refactor work
> (`decomposition-roadmap-refactor-plan-2026-04-26.md`). Project-setup work
> goes upstream of that refactor — without it, the decomposition refactor
> requires special-casing scaffold tasks. With it, scaffold tasks reference
> a real registered slug like any other component.
>
> **Trial code:** P05 (planning skill, fifth iteration trial — first run
> after this plan lands).

---

## 1. Where to read in (do this first)

A fresh session must load these before proposing edits.

**Memory repo (always loaded at session start):**

- `~/claude-project-memory/prototype-driven-planning-skill/README.md`
- `~/claude-project-memory/prototype-driven-planning-skill/LEARNINGS.md`
- `~/claude-project-memory/prototype-driven-planning-skill/trials/_SUMMARY.md`

**Memory repo (on demand for this work):**

- `~/claude-project-memory/prototype-driven-planning-skill/trials/R01-roadmap-id-parity-and-actor-misplacement.md`
- `~/claude-project-memory/prototype-driven-planning-skill/decomposition-roadmap-refactor-plan-2026-04-26.md`
  (the downstream plan this work clears the path for)

**Planning skill — full file reads required:**

- `~/claude-devtools/skills/prototype-driven-planning/SKILL.md`
- `~/claude-devtools/skills/prototype-driven-planning/references/phase-1-discovery.md`
- `~/claude-devtools/skills/prototype-driven-planning/references/phase-3-design-doc.md`
- `~/claude-devtools/skills/prototype-driven-planning/references/design-doc-template.md`

**Planning skill — read for context (not edited in this work):**

- `~/claude-devtools/skills/prototype-driven-planning/references/phase-2-prototype.md`

**Existing design doc (treat as canonical example of what must be regenerated):**

- `~/health-data-ai-platform/docs/design/airflow-gdrive-ingestion-2026-04-24.md`

**Roadmap skill (for understanding downstream contract — not edited):**

- `~/claude-devtools/skills/prototype-driven-roadmap/SKILL.md`
- `~/health-data-ai-platform/docs/roadmap/airflow-gdrive-ingestion/components.yml`
  (R02 output — current state of the registry)

---

## 2. Why this work

The decomposition-roadmap refactor (`decomposition-roadmap-refactor-plan-
2026-04-26.md`) introduces a required `roadmap_component` field on every
task. The plan acknowledged a pain point in §9.1: scaffold tasks have no
natural component to belong to. The plan's mitigation was "force the choice
to the orchestrator component for D01 and accept the awkwardness, escalate
later if needed."

Pulling on that thread surfaced a deeper omission: **scaffold concerns
have all the structural properties of a component** — Gherkin'able
behaviors, OWASP categories (V14.x build process and dependency management),
real failure modes (broken conftest blocks every later test task, T14
task-16's `services.compose.yml` gap), real position in the dependency
graph (root) — but the planning skill never produces them as components.
This is because the planning skill's `### Components` section captures
runtime/architectural components only.

Project setup is also **conditional**. Features that extend an existing
service inherit project setup from the parent — they have no scaffold
work to do, no scaffold component to enumerate. Features that create a
new service have all of it.

Adding a project-setup decision to Phase 1 makes this binary visible at
the right moment (before the prototype is built, where the user can
override) and produces a Project Setup component in the design doc when
greenfield. Downstream skills then handle scaffold work the same way they
handle any other component.

The cross-cutting pattern this matches: **force the model's reasoning into
a visible, machine-checkable artifact.** Same shape as Performed-by
(roadmap), test_command (decomposition), Surface Coverage Check (planning
P02). The decision is "is this greenfield or extending?" and it surfaces
in the Phase 1 proposal as a labeled answer the user reviews.

---

## 3. The decision rule

Phase 1 gains a step (1.5) determining greenfield vs. extending status.

A feature is **greenfield project setup** when *any* of the following are
true:

- The feature creates a new service directory with its own dependency
  manifest (a new `pyproject.toml`, `package.json`, `Cargo.toml`,
  `build.gradle`, etc.).
- The feature requires a new container image not derived from extending
  an existing one (a new `Dockerfile`).
- The feature requires new test infrastructure (`conftest.py`,
  `jest.config.*`, `pytest.ini`) that doesn't currently exist for the
  service.
- The feature requires a new lint configuration distinct from the parent
  project's.
- The feature requires new local-services orchestration (a new
  `docker-compose.yml` or equivalent declaring services not currently
  orchestrated).

A feature is **extending existing setup** when none of the above are true
— it adds files inside a service whose `pyproject.toml`, Dockerfile,
conftest, lint config, and (where applicable) services compose are
already in place and continue to apply.

### Edge cases

- **New service inside a monorepo:** **greenfield** for the new service,
  even if the monorepo's top-level setup is reused. The new service has
  its own `pyproject.toml` etc.
- **New tooling added to existing service** (e.g., adding `pytest-bdd`
  alongside the existing pytest): **extending** for project-setup
  purposes. The new tool gets recorded under `## Tooling` rather than
  triggering a Project Setup component.
- **New Dockerfile reusing everything else** (e.g., adding a sidecar
  container to an existing service): **greenfield**. The new Dockerfile
  carries its own scaffold concerns even when the surrounding service
  setup is reused.

### How the decision surfaces

The Phase 1 proposal template gains a labeled answer near the top:

```
**Project setup**: Greenfield — new service at services/<n>/
                 | Extending — services/<n>/ already exists with
                   pyproject.toml, Dockerfile, conftest
```

Surfacing as a labeled answer (not a buried table cell) gives the user a
clear chance to override at the Phase 1 STOP, before any prototype is
built.

### Why no flag in the design doc prelude

Considered: a one-line metadata flag like `> Project setup: greenfield`
in the prelude. **Rejected.** The presence or absence of a Project Setup
entry in `### Components` is itself the signal. Adding a flag would
duplicate the answer in two places — the same drift class the planning
skill's own discipline rejects. Downstream skills detect status by
checking whether `### Components` includes a Project Setup entry.

---

## 4. Phase 1 changes

### 4.1 New step in `phase-1-discovery.md`

Insert a "Step 1.5: Determine project-setup status" section between the
current Step 1 (Project Inventory) and Step 2 (Identify integration
boundaries).

The new section:

- States the decision question.
- Lists the five greenfield triggers (matching §3 above).
- Lists the extending criterion.
- Lists the three edge cases (matching §3 above).
- Notes that the decision surfaces in the Phase 1 proposal as a labeled
  answer.

### 4.2 Phase 1 proposal template gains a Project setup line

The current template at the bottom of `phase-1-discovery.md` becomes:

```
## Prototype Proposal: <feature-name>

**Project setup**: <Greenfield: new service at <path> | Extending: <path>
already exists with pyproject.toml, Dockerfile, conftest>

**Integration boundaries identified**:

| Boundary | Category | In prototype? |
|---|---|---|
| ... | ... | ... |

**Core risk being tested**: ...

[rest unchanged]
```

The Project setup line goes first — it's the project-context decision the
rest of the proposal is shaped by.

### 4.3 SKILL.md Phase 1 step list

The current SKILL.md Phase 1 step list:

```
1. Inventory the project.
2. Map integration boundaries.
3. Categorize each boundary.
4. Research.
5. Propose the prototype scope.
```

Becomes:

```
1. Inventory the project.
2. Determine project-setup status. Greenfield (new service infrastructure
   needed) or extending (inherits existing setup). See
   `references/phase-1-discovery.md` § "Step 1.5: Determine project-setup
   status" for the full rule and edge cases.
3. Map integration boundaries.
4. Categorize each boundary.
5. Research.
6. Propose the prototype scope. Include the project-setup status as a
   labeled answer at the top of the proposal.
```

### 4.4 No Phase 2 changes

Phase 2's existing toolchain validation (Step 2 in `phase-2-prototype.md`)
already validates the Project Setup component for greenfield features:
`uv sync` runs, lint runs clean, tests run, Dockerfile builds, security
tooling runs. The prototype's `pyproject.toml`, `Dockerfile`,
`tests/conftest.py`, and lint configs become the prototype-evidence for
the design doc's Project Setup component.

For extending features, the same validation runs but inherits — the
commands are the existing project's. No new component is generated; the
Tooling section records the inherited commands.

This work explicitly does not touch Phase 2.

---

## 5. Phase 3 / design doc template changes

### 5.1 New rule in `phase-3-design-doc.md`

Add a "Project Setup component rule" subsection under the section-by-
section guidance, near the Architecture Overview entry:

> **Project Setup component rule.** If Phase 1 declared this feature
> greenfield, the design doc's `### Components` section must include a
> Project Setup entry as the *first* component. The entry's responsibility,
> prototype evidence, and production considerations are derived from
> Phase 2's toolchain validation outputs (the `## Tooling` section) and
> the prototype's actual setup files. If Phase 1 declared this feature
> extending, the design doc must NOT include a Project Setup entry, and
> the absence is the signal to downstream skills that no scaffold work
> exists.

### 5.2 Position of Project Setup in `### Components`

**First.** This matches:

- **Implementation order.** Project setup is the foundation everything
  depends on; the first task a developer (or pipeline) executes.
- **Dependency graph order.** Project Setup is always a root when
  present; runtime components depend on it.
- **The roadmap skill's existing Phase 1 message ordering** (roots-first
  in the dependency graph display).

Reading order convention follows implementation order, consistent end-
to-end through planning → roadmap → decomposition.

### 5.3 Project Setup component template

Add to `design-doc-template.md` an example Project Setup entry that
appears in `### Components` when greenfield. Template content:

```markdown
**Project Setup**
- **Responsibility**: Establishes the service's build, test, and runtime
  infrastructure: dependency manifest with pinned versions, container
  image, test framework configuration, lint configuration, and (where
  applicable) local-services orchestration.
- **Prototype evidence**: `prototypes/<feature>/<dependency-manifest>`,
  `prototypes/<feature>/Dockerfile` (if applicable),
  `prototypes/<feature>/tests/conftest.py`,
  `prototypes/<feature>/<lint-config>`,
  `prototypes/<feature>/<services-compose>` (if applicable).
- **Production considerations**:
  - All third-party dependencies pinned to specific versions; the build
    process is deterministic.
  - Container base image pinned to a specific tag with security-patched
    dependencies (note any specific CVE clusters resolved by the chosen
    version, as Phase 2's tooling validation surfaced).
  - Test infrastructure passes the framework's empty-collection check
    against an empty test directory (validates conftest, fixtures,
    plugin loading).
  - Lint configuration applies cleanly to the prototype's source files.
  - (When applicable) Local-services compose declares healthchecks for
    every service so integration tests can wait on readiness.
```

The exact wording adapts per feature; the template is a starting point.
The design doc's existing prose-grounded-in-prototype-evidence pattern
still applies — the production considerations are observations from
Phase 2, not boilerplate.

### 5.4 Note added to the existing Tooling section

Add a sentence to the existing `## Tooling` section description in
`design-doc-template.md`:

> When the design doc includes a Project Setup component (greenfield
> features), the Tooling section's commands are the structured-for-
> machine-consumption form of what the Project Setup component
> describes narratively. The two views must agree; the Tooling fields
> are the source of truth for downstream pipelines.

### 5.5 No changes to existing runtime component templates

The runtime component template in `design-doc-template.md` is
unchanged. Project Setup is an additional component type with the same
shape (Responsibility / Prototype evidence / Production considerations).

### 5.6 No new principle in SKILL.md

Considered adding a Principle: "Greenfield features carry a Project
Setup component; extending features explicitly declare they inherit
existing setup." **Decided against.** The principle already follows
from existing principles ("Observe, don't predict" and "Tables are
starting points, not terminuses"). Adding a redundant principle
overcomplicates the SKILL.md principles section, which is already
dense.

The rule lives in `phase-3-design-doc.md` § "Project Setup component
rule" and the SKILL.md Phase 1 step list. That's two places, both
load-bearing, no redundancy.

---

## 6. What this enables downstream

### 6.1 Roadmap skill (no changes expected; user verifies via R03)

When the design doc's `### Components` includes Project Setup, the
roadmap skill's existing logic produces a `project-setup.md` file with:

- **Functional Scenarios** — derived from Phase 2's toolchain validation
  observations. Examples: "Given a fresh checkout, when `uv sync` runs,
  then dependencies install at pinned versions." "Given an empty `tests/`
  directory, when `pytest --collect-only` runs, then it succeeds with
  exit 5 (no-tests-collected) or 0."
- **Security Scenarios** — ASVS V14.1.1 (Build Process), V14.2.1
  (Dependency Management), V14.3.x (Configuration), depending on what's
  actually present in the prototype.
- **Dependencies** — `[]` (Project Setup is the root of the graph).
- **Out of Scope** — references to runtime components that consume the
  setup ("Dockerfile contents specific to the orchestrator are owned by
  `airflow-dag`," etc.).

The roadmap skill's `references/owasp-asvs-mapping.md` may need a small
addition to ensure V14.x categories are well-covered. **This is a
verification step we run after R03** (the next roadmap-skill trial),
not pre-emptive work. If R03 surfaces a gap, fix it then.

When extending, no Project Setup component → no `project-setup.md` file.
Roadmap skill behaves identically to today.

### 6.2 Decomposition-roadmap refactor (the original target)

The plan's §9.1 ("scaffold awkwardness") goes away. Scaffold tasks get
`roadmap_component: "project-setup"`, the validator confirms
`project-setup` is registered in `components.yml` like any other slug,
no special cases.

For extending features, scaffold tasks don't exist (the project is
already set up). The decomposer doesn't generate them, the schema
validates the same way for every task.

The decomposition refactor plan (`decomposition-roadmap-refactor-plan-
2026-04-26.md`) needs a small revision after this work lands:
§9.1 ("Risk: roadmap-component placement awkward for cross-cutting
tasks") becomes "resolved upstream — `project-setup` is now a real
component when greenfield." That revision is the very last step of this
work (before D01 is run).

---

## 7. Risks and how to handle them

### 7.1 Risk: false greenfield-vs-extending classification

**Symptom:** A feature that should be classified as extending (small
addition to an existing service) gets classified as greenfield, generating
a Project Setup component for setup that already exists. Or the reverse —
a feature that needs new scaffold gets classified as extending, missing
the Project Setup component.

**Mitigation:** The decision surfaces in the Phase 1 proposal as an
explicit labeled answer. The user reviews and overrides at the Phase 1
STOP, before any prototype is built. The cost of a wrong classification
is bounded — at worst, the user corrects it before Phase 2 starts. No
silent default.

### 7.2 Risk: edge cases not covered by the rule

**Symptom:** A feature comes up that doesn't cleanly match any of the
three edge cases in §3 ("New service in monorepo," "New tooling added
to existing service," "New Dockerfile reusing everything else").

**Mitigation:** The decision is binary — greenfield or extending — and
the user reviews the proposal. If the rule doesn't cover the case, the
user adjusts at the Phase 1 STOP and the next-iteration update to this
plan can codify the edge case. Don't pre-build edge cases that haven't
appeared.

### 7.3 Risk: design doc gets noisy with Project Setup boilerplate

**Symptom:** Every greenfield design doc carries a Project Setup
component with similar-looking content (pinned deps, deterministic
builds, healthchecks, lint passes).

**Mitigation:** Acceptable. The boilerplate isn't *meaningless* — it
documents that the prototype validated these properties for *this*
feature's stack. The OWASP V14.x categories that flow downstream need a
place to live; without Project Setup as a component, they'd float
homeless.

The redundancy across features is the right shape — every greenfield
project has these concerns and they should be visible. If review fatigue
becomes a real problem, the response is to factor common production-
considerations into a named-pattern reference doc that the design doc
cites. That's a future iteration if needed.

### 7.4 Risk: regenerating the airflow-gdrive design doc loses content

**Symptom:** Re-running the planning skill on the airflow-gdrive feature
to add the Project Setup component produces a doc that's structurally
similar but loses some of the existing content (the careful Judgment-vs-
Observation labeling, the Mitigation Ladder records, etc.).

**Mitigation:** Two options:

- **Re-run the full planning skill on the existing prototype.** The
  prototype is unchanged; the skill should reproduce the same content for
  the four runtime components. The Project Setup component is *added* to
  what the skill would otherwise produce.
- **Manually amend the existing design doc.** Add the Project Setup
  component to `### Components`, update the prelude if needed, leave the
  rest unchanged. Cheaper, lower regression risk.

Decision deferred to the user — the user runs the planning skill (P05)
and chooses. The README's Next Steps will list both options.

### 7.5 Risk: the airflow-gdrive prototype doesn't actually validate
some of the V14.x security categories

**Symptom:** The Project Setup component template in §5.3 mentions ASVS
V14.x security scenarios. If the airflow-gdrive prototype's Phase 2 didn't
actually validate (e.g.) a specific dependency-pinning property, the
generated security scenario for V14.x would be speculation — the
labeling rule from `phase-3-design-doc.md` § "Judgment vs. Observation"
would flag it.

**Mitigation:** This is acceptable behavior. If Phase 2 didn't validate
something, the design doc labels it ("Prescribed (not validated)" or
"Not observed") per the existing rules. Project Setup follows the same
labeling discipline as runtime components — observations cite evidence,
prescriptions are labeled. The skill's existing rules already handle
this correctly.

---

## 8. Implementation order

A fresh session does this work in this sequence so each step is
reviewable in isolation.

1. **Update `phase-1-discovery.md`.** Add Step 1.5 (project-setup
   decision) and update the proposal template (per §4.1, §4.2).
2. **Update `phase-3-design-doc.md`.** Add the Project Setup component
   rule (per §5.1).
3. **Update `design-doc-template.md`.** Add the Project Setup component
   template to `### Components` and the note to `## Tooling` (per §5.3,
   §5.4).
4. **Update `SKILL.md`.** Phase 1 step list gains the project-setup
   decision (per §4.3).
5. **Memory repo updates.** Update README's Current State to note this
   work landed; update Next Steps to list P05 trial; update
   `LEARNINGS.md` "From Planning Skill" with the project-setup design
   choice; rev the decomposition-roadmap refactor plan to reference the
   cleaner upstream sequence (§9.1 mitigation note).
6. **(Manual)** User commits and pushes both repos.
7. **(Next session)** User runs the planning skill (P05 trial) on the
   airflow-gdrive feature to regenerate or amend the design doc with the
   Project Setup component. Trial record at
   `~/claude-project-memory/prototype-driven-planning-skill/trials/
   P05-project-setup-component.md` (placeholder created in step 5;
   filled in after the trial).
8. **(Next session)** User runs the roadmap skill (R03 trial) against
   the amended design doc to generate `project-setup.md` and update
   `components.yml`. Trial record at `trials/R03-project-setup-rollup.md`.
9. **(Next session)** Resume the decomposition refactor (the
   `decomposition-roadmap-refactor-plan-2026-04-26.md`), now with
   `project-setup` as a real registered slug.

---

## 9. What this plan deliberately doesn't change

- **Phase 2 of the planning skill.** The existing toolchain validation
  already validates project setup for greenfield features. No new
  validation work needed.
- **Security tooling rules.** Severity-indexed handling, Mitigation
  Ladder, Environmental Risk Assessment all continue to apply.
- **The roadmap skill.** R03 will tell us if anything's needed; betting
  it isn't.
- **The existing `## Tooling` section structure.** Continues to record
  lint/test/security commands. Project Setup component is a *narrative*
  addition; the structured Tooling fields are unchanged.
- **Existing `### Components` for runtime components.** Untouched.
- **The prelude/metadata block format.** No project-setup flag added —
  presence/absence of the Project Setup component is the signal.
- **Phase 2 ↔ Phase 3 loopback discipline.** Existing rule (prototype
  immutable after sign-off) applies unchanged.

---

## 10. Acceptance bar for P05

After this work lands and the user re-runs the planning skill against
airflow-gdrive (or another feature), the trial passes when:

- Phase 1 proposal includes a labeled "Project setup" line at the top.
- The user (or the skill, when greenfield is unambiguous) declares the
  status before Phase 2 begins.
- Phase 3 design doc, when greenfield, includes a Project Setup
  component as the first entry in `### Components`. When extending,
  no Project Setup component appears, and the absence is consistent
  with Phase 1's declaration.
- The Project Setup component's Production considerations cite specific
  prototype evidence for every claim, following the existing Judgment-
  vs-Observation rules. No unbacked claims.
- Existing rules (Open Questions Triage, Scope-Removal Triage,
  Mitigation Ladder, etc.) continue to fire correctly. This work
  doesn't regress any of them.
- The amended design doc is readable end-to-end; the new component
  doesn't disrupt the narrative flow of the runtime components.

If the trial run reveals any of these criteria fail, the fix goes into
this plan's §11 ("Open items for the next iteration") and a same-day
P06 follow-up.
