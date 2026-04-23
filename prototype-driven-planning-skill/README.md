# Prototype-Driven Planning Skills — Project Context

> **Purpose**: Persistent memory across chat sessions for the prototype-driven
> skill set (planning → task decomposition → implementation).
>
> **Skill locations**:
> - `~/claude-devtools/skills/prototype-driven-planning/`
> - `~/claude-devtools/skills/prototype-driven-task-decomposition/`
> - `~/claude-devtools/skills/prototype-driven-implementation/`
> - `~/claude-devtools/skills/prototype-driven-roadmap/` (planned; see
>   `skill-expansion-plan-2026-04-21.md`)
>
> **Commands**:
> - `/prototype-plan <feature>` → planning skill
> - `/prototype-task-decompose <design-doc>` → decomposition skill
> - `/prototype-implement <feature>` → implementation skill
> - `/prototype-roadmap <feature>` → roadmap skill (planned)
>
> **Test project**: `~/health-data-ai-platform` (airflow Google Drive ingestion)

---

## Conversation-Start Protocol

Read these files in order:
1. **This file** — orientation, standings, open issues
2. **`LEARNINGS.md`** — distilled principles (always relevant)
3. **`trials/_SUMMARY.md`** — scoreboard

Load on-demand only when needed:
- `references/architecture-rationale.md` — why prototype-first, multi-model design, tool selection
- `references/stack-reference.md` — tool versions, configs, CLI flags, doc links
- `gemini_conversation.txt` — raw Gemini consultation transcript (historical)
- `trials/_INDEX.md` — structured tags per trial (find trials by failure pattern)
- `trials/T<NN>-*.md` — individual trial detail (read when analyzing a specific trial)
- `refactor-plan-2026-04-17.md` — T13 refactor plan (landed in T14)
- `refactor-plan-2026-04-19.md` — T14 refactor plan (landed same day; validates in T15)
- **`skill-expansion-plan-2026-04-21.md`** — **active plan**. Closed open
  questions in planning, new `prototype-driven-roadmap` skill, prototype
  security-tooling validation. Not yet landed. Read this when resuming work
  on the expansion.

---

## Current State (2026-04-19)

### Built and Validated

**prototype-driven-planning** — 3 phases (Discovery → Tracer Bullet → Design Doc)
with mandatory pauses. Design doc template includes Tooling section with lint,
auto-fix, test, bootstrap, and service root fields.

**prototype-driven-task-decomposition** — 3 phases (Analysis → Task Generation →
Validation/Output). Produces `tasks/<feature>/tasks.json` with strict TDD
pairing and per-task `test_command` enforced by PydanticAI schema validators.

**prototype-driven-implementation** — LangGraph pipeline with templated stable
files and verbatim `test_command` copy from the schema. Scaffold verification
runs bootstrap + lint-tool check + the scaffold's own test_command.

### T14 Run (2026-04-19): 16/17 passed

Full detail in `trials/T14-test-command-gap.md`. Summary:

- All T13 refactor items landed before T14: tight task-doc template
  (Component / Component type / Interface / Behaviors / Expected failure
  mode / Out of scope), JSON-only decomposition output (no per-task `.md`),
  `expected_test_failure_modes` schema field wired through `verify_task`,
  `compose_prompt.py.template` with the T13-validated system-prompt
  tightening.
- **16/17 tasks passed.** Jump from T13's 5/19. task-05 (test over-spec)
  and task-07 (fixture path) — the T13 failures explicitly deferred as
  out of scope — both passed in T14 without targeted fixes.
- **Only task-16 (integration test) failed, all 4 attempts.** Failure
  mode was `ERROR at setup of test_upload_avro_round_trip`: the
  `pytest.fail()` call inside the fixture when MinIO is unreachable.
  Claude's T1-R1 attempt correctly diagnosed the fixture as working as
  designed.

**Root cause of the single failure:** the decomposer wrote the correct
Docker-compose-wrapped test command into task-16's `description` prose,
but the Phase 2 generator's `TASK_TEST_COMMANDS` derivation ignored
descriptions and constructed a plain `uv run pytest tests/test_integration.py
-x`. Tests ran without Docker services. Structural issue: prose is a
lossy transport between decomposer and generator.

### T14 Refactor Landed (2026-04-19)

See `refactor-plan-2026-04-19.md` for full plan.

