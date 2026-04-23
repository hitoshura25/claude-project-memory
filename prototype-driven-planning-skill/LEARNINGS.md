# Key Learnings & Principles

> Distilled from test runs across prototype-driven skills. These rules govern
> skill development. Always loaded at conversation start alongside `README.md`.

---

## From Planning Skill

### Core planning principles

- **Integration boundary mapping over single-risk identification**: Phase 1
  should map all integration boundaries, not just one "core risk."
- **Blocker handling must be explicit**: Skills should instruct the model to
  ask for help when blocked, not silently defer.
- **End-to-end validation is distinct from internal validation**: Running code
  internally is necessary but not sufficient.
- **Conditional Dockerfiles**: Skip for mobile apps, libraries, CLI tools.

### From Part A + Part C rollout (P01–P03, 2026-04-23)

The planning skill's Open Questions Triage (Part A) and prototype
security-tooling validation (Part C) from `skill-expansion-plan-2026-04-21.md`
landed through a three-iteration refinement arc against
`health-data-ai-platform`. Each iteration surfaced a distinct failure mode
that prose-level rules alone didn't catch; each fix forced the model's
reasoning into a visible artifact.

- **Tables are starting points, not terminuses.** When the skill provides a
  reference table of tools or defaults (security tooling, lint auto-fix, dep
  scanners), the model reads it as a complete specification — one row per
  question, pick the matching cell, stop. A prototype with a Dockerfile and
  docker-compose file will pass `bandit` (the Python row for SAST) cleanly
  while shipping real security issues that the table's row doesn't cover.
  The fix is to make "start from the table, then run a surface-coverage
  check" an explicit mandatory step, not an implied one — and to name the
  failure pattern in the skill so the model recognizes the temptation.
  (P01)

