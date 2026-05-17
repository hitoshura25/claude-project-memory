# BDD-Scenario-Driven Productionalization — Proposal

**Status:** Draft for discussion. Not yet validated, not yet implemented.
**Date:** 2026-05-14
**Origin:** End of the T16 session, after a discussion about whether the
post-prototype chain (planning → roadmap → decomposition → prompts →
implementation pipeline) was earning its keep.

---

## Context

After 16 pipeline trial runs (T01–T16), the chain has produced exactly
one clean run (T06, 21/21 — and even that had post-run code quality
issues). T14 reached 16/17. Every other run partial-passed or stalled.
T16 (the most recent, against the refactored prompt-consumer pipeline)
got 2/13 before Gemini quota exhaustion and Claude timeouts collapsed
the run.

The honest assessment: the orchestration machinery hasn't crossed a
usefulness threshold. The chain was implicitly built around a "weak
models + strong orchestration" premise — multi-tier executors, TDD
scaffolding to give weak models a clear contract, structural signals
to compensate for prose inference. When strong models are used anyway
(which has been every clean-ish run), the orchestration costs more
than it saves.

What *has* earned its keep:
- The prototype phase
- Some of the planning-skill discipline (security severity handling,
  scope-removal triage, cliff-edge labeling)
- The verification rigor (test_command + verifier referenced in
  prompts + executor runs verifier before claiming done)

What *hasn't* earned its keep:
- The roadmap as an executor-consumable artifact (it works as a
  human-readable artifact but never reached its real consumer)