**Decomposition skill changes:**
- Added required `test_command: str` field to `Task` schema, with
  `validate_test_command_non_empty` and
  `validate_integration_test_lifecycle` validators. Existing T14
  `tasks.json` now fails validation with "Field required" on every
  task — the expected signal to regenerate.
- `task-writing-guide.md` — new "Task `test_command`" section with
  per-task-kind × per-language table and the canonical
  integration-test lifecycle pattern (with its five rules: `--wait`
  on up, `&&` between up and test-runner, `;` before down, `rc=$?`
  + `exit $rc`, `-v --remove-orphans` on down).
- `output-format.md` — example JSON shows `test_command` on all task
  kinds including an integration example; validation checklist item
  12 added; summary table gained a Test Command column.
- `SKILL.md` — schema reference table updated; Phase 2 and Principles
  mention the new field.

**Implementation skill changes:**
- `templates/config.py.template` — `TASK_TEST_COMMANDS: dict[str, str]`
  (dropped `| None`); `_validate_docker_if_needed` comment updated.
- `templates/nodes/verify_task.py` — scaffold branch extended: after
  bootstrap + lint-tool check, run the scaffold's own `test_command`
  as the final gate. Stale pytest-availability check (`pytest --co -q
  || true`) removed from `_run_scaffold_bootstrap`. Syntax-checked
  clean.
- `references/phase-1-analysis.md` — "Per-Task Test Command Derivation"
  section replaced with "Per-Task Test Commands" that explicitly
  defers to the schema; integration-test-task detection section added;
  presentation-summary table now shows `test_command`.
- `references/phase-2-generation.md` — `TASK_TEST_COMMANDS` now
  "verbatim from `task.test_command`. No derivation, no fallback, no
  defaults." Generation Principles add an entry emphasizing this.
- `references/phase-3-handoff.md` — Config Validation gained a
  "TASK_TEST_COMMANDS completeness" check; Precondition Validation
  gained "Task ID coverage (reverse)"; What-happens list describes
  the new scaffold gate.
- `SKILL.md` — Phase 1 no longer says "Derive per-task test commands";
  Phase 3 precondition checks updated; Principles gained
  "`test_command` is the decomposer's field" and "Every task has a
  test gate".

**Not changing:**
- Pipeline templates beyond `verify_task.py` and
  `config.py.template` are untouched.
- `INTEGRATION_TEST_TASK_IDS` stays (orthogonal verification-mode
  concern).
- `GLOBAL_TEST_CMD` stays (kept for manual runs).
- Existing `expected_test_failure_modes` field and its validators are
  unchanged.

### T10–T13 Arc (2026-04-16 through 2026-04-17)

Four runs on the same 19-task decomposition. Full detail in
`trials/T10-T13-tightening-arc.md`. Summary:

- **T10**: 5/19. Templating refactor held. Split-module test bug (parser
  across task-07/08 sharing test file) and mock path inconsistency
  (task-05) exposed test-writing as a coherence problem.
- **T11**: 6/19. Gemini upgrade fixed intra-file mock drift. New failure
  class: defensive-default tests that pass against partial stubs instead
  of raising NotImplementedError.
- **T12**: 2/19. Claude-as-test-writer experiment. Revealed `verify_task`
  rigidity — correct partial stub rejected by hardcoded single-pattern check.
- **T13**: 5/19. Tight system prompt + tight task-02 spec. **All 3 test tasks
  passed Gemini tier 0 retry 0.** ~55% prompt size reduction for task-02.
  Remaining failures were test over-specification (task-05) and fixture path
  resolution (task-07) — different failure class than prompt-structure
  issues; deferred.

**Key findings that drove the T13 refactor (landed in T14):**

1. System-prompt bloat confuses models more than per-task bloat.
2. Tight task-doc templates with fixed fields eliminate prompt contradictions.
3. Test over-specification is distinct from under-specification and
   doesn't get better with a more capable test-writer.
4. Partial-stub components need a structural fix (`expected_test_failure_modes`
   schema field), not more prose.
5. Dependency inlining should filter to files the task could actually import.
6. Duplicate rule blocks across prompt sections silently contradict — each
   rule belongs in exactly one section.

### Features List

