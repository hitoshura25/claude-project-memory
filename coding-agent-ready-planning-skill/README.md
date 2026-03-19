# Coding Agent Ready Planning Skill — Project Context

> **Purpose**: Persistent memory across chat sessions for the `devtools:agent-ready-plans` and
> `devtools:implementation-planning` skills. Read this file at the start of every new chat.
> For detailed trial analysis, see `trials/T<NN>-*.md`. For the scoreboard, see `trials/_SUMMARY.md`.
>
> **Skill location**: `~/claude-devtools/skills/agent-ready-plans/`
> **Test project**: `~/health-data-ai-platform` (airflow Google Drive ingestion service)

---

## Skill Overview

Two paired skills:
1. **`devtools:implementation-planning`** — turns a feature idea into a design doc + implementation plan with interface contracts and behavioral specs
2. **`devtools:agent-ready-plans`** — takes those artifacts and produces self-contained task files + scaffold + runner script for local coding agents (Aider + local models via LM Studio)

**Key architectural decision**: Claude Code writes complete, verified tests for each task (TDD approach). The small local model implements the code to make them pass. Claude Code owns test correctness — the small model owns implementation.

---

## Skill File Structure

```
claude-devtools/
  skills/
    agent-ready-plans/
      SKILL.md
      task-template.md
      references/
        writing-guide.md
        tooling.md
        stacks/
          python-pytest.md
          python-pytest/
            fixture-patterns.md  <- Fixture templates by behavioral pattern
          typescript-jest.md
          kotlin-junit.md
          infra.md             <- Docker/compose/Terraform/k8s tooling
      scripts/
        lint-ruff-wrapper.sh
        infra-lint-wrapper-template.sh
        docker-smoke-test-template.sh
        run-tasks-template.sh
    implementation-planning/
      SKILL.md
      references/
        plan-format.md
        wiring-completeness.md
```

---

## Strategy (Current)

**Strategy 3: TDD — Claude Code Writes Tests.** Claude Code writes complete, verified tests
per task (Step 3b). Small model implements to pass them. Strategies 1 (Code-Complete) and
2 (Spec-Based) were abandoned — see `trials/T01-strategy-comparison.md` for rationale.

---

## Model Standings (as of T28 / Chat 7)

- **Gemini 3.1 Flash Lite**: Reference model. Clean sweeps on T12, T17, T20. T28: 17/17 service tasks clean (26 calls). Docker exit(1) is task doc gap not model regression.
- **Qwen 3 Coder 30B**: Clean sweeps on T15, T18. T27: 14✅ 3⚠️ service tasks. E501 on extractors (Avro schema + inline SQL). Docker exit(1) same as Gemini.
- **Codestral 22B**: Permanently disqualified (T8, T11, T16). Not fixable at skill level.

---

## Key Learnings & Principles

- **Fixes must be generic and upstream** in the skill files, never band-aids on individual task docs.
- **Context length floor**: Do not reduce LM Studio context below 32k. MLX pre-allocates a fixed GPU KV cache; reducing to 12k causes Metal GPU OOM segfaults mid-run (T04).
- **SQLite traps**: Two documented patterns in `python-pytest.md`: the `:memory:` multi-connection trap and the multi-column IN clause trap.
- **Layer 0 lint gate**: Linter must return zero errors against pre-written test files before they can be embedded in task docs.
- **Import integrity pattern**: Wiring task docs must enumerate exact class names with explicit instruction not to import anything not listed.
- **Cascade isolation**: Component tasks create files only; wiring is always a separate task. Component test_commands never include shared files.
- **SQL Constants Pattern**: All SQL strings must be assigned to named module-level constants, never inlined in method bodies (eliminates E501 surface).
- **Deferred vs Service-Gated**: Integration tests are service-gated (runner skips when services unavailable), not deferred (which halts the runner).
- **`:memory:` fixture/Behavior pairing**: If a test fixture uses `:memory:`, the task doc Behavior section must include the persistent connection rule. They are a matched pair.
- **Fixture interaction rules**: Capture mocks block downstream side effects. Never combine a capture mock with an assertion on the captured function's output. See `python-pytest/fixture-patterns.md`.
- **Pip version pinning in Dockerfiles**: Claude Code must build unpinned first, capture resolved versions via `pip freeze`, pin them in the Dockerfile, and rebuild. Prevents both model version fabrication (T25) and hadolint DL3013 spirals (T26).
- **Tests referenced by path, not embedded**: Task docs point to on-disk test files rather than embedding copies. Embedding creates a second source of truth that diverges due to LLM non-determinism — the same class of bug as T23/T24 but at the task-doc generation stage.
- **Dockerfile is scaffold, not a task deliverable**: Claude Code writes, builds, pins versions, and validates the Dockerfile with hadolint during Step 3. It stays on disk — the small model only creates compose files. Every Docker task failure (T21, T22, T25, T26) was caused by the model recreating something Claude Code had already verified.
- **Test compose is scaffold too**: Claude Code writes the test compose and verifies the full stack starts healthy via `docker compose up --wait`. This catches missing env vars and config issues that caused T27/T28 container exit(1).
- **Long literals must be multi-line in Behavior sections**: SQL queries, Avro schemas, and nested dicts shown in task docs must be broken across lines. The model copies whatever form it reads — single-line forms trigger E501 lint spirals (T27 exhausted reflections on 3 extractor tasks).

