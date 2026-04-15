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
- **Aider's lint command must auto-fix before reporting**: Aider's
  `--auto-lint` flag runs the lint command after each edit and gives the
  model a reflection turn to fix any errors found. Trivially auto-fixable
  issues like I001 (import sorting) and F401 (unused imports) waste the
  model's limited reflection budget when the linter itself could fix them.
  The lint command passed to `--lint-cmd` should be a composite that
  auto-fixes first, then checks: `"<fix-cmd> && <check-cmd>"`. The
  pipeline's `verify_task` node still runs its own independent lint check
  as the authoritative gate.
- **Stdout tee is required for run logs**: Graph nodes use `print()` for
  progress output. Python's `logging.basicConfig` with a file handler
  captures nothing from `print()`. The fix is to wrap `sys.stdout` with a
  tee writer in `run.py` that writes to both console and the log file.
  Do not rewrite all nodes to use `logging.info()` — that's invasive.
- **Integration tests are just another TDD pair with Docker lifecycle**:
  Integration test tasks follow the same test/implementation pattern as unit
  tests. The only difference is that the test command wraps `docker compose
  up/down` around `pytest`. The services compose file belongs in the scaffold
  task (it's project infrastructure). The integration test task description
  must include exact function signatures for every module under test — without
  them, the model guesses arities and produces syntactically valid but
  functionally broken tests. No special schema fields or pipeline metadata
  are needed; the service lifecycle is entirely in the test command.
- **Orchestrator tasks must depend on every task they import from**: The
  implementation pipeline inlines dependency source code into the prompt,
  but only for direct dependencies. If a DAG/wiring task imports `Settings`
  from the scaffold task but doesn't list the scaffold in `depends_on`, the
  model never sees the Settings class and guesses field names. Every
  `from X import Y` in the task's code must trace back to a task in
  `depends_on`.

### Task Sizing

- **Use code quality thresholds for decomposition.** Cyclomatic
  complexity > 5, cognitive complexity > 10, fan-out > 5, parameter count > 4
  — adapted from SonarQube/CodeClimate with stricter limits to keep tasks
  within reach of smaller coding agents.
- **Single source of truth for config values.** When skill reference files
  repeat the same value in example code and prose, the generating model
  picks one arbitrarily. Use symbolic references in example code, never
  repeat literals.
- **Auto-fix chain must include the formatter.** Linter auto-fix handles
  import sorting and unused vars but not line length. Without the formatter
  in the chain, line-length errors waste retries on a mechanically fixable
  issue.
- **Test writing rules must prohibit asserting on stub errors.** Saying
  "tests should fail with NotImplementedError" is ambiguous — models write
  `pytest.raises(NotImplementedError)`, which passes against the stub. The
  rule must explicitly prohibit catching or asserting on the stub's
  placeholder error.

### Pipeline Architecture

- **Template stable files, generate only what varies.** Pipeline files like
  `graph.py`, `run.py`, `agent_bridge.py`, and all node files except
  `compose_prompt.py` are identical across projects. Regenerating them from
  memory or reference docs introduces value drift (e.g., EXECUTOR_TIMEOUT
  reverting to 600s from a prior run). Ship these as verbatim templates that
  are copied, not rewritten. Only `config.py`, `compose_prompt.py`, and
  `README.md` are generated per-project.
- **Config template with placeholders prevents drift.** When a model
  generates `config.py` from scratch, it may inject values from previous
  pipeline runs stored in its memory/context. A `config.py.template` with
  `{{PLACEHOLDER}}` markers and hardcoded fixed values ensures critical
  settings like timeouts and retry limits are always correct.
- **Pipeline templates must be language-agnostic.** Template files
  (verify_task, bootstrap, etc.) must not contain hardcoded language
  patterns like `.py` extensions, `NotImplementedError`, or `uv add --dev`.
  All platform-specific behaviour is driven by config fields:
  `SOURCE_FILE_EXTENSIONS`, `STUB_ERROR_PATTERN`,
  `TEST_COLLECTION_ERROR_PATTERNS`, `TEST_COLLECTED_PATTERNS`,
  `SCAFFOLD_MARKER_FILE`, and `BOOTSTRAP_TOOL_CHECKS`.
- **Bootstrap must verify tool availability.** After the bootstrap command
  runs, verify that lint and test tools are actually available. The
  `BOOTSTRAP_TOOL_CHECKS` config field provides (verify_cmd, install_cmd)
  pairs that the bootstrap node runs in sequence. This is config-driven
  and language-agnostic — no hardcoded tool names in the template.
- **Scaffold dev dependencies must include lint tools.** The design doc's
  Tooling section specifies which linter to use, but this doesn't guarantee
  the scaffold task's project config includes it in dev dependencies.
  Bootstrap tool checks catch this gap, but the decomposition should
  also be explicit about it in the scaffold task description.
- **Error context for retries must be file-based, not truncated.** Test
  framework output includes headers, separator lines, and traceback
  formatting that consume most of any fixed character budget before the
  actual error message appears. Truncating to a fixed limit (e.g., 800
  chars) can cut off the diagnostic message that would let the model fix
  the issue. Instead, write full error output to a file and direct the
  executor to read it. This gives the model complete diagnostic info
  without inflating prompt size.

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
