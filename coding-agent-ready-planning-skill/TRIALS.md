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

### Trial Set 21 — Qwen on Revised Task Set with Infra Support (2026-03-16)
**Log**: `run-20260316-112706.log` (385 KB)
**Model**: Qwen 3 Coder 30B (via LM Studio)
**Skill state**: Post Chat 5 — new task set with Docker deployment task (task 17) and hard-fail integration test (task 18)
**Result**: **16/18 ✅, 1 degraded ⚠️ (task 17 Docker), 1 hard-fail ❌ (task 18 — services unavailable)**

| Task | Result | Notes |
|------|--------|-------|
| 01–05 | ✅ all | UUIDStore, extractors, writers — RabbitMQ `is_closed` fix confirmed |
| 06–15 | ✅ all | All 10 extractors clean |
| 16 Wire DAG | ✅ | |
| 17 Docker | ⚠️ | Wrong base image tag in task doc spec — `apache/airflow:2.9-python3.11` doesn't exist on Docker Hub |
| 18 Integration | ❌ | Hard-fail: minio, rabbitmq unavailable — **correct behavior**, runner printed `--start 18` resume instruction |

**Runner summary**: `16 tasks completed, 1 degraded, 1 hard-fail (services unavailable)`

#### T21 Root Cause Analysis

**Task 17 — Wrong Airflow image tag (task doc authoring error):**

The task doc's Dockerfile spec embedded `FROM apache/airflow:2.9-python3.11`. That tag does not exist on Docker Hub — the correct format is `apache/airflow:2.9.0-python3.11` (with patch version). Every smoke test attempt failed immediately at `docker build` with `failed to resolve source metadata`. Qwen correctly identified the issue in reflection ("A valid tag would be `apache/airflow:2.9.0-python3.11` or similar") but the task doc spec was authoritative and the model couldn't override it. All 3 reflections consumed on the same pull failure.

This is **not a Qwen failure** — the task doc contained incorrect content that no small model could fix. It is a **Claude Code authoring gap**: Step 3b validation of the smoke test should have caught this. Running `bash smoke-test-airflow-ingestion.sh` during scaffold validation would have failed immediately with the same image pull error, surfacing the wrong tag before the task doc was finalised.

**Secondary: hadolint warnings not blocking lint gate:**

hadolint fired `DL3013` (unversioned `pip install uv`) and `DL3002` (last USER is root) as warnings. hadolint exits 0 on warnings by default, so these didn't block the run. However, both violations were introduced by the Dockerfile spec in the task doc itself — meaning the spec wasn't hadolint-clean before being embedded. The Layer 0 lint gate (`hadolint` run against the spec content) should have caught these before the task doc was written.

**Task 18 hard-fail — correct behavior confirmed:**

Runner exited with a clear message identifying minio and rabbitmq as unavailable, printed the `--start 18` resume command, and stopped. No degraded marker, no silent skip — exactly the intended behavior from the runner redesign.

**URL scraping noise at task 17 start:**

The `ERR_CONNECTION_REFUSED` errors at the very start of task 17 are aider's own context-gathering — it attempted to fetch the URLs mentioned in the task doc (health endpoint, MinIO) before sending to the model. This is normal aider behavior, not a failure.

#### T21 Required Fixes (two actionable issues)

**Fix 1 — `stacks/infra.md` Step 3b validation**: Add an explicit pre-flight check to the "Validate the smoke test before embedding" section: run `docker manifest inspect <base-image-tag>` to verify the tag exists before writing the Dockerfile spec into the task doc. If the tag doesn't exist, look up the correct tag and fix it before proceeding. This is the upstream fix — it catches wrong tags at Claude Code authoring time, not at model execution time.

**Fix 2 — `stacks/infra.md` Layer 0 lint gate for Dockerfiles**: The Dockerfile spec embedded in task docs must be hadolint-clean before it's written into the task doc. Add an explicit "run hadolint against the spec content before embedding" step, analogous to the ruff Layer 0 gate for Python test files. Any DL* warnings in the spec must be resolved first. Common patterns to check: `DL3002` (last USER must not be root — switch back to `USER airflow` after root steps), `DL3013` (pin pip versions), `DL3042` (use `--no-cache-dir`).

---

## Model Comparison Summary

| Metric | Gemini T20 | Qwen T21 |
|--------|------------|----------|
| Task set | New (Chat 5) | New (Chat 5) + infra |
| Pass rate | 18/18 ✅ | 16/18 ✅ |
| Degraded | 0 | 1 ⚠️ (task doc error, not model) |
| Hard-fail | 0 | 1 ❌ (services — correct behavior) |
| RabbitMQ `is_closed` | not triggered | ✅ confirmed fixed (task 05 passed) |
| Docker smoke test | N/A | ⚠️ wrong base image tag in spec |
| Integration hard-fail | N/A | ✅ correct behavior |

**Standings:**
- **Gemini 3.1 Flash Lite**: three clean sweeps (T12, T17, T20). Reference model.
- **Qwen 3 Coder 30B**: consistent on service tasks; Docker degradation is a task doc authoring error, not a model failure. Issues #7 and #8 fully resolved. Two new upstream fixes identified for infra.md.
- **Codestral 22B**: permanently disqualified.

---

## Open Issues

1. **RESOLVED — Wire DAG callable body snippets**
2. **RESOLVED (Chat 5) — UUIDStore SQL E501**
3. **ACTIONABLE — Runner: pre-task file backup + restore on critical export loss**
4. **RESOLVED (Chat 5) — Integration test deferral**
5. **Codestral — permanently disqualified**
6. **Context length floor — 32k (Qwen/MLX)**
7. **RESOLVED (Chat 5) — RabbitMQ `is_closed` mock trap**
8. **RESOLVED (Chat 5) — Docker task test_command / runner redesign + upstream plan-format.md**
9. **ACTIONABLE (T21) — Base image tag verification**: `stacks/infra.md` Step 3b must require `docker manifest inspect <tag>` before writing Dockerfile spec into task doc. Wrong tag = immediate smoke test failure that no model can fix.
10. **ACTIONABLE (T21) — Dockerfile Layer 0 hadolint gate**: `stacks/infra.md` must require running hadolint against the Dockerfile spec content before embedding in the task doc. Common violations to check: `DL3002` (last USER not root), `DL3013` (pin pip versions), `DL3042` (--no-cache-dir).

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
| 2026-03-15 (Chat 5) | `scripts/docker-smoke-test-template.sh` | **New**: Parameterised Docker smoke test template |
| 2026-03-15 (Chat 5) | `scripts/infra-lint-wrapper-template.sh` | **New**: Infrastructure lint wrapper |
| 2026-03-15 (Chat 5) | `references/tooling.md` | **Fix**: Mixed-Technology Projects section; infra.md in stack table |
| 2026-03-15 (Chat 5) | `run-tasks-template.sh` | **Redesign**: Per-task `lint_cmd` override; no global-suite fallback; `requires_services` hard-fail |
| 2026-03-15 (Chat 5) | `SKILL.md` (agent-ready-plans) | **Update**: infra task detection, setup, smoke test validation, manifest example |
| 2026-03-15 (Chat 5) | `implementation-planning/references/plan-format.md` | **Fix**: Phase N+1 Deployment in template; Phase 7 guidance; hard-fail language throughout |
| 2026-03-15 (Chat 5) | `implementation-planning/SKILL.md` | **Fix**: service-gated not deferred; deployment tasks bullet; validation checklist updated |
| 2026-03-16 (T21, Chat 5) | Open issues logged | Base image tag verification (#9); Dockerfile Layer 0 hadolint gate (#10) |
