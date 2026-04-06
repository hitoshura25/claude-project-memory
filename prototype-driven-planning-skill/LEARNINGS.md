# Key Learnings & Principles

> Distilled from test runs across prototype-driven skills. These rules govern
> skill development. Always loaded at conversation start alongside `README.md`.

---

## From Planning Skill

- **Integration boundary mapping over single-risk identification**: Phase 1
  should map all integration boundaries, not just one "core risk."
- **Blocker handling must be explicit**: Skills should instruct the model to
  ask for help when blocked, not silently defer.
- **End-to-end validation is distinct from internal validation**: Running code
  internally is necessary but not sufficient.
- **Conditional Dockerfiles**: Skip for mobile apps, libraries, CLI tools.

## From Task Decomposition Skill

- **TDD pairing is structural, not advisory**: The schema enforces
  test-before-implementation via typed tasks and dependency validation.
  Not left to model judgment.
- **Self-containment is critical**: Each task must be understandable without
  the design doc. Local models (~30B) see one task at a time.
- **Interface dependencies prevent import errors**: If task B imports from
  task A's module, task B must depend on task A.
- **Numbered questions save round-trips**: Surfacing ambiguities as numbered
  questions at Phase 1 lets the user answer everything in one message.
- **Schema validation catches real bugs**: The `validate_tdd_pairing` validator
  caught a task with tests but no test-task dependency during a live run.
- **`uv run --with <package>` over venv activation**: venv activation doesn't
  persist in Claude Code; `uv run` is reliable.
- **Scaffold stubs enable proper TDD**: Test tasks create stub files alongside
  test files. Stubs define the public interface with `NotImplementedError`
  bodies so tests can import and run against them. The `stub: true` field in
  the task schema marks these files. Implementation tasks use
  `operation: modify` to replace stub bodies with real logic. Schema validators
  enforce: only test tasks may create stubs; implementation tasks must use
  `modify` (not `create`) for stubbed files.
- **Security goes on implementation tasks, not test tasks**.

## From Implementation Skill (In Progress)

- **Scaffold tasks must run from project root**: Scaffold-phase tasks run from
  project root, others from service root. File paths rebased accordingly.
- **Tooling environment must be bootstrapped**: After scaffold creates config,
  a bootstrap node fires automatically to install deps and make lint/test
  commands available. This is a pipeline concern, not an upstream skill concern.
- **Dry-run mode masks failures**: Removed dry-run; replaced with precondition
  validation (config consistency, path rebasing, schema import checks).
- **Aider scripting flags**: `--yes-always`, `--no-git`, `--no-check-update`,
  `--no-show-model-warnings`. Prototype references inlined into `--message-file`
  (not `--read` flags).
- **Local thinking models need explicit config via Aider**: Qwen 3 Coder 30B
  running with Aider's defaults (temperature 0, no thinking config) produces
  degenerate repetition loops — 27K tokens of repeated text. Phase 1 must
  research and verify Aider settings (thinking mode, temperature, edit format)
  for each detected local model before generating the pipeline.
- **Aider needs test files in --file for implementation tasks**: Without the
  test file in `--file`, Aider can only run tests via `--auto-test` and see
  pass/fail output but cannot read the test code. This causes Aider to say
  "test file not found" and produce blind implementations. Include the
  corresponding test file so Aider understands what assertions to satisfy.
- **Task complexity is about lines and functions, not file count**: A single
  file with 270 lines and 6 independent parser functions is too complex for
  a ~30B local model. Split by function group when prototype code exceeds
  150 lines. The decomposition skill's sizing rules must count prototype
  lines, not just task file count.
- **Pipeline handles rate limits correctly via existing retry/verify flow**:
  When an executor returns non-zero (rate limit, capacity error, etc.), the
  verify_task node's independent lint/test checks catch the unchanged code.
  The retry/escalation/mark-failed flow handles it without needing output
  string matching. The executor stays available for later tasks in case
  the limit resets.
- **Single source of truth for implementing models**: Task docs must be
  self-contained. When prototype code and task description conflict, models
  follow the code because working code is a stronger signal than prose
  instructions. The fix is to remove prototype references from the pipeline
  entirely and embed adapted patterns directly in task descriptions during
  decomposition.
- **Output field contracts prevent cross-task drift**: When task A produces
  data that task B consumes via a schema, both tasks must specify exact field
  names in their descriptions. The decomposing model must reconcile source
  names (e.g., database column `heart_rate_variability_millis`) with output
  names (e.g., Avro field `rmssd_ms`) at decomposition time, not leave it to
  the implementing model.
- **Tasks without test gates can hide broken code**: If a task only has a
  lint gate (no tests), syntactically valid but functionally broken code
  passes the pipeline. Integration test tasks are especially vulnerable —
  they may reference function signatures from modules not in their
  `depends_on` chain and get them all wrong. Consider adding import-level
  checks or requiring interface dependencies for all cross-module references.

## From Prior Skill Set (49 Trials)

- LLM non-determinism makes "Big Design Up Front" a losing strategy.
- What works: iteration against concrete feedback (write code, run tests,
  fix based on real results).
- The prototype-first approach eliminates "speculative planning" bugs.
- Smaller local models need very explicit instructions with exact values.

## Upstream-Only Rule

- **Fixes must be generic and upstream** in skill files, never band-aids on
  individual projects.
- **Skill content must not reference trial numbers or chat-specific history**.
  Skill guidance should explain the *principle* and *why*.
