# Coding Agent Ready Planning Skill — Trial Log

> **Purpose**: Persistent memory across chat sessions for the `devtools:agent-ready-plans` and
> `devtools:implementation-planning` skills. Each entry documents a trial run, findings, and
> any skill/script changes made. Read this at the start of every new chat in this project.
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
          typescript-jest.md
          kotlin-junit.md
          infra.md             <- NEW (Chat 5): Docker/compose/Terraform/k8s tooling
      scripts/
        lint-ruff-wrapper.sh
        infra-lint-wrapper-template.sh  <- NEW (Chat 5)
        docker-smoke-test-template.sh   <- NEW (Chat 5)
        run-tasks-template.sh
    implementation-planning/
      SKILL.md
      references/
        plan-format.md
        wiring-completeness.md
```

---

## Strategy History

### Strategy 1: Code-Complete Tasks (abandoned)
### Strategy 2: Spec-Based Tasks (abandoned)
### Strategy 3: TDD — Claude Code Writes Tests (current)

Claude Code writes complete, verified tests per task (Step 3b). Small model implements to pass them.

---

## Trial Runs

### Trial Sets 1–14
See prior chat history. Summary: TDD approach validated, Codestral disqualified, Qwen and Gemini reach reliability through iterative skill fixes.

---

### Trial Set 15 — Qwen After Callable-Body Snippet Fix (2026-03-14)
**Result**: **18/18 ✅ — first complete Qwen clean sweep.**

### Trial Set 16 — Codestral Final Confirmation (2026-03-14)
**Result**: 2/7 ✅, 1 ❌. **Codestral disqualified — third and final confirmation.**

### Trial Set 17 — Gemini 3.1 Flash Lite — Second Clean Sweep (2026-03-14)
**Result**: **18/18 ✅, 0 degraded** — 21 LLM calls.

### Trial Set 18 — Qwen Second Clean Sweep — Loop Closed (2026-03-14)
**Result**: **18/18 ✅, 1 ⚠️ (task 2 UUIDStore — lint, tests pass)**. Total LLM calls: 23.

---

### Trial Set 19 — Qwen on New Task Set (2026-03-15)
**Log**: `run-20260315-140047.log` (337 KB)
**Model**: Qwen 3 Coder 30B (via LM Studio)
**Result**: **17/19 ✅, 2 degraded ⚠️ (tasks 06, 18), 1 skipped ⏭ (task 19)**

Root causes: (1) Qwen `is_closed` mock trap on pika connection; (2) empty `test_command` → global fallback → Docker task cascaded on task 06 failure.

---

### Trial Set 20 — Gemini on New Task Set — Third Clean Sweep (2026-03-15)
**Log**: `run-20260315-142006.log` (2,067 lines)
**Model**: `gemini/gemini-3.1-flash-lite-preview` (Gemini API)
**Result**: **18/18 ✅, 0 degraded, 1 skipped ⏭ (task 19)**

Key findings: `is_closed` trap is Qwen-specific; Docker global fallback structurally fragile.

---

## Model Comparison Summary

| Metric | Gemini T20 | Qwen T19 |
|--------|------------|----------|
| Task set | New (Chat 5) | New (Chat 5) |
| Pass rate | 18/18 ✅ | 17/19 ✅ |
| Degraded | 0 | 2 ⚠️ (addressable) |
| UUIDStore E501 | self-fixed | **0** (SQL constants fix confirmed) |

**Standings:**
- **Gemini 3.1 Flash Lite**: three clean sweeps (T12, T17, T20). Reference model.
- **Qwen 3 Coder 30B**: clean on original task set (T15, T18); two addressable failures on new task set (T19). Issue #7 fixed; issue #8 addressed in runner redesign (Chat 5).
- **Codestral 22B**: permanently disqualified.

---

## Open Issues

1. **RESOLVED — Wire DAG callable body snippets**
2. **RESOLVED (Chat 5) — UUIDStore SQL E501**
3. **ACTIONABLE — Runner: pre-task file backup + restore on critical export loss**
4. **RESOLVED (Chat 5) — Integration test deferral**
5. **Codestral — permanently disqualified**
6. **Context length floor — 32k (Qwen/MLX)**
7. **RESOLVED (Chat 5) — RabbitMQ `is_closed` mock trap**: `mock_conn.is_closed = False` in fixture + Pika Connection Lifecycle Trap section in `python-pytest.md`
8. **RESOLVED (Chat 5) — Docker task test_command / runner redesign**: Runner no longer falls back to global suite when `test_command` is null/empty. `requires_services` is now a hard-fail (exit) not a skip. Infrastructure tasks get dedicated Docker smoke tests via the new two-compose pattern.

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
| 2026-03-15 (Chat 5) | `references/stacks/infra.md` | **New**: Infrastructure stack file — Docker/compose tooling, two-compose pattern, smoke test setup, hadolint, sequencing principle, Terraform/k8s stub |
| 2026-03-15 (Chat 5) | `scripts/docker-smoke-test-template.sh` | **New**: Parameterised Docker smoke test template — build, --wait, health poll, assertions, cleanup trap |
| 2026-03-15 (Chat 5) | `scripts/infra-lint-wrapper-template.sh` | **New**: Infrastructure lint wrapper — routes Dockerfiles→hadolint, compose→docker compose config, Python→ruff |
| 2026-03-15 (Chat 5) | `references/tooling.md` | **Fix**: Added "Mixed-Technology Projects" section with detection table and pointer to stacks/infra.md; updated stack file table to include infra.md |
| 2026-03-15 (Chat 5) | `run-tasks-template.sh` | **Redesign**: (1) Per-task `lint_cmd` override — infra tasks use their own linter; (2) Removed global-suite fallback — null/empty `test_command` means no test gate, not "use global"; (3) `requires_services` is now hard-fail (exit 1) not skip-and-continue |
| 2026-03-15 (Chat 5) | `SKILL.md` | **Update**: Step 1 adds infra task detection; Step 2 adds infra tooling detection note; Step 3 adds infra setup instructions; Step 3b adds smoke test validation; Step 6 manifest example includes Docker task with per-task `lint_cmd`; Bundled Resources table updated with three new scripts and infra.md |