- Task decomposition as a separate concept (tasks are units of work
  for a decomposed pipeline; without the pipeline, they're middleware)
- The implementation pipeline (16 runs, never reliably produced a
  working service)

**But** "just hand the design doc to Claude Code and say 'productionalize
it'" doesn't work either — strong models confidently produce wrong
code. Verification is non-negotiable.

The proposal is to collapse the middleware while keeping the
verification rigor.

## Core proposal

Replace the (roadmap + decomposition + prompt-composition +
implementation pipeline) chain with a single BDD-scenarios-driven
flow:

```
Phase 1: Planning (unchanged)              → design doc
Phase 2: Prototype (unchanged)             → working prototype
Phase 3: BDD Scenarios (new/trimmed)       → flat list of testable contracts
Phase 4: One prompt per scenario (simple)  → prompt files
Phase 5: Execution (human-driven)          → human runs prompts in Claude Code
                                              one at a time; verification
                                              runs inside the executor
```

No LangGraph pipeline. No agent_bridge. No tier escalation. No
task_status.json. No verify_task as a separate node. The verification
step *moves into the prompt* — the prompt tells the executor to run
the verifier and fix until it passes.

## Why BDD scenarios as the unit (not tasks)

Tasks were a derivative concept — units of work for a decomposed
pipeline. Scenarios are the contract the productionalized app must
honor. Once the pipeline is removed, scenarios are the natural unit:

- One scenario = one Given/When/Then contract
- One scenario = one (or one-and-only-one) verifier command
- One scenario = one prompt for the executor
- One scenario = one independently-runnable test (could be a file,
  could be a function in a shared file — scenario writer decides)

The granularity is coarser than the current roadmap's 33 scenarios.
The target is 8–15 scenarios per project, where each scenario
describes a behavior the productionalized app must demonstrate.

The roadmap's 33 scenarios decomposed component-internal behaviors
for executor consumption. Without the executor, that level of
decomposition is over-specification. What's needed is a list of
contracts the app must satisfy as a whole.

## What "productionalize" means (concretely)

The BDD scenario skill needs a checklist of categories to enumerate
scenarios across. From the airflow project, the categories are:

- **Lifecycle**: container builds, services start, healthchecks pass
- **Dependency hygiene**: lint clean, pinned dependencies, security
  mitigations applied (per design doc's Mitigation Ladder findings)
- **Functional behavior**: the prototype's happy path works in the
  productionalized form
- **Service interactions**: external dependencies (RabbitMQ, MinIO,
  Google Drive) integrate correctly
- **Configuration**: env vars, connection strings, secret handling
  match design doc decisions
- **Failure modes**: cliff-edge scenarios from the design doc are
  validated (e.g., the prototype's specific failure mode for the
  alternative configuration does not occur)
- **Observability**: structured logging produces expected fields;
  retries are visible
- **Idempotency / retries**: matches design doc's stated retry
  semantics

Without a checklist, the model writes scenarios for the easy parts
(unit-test-shaped functional behaviors) and skips Docker/infra. This
was the P01 failure pattern — security tool selection table read as
complete spec. The BDD scenario skill needs the same kind of
"surface coverage" discipline.

## Scenario shape

Each scenario carries:

| Field | Purpose |
|-------|---------|
| `id` | Stable kebab-case identifier; cited by prompt-composition |
| `title` | One-line summary |
| `given` / `when` / `then` | Standard BDD prose |
| `criticality` | `cliff_edge` / `behavioral` / `prescribed` (from R04) |
| `verification` | `unit_test` / `integration_test` / `tool_invocation` / `static_assertion` (from R04) |
| `verifier_command` | Concrete command that, when exit-0, proves the scenario passes |
| `setup_shared_with` | Optional list of other scenario IDs whose fixtures/services overlap (informs whether to consolidate into one test file) |
| `evidence` | Where this scenario came from: prototype observation, design-doc cliff edge, Mitigation Ladder finding, etc. |

No `depends_on` between scenarios at the artifact layer. Order of
execution is human-chosen at run time. If scenario B builds on code
scenario A wrote, scenario B's prompt says "the codebase will already
have whatever A required."

## Validators (the parts of the chain worth keeping)

Three structural checks survive in the BDD skill:

1. **Cliff-edge coverage**: every `**Cliff edge:**` label in the
   design doc has at least one scenario with `criticality:
   cliff_edge` covering it. Mechanism is the same as R04/D03 — count
   labels via regex, count cliff-edge-criticality scenarios, require
   the second ≥ the first.

2. **Mitigation Ladder coverage**: every "implementing" entry in the
   design doc's Mitigation Ladder finding sections has at least one
   scenario verifying the mitigation. Catches the "model skipped the
   pinning we agreed to" failure mode.

3. **Verifier non-empty**: every scenario has a runnable
   `verifier_command`. Caught the T14 task-16 failure (integration
   test command embedded in prose, never reached TASK_TEST_COMMANDS).

That's it. No 31-rule validator like roadmap currently has. The
purpose is to catch a small set of high-value mistakes, not to enforce
a typed schema across the entire chain.

## What the prompt looks like

Each scenario produces one prompt:

```
# Role

You are productionalizing a working prototype. You will implement
one BDD scenario at a time. Each scenario has a verifier command;
run it before declaring done. If verification fails, debug and
retry until it passes.

# Context

The prototype is at: <project-root>/prototypes/<feature>/
The design doc is at: <project-root>/specs/<feature>/design.md
The codebase under productionalization is at:
<project-root>/services/<feature>/

# Scenario

ID: <scenario-id>
Title: <title>

Given <given>
When <when>
Then <then>

Criticality: <criticality>
<if cliff_edge: this scenario describes a boundary with a documented
failure mode for the alternative configuration. The verifier MUST
pass; do not negotiate the alternative.>

# Verification

Run this command from the project root:

    <verifier_command>

The scenario passes when this command exits 0. If it exits non-zero:
read the error output, fix the cause, run again. Repeat until clean.

# Evidence

This scenario comes from: <evidence>

# Output

Modify or create whatever files are needed. The codebase may already
have code from prior scenarios; build on it. Do not invent
infrastructure not described in the design doc.
```

That's the whole prompt. No dependency inlining (the executor reads
the codebase). No preamble dispatch (test vs impl — the executor
writes both as needed). No Previous Attempts section (each prompt is
independent; if a prior attempt left broken code, the next invocation
starts fresh with the current state).

## What gets dropped from the existing chain

- **Roadmap skill**: dropped, or repurposed as "first draft input to
  BDD scenario generation." The roadmap's structural rules (Performed-by,
  ID-set parity, OWASP version checks) move into the BDD scenario skill
  *only if they have a security-coverage purpose*. Most don't.

