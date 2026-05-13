# D03 — No-prototype-references; cliff-edge coverage; relaxed scaffold citation

**Date:** 2026-05-11
**Target:** prototype-driven-task-decomposition skill
**Project context:** airflow-gdrive-ingestion (regenerated twice; first pass
exposed scaffold coverage gap; second pass clean sweep after rule relaxation)
**Tags:** `prototype-decomposer-only`, `cliff-edge-coverage-at-task-layer`,
`relaxed-scaffold-citation`, `schema-field-removal`, `structural-signal-chain`
**Sister trials in arc:** P04 (cliff-edge labeling discipline), R04
(criticality + verification fields), PC01 (task-type preambles +
criticality grouping)
**Result:** Schema's `FileChange.description` dropped; prototype
references removed from task content; cliff-edge coverage validator
added; scaffold citation rule relaxed; airflow decomposition
regenerated with 4 cliff-edge scenarios cited and full prototype-free
task content

---

## Why this iteration

D03 is the middle of the arc. P04 introduced cliff-edge labels in
the design doc; R04 turned them into criticality-tagged scenarios in
the roadmap. D03 makes sure those scenarios are *cited* by tasks and
that the decomposition itself no longer carries the failure surface
that triggered the arc.

Three coupled changes:

1. **Drop `FileChange.description` from the schema.** The
   session-status-2026-05-10 update-3 diagnosis identified per-file
   prose as the surface where decomposition restated content
   (already in the task-level description, already in cited
   scenarios) and the restatement introduced contradictions that no
   executor resolved consistently. Removing the field eliminates the
   surface entirely.

2. **Remove all prototype references from task content.** During
   discussion this iteration, we considered three options for the
   prototype's relationship to tasks: (A) inline snippets (the
   pre-arc behavior — caused drift), (B) path-only references (gives
   the executor a path it cannot use, since the implementation
   pipeline doesn't surface the prototype to executors), (C) drop
   prototype references entirely (decomposer reads the prototype
   during planning; tasks don't reference it). C was chosen: the
   roadmap's now-richer scenarios (with criticality, verification,
   detailed Given/When/Then) carry enough behavioral signal that
   the prototype reference is redundant for tasks. The
   prompt-composition skill (PC01) becomes responsible for any
   prototype context the executor needs, if any.

3. **Add a cliff-edge coverage validator + relax scaffold-citation
   rule.** R04 ensured every design-doc label produces at least one
   roadmap scenario; D03 ensures every roadmap cliff-edge scenario
   is cited by at least one task. The discovery during the airflow
   regeneration: scaffold and infrastructure tasks had been
   structurally excluded from citing scenarios, but the scaffold's
   cliff edges (`airflow-init-single-line-bash`,
   `dockerfile-runs-as-airflow-user`) live on the `project-setup`
   component and need to be cited from scaffold tasks. The original
   rule was relaxed mid-iteration to let scaffold/infrastructure
   tasks cite the tool-invocation scenarios their `test_command`
   verifies.

## What changed

### Schema — `scripts/task_schema.py`

Two changes:

- **`FileChange.description` removed**. The model now carries only
  `path`, `operation`, and the `stub` flag. The schema's docstring
  was updated to document why: the prose field was the contradiction
  surface; task-level description and cited roadmap scenarios provide
  sufficient context for what each file should contain.

- **New `validate_cliff_edge_coverage` model_validator on
  `TaskDecomposition`**. Loads `roadmap.json` via the
  project-shipped schema; collects every scenario with
  `criticality == "cliff_edge"` (across both functional and security
  lists, across all components); compares against the union of
  `roadmap_functional_scenarios` and `roadmap_security_scenarios`
  citations across all tasks. Uncited cliff edges produce a clear
  error message naming the missing IDs and their owning components,
  with a fix suggestion pointing at the scaffold-citation relaxation
  in the task-writing guide.

The new validator is the decomposition-layer parallel to R04's
cross-file coverage check. Three layers of structural cliff-edge
coverage form a chain:

```
design doc labels  →  roadmap cliff-edge scenarios  →  task citations
   (P04 ensures           (R04 validator                (D03 validator
    capture)               checks coverage)              checks coverage)
```

Each layer's validator ensures the next layer didn't silently drop a
cliff edge.

The validator is intentionally scoped to cliff-edge tier only.
Behavioral and prescribed scenarios are not subject to mandatory
coverage; some genuinely don't need a dedicated citation (e.g., a
behavioral scenario exercised implicitly by a broader integration
test cited elsewhere). Strict coverage is reserved for cliff edges,
where omission is non-recoverable.