- **Removals from approved Phase 1 scope are user decisions, not model
  decisions.** Mid-phase, the model is tempted to simplify by dropping
  "items that aren't needed for the prototype" — an approved dependency
  service, an additional data format, a retry path, a non-happy-path code
  branch. Rephrased in user-facing terms, this is a silent scope change.
  The skill's forcing function is a three-bucket Scope-Removal Triage
  (User-confirmed removal / Requires user decision / Must be validated)
  with the rule that model-initiated removals of approved items never
  happen silently. A mandatory STOP-report bullet ("Removals from Phase 1
  scope — if there were no removals, say so explicitly") is the backstop.
  (P01)

- **Observation and judgment are labeled distinctly in the design doc.**
  The design doc is not an observation log — it legitimately contains
  model-derived judgments (recommendations, prescriptions, inferences).
  But those judgments must be labeled. Behavioral claims without prototype
  evidence carry "*Not observed — based on inference*" labels; prescriptive
  claims ("should be refactored to X") carry "**Prescribed (not validated)**"
  labels. Unlabeled judgment in fact-shaped prose is systematically
  misleading even when the judgments themselves are sound — a future
  implementer can't distinguish tested pattern from model hypothesis. (P02)

- **No feasibility question ships in the design doc; both the difference
  test and the assertion test apply.** Open Questions Triage originally
  used one diagnostic — the difference test ("does the answer change the
  architecture?"). It's necessary but not sufficient. Items can pass the
  difference test (they look operational) while failing an unstated
  assertion test: accepting the item as "deferred to implementation"
  requires the design doc to assert something the prototype didn't observe.
  A "version bump is operational" deferral where the design doc must
  assert API-surface compatibility is the canonical shape. Both diagnostics
  run on every item. The triage-output template has an explicit "Passes
  assertion test: ..." field to force the check. (P02)

- **Phase 1 scope deferrals and prototype design choices are different
  things and must be recorded separately.** The design-doc template
  previously had one "Limitations of the prototype" list that conflated
  two provenances: items the user agreed to defer during Phase 1 (user
  decisions) and design choices the model made about minimum viable
  validation within approved scope (model decisions). A new `## Scope
  Deferrals from Phase 1` section captures the user-decision items
  explicitly; the Prototype Reference "Limitations" subsection is now
  scoped to model-design-choice items only. If nothing was deferred in
  Phase 1, the section reads "None — all Phase 1 scope was validated" —
  silence is not an allowed outcome. (P02)

- **Security findings get severity-indexed handling, not blanket deferral.**
  Before P03 the skill had no policy distinguishing Critical/High/Medium/
  Low — every finding went through the same "propose deferral, await
  confirmation" flow. Real trial behavior: Critical transitive CVEs
  proposed for routine deferral. The policy is now severity-indexed:
  Critical findings are blockers requiring the full Mitigation Ladder;
  High findings must attempt a fix; Medium and Low attempt if low-cost and
  surface-with-recommendation otherwise. "Attempt fix" means a concrete
  version change (forward OR backward — downgrading is a valid move),
  transitive override, exclusion, or replacement — not deferral as a
  first response. Secrets-scan findings have no severity tiering; any
  finding is Critical. (P03)

- **Security mitigation has an ordered option space; explore before
  accepting.** The Mitigation Ladder is five ordered options: direct
  upgrade of the top-level dep → override/pin/downgrade the transitive
  dep → exclude the transitive dep if pulled in by an unused extra →
  replace the top-level dep → accept with compensating controls. The
  model must work the ladder and record the attempt log. "Upgrade to
  version N makes things worse (introduces new CVEs), so we stay on the
  current version" is the exact failure mode this ladder exists to
  prevent — picking the lesser of two evils in a two-option space when
  three more options existed. Option 5 (accept) requires explicit user
  decision plus a compensating control, not just a written rationale.
  (P03)

- **Environmental risk assessments are proposals, not decisions.**
  Contextual CVSS reasoning ("the Critical score assumes public-facing
  deployment, which we're not") is legitimate security practice but
  dangerous as a model output. The model surfaces the assessment as part
  of Mitigation Ladder option 5; it does not unilaterally finalize.
  Reachability must be addressed specifically — "not running a public
  proxy" is not enough, the assessment must cite module-level or
  function-level reachability evidence. Assessments are labeled as
  judgment (per Judgment vs. Observation). Critical-severity assessments
  additionally name a condition under which the assessment would be
  wrong, forcing the model to surface its own uncertainty. (P03)

### Cross-cutting meta-pattern from P01–P03

The six lessons above share a single underlying pattern: **an LLM can
reliably do reasoning it has to make visible; it cannot reliably do
reasoning it can internalize and shortcut.** The skill's job is to force
visibility at every boundary where judgment replaces observation.

Surface Coverage Check makes tool-selection reasoning visible.
Scope-Removal Triage makes scope-change reasoning visible. The assertion
test makes deferral-classification reasoning visible. Judgment vs.
Observation makes prose-level claims visible. The Mitigation Ladder makes
security-mitigation reasoning visible. Environmental Risk Assessment rules
make contextual-risk reasoning visible.

When a new failure mode emerges, the useful question is not "what rule
prevents this?" but "what reasoning did the model do silently that should
have been made visible?" The artifact that forces the visibility is the
fix.

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
  The `validate_test_command_non_empty` validator would have caught the T14
  task-16 integration-test gap (Docker-wrapped command in prose only).
- **`uv run --with <package>` over venv activation**: venv activation doesn't
  persist in Claude Code; `uv run` is reliable.
- **Scaffold stubs enable proper TDD**: Test tasks create stub files alongside
  test files. Stubs define the public interface with `NotImplementedError`
  bodies so tests can import and run against them. The `stub: true` field in
  the task schema marks these files. Implementation tasks use
  `operation: modify` to replace stub bodies with real logic. Schema validators
  enforce: only test tasks may create stubs; implementation tasks must use
  `modify` (not `create`) for stubbed files.
- **Stubs must import mockable dependencies**: When tests mock a third-party
  library at the module boundary (via Python's `unittest.mock.patch`, Java's
  Mockito, TypeScript's Jest `jest.mock()`, etc.), the mocking framework
  resolves the dependency as an attribute of the module under test. If the
  stub omits the import, the framework cannot find the attribute and tests
  fail at setup before any test logic runs. The decomposing model must
  include these imports in the stub code it writes into the task description,
  even though the stub body never calls the dependency.
- **Security goes on implementation tasks, not test tasks**.

## From Implementation Skill (In Progress)

- **Scaffold tasks must run from project root**: Scaffold-phase tasks run from
  project root, others from service root. File paths rebased accordingly.
- **Tooling environment must be bootstrapped as part of scaffold**: After
  scaffold creates config, verify_task runs the bootstrap command
  (`SCAFFOLD_BOOTSTRAP_CMD`) to install deps and make lint/test commands
  available. If bootstrap fails, the scaffold task fails and can be
  retried/escalated. This is a pipeline concern, not an upstream skill concern.
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
- **Every task needs a verification gate beyond lint.** Syntactically valid
  but functionally broken code passes lint — wiring tasks with wrong
  function signatures, integration tests without services running,
  Dockerfiles with broken COPY directives, scaffold tasks with
  syntax-broken conftest. The schema-required `test_command` field on
  every task closes this: test tasks run their test file, implementation
  tasks run the paired tests, wiring tasks run an AST parse or import
  check, infrastructure tasks run `docker build` or `docker compose
  config`, scaffold tasks run the test runner with "no tests collected =
  success" semantics to verify test infrastructure before any tests
  exist. This supersedes the older "tasks without test gates can hide
  broken code" observation.
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
  functionally broken tests. The full wrapped command lives in the task's
  required `test_command` schema field, not prose — the decomposer owns
  it, the schema validates it, Phase 2 copies it verbatim into
  `TASK_TEST_COMMANDS`.
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
- **Long string literals must be named constants at file scope.** SQL
  queries, API URLs, format strings, regex patterns, and long error messages
  inlined in function bodies trigger line-length lint violations that code
  formatters cannot fix (formatters don't break string contents). Small
  models consistently write these as single-line literals, burn reflection
  budget on formatting, and never fix the root cause. The prompt's coding
  conventions section instructs models to extract long strings to named
  constants at module/file scope. This is language-agnostic and prevents
  the problem at the source.

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
  (verify_task, etc.) must not contain hardcoded language patterns like
  `.py` extensions, `NotImplementedError`, or `uv add --dev`. All
  platform-specific behaviour is driven by config fields:
  `SOURCE_FILE_EXTENSIONS`, `STUB_ERROR_PATTERN`,
  `TEST_COLLECTION_ERROR_PATTERNS`, `TEST_COLLECTED_PATTERNS`,
  `SCAFFOLD_MARKER_FILE`, and `BOOTSTRAP_TOOL_CHECKS`.
- **Scaffold verification must include bootstrap and tool checks.** After
  the scaffold executor creates project files, verify_task runs the
  bootstrap command and verifies that lint and test tools are available.
  The `BOOTSTRAP_TOOL_CHECKS` config field provides (verify_cmd,
  install_cmd) pairs that verify_task runs during scaffold verification.
  If bootstrap or tool checks fail, the scaffold task fails and can be
  retried/escalated — unlike the previous design where bootstrap ran as
  a separate node after verify_task had already marked the scaffold as
  passed.
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
- **Structured log directory separates concerns.** Run logs, lint errors,
  and test errors go to separate subdirectories under `logs/` (`runs/`,
  `lint/`, `tests/`). This keeps diagnostics organized and makes error
  files easy to reference in retry/escalation prompts.

### From T10–T13 Prompt & Spec Tightening

- **System-prompt bloat is a larger source of model confusion than
  per-task bloat.** When the universal preamble for every task carries
  component-specific domain knowledge (database schema nuances, third-party
  library quirks, domain-specific unit conversions), every task's prompt is
  polluted with context 95% of it doesn't need. Tightening the universal
  preamble to generic rules only (role, project skeleton, test/stub rules,
  coding conventions, output format) — and letting per-task content carry
  the component-specific detail — eliminates a class of confusion that
  tighter task specs alone don't. In practice, this alone moved three
  test tasks from multi-retry-or-escalation to first-attempt success on
  the mid-tier (Gemini Flash) executor, even without per-task tightening.
- **Tight task-doc templates with fixed fields beat freeform prose.**
  Freeform descriptions accumulate internal contradictions (one sentence
  says "keep the class instantiatable," another says "every method raises
  NotImplementedError") that models resolve by picking one or the other
  arbitrarily. A fixed template — Component / Component type / Interface /
  Behaviors / Expected failure mode / Out of scope — forces the decomposer
  to commit to a coherent story before emitting the task, because each
  field has a specific job and contradictions become visible.
- **Test over-specification is a distinct failure class from
  under-specification.** Under-specified tests fail because they can't
  import, can't find fixtures, or have inconsistent mock paths. Over-
  specified tests fail because they assert on details (argument values,
  call counts, specific parameter names) that the task description never
  prescribed. No implementation can satisfy them, because the constraint
  lives only in the test file. This doesn't get better with a more capable
  test-writer (a Claude-as-test-writer experiment exhibited the same
  pattern); it gets better only with explicit guardrails on what tests
  may assert.
- **Partial-stub components need a structural fix, not more prose.**
  Components like `pydantic-settings.BaseSettings` are "partial stubs":
  field declarations are real (they're the contract), but one or more
  methods are stubbed with `NotImplementedError`. A hardcoded single-
  pattern check in `verify_task` can't distinguish correct partial stubs
  from leaked-logic stubs when test ordering hides the raise. The fix is
  a schema field `expected_test_failure_modes: list[str]` driving the
  check, not more prompt prose.
- **Filter dependency inlining by file relevance.** Inlining every
  dependency file into every prompt (Avro schemas, compose YAML,
  Dockerfiles) adds noise for tasks that don't consume those file types.
  Limit dependency inlining to files the current task could actually
  `import` at the source level (`.py`, `.toml`, `.cfg`, `.ini` for Python
  projects; adapt per ecosystem).
- **Duplicate rule blocks across prompt sections silently contradict.**
  If the universal preamble and the per-task section both describe stub
  rules or test rules in overlapping prose, they drift over time and the
  model gets two conflicting versions of the same rule. Each rule belongs
  in exactly one section of the composed prompt.

### From T14 Test Command Gap

- **Prose is a lossy transport between decomposer and generator.** When
  the decomposer writes a specific command or contract into a task's
  description but the pipeline generator has no schema field to read it
  out of, the specific form does not survive the transition. The fix is
  a dedicated schema field and a generator rule that copies it verbatim.
  T14's failure mode was the decomposer writing a Docker-compose-wrapped
  test command into task-16's description while Phase 2 derived a plain
  pytest command from task file paths; tests ran without services and
  failed at fixture setup by design.
- **Runtime failure alone is not evidence of what to fix.** Task-16 failed
  all 4 attempts with `pytest.fail()` fires at fixture setup — exactly
  what the spec required when services are unavailable. Claude's
  escalation-retry correctly diagnosed "no changes needed." The bug was
  one layer up: the generator, not the executor. Post-mortem must trace
  the generated pipeline configuration back to the decomposition source
  before concluding what needs to change.
- **Promote a field to the schema when its absence causes a real bug, not
  speculatively.** `test_command` earned its place by failing T14.
  `expected_test_failure_modes` earned its place by failing T12. Fields
  that have not caused a real failure stay in prose.
- **Validators catch a class of bug, not individual bugs.** The schema's
  non-empty-`test_command` validator fires on every task equally. The
  integration-lifecycle validator is a light heuristic (description
  mentions docker/compose AND test_type is integration/e2e AND command
  lacks up/down verbs or testcontainers) — false-negative prone by
  design, because false positives would reject valid decompositions
  that use in-process service stubs or unusual naming conventions.
- **Scaffold tasks deserve a real test gate too.** The old behavior
  verified `pytest --co -q || true` (always exits 0) as a proxy for
  "test runner is installed." The new behavior runs the scaffold's own
  `test_command` (e.g., `uv run pytest tests/ -x || [ $? -eq 5 ]`),
  which exercises the actual test infrastructure — conftest loads,
  pyproject.toml configures pytest correctly, pythonpath resolves — on
  an empty test directory. If any of those are broken, the scaffold
  task fails early rather than every later test task failing mysteriously.
- **Keep the verification-mode selector separate from the command.**
  `INTEGRATION_TEST_TASK_IDS` (pipeline-level set that switches
  verify_task between "must pass" and "must fail with stub error")
  remained a separate concern from `test_command` (the shell command
  to run). They are orthogonal — a task can have an integration-style
  command without being in the set, or vice versa. Fusing them would
  conflate "what runs" with "how success is judged."

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