- **Decomposition skill**: dropped entirely. No tasks, no TDD pairing,
  no dependency graph, no scaffold task type, no `expected_test_failure_modes`.
  The TDD pairing was about giving weak models a clear contract; the
  executor is now strong (Claude Code) and writes its own tests as part
  of satisfying the scenario.

- **Implementation pipeline**: dropped entirely. No LangGraph, no
  agent_bridge, no verify_task, no executor tier escalation, no
  task_status.json, no compose_prompt node, no check_preconditions
  node. Verification happens inside the executor at the executor's
  initiative, instructed by the prompt.

- **Prompt-composition skill**: trimmed to ~30% of its current size.
  Reads the BDD scenarios, writes one prompt per scenario. No
  task-type-specialized preambles (one unified prompt template). No
  criticality grouping (one scenario per prompt). No file-inlining,
  no dependency rendering. Each scenario is independent.

## What gets kept from the existing chain

- **Planning skill, mostly unchanged**: design doc with security
  severity handling, scope deferrals, cliff-edge labels, Mitigation
  Ladder findings. All of these inform the BDD scenarios. The
  planning skill's "force visibility" pattern (P01–P03) continues
  to work because a human is reading the design doc before scenario
  generation.

- **Cliff-edge label discipline**: P04's structural signal still
  matters. Labels in the design doc → criticality field in scenarios.
  Validator stays.

- **Verification rigor**: every scenario has a concrete verifier
  command; the prompt instructs the executor to run it. This is the
  one architectural pattern from Option B (mid-session this session)
  that survives.

- **Memory repo + trial records**: the failure-mode catalog
  (`_INDEX.md` tag glossary) and the structural-fix patterns
  (`LEARNINGS.md`) are durable knowledge even if the chain
  architecture changes.

## Experiment to validate the approach (before building)

Two-prompt experiment, runnable in an afternoon:

**Step 1**: Manually write a BDD scenario for one airflow project
behavior. Pick something non-trivial — task-03's `download_zip` from
Google Drive is a good candidate. Include verifier command, evidence,
criticality, the works.

**Step 2**: Manually write the prompt using the template above.

**Step 3**: Hand the prompt to Claude Code (or Pi+Qwen, or Pi+Gemma —
all three were tested earlier this session on task-01 and task-02).
See what comes out.

**Step 4**: Repeat with a cliff-edge scenario (Dockerfile USER
airflow, or airflow-init bash single-liner). See if the criticality
framing changes executor behavior.

If the experiment produces working code + passing verifier in one
shot for both, the architecture is validated. If it stalls or
produces wrong code, we learn what the prompt was missing — and we
learn it cheaply, without rebuilding the chain.

## Open questions

1. **Granularity of scenarios.** Is 8–15 the right number, or is it
   closer to 20? The roadmap's 33 was over-decomposed; "one scenario
   per design-doc-section" might be the right heuristic, but worth
   testing.

2. **How to handle scenario interdependence.** "Build on existing
   code" is a soft contract. If scenario A wrote a broken
   foundation that scenario B needs, scenario B might either fix it
   (good) or work around it (bad). Worth thinking about whether
   scenarios should have explicit "depends on these files existing
   and working" preconditions, or whether the executor figures it
   out.