### Reference docs

- **`references/task-writing-guide.md`** —

  - Replaced "Writing Inline Patterns (No External References)"
    section with "Where the prototype lives." The new section
    documents Option C explicitly: the prototype is an input to the
    decomposer's planning phase but is not referenced in task output.
    No prototype paths in task descriptions, no inlined snippets, no
    "see prototype X" prose carried forward.
  - Roadmap-Driven Task Authoring rule list expanded from three to
    four rules. Rule 3 relaxed: scaffold/infrastructure tasks
    explicitly may cite tool-invocation scenarios their `test_command`
    verifies. Rule 4 is new: every cliff-edge scenario must be cited.
  - TDD example updated: per-file `description` fields removed from
    `files` entries (one in the test task block, one in the
    implementation task block).
  - Service-compose example updated: removed inline-pattern prose;
    added scenarios-as-source-of-truth note.
  - "Inline patterns" bullet in test-task structure replaced with a
    pointer to the new "Where the prototype lives" section.
  - Self-Containment Rule updated: implementing model has access to
    the growing codebase but not to the prototype, design doc, or
    other task definitions; cited scenarios are inlined at prompt
    compose time by the prompt-composition skill.
  - "The prototype is the sizing reference" subsection renamed to
    "The prototype is the decomposer's sizing reference" with a
    note clarifying this is decomposer-only.

- **`references/output-format.md`** — four file-entry examples
  updated to remove `description` field.

- **`references/analysis-guide.md`** —
  - Top paragraph updated: prototype is decomposer-only.
  - `prototype_evidence` description updated: decomposer reads
    these files during planning to size tasks; files are not
    referenced in task output.
  - "What the roadmap doesn't carry" item added a historical note:
    inline-pattern extraction was an earlier behavior; current
    skill is prototype-decomposer-only.
  - "Inventorying the Prototype" section rewritten: emphasizes
    sizing and planning over pattern extraction.

- **`SKILL.md`** —
  - Quick Reference table: prototype role clarified.
  - Quick Reference paragraph: prototype is decomposer-only.
  - How to Start list: prototype usage clarified.
  - Phase 1 step 4 (Inventory the prototype) rewritten as
    decomposer-only.
  - Phase 2 step 5 (citation rule) relaxed for scaffold/infra
    tasks; new mention of cliff-edge coverage enforcement.
  - Phase 2 step 6 (Reference the prototype inline) replaced with
    "Do not reference the prototype in task content."
  - Schema Reference `files` row updated: path/operation only.
  - STOP reminder updated: prototype not referenced in output.
  - "Tasks are self-contained" principle: prototype removed from
    list of things model has access to.
  - "Reference, don't copy" principle renamed to "Prototype is
    decomposer-only" with rewrite.

## Regeneration arc against airflow-gdrive-ingestion

The decomposition was regenerated twice in this iteration.

### First pass — partial success

After dropping `FileChange.description` and removing prototype
references from task-writing-guide, the airflow decomposition
regenerated cleanly:

- 90+ `files[]` entries across 13 tasks, all carrying only
  `path`/`operation`/`stub` (no `description` field anywhere).
- Task descriptions free of `prototypes/...` paths and inline
  snippets. One borderline phrase ("Two cliff edges from prototype")
  in task-02 was flagged for future cleanup.
- Conftest.py fixture problem from session-status update-3
  directly addressed: task-05 now extends the placeholder conftest
  with `sample_db_path` fixture spelled out.

But: cliff-edge coverage was incomplete. Reviewing the output:

- `key-path-and-scope-required` → cited by task-03 and task-04 ✓
- `tempfile-not-hardcoded-tmp` → cited by task-04 ✓
- `airflow-init-single-line-bash` → cited by **no task** ✗
- `dockerfile-runs-as-airflow-user` → cited by **no task** ✗

