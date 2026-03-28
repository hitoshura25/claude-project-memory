# Key Learnings

> Distilled from 3 test runs of the prototype-driven-planning skill.

## Prototype Scope

- **Toolchain validation is essential, not optional.** Lint config, test framework
  setup, and Docker entrypoint behavior are where downstream models get stuck.
  Proving them in the prototype prevents iteration loops in implementation.
- **End-to-end validation must prove the prototype works from the outside.** Building
  a Docker image ≠ proving the service works. Running `airflow dags test` inside
  the container ≠ running a script with `python main.py`. The prototype must be
  validated the way its actual consumer will use it.
- **End-to-end validation is technology-dependent.** For Docker services: health
  check or request/response. For mobile apps: build + install + UI test. For
  libraries: external consumer imports the public API. For CLI tools: end-to-end
  invocation with real input.
- **"Minimal tests" means enough to prove the toolchain and core logic — not one
  test, not exhaustive coverage.** If 6 extractors follow the same pattern, test
  1-2. If each has different conversion logic, test each conversion.

## Skill Architecture

- **Skill files live at `~/claude-devtools/` only.** Never push them to
  `claude-project-memory` or any other repo automatically.
- **The `prototypes/` directory convention is sufficient for immutability.** No
  freeze script or copy mechanism needed. The convention itself signals that
  prototypes shouldn't be modified.
- **Dockerfile is conditional on project type.** Deployable services, scheduled
  jobs → include. Libraries, CLI tools, mobile apps, features added to existing
  services → skip.
- **Pauses between phases are important.** The user must confirm before the model
  proceeds. "Sure" and "go ahead" are sufficient confirmation.

## Design Doc Quality

- **Every claim must be traceable to the prototype or research.** If the prototype
  didn't touch a concern, say "not validated by prototype" — don't speculate.
- **Toolchain notes in the README feed the design doc.** Surprises discovered during
  lint, test, or container setup (specific lint rules, import path quirks, Docker
  entrypoint behavior) become grounded content in the design doc.
- **The design doc's "Open Questions" section is one of its most valuable parts.**
  Run 3's top question (message format alignment with HealthDataMessage) only
  surfaced because the prototype actually published to RabbitMQ. Honest gaps are
  better than speculative answers.

## Claude Code Session Logs

- Session logs are at `~/.claude/projects/<encoded-project-path>/<session-id>.jsonl`
- Project path uses `-` as separator for `/`
- User message type field is `"user"` (not `"human"`)
- Message types in logs: `user`, `assistant`, `system`, `file-history-snapshot`, `last-prompt`
