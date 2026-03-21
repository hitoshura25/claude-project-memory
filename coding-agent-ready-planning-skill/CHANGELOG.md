# Skill Changes Log

> Chronological record of every skill file modification. Load on-demand when checking
> whether a specific fix has already been applied.

| Date | File | Change |
|------|------|--------|
| 2026-03-03 | `run-tasks-template.sh` | Added `--timeout 600` to aider invocation |
| 2026-03-03 | `references/writing-guide.md` | Added ABC call site rule |
| 2026-03-04 | `SKILL.md` | Added Step 0: prohibit `git checkout HEAD` restoration |
| 2026-03-04 | `SKILL.md` Step 7 | Always copy runner from template, not git |
| 2026-03-04 | `run-tasks-template.sh` | Reverted `timeout` shell wrapper; kept `--timeout` flag |
| 2026-03-08 | `references/plan-format.md` | ABC contract fit verification; extract()-level override pattern |
| 2026-03-08 | `references/tooling.md` | Positional argument trap fixture criterion; mock_fastavro_writer |
| 2026-03-08 | `run-tasks-template.sh` | Corrected `--timeout` comment |
| 2026-03-09 | `references/tooling.md` | Dotted mock path registration rule; persistence class stub rule |
| 2026-03-10 | `references/tooling.md` | Refactor: language-neutral; stacks/ table |
| 2026-03-10 | `references/writing-guide.md` | Refactor: language-neutral stub patterns |
| 2026-03-10 | `implementation-planning/references/plan-format.md` | Refactor: language-neutral interface examples |
| 2026-03-10 | `SKILL.md` | Refactor: Steps 2/3/3b generalized; stacks/ in Bundled Resources |
| 2026-03-10 | `references/stacks/python-pytest.md` | New: all Python-specific content |
| 2026-03-10 | `references/stacks/typescript-jest.md` | New: TypeScript/Jest stub |
| 2026-03-10 | `references/stacks/kotlin-junit.md` | New: Kotlin/JUnit/Gradle stub |
| 2026-03-10 | `implementation-planning/references/plan-format.md` | **Fix**: component tasks never modify shared files; wiring always deferred; phasing guidelines rewritten |
| 2026-03-10 | `references/writing-guide.md` | **Fix**: component/wiring structural separation; Deferred Tasks updated |
| 2026-03-11 | `SKILL.md` | **Fix**: removed stale wiring/test-scope bullets from Step 5; updated manifest example |
| 2026-03-11 | `task-template.md` | **Fix**: removed Files to Modify and Wiring sections; added explanation |
| 2026-03-12 | `implementation-planning/references/plan-format.md` | **Fix**: prohibit module-level instantiation of environment-dependent objects |
| 2026-03-12 | `references/writing-guide.md` | **Fix**: Three-Layer Validation Gate; Layer 0 lint gate |
| 2026-03-12 | `references/stacks/python-pytest.md` | **Fix**: SQLite Trap Patterns |
| 2026-03-12 (Chat 4) | `implementation-planning/references/plan-format.md` | **Fix**: wiring tasks no longer deferred; `import_integrity` mandatory |
| 2026-03-12 (Chat 4) | `references/writing-guide.md` | **Fix**: Wiring Task Tests section; import integrity check |
| 2026-03-13 (pass 1–3) | `references/writing-guide.md` | **Fix**: Unconditional code snippets for wiring callable bodies |
| 2026-03-14 (Chat 5) | `references/stacks/python-pytest.md` | **Fix**: SQL Constants Pattern; Ruff config; E501 suppression prohibition |
| 2026-03-14 (Chat 5) | `references/writing-guide.md` | **Fix**: Deferred vs Service-Gated Tasks section |
| 2026-03-14 (Chat 5) | `run-tasks-template.sh` | **Fix**: `requires_services` + `service_check_commands` support |
| 2026-03-14 (Chat 5) | `SKILL.md` Step 5 | **Fix**: deferred vs service-gated distinction |
| 2026-03-14 (Chat 5) | `implementation-planning/references/plan-format.md` | **Fix**: integration tests service-gated throughout |
| 2026-03-15 (Chat 5) | `references/stacks/python-pytest.md` | **Fix**: pika `is_closed` mock trap |
| 2026-03-15 (Chat 5) | `references/stacks/infra.md` | **New**: Infrastructure stack file |
| 2026-03-15 (Chat 5) | `scripts/docker-smoke-test-template.sh` | **New**: Parameterised Docker smoke test template |
| 2026-03-15 (Chat 5) | `scripts/infra-lint-wrapper-template.sh` | **New**: Infrastructure lint wrapper |
| 2026-03-15 (Chat 5) | `references/tooling.md` | **Fix**: Mixed-Technology Projects section |
| 2026-03-15 (Chat 5) | `run-tasks-template.sh` | **Redesign**: Per-task `lint_cmd` override; `requires_services` hard-fail |
| 2026-03-15 (Chat 5) | `SKILL.md` (agent-ready-plans) | **Update**: infra task detection, setup, smoke test validation |
| 2026-03-15 (Chat 5) | `implementation-planning/references/plan-format.md` | **Fix**: Phase N+1 Deployment; hard-fail language |
| 2026-03-15 (Chat 5) | `implementation-planning/SKILL.md` | **Fix**: service-gated not deferred; deployment tasks |
| 2026-03-16 (Chat 6) | `references/stacks/infra.md` | **Fix**: Base Image Verification + `docker build` gate |
| 2026-03-16 (Chat 6) | `SKILL.md` (agent-ready-plans) | **Fix**: Step 3 + Step 3b — Dockerfile build verification |
| 2026-03-16 (Chat 6) | `implementation-planning/references/plan-format.md` | **Fix**: image family not exact tag |
| 2026-03-16 (Chat 6/T23) | `references/stacks/python-pytest.md` | **Fix**: `:memory:` fixture/Behavior pairing rule |
| 2026-03-17 (Chat 6/T24) | `references/stacks/python-pytest/fixture-patterns.md` | **New**: Fixture pattern templates + interaction rules |
| 2026-03-17 (Chat 6/T24) | `references/stacks/python-pytest.md` | **Refactor**: pointer to `fixture-patterns.md` |
| 2026-03-17 (Chat 6/T24) | `SKILL.md` (agent-ready-plans) | **Update**: Step 3 + 3b reference `fixture-patterns.md` |
| 2026-03-17 (Chat 6/T25+T26) | `references/stacks/infra.md` | **Fix**: pip freeze version pinning flow |
| 2026-03-18 (Chat 7) | `task-template.md` | **Redesign**: test reference-by-path |
| 2026-03-18 (Chat 7) | `SKILL.md` (agent-ready-plans) | **Update**: reference-by-path; prose tightened |
| 2026-03-18 (Chat 7) | `references/writing-guide.md` | **Refactor**: reference-by-path; long-literal rule; trial refs removed |
| 2026-03-18 (Chat 7) | `implementation-planning/references/plan-format.md` | **Fix**: reference-by-path; Dockerfile + test compose scaffold |
| 2026-03-18 (Chat 7) | `references/stacks/infra.md` | **Redesign**: Dockerfile + test compose scaffold; trial refs removed |
| 2026-03-18 (Chat 7) | `SKILL.md` (agent-ready-plans) | **Update**: scaffold includes Dockerfile + test compose |
| 2026-03-19 (Chat 7/T29+T30) | `references/stacks/python-pytest/fixture-patterns.md` | **Fix**: Pattern 3 enforces `:memory:` only; `tmp_path` prohibited |
| 2026-03-19 (Chat 7/T29+T30) | `references/stacks/python-pytest.md` | **Fix**: Trap 1 reframed — `:memory:` is quality standard |
| 2026-03-20 (Chat 8) | `references/writing-guide.md` | Added then reverted I/O data format + no cross-task reference rules — subsumed by code-grounding rule |
| 2026-03-20 (Chat 8) | `SKILL.md` (agent-ready-plans) Step 5 | **Fix**: Code-grounding rule — Behavior sections derived from test files and scaffold code, not plan prose |
| 2026-03-20 (Chat 8/T33+T34) | `SKILL.md` (agent-ready-plans) Step 5 | **Fix**: Grounding rule refined — explicit that small model can't navigate codebase; Claude Code must read source definitions and inline verified details into task doc |
| 2026-03-20 (Chat 8) | `scripts/docker-smoke-test-template.sh` | **Fix**: Capture `docker compose up --wait` exit code; dump container status + logs (80 lines) on failure before exiting |
| 2026-03-20 (Chat 8) | `references/stacks/infra.md` | **Redesign**: Three-Compose Pattern — services compose (deps only), full test compose (includes services + app), production compose. Replaces Two-Compose Pattern |
| 2026-03-20 (Chat 8) | `scripts/run-tasks-template.sh` | **Fix**: `service_compose` support — runner auto-starts services compose when `requires_services` unavailable, tears down after task |
| 2026-03-20 (Chat 8) | `SKILL.md` (agent-ready-plans) Step 3 | **Update**: Three-compose scaffold; `service_compose` in manifest for integration tests |
| 2026-03-20 (Chat 8) | `SKILL.md` (agent-ready-plans) Step 6 | **Update**: Manifest example includes `service_compose` field |
