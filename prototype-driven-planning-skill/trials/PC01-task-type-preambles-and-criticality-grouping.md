# PC01 — Task-type preambles and criticality-grouped behaviors

**Date:** 2026-05-11
**Target:** prototype-driven-prompt-composition skill
**Project context:** airflow-gdrive-ingestion (regenerated end-to-end; 13
prompts produced; criticality grouping rendered correctly across all
task types)
**Tags:** `task-type-specialized-preamble`, `criticality-grouped-behaviors`,
`verification-form-rendered`, `description-field-removed`,
`structural-signal-rendering`
**Sister trials in arc:** P04 (cliff-edge labeling discipline), R04
(criticality + verification fields), D03 (no-prototype-references +
task-level cliff-edge coverage)
**Result:** Composition script extended with two task-type preambles;
behaviors section grouped by criticality with verification hints;
airflow prompts regenerated cleanly with cliff-edge scenarios
framed front-and-center

---

## Why this iteration

This is the first iteration trial of the prompt-composition skill —
the new `PC` prefix. The skill is the chain's terminal stage: it
consumes `tasks.json` (with cited scenario IDs) and `roadmap.json`
(with the scenario content), and produces one self-contained markdown
prompt per task.

PC01 lands the rendering changes that complete the arc:

- Task-type-specialized preambles (test tasks vs implementation tasks
  see different framing)
- Behaviors section grouped by criticality (cliff_edge → behavioral →
  prescribed) with verification-form hints
- Files section without per-file prose (the dropped `description`
  field from D03)

Without these renderings, R04's criticality and verification fields
would arrive at the executor without framing — the cliff-edge tier
would render identically to behavioral, and the executor would have
no signal that cliff edges are non-negotiable.

The session-status-2026-05-11 plan called for two prompt files per
task (`task-NN-tests.md` + `task-NN-impl.md`). On reading the existing
schema, the test/impl split is already encoded as `task_type`, and
the task chain produces test tasks and implementation tasks as
separate `tasks.json` entries. Splitting each task into two prompts
would have been redundant; one prompt per task with task-type-derived
preamble achieves the same outcome with less artifact duplication.
The plan was adjusted to one prompt per task during this iteration.

## What changed

### Script — `scripts/compose_prompts.py`

Six functional changes:

- **Two preamble filenames**. `_PREAMBLE_FILENAME` (single) replaced
  with `_PREAMBLE_TEST_FILENAME = "../references/preamble-test.md"`
  and `_PREAMBLE_IMPL_FILENAME = "../references/preamble-impl.md"`.

- **`_load_preamble(skill_dir, filename)`** refactored to take a
  filename parameter. Same parsing rule (start of prose at the first
  bare-line `# Role` heading); same error handling. The function
  loads either preamble cleanly.

- **`_load_preambles(skill_dir)` added**. Returns a dict
  `{"test": <prose>, "implementation": <prose>}`. Loads both files
  once at startup so per-task dispatch is a dict lookup.

- **`_format_functional_scenario` / `_format_security_scenario`
  updated**. Each scenario block now includes a `**Verification form**`
  line rendering the new `verification` field from R04 (e.g.,
  `unit_test`, `tool_invocation`). Security scenarios continue to
  carry `OWASP requirement` and `Performed by` lines that distinguish
  them from functional.

- **`_inline_roadmap_scenarios` restructured to group by criticality**.
  Cited scenarios are bucketed into three lists keyed by
  criticality (`cliff_edge`, `behavioral`, `prescribed`). Each
  non-empty bucket becomes a subsection in the rendered output with
  a descriptive header:
  - "Cliff edges (non-negotiable boundaries — alternatives break
    loudly with documented failure modes)"
  - "Behavioral contract (proven path from prototype)"
  - "Prescribed (security or production additions; not in prototype)"

  Within each bucket, functional scenarios appear first (in citation
  order from `task.roadmap_functional_scenarios`), then security
  scenarios (in citation order from `task.roadmap_security_scenarios`).
  Subsections are omitted when empty. The functional/security
  distinction is preserved via the per-scenario render shape (OWASP
  fields on security scenarios) rather than as a top-level grouping
  key.