1. `EXECUTORS` + `EXECUTOR_ROLES` config with type-based dispatch
2. Multi-executor dispatch via `agent_bridge.py`
3. Lint auto-fix as a post-executor step in `verify_task`
4. Executor escalation via `escalate_executor` node
5. Phase 1 live CLI research + test prompt verification
6. Phase 1 Step 1b: Aider model settings research for local models
7. Prompt composition with dependency inlining and test-task guidance
8. Enum serialization fix (`model_dump(mode="json")`)
9. Aider test file inclusion for implementation tasks
10. `AIDER_MODEL_EXTRA_ARGS` per-model config
11. Stub files in test tasks with `stub: true` schema field
12. `validate_stub_on_test_tasks_only` and `validate_stub_to_modify` validators
13. verify_task test-task logic: config-driven stub error pattern = pass, collection error = fail
14. Stub writing rules in test-task prompt composition
15. Prototype references removed — task descriptions are sole source of truth
16. Inline patterns and output field contracts in decomposition skill
17. Implementation pipeline no longer reads prototype directory or design doc
18. `AIDER_LINT_CMD` — auto-fix before check in Aider's `--lint-cmd`
19. `TeeWriter` stdout capture in `run.py` for run log completeness
20. `EXECUTOR_TIMEOUT` default reduced from 600s to 300s
21. Integration test Docker lifecycle in test commands (compose up/test/down)
22. Docker availability validation at startup when integration tests present
23. Scaffold task creates `services.compose.yml` for dependency services
24. Integration test task descriptions require exact function signatures
25. Orchestrator/wiring tasks must depend on scaffold if they import config/settings
26. Pipeline templates — stable files copied verbatim, config/compose_prompt/README generated
27. Integrated scaffold verification — marker file, bootstrap, tool checks in one verify_task pass
28. Config template with placeholders — prevents value drift from model memory
29. Language-agnostic templates — platform-specific patterns driven by config fields
30. Stub mock-import rule — stubs import third-party dependencies tests will mock
31. **Tight task-description template** (Component / Component type / Interface /
    Behaviors / Expected test failure mode / Out of scope) — landed T14
32. **`expected_test_failure_modes` schema field** wired into `verify_task` —
    enables correct handling of partial stubs. Landed T14.
33. **`compose_prompt.py.template`** — T13-validated tight system prompt
    with duplicate-rule removal and filtered dependency inlining baked in.
    Landed T14.
34. **JSON-only decomposition output** — no per-task `.md` files; summary
    table printed at decomposition time is the human-review artifact.
    Landed T14.
35. **Required `test_command` schema field** — every task specifies its
    own test gate command; populated verbatim into `TASK_TEST_COMMANDS`
    during Phase 2. Scaffold tasks included. Validators enforce non-empty
    and integration-lifecycle wrapping. Landed 2026-04-19 after T14.
36. **Scaffold test-infrastructure gate** — `verify_task` runs the
    scaffold's `test_command` after bootstrap/lint-tool checks. Catches
    broken `conftest.py`, wrong pytest config, missing pythonpath before
    any real test tasks run. Landed 2026-04-19 after T14.

### Planned — Skill Expansion (drafted 2026-04-21)

Full detail in `skill-expansion-plan-2026-04-21.md`. Three parts:

- **Part A (planning skill):** Phase 3 gains an Open Questions triage
  step that closes feasibility questions (via prototype-2 loopback) or
  decisions (via user input) before the design doc is considered final.
  Section renamed Open Questions → Deferred Decisions with a hard rule:
  no feasibility questions allowed.
- **Part B (new skill):** `prototype-driven-roadmap` — one markdown file
  per component identified in the design doc's Architecture Overview,
  each with BDD Functional Scenarios and data-flow-scoped Security
  Scenarios citing ASVS/MASVS requirement IDs. Always required after
  planning. Markdown + validator script (no Pydantic schema yet).
- **Part C (planning skill Phase 2):** Prototype security-tooling
  validation — dependency scan (always), secrets scan (always), SAST
  (conditional on ecosystem). Feeds a new `### Security Tooling`
  subsection of the design doc's Tooling section.

Execution order: plan doc → Part C → Part A → Part B → T15 trial.
Plan doc persisted 2026-04-21 awaiting user review before Part C starts.

---

## Pipeline Run History

