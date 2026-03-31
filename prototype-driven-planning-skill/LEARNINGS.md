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
- **Scaffold stubs enable proper TDD**: Stubs with `NotImplementedError`
  (not missing files) let test tasks import and write tests that fail for
  the right reason.
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