- **`_format_files_section` updated**. The `description` field was
  dropped from `FileChange` in D03; this function now renders only
  path, operation, and (for stub files) a `; stub` suffix:
  `- **`<path>`** (<operation>)` or `- **`<path>`** (<operation>; stub)`.

- **`_build_prompt` updated**. Takes `preambles: dict[str, str]` (was
  single `preamble: str`). Dispatches on `task.task_type.value` to
  pick the test or implementation preamble. Fails loudly with a
  clear error if a task carries an unexpected `task_type` value.

### Reference files

Two new preamble files; one tombstoned; three reference docs updated.

- **`references/preamble-test.md`** — new file. Task-type-specialized
  for `task_type: "test"` tasks. Sections:
  - Role (writing tests + stub; paired implementation task fills in)
  - Test writing rules (real assertions, mock framework, single
    test class per source class, no assertions on details not in
    spec)
  - **Criticality framing for cited scenarios** (new): how to write
    tests for cliff_edge scenarios (verify both sides of the
    boundary), behavioral scenarios (verify the proven path),
    prescribed scenarios (verify the prescription)
  - **Verification field hints** (new): mapping the four verification
    forms to test forms (unit_test → pytest function with mocks;
    integration_test → pytest function with real services;
    tool_invocation → run a tool, assert exit code/output;
    static_assertion → grep/regex/AST check)
  - Stub writing rules (smallest file that makes tests importable;
    declarative parts stay declarative; import third-party symbols
    at module boundary for mock paths)
  - Coding conventions (line length, string-literal extraction,
    type annotations)
  - Output format (file changes only, no prose)