### Run 1 (2026-03-31) — Single-tier Aider + Qwen
27 tasks, all attempted. 20/31 invocations hit reflection exhaustion. Dominant
failure: I001/F401 lint loops.

### Run 2 (2026-04-01) — Aider + Gemini Flash (model roles, no CLI research)
18 tasks. Stalled at task-02. Empty stubs from oversized scaffold, enum
serialization bug, single-tier test role.

### Run 3 (2026-04-02) — Claude CLI as scaffold/test executor
Pipeline hung on task-01. Hardcoded `--allowedTools` was wrong.

### Run 4 (2026-04-03) — Full escalation: Aider+Qwen → Gemini → Claude
18 tasks, ~2.5 hours. Best run to that point — all implementation code
produced. Claude rate limited after ~1 hour. 3 Qwen repetition loops.

### Run 5 (2026-04-04) — Re-decomposed with task sizing
21 tasks. Stalled at task-02. verify_task rejected valid test task due to
ModuleNotFoundError from missing stub.

### Run 6 (2026-04-05) — First clean run: Aider+Qwen → Gemini → Claude
21 tasks, ~2h 19m. First clean 21/21 run. Post-run review found field name
drift, wrong signatures, prototype-over-prose copying.

### Run 7 (2026-04-07) — Re-decomposed with inline patterns
31 tasks. I001 lint loops on all Aider+Qwen tasks, Gemini 429 on escalation.
Led to AIDER_LINT_CMD, TeeWriter, 300s timeout.

### Run 8 (2026-04-09) — Auto-fix + TeeWriter + 300s timeout
22 tasks, ~6.9h. 19/22 passed. Timeout was still 600s due to config drift.

### Run 9 (2026-04-13) — Re-decomposed (17 tasks)
17 tasks, ~1h 47m. 8 passed, 4 degraded, 1 failed (task-13), 1 skipped,
3 not_run. Timeout still 600s (memory contamination). ruff not in dev deps.
Task-13 failed: stub missing pika import for test patching. Led to
pipeline templates refactor.

### Run 10 (2026-04-16) — Templated pipeline + Aider+Qwen → Gemini → Claude
19 tasks. 5/19. Templating refactor held (300s timeout stable). Split-file
test bug (task-07) and mock-path inconsistency (task-05) exposed
test-writing quality as a coherence problem.

### Run 11 (2026-04-16) — Newer Gemini
19 tasks. 6/19. Gemini upgrade fixed intra-file mock drift. Stubs-pass
failures surfaced (defensive defaults pass against partial stubs).

### Run 12 (2026-04-16) — Claude-as-test-writer
19 tasks. 2/19. Exposed verify_task rigidity around partial stubs.

### Run 13 (2026-04-17) — Tight system prompt + tight task-02 spec
19 tasks. 5/19. All 3 test tasks passed Gemini tier 0 r0. Remaining
failures: test over-specification (task-05), fixture path (task-07).
Led to refactor-plan-2026-04-17.

### Run 14 (2026-04-19) — Tight task-doc refactor applied
17 tasks. **16/17 passed.** Only task-16 (integration test) failed; root
cause: Docker-wrapped test command embedded in task description but
never copied into pipeline. Led to refactor-plan-2026-04-19: required
`test_command: str` schema field.

---

## Next Steps

- **Skill expansion (plan drafted 2026-04-21).** See
  `skill-expansion-plan-2026-04-21.md`. Execution order after user
  sign-off on the plan:
  1. Part C: Phase 2 security-tooling validation (smallest; lands first
     so both Part A and Part B can rely on the design-doc Security
     Tooling subsection).
  2. Part A: Phase 3 Open Questions triage.
  3. Part B: new `prototype-driven-roadmap` skill.
  4. End-to-end trial (T15 or next available).

- **T15 validation run.** Regenerate `tasks/airflow-google-drive-ingestion/tasks.json`
  under the new schema (which will now fail validation and force the
  decomposer to populate `test_command` on every task). Regenerate the
  pipeline. Run. Acceptance bar:
  - Match T14's 16/17 at minimum.
  - Task-16 passes (services started by Docker-wrapped `test_command`).
  - Task-15 and task-17 test_commands exercise the AST-parse and
    `docker build` commands from their acceptance criteria (not lint-only
    anymore).
  - Scaffold task-01's test_command runs cleanly against the empty
    scaffold (pytest exit 5, normalized to exit 0 by the
    `|| [ $? -eq 5 ]` suffix).
  - If the skill expansion (above) lands before T15 runs, T15 doubles as
    the expansion validation: new planning skill produces a design doc
    with Security Tooling subsection, no feasibility questions survive,
    roadmap skill produces per-component BDD files.