---

## Open Issues

1. **RESOLVED** — Wire DAG callable body snippets (T15, T17, T18)
2. **RESOLVED** — UUIDStore SQL E501 (Chat 5: SQL Constants Pattern)
3. **ACTIONABLE** — Runner: pre-task file backup + restore on critical export loss
4. **RESOLVED** — Integration test deferral → service-gated (Chat 5)
5. **Codestral** — permanently disqualified
6. **Context length floor** — 32k (Qwen/MLX)
7. **RESOLVED** — RabbitMQ `is_closed` mock trap (Chat 5)
8. **RESOLVED** — Docker task test_command / runner redesign (Chat 5)
9. **RESOLVED (Chat 6)** — Base image tag verification: `stacks/infra.md` § "Base Image Verification".
10. **RESOLVED (Chat 6)** — Dockerfile Layer 0 validation gate: `docker build` against stubs.
11. **RESOLVED (Chat 6/T23)** — `:memory:` fixture/Behavior pairing rule.
12. **RESOLVED (Chat 6/T24)** — Fixture interaction rules: `python-pytest/fixture-patterns.md` with behavioral pattern templates + interaction constraints.
13. **RESOLVED (Chat 6/T25+T26)** — Pip version pinning: `stacks/infra.md` Step 2 rewritten with `pip freeze` capture flow. Prevents fabricated versions and hadolint DL3013.
14. **RESOLVED (Chat 7)** — Test embedding divergence: task docs now reference test files by path instead of embedding copies. Eliminates T23/T24/T27 class of LLM non-determinism bugs where validated on-disk test and task doc copy diverge.
15. **RESOLVED (Chat 7)** — Dockerfile as scaffold: Claude Code writes, builds, pins, and validates the Dockerfile during Step 3. It stays on disk — the small model only creates compose files. Eliminates T21/T22/T25/T26 class of Docker task failures.
16. **RESOLVED (Chat 7/T27+T28)** — Test compose as scaffold: Claude Code writes the test compose and verifies the full stack starts healthy via `docker compose up --wait` during Step 3. Eliminates T27/T28 missing env var class (container exit(1)).
17. **RESOLVED (Chat 7/T27+T28)** — Long-literal E501 surface: `writing-guide.md` now requires multi-line form for SQL queries, Avro schemas, and nested dicts in Behavior sections. Same principle as SQL constants and wiring snippets.

---