The two `project-setup` cliff edges were captured in task-02's
prose description as task-scoped knowledge (`USER airflow before
RUN pip install`, `single-line bash -c command`), but they did
not appear as cited scenarios.

The root cause: the original task-writing-guide rule said
"scaffold, wiring, and pure-infrastructure tasks may cite none."
Task-02 is an infrastructure task; the decomposer followed the
guide and left `roadmap_security_scenarios` empty for it. The
cliff-edge framing the criticality field was supposed to enable
downstream (PC01) didn't flow through.

### Mid-iteration rule relaxation

This forced a decision: leave scaffold tasks unable to cite
scenarios and have PC01 work around it (pulling component-level
cliff-edge scenarios into the prompt even when task citations are
empty), or relax the decomposition rule to let scaffold/infra tasks
cite the scenarios their `test_command` verifies.

The relaxation path was chosen because:

- It preserves the "tasks cite the scenarios their work verifies"
  invariant cleanly across all task types.
- The decomposition validator can then enforce cliff-edge coverage
  uniformly without per-task-type special cases.
- PC01 stays simple: render whatever the task cites.

The relaxation: every task cites the scenarios its work verifies,
regardless of task type. Scaffold and infrastructure tasks
explicitly may cite tool-invocation scenarios their `test_command`
verifies. Tasks that only create trivial files (empty `__init__.py`,
etc.) with no meaningful verification may cite none. The
cliff-edge coverage validator enforces that every cliff-edge
scenario is cited by some task.

### Second pass — clean sweep

After the rule relaxation and validator addition, the airflow
decomposition regenerated again:

- All 4 cliff-edge scenarios cited:
  - `airflow-init-single-line-bash` → cited by task-02 ✓
  - `dockerfile-runs-as-airflow-user` → cited by task-02 ✓
  - `key-path-and-scope-required` → cited by task-03 and task-04 ✓
  - `tempfile-not-hardcoded-tmp` → cited by task-04 ✓
- task-01 (scaffold) cites `ruff-passes-clean` (behavioral,
  tool_invocation) and `service-account-key-not-in-source`
  (security, tool_invocation). Citations match the test_command's
  verification work.
- task-02 (infrastructure) cites three functional and one security
  scenario, including both project-setup cliff edges. test_command
  uses hadolint and docker compose config, which together verify
  both cliff edges.
- Borderline "from prototype" phrasing absent on second pass.
- Conftest.py fixture organization improved: task-01 creates an
  empty placeholder, task-05 extends it via `operation: modify` to
  add `sample_db_path`. Fixtures live alongside the tests they
  support.
- Comprehensive scenario coverage: every roadmap scenario has at
  least one task citation (not enforced by the validator for
  non-cliff-edge tiers, but achieved naturally given the relaxed
  rule).
- task-13 reclassified as a single integration test task
  (`task_type: "implementation"` with no paired test task) — a
  reasonable design call for a test that exercises already-implemented
  code, though slightly unusual.
- Dependency chains coherent across 13 tasks with no circular
  dependencies and no missing references.

## Failure modes addressed

The session-status-2026-05-10 update-3 failure mode (three executors
producing the same wrong conftest.py and requirements.txt) is now
structurally addressed at the decomposition layer:

- The `FileChange.description` removal eliminates the prose surface
  where the contradiction lived.
- The task-level description still carries the structured slots
  (Component / Component type / Interface / Expected test failure
  mode / Out of scope), but no per-file restatement of behavior.
- Cited scenarios (with criticality and verification fields from
  R04) carry the behavioral signal.
- The conftest.py fixture is now spelled out in task-05's Interface
  section as part of the structured task description, not in a
  per-file description paragraph.

The arc's central design goal — that "task descriptions are sole
source of truth" without contradiction surfaces — is met at the
decomposition layer. The remaining work is at the prompt-composition
layer (PC01).

## Key findings