- **`references/preamble-impl.md`** — new file. Task-type-specialized
  for `task_type: "implementation"` tasks. Sections:
  - Role (make tests pass; for scaffold/infra, create project files
    such that tool-invocation scenarios pass)
  - Implementation rules (make tests pass *without modifying them*;
    read cited dependency files; match stub signatures exactly;
    implement only what the task scopes)
  - **Criticality framing for cited scenarios** (load-bearing): how
    to treat each tier — cliff_edge boundaries are non-negotiable
    ("change the code, not the test"; "if you find yourself
    considering whether to relax the test, that is the cliff edge
    reasserting itself"); behavioral scenarios are the proven path;
    prescribed scenarios verify design-doc additions
  - Stub-replacement rules (for test/impl pair tasks: preserve
    interface, preserve third-party imports, replace NotImplementedError
    bodies)
  - Scaffold and infrastructure tasks (for tasks without paired
    tests: create files such that cited tool-invocation scenarios
    pass; structure dictated by tool format and cliff-edge/prescribed
    scenarios; follow Interface section when it conflicts with
    general practice)
  - Coding conventions (same as test preamble)
  - Output format (same as test preamble)

- **`references/preamble.md`** — tombstoned. Filesystem MCP cannot
  delete files, so the file was overwritten with a TOMBSTONE marker
  asking the user to delete manually. The composition script no
  longer reads this file.

- **`references/prompt-template.md`** — substantial updates:
  - Section-order header updated to reference the two preamble files
    instead of the single `preamble.md`
  - Universal preamble section rewritten to document the task-type
    split with rationale
  - Files section docs updated for path/operation/stub-only (no
    description)
  - Behaviors section rewritten to document criticality-first
    grouping with all three subsection labels, the within-subsection
    order rule (functional first, then security), and the
    verification-form line
  - "What's NOT in the template" list extended (added entry on
    dropped per-file description; added entry on dropped mixed
    scenario-kind grouping)
  - Example skeleton updated to show a criticality-grouped scenario
    block with verification-form lines

- **`SKILL.md`** — Reference Files section updated (two preambles
  listed); Principles updated ("Task-type-specialized preamble"
  replaces "Universal preamble, no project block").

- **`references/dependency-handling.md`** — no changes. The
  path-only dependency rendering was already correct and didn't
  conflict with the arc's design.

- **`references/log-conventions.md`** — no changes.

## Regeneration against airflow-gdrive-ingestion

Prompts regenerated end-to-end after D03's tasks.json validation
passed. Phase 3 validation produced 13 prompts (one per task).

### Preamble dispatch — correct across all task types

Verified by inspecting four representative prompts:

| Task | task_type | Preamble used |
|---|---|---|
| task-01 (scaffold) | implementation | preamble-impl ✓ |
| task-02 (infra) | implementation | preamble-impl ✓ |
| task-03 (test task for drive-downloader) | test | preamble-test ✓ |
| task-04 (impl for drive-downloader) | implementation | preamble-impl ✓ |

The script's `task_type.value`-based dispatch worked uniformly.

### Criticality grouping — correct subsection placement

Verified by inspecting four prompts:

- **task-01**: Cliff edges section absent (no cliff edges cited);
  Behavioral subsection has 1 scenario (`ruff-passes-clean`);
  Prescribed subsection has 1 (`service-account-key-not-in-source`).
  Empty subsections correctly omitted.

- **task-02**: Cliff edges subsection has 2 scenarios
  (`airflow-init-single-line-bash`, `dockerfile-runs-as-airflow-user`);
  Behavioral has 1 (`docker-healthchecks-gate-startup`); Prescribed
  has 1 (`pip-audit-targets-installed-packages`). All three
  subsections rendered.

- **task-03** (test task): Cliff edges has 1
  (`key-path-and-scope-required`); Behavioral has 3 (including
  `drive-api-uses-tls` security scenario — correctly grouped by
  criticality, not by kind); Prescribed has 1
  (`tempfile-restrictive-permissions`).

- **task-04** (impl task for the same component): Cliff edges has 2
  (`key-path-and-scope-required`, `tempfile-not-hardcoded-tmp`);
  Behavioral has 3; Prescribed has 2.

Within each subsection, functional scenarios appear first, then
security scenarios. OWASP/performed_by fields render correctly on
security scenarios. Evidence-kind line renders only when
`evidence_kind == "prescribed"`.

### Verification form rendered consistently

Every scenario carries a `**Verification form**: `<value>`` line.
Spot-checked values match the upstream `verified_by` artifact in
expected ways:
- Pytest paths → `unit_test` or `integration_test`
- Shell commands (ruff, bandit, gitleaks, docker compose) →
  `tool_invocation`
- Grep/AST checks → `static_assertion`

### Files section clean

No `description` field anywhere in any prompt's Files section.
Stub markers (`; stub`) render correctly for files where
`stub == True`.

## One small content note worth recording

The cliff-edge scenario `key-path-and-scope-required` (cited by
task-03 and task-04) declares `verification: integration_test` —
the strict "verify both failure modes" framing of the preamble
implies an integration test against real Drive credentials.
However, the rest of the test suite mocks `GoogleDriveHook`. A
reasonable executor will write a unit test that asserts the
connection URI is configured correctly, even though the strict
verification form can't fully be done as a unit test mock. The
preamble's "If two reasonable forms exist for a scenario, pick the
one matching the scenario's `verified_by` field" gives flexibility.

This is a content issue, not a prompt-composition bug. Noted here
so future planning iterations can consider whether `verified_by`
fields for cliff edges should always cite an actual test that
exercises the boundary, rather than the prototype's working
configuration.

## Failure modes addressed

The arc's central goal — reducing the contradiction surface that
caused the session-status-2026-05-10 update-3 failure — is met at
the prompt-composition layer in two ways:

1. **Criticality grouping puts cliff edges front-and-center**. An
   executor reading task-03's prompt sees the `key-path-and-scope-required`
   cliff-edge scenario *first* under a subsection header that names
   it as non-negotiable. The preamble reinforces this framing with
   explicit "change the code, not the test" instructions. This
   makes it structurally harder for the executor to drift away from
   the cliff edge in the way that produced the original three-executor
   failure.

2. **No per-file prose, no prototype references**. The prompt's
   Files section lists paths only; the executor has nothing to
   "mirror exactly" except the explicit interface in the task-level
   description. The contradiction surface — "mirror prototype" vs
   "include X prototype doesn't have" — does not exist in the new
   prompt format.

The arc's structural enforcement chain is now end-to-end:

```
prototype README breadcrumb
  → design doc **Cliff edge:** label                   (P04)
  → roadmap scenario with criticality=cliff_edge       (R04, validated by R04)
  → task citing that scenario                          (D03, validated by D03)
  → prompt subsection framing the scenario as          (PC01)
    non-negotiable with verification hint
```

Each step's validator ensures the previous step's signal survives.
No layer can silently drop a cliff edge.

## Key findings

1. **One prompt per task, task-type-specialized preamble, was the
   right design**. The session-status plan called for two files per
   task (`tests.md` + `impl.md`). Reviewing the schema during this
   iteration showed the test/impl split is already encoded as
   `task_type`, and the decomposition produces test and
   implementation tasks as separate `tasks.json` entries. Two files
   per task would have doubled the artifact count for no structural
   gain. One file per task with type-dispatched preamble achieves
   the same outcome: test tasks see test-writing rules and stub
   rules; implementation tasks see "make tests pass" rules and
   cliff-edge non-negotiability framing.

2. **Criticality grouping at the prompt layer is the load-bearing
   render**. Without it, all scenarios would render identically and
   the criticality field would be invisible to the executor. The
   subsection headers ("Cliff edges (non-negotiable boundaries —
   alternatives break loudly with documented failure modes)") carry
   meaningful instructional load: an executor scanning the prompt
   sees the framing before reading the individual scenario blocks.
   This is the rendering form that turns R04's typed criticality
   field into executable executor framing.

3. **Functional/security distinction stays visible per-scenario, not
   as a top-level group**. The pre-arc design grouped scenarios as
   "Functional behaviors" vs "Security behaviors" at the top
   subsection level. PC01 moved to criticality-first grouping.
   Functional vs security distinction is preserved via per-scenario
   render shape (security scenarios carry OWASP requirement and
   performed-by lines). This is the right division: criticality
   drives instruction framing; OWASP source drives the verification
   approach.

4. **Verification form as scenario-level hint, not subsection
   header**. The four verification forms (`unit_test`,
   `integration_test`, `tool_invocation`, `static_assertion`) appear
   as a per-scenario line rather than a grouping key. A single task
   may cite cliff-edge scenarios with `tool_invocation` verification
   (validated by docker compose) *and* `unit_test` verification
   (validated by pytest mocks). The shared criticality groups them;
   the per-scenario verification form tells the executor what shape
   each test should take.

5. **The deterministic-script principle held**. The pre-arc design
   already established that prompt composition is a deterministic
   Python script with byte-identical output for byte-identical
   inputs. PC01's changes preserve this: same `tasks.json` +
   `roadmap.json` + preamble files produce same prompts. The snapshot
   test in `tests/expected/` (not yet regenerated in this iteration
   — to be done before re-running the script for validation) will
   capture the new expected output.

6. **Tombstoning for manual deletion is the right pattern when MCP
   can't delete**. The `preamble.md` file is no longer used but
   Filesystem MCP cannot delete files. Writing a TOMBSTONE marker
   into the file (with a clear "please delete this file manually"
   instruction) preserves the change intent in the git history while
   letting the user execute the cleanup. Same convention as prior
   tombstoned skill files in the project.

## Related plan documents

- `session-status-2026-05-11-cliff-edges-and-two-prompt-split.md` —
  arc-level plan
- P04 trial record — upstream design-doc labeling discipline
- R04 trial record — upstream roadmap criticality + verification
  fields with cross-file coverage check
- D03 trial record — task-level cliff-edge coverage + no-prototype-
  references + relaxed scaffold citation

## Skill change summary

- `scripts/compose_prompts.py`:
  - Two preamble filename constants (`_PREAMBLE_TEST_FILENAME`,
    `_PREAMBLE_IMPL_FILENAME`)
  - `_load_preamble` refactored to take a filename parameter
  - `_load_preambles` added, returns dict keyed by task_type value
  - `_format_functional_scenario` / `_format_security_scenario`
    add `**Verification form**` line
  - `_inline_roadmap_scenarios` restructured to group by criticality
    (three subsections, omitted when empty)
  - `_format_files_section` updated for path/operation/stub-only
  - `_build_prompt` takes `preambles` dict, dispatches by
    `task_type.value`
- `references/preamble-test.md`: new file (test-task preamble)
- `references/preamble-impl.md`: new file (implementation-task
  preamble)
- `references/preamble.md`: tombstoned (manual deletion required)
- `references/prompt-template.md`: section-order header, universal
  preamble section, files section, behaviors section, "what's NOT"
  list, example skeleton all updated
- `SKILL.md`: Reference Files section updated; "Task-type-specialized
  preamble" principle replaces "Universal preamble, no project
  block"