## Skill Changes Log

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
| 2026-03-12 | `implementation-planning/references/plan-format.md` | **Fix**: prohibit module-level instantiation of environment-dependent objects in interface contracts |
| 2026-03-12 | `references/writing-guide.md` | **Fix**: Three-Layer Validation Gate; Layer 0 lint gate; Deferred Tasks clarified |
| 2026-03-12 | `references/stacks/python-pytest.md` | **Fix**: SQLite Trap Patterns |
| 2026-03-12 (Chat 4) | `implementation-planning/references/plan-format.md` | **Fix**: wiring tasks no longer deferred; `import_integrity` mandatory |
| 2026-03-12 (Chat 4) | `references/writing-guide.md` | **Fix**: Wiring Task Tests section; import integrity check |
| 2026-03-13 (pass 1–3) | `references/writing-guide.md` | **Fix**: Unconditional code snippets for wiring callable bodies (three passes) |
| 2026-03-14 (Chat 5) | `references/stacks/python-pytest.md` | **Fix**: SQL Constants Pattern; Ruff config; E501 suppression prohibition |
| 2026-03-14 (Chat 5) | `references/writing-guide.md` | **Fix**: Deferred vs Service-Gated Tasks section |
| 2026-03-14 (Chat 5) | `run-tasks-template.sh` | **Fix**: `requires_services` + `service_check_commands` support |
| 2026-03-14 (Chat 5) | `SKILL.md` Step 5 | **Fix**: deferred vs service-gated distinction |
| 2026-03-14 (Chat 5) | `implementation-planning/references/plan-format.md` | **Fix**: integration tests service-gated throughout |
| 2026-03-15 (Chat 5) | `references/stacks/python-pytest.md` | **Fix**: pika `is_closed` mock trap — fixture + Pika Connection Lifecycle Trap section |
| 2026-03-15 (Chat 5) | `references/stacks/infra.md` | **New**: Infrastructure stack file — Docker/compose tooling |
| 2026-03-15 (Chat 5) | `scripts/docker-smoke-test-template.sh` | **New**: Parameterised Docker smoke test template |
| 2026-03-15 (Chat 5) | `scripts/infra-lint-wrapper-template.sh` | **New**: Infrastructure lint wrapper |
| 2026-03-15 (Chat 5) | `references/tooling.md` | **Fix**: Mixed-Technology Projects section; infra.md in stack table |
| 2026-03-15 (Chat 5) | `run-tasks-template.sh` | **Redesign**: Per-task `lint_cmd` override; no global-suite fallback; `requires_services` hard-fail |
| 2026-03-15 (Chat 5) | `SKILL.md` (agent-ready-plans) | **Update**: infra task detection, setup, smoke test validation, manifest example |
| 2026-03-15 (Chat 5) | `implementation-planning/references/plan-format.md` | **Fix**: Phase N+1 Deployment in template; Phase 7 guidance; hard-fail language throughout |
| 2026-03-15 (Chat 5) | `implementation-planning/SKILL.md` | **Fix**: service-gated not deferred; deployment tasks bullet; validation checklist updated |
| 2026-03-16 (T21/T22) | Open issues logged | Base image tag verification (#9); Dockerfile Layer 0 validation gate (#10) |
| 2026-03-16 (Chat 6) | `references/stacks/infra.md` | **Fix**: Base Image Verification section — `docker manifest inspect` + `docker build` gate |
| 2026-03-16 (Chat 6) | `SKILL.md` (agent-ready-plans) | **Fix**: Step 3 + Step 3b — Dockerfile build verification |
| 2026-03-16 (Chat 6) | `implementation-planning/references/plan-format.md` | **Fix**: Deployment tasks specify image family not exact tag |
| 2026-03-16 (Chat 6/T23) | `references/stacks/python-pytest.md` | **Fix**: Mandatory `:memory:` fixture/Behavior pairing rule |
| 2026-03-17 (Chat 6/T24) | `references/stacks/python-pytest/fixture-patterns.md` | **New**: Fixture pattern templates (Capture/Client/Stateful) + interaction rules |
| 2026-03-17 (Chat 6/T24) | `references/stacks/python-pytest.md` | **Refactor**: Inline fixture code → pattern summary + pointer to `python-pytest/fixture-patterns.md` |
| 2026-03-17 (Chat 6/T24) | `SKILL.md` (agent-ready-plans) | **Update**: Step 3 + 3b reference `python-pytest/fixture-patterns.md`; Bundled Resources updated |
| 2026-03-17 (Chat 6/T25+T26) | `references/stacks/infra.md` | **Fix**: Step 2 rewritten — pip freeze version pinning flow. Build unpinned → capture versions → pin → rebuild → hadolint |
| 2026-03-18 (Chat 7) | `task-template.md` | **Redesign**: `## Tests` section references test file by path instead of embedding code. Eliminates copy-divergence bug class. |
| 2026-03-18 (Chat 7) | `SKILL.md` (agent-ready-plans) | **Update**: Step 5 updated for reference-by-path; prose tightened (-15 lines) |
| 2026-03-18 (Chat 7) | `references/writing-guide.md` | **Refactor**: Test embedding → reference-by-path throughout; accumulated prose condensed (-96 lines) |
| 2026-03-18 (Chat 7) | `implementation-planning/references/plan-format.md` | **Fix**: "embeds it in the task doc" → "saves to disk, references by path" |
| 2026-03-18 (Chat 7) | `references/stacks/infra.md` | **Redesign**: "Base Image Verification" → "Dockerfile as Scaffold". Dockerfile stays on disk; model only creates compose files. |
| 2026-03-18 (Chat 7) | `SKILL.md` (agent-ready-plans) | **Update**: Step 3 scaffold includes Dockerfile; Step 3b simplified for infra; manifest Dockerfile removed from `files_created` |
| 2026-03-18 (Chat 7) | `implementation-planning/references/plan-format.md` | **Fix**: Deployment task Dockerfile moves from `Create:` to `Scaffold:`; Phasing Guidelines updated |
| 2026-03-18 (Chat 7/T27+T28) | `references/stacks/infra.md` | **Redesign**: Test compose added to scaffold alongside Dockerfile. Compose startup verification gate (`docker compose up --wait`) added to Step 4. |
| 2026-03-18 (Chat 7/T27+T28) | `SKILL.md` (agent-ready-plans) | **Update**: Step 3 scaffold includes test compose; model creates only production compose |
| 2026-03-18 (Chat 7/T27+T28) | `implementation-planning/references/plan-format.md` | **Fix**: Test compose moves to Scaffold; Phasing Guidelines updated |
| 2026-03-18 (Chat 7/T27+T28) | `references/writing-guide.md` | **Fix**: Long-literal formatting rule — multi-line form for SQL, Avro schemas, nested dicts in Behavior sections |

---

## Context Repository Structure

```
coding-agent-ready-planning-skill/
├── README.md              ← This file (read at conversation start)
├── SKILL_CHANGES.md       ← Detailed explanation of the 2026-03-11 SKILL.md/task-template.md fix
└── trials/
    ├── _SUMMARY.md        ← Scoreboard table + model standings
    ├── T01-strategy-comparison.md
    ├── T02-tdd-approach.md
    ├── ...
    └── T28-gemini-chat7-validation.md
```

Each trial file is **immutable once written**. New trials add a new file + a row in `_SUMMARY.md`.