- **Manual cleanup**: delete
  `~/claude-devtools/skills/prototype-driven-implementation/templates/nodes/bootstrap.py`
  (tombstone file from bootstrap merge; noted but not confirmed present).

---

## Test Run Results (session history)

### Planning Skill
- Session `f75b5f43-fd52-4138-87ad-c7c18589fa07` — First test run
- Session `a7c48f00-b614-4086-a640-b623a00f5a97` — Second test run

### Decomposition Skill
- Session `6d471491-32b7-4f74-a720-8fdbf0060023` — First run (8 tasks)
- Session `b2354707-0024-45db-bb9a-7ff872e39271` — Second run (11 tasks)
- Session `64052f92-5393-4425-8286-1389124c6feb` — Third run (27 tasks)

### Implementation Skill — runs 1–14
See `trials/_SUMMARY.md` for the canonical scoreboard.

---

## File Map

```
~/claude-project-memory/prototype-driven-planning-skill/
├── README.md                              # This file (read first)
├── LEARNINGS.md                           # Distilled principles (read second)
├── gemini_conversation.txt                # Raw Gemini consultation (historical)
├── refactor-plan-2026-04-17.md            # T13 refactor (landed in T14)
├── refactor-plan-2026-04-19.md            # T14 refactor (landed same day; validates in T15)
├── skill-expansion-plan-2026-04-21.md     # Expansion plan (drafted; awaiting sign-off)
├── references/
│   ├── architecture-rationale.md
│   └── stack-reference.md
└── trials/
    ├── _SUMMARY.md                        # Scoreboard (read third)
    ├── _INDEX.md
    └── T<NN>-<slug>.md

~/claude-devtools/skills/prototype-driven-planning/
├── SKILL.md
└── references/
    ├── design-doc-template.md             # Includes Tooling section
    ├── phase-1-discovery.md
    ├── phase-2-prototype.md               # Includes auto-fix discovery
    └── phase-3-design-doc.md

~/claude-devtools/skills/prototype-driven-task-decomposition/
├── SKILL.md                               # Updated 2026-04-19: test_command field
├── scripts/
│   └── task_schema.py                     # Updated 2026-04-19: test_command required + 2 validators
└── references/
    ├── analysis-guide.md
    ├── task-writing-guide.md              # Updated 2026-04-19: Task test_command section
    └── output-format.md                   # Updated 2026-04-19: test_command in examples + checklist

~/claude-devtools/skills/prototype-driven-implementation/
├── SKILL.md                               # Updated 2026-04-19: Phase 1/3 and Principles
├── templates/                             # Verbatim pipeline files (language-agnostic)
│   ├── run.py                             # Entry point with TeeWriter
│   ├── pipeline_state.py                  # LangGraph state TypedDicts
│   ├── graph.py                           # StateGraph, routing, pick/retry/escalate nodes
│   ├── agent_bridge.py                    # Executor dispatch, subprocess wrappers
│   ├── requirements.txt                   # langgraph, pydantic
│   ├── config.py.template                 # Updated 2026-04-19: TASK_TEST_COMMANDS: dict[str, str]
│   └── nodes/
│       ├── __init__.py
│       ├── load_tasks.py                  # Task loading, schema validation
│       ├── compose_prompt.py.template     # T13 tight system prompt with 3 placeholders
│       ├── execute_task.py                # Executor dispatch node
│       ├── verify_task.py                 # Updated 2026-04-19: scaffold runs test_command
│       └── report.py                      # Final summary
└── references/
    ├── phase-1-analysis.md                # Updated 2026-04-19: test_commands come from schema
    ├── phase-2-generation.md              # Updated 2026-04-19: TASK_TEST_COMMANDS verbatim
    ├── langgraph-patterns.md              # State machine design reference
    ├── executor-integration.md            # Executor dispatch and prompt composition
    └── phase-3-handoff.md                 # Updated 2026-04-19: reverse task-ID coverage check

~/claude-devtools/commands/
├── prototype-plan.md
└── prototype-task-decompose.md
```