1. **The relaxation of the scaffold-citation rule was the right
   move**. The original rule was an under-specification, not an
   active intent. Letting scaffold/infrastructure tasks cite the
   tool-invocation scenarios their `test_command` verifies makes
   citation uniform across task types and lets the cliff-edge
   coverage validator work without special cases. The relaxation
   surfaced in the middle of the first regeneration pass — a
   reminder that validation against a real project is what catches
   under-specifications that look fine in isolation.

2. **Coverage at the decomposition layer is the natural enforcement
   point**. P04's labels and R04's scenarios get the cliff edges
   into the upstream artifacts; D03's coverage check is what binds
   them to tasks. Without it, a roadmap could have cliff-edge
   scenarios that no task addresses, and the chain would silently
   break at the decomposition-to-prompt boundary. The validator's
   error message names the missing IDs and their owning components,
   so the fix is obvious and local.

3. **Dropping the prose description was load-bearing**.
   Independently of the cliff-edge chain, removing `FileChange.
   description` solves the session-status-update-3 contradiction
   directly. The session diagnosis identified this field as *the*
   contradiction surface; the structured slots in the task-level
   description plus cited scenarios cover the same ground without
   the prose-restatement gap. Removing the field is a small change
   (one schema field, a handful of reference-doc example updates)
   with a disproportionate effect on output quality.

4. **The "prototype is decomposer-only" choice handles the broken
   path-reference problem cleanly**. Option B (path-only references
   in tasks) would have given executors a path they cannot read,
   since the implementation pipeline doesn't surface the prototype
   directory to executor agents. Option C (drop references entirely)
   pushes the responsibility to PC01 if needed — but the roadmap's
   richer scenarios mean PC01 typically doesn't need it either.
   The cleanest division of responsibility: prototype is for
   decomposition planning, scenarios are for executor instruction.

5. **The chain of structural signals is now end-to-end**. P04's
   labels feed R04's criticality field; R04's scenarios feed D03's
   citations; D03's citations feed PC01's prompt framing. At each
   step, a validator enforces that the previous step's signal
   wasn't dropped. The "cliff edge" concept is no longer a
   documentation convention — it's a typed field that flows
   structurally from prototype iteration to executor prompt with
   coverage checks at each transition.

6. **The validator's pattern: load upstream, count, compare, fail
   loudly**. Both R04's design-doc → roadmap coverage check and
   D03's roadmap → tasks coverage check follow the same shape: load
   the upstream artifact, count the cliff-edge signal occurrences
   in it, compare against the downstream artifact's coverage, fail
   with a message that names the missing IDs and the fix. This
   pattern generalizes — any "every signal must be covered downstream"
   invariant can use it. Worth keeping in mind for future schema
   extensions.

## Related plan documents

- `session-status-2026-05-11-cliff-edges-and-two-prompt-split.md` —
  arc-level plan
- `session-status-2026-05-10-update-3.md` — original failure diagnosis
  that triggered the arc
- P04 trial record — upstream design-doc labeling
- R04 trial record — upstream roadmap criticality + verification
  fields; cross-file cliff-edge coverage check
- PC01 trial record (sibling) — downstream prompt rendering of the
  criticality-tagged scenarios

## Skill change summary

- `scripts/task_schema.py`:
  - `FileChange.description` field removed
  - `TaskDecomposition.validate_cliff_edge_coverage` model_validator
    added
  - Updated `FileChange` docstring documenting the field-removal
    rationale
- `references/task-writing-guide.md`:
  - "Writing Inline Patterns" section replaced with "Where the
    prototype lives"
  - Roadmap-Driven Task Authoring rule list expanded to four rules;
    rule 3 relaxed (scaffold/infra cite tool-invocation scenarios);
    rule 4 new (cliff-edge coverage)
  - Self-Containment Rule updated (no prototype access for executor)
  - TDD example, service-compose example updated to remove
    description-field usage
  - Sizing-reference subsection clarified as decomposer-only
- `references/output-format.md`: four file-entry examples updated
- `references/analysis-guide.md`: top paragraph, `prototype_evidence`
  description, Inventorying-the-Prototype section updated for
  decomposer-only role
- `SKILL.md`: Quick Reference, Phase 1 step 4, Phase 2 steps 5 and
  6, Schema Reference, two principles updated