3. **What about scenarios that require setup the prototype doesn't
   have?** E.g., "integration test with real RabbitMQ via testcontainers"
   when the prototype used a mock. The scenario specifies what's
   needed, the executor adds the dependency. Probably fine, but
   worth confirming with the experiment.

4. **Where does the BDD scenario skill's "checklist of productionalization
   categories" live?** It needs to be in the skill's reference docs, but
   it's project-language-dependent (a Python airflow service has different
   categories from a Rust web service). Either a generic checklist with
   per-language addenda, or per-language playbooks. The planning skill
   already has language detection in Phase 1; this could ride on that.

5. **Migration path from existing artifacts.** The airflow project
   has a roadmap.json, tasks.json, and 13 prompt files. Are any of
   these useful inputs to the new BDD scenarios, or do we start from
   the design doc fresh? Probably "design doc fresh" but worth
   confirming.

6. **What replaces the implementation pipeline for "I want to run all
   the scenarios in sequence with logging"?** Maybe nothing — the
   user runs them in Claude Code one at a time. Maybe a thin shell
   script that lists scenario IDs in order and pauses between them.
   Definitely not a LangGraph state machine.

7. **What about the orchestration robustness work T16 surfaced?**
   (RC-1 environmental failure detection, RC-2 timeout sizing,
   RC-3 stream stdout, RC-4 E902 misclassification, RC-5 cosmetic.)
   All of these become moot if the pipeline is removed. The work is
   not lost — it's documented in T16 — but it stops being needed.

## What this looks like as a workstream

If the experiment validates the direction, the work is roughly:

1. **Build a BDD scenarios skill** (new, ~1 day): scenario schema +
   3 validators + reference docs + first-draft prompt template.
2. **Trim the prompt-composition skill** (~half day): drop
   roadmap/decomposition consumption, drop preamble dispatch, drop
   criticality grouping, simplify to one-prompt-per-scenario.
3. **Tombstone roadmap + decomposition + implementation skills**
   (~half day): mark as superseded; preserve the trial records and
   `LEARNINGS.md` material; update the project's CLAUDE.md to
   reflect the new chain.
4. **Migrate the airflow project to the new flow** (~1 day):
   regenerate BDD scenarios from existing design doc; regenerate
   prompts; run a scenario manually to validate; iterate.
5. **Document the new approach in the project memory README** (~half
   day): update structure, rationale, what to do next.

Total: ~3.5 days of focused work, vs. the open-ended orchestration-
robustness workstream T16 was queuing up.

## Honest assessment of the proposal

What I like:
- Collapses the middleware that hasn't earned its keep
- Keeps the verification rigor that's actually load-bearing
- Pulls the executor (Claude Code) into the role it's good at:
  reading a clear contract, writing code, running tests, debugging
- Removes the "weak model orchestration" assumption that the
  architecture was implicitly built on but isn't validated by the
  available executors

What I'm uncertain about:
- Whether 8–15 scenarios is the right granularity (could be 20)
- Whether "build on existing code" works in practice as a soft
  contract or needs harder dependencies
- Whether the BDD scenario skill ends up being roadmap-with-a-different-
  name (which would be a failure mode)

What I'd want to see before fully committing:
- The two-prompt experiment
- A test of cliff-edge framing actually changing executor behavior
  (otherwise the structural-signal-chain doesn't earn its keep
  either)

## Related material

- **T16 trial record** — documents the pipeline-run failure that
  motivated this reconsideration
- **I01 trial record** — documents the latest pipeline refactor
  (which works architecturally but doesn't change the outcome enough)
- **LEARNINGS.md** — the durable patterns that survive any
  architecture choice
- **README.md** in the memory repo — current state of the chain;
  would need updating to reflect this proposal if accepted

---

*To pick up in a new session: re-read this file, decide whether to
run the two-prompt experiment first or commit to building the BDD
scenarios skill. If the experiment, write the manual scenario and
prompt by hand against the airflow project. If building, start with
the scenario schema and the three validators.*
