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

Root causes: (1) Qwen `is_closed` mock trap; (2) empty `test_command` → global fallback cascade.

---

### Trial Set 20 — Gemini on New Task Set — Third Clean Sweep (2026-03-15)
**Log**: `run-20260315-142006.log` (2,067 lines)
**Model**: `gemini/gemini-3.1-flash-lite-preview` (Gemini API)
**Result**: **18/18 ✅, 0 degraded, 1 skipped ⏭ (task 19)**

---

### Trial Set 21 — Qwen on Revised Task Set with Infra Support (2026-03-16)
**Log**: `run-20260316-112706.log` (385 KB)
**Model**: Qwen 3 Coder 30B (via LM Studio)
**Result**: **16/18 ✅, 1 degraded ⚠️ (task 17 Docker), 1 hard-fail ❌ (task 18 — services unavailable)**

Root cause: Wrong Airflow image tag in task doc spec (`2.9-python3.11` doesn't exist; `2.9.0-python3.11` does). Task doc authoring error — Qwen correctly diagnosed it but couldn't override the spec. Hard-fail on task 18 confirmed correct.

---

### Trial Set 22 — Gemini on Revised Task Set with Infra Support (2026-03-16)
**Log**: `run-20260316-121437.log` (483 KB)
**Model**: `gemini/gemini-3.1-flash-lite-preview` (Gemini API)
**Skill state**: Identical to T21 — same task set, no skill changes between runs
**Result**: **16/18 ✅, 1 degraded ⚠️ (task 17 Docker), 1 hard-fail ❌ (task 18 — services unavailable)**

| Task | Lines | Notes |
|------|-------|-------|
| 01 UUIDStore | 108 | ✅ |
| 02 BaseExtractor | 176 | ✅ |
| 03 GDriveClient | 161 | ✅ |
| 04 MinIOWriter | 103 | ✅ |
| 05 RabbitMQ | 81 | ✅ — `is_closed` fix confirmed again |
| 06–15 Extractors | ~59 avg | ✅ all |
| 16 Wire DAG | 159 | ✅ |
| 17 Docker | 3572 | ⚠️ — see below |
| 18 Integration | ❌ | Hard-fail: services unavailable — correct |

**Runner summary**: `16 tasks completed, 1 degraded, 1 hard-fail (services unavailable)`
**Task 17 LLM calls: 27** (vs Qwen T21's 3) — massive spiral

#### T22 Root Cause Analysis

**Task 17 — Same image tag error, but Gemini's recovery exposed a second problem:**

Gemini followed the same cascade as Qwen:
1. Attempt 1: Wrote spec-as-given (`FROM apache/airflow:2.9-python3.11`) + fixed hadolint warnings (`DL3013`, `DL3042`). Build failed: image tag not found.
2. Attempt 2: Fixed the image tag (`2.9.1-python3.11`) — but was still running `pip install` as `USER root` inside the official Airflow image. The Airflow base image actively blocks root pip installs ("You are running pip as root. Please use 'airflow' user!"). Build failed: `pip install` exit code 1.
3. Attempt 3: Moved `pip install --user` under `USER airflow`. But `pip install --user` inside an Airflow container doesn't work either — the pip binary doesn't exist for the airflow user, and uv isn't on PATH. Build failed: exit code 1.

After attempt 3, Gemini hit the **free-tier input token quota** (250,000 tokens/session). The aider summarizer failed with "cannot schedule new futures after shutdown", consuming the final reflection slot on a garbled output. The run degraded.

**The underlying issue is that the Dockerfile spec itself is structurally wrong** for the Airflow base image:
- The official `apache/airflow` image already has pip-as-airflow configured; it doesn't allow root pip
- `RUN pip install uv` should be `RUN pip install --no-cache-dir uv` run **as airflow**, or better: use `pip install --constraint "..." uv` following Airflow's recommended pattern
- The correct approach for installing uv in an Airflow container is either as the `airflow` user with the right PATH, or using the Airflow-provided pip wrapper

This is still fundamentally a **task doc authoring error** — the Dockerfile spec was not validated against the actual base image's constraints before being embedded. The correct fix remains issues #9 and #10: verify the image tag exists and run hadolint (and attempt an actual build) before finalising the spec.

**T22 vs T21 comparison on task 17:**

| | Qwen T21 | Gemini T22 |
|---|---|---|
| LLM calls | 3 | 27 |
| Image tag identified | ✅ (in reflection) | ✅ (fixed in attempt 2) |
| Got past image pull | ❌ | ✅ |
| Hit pip/USER issue | ❌ | ✅ (new failure mode) |
| Quota exhaustion | No | Yes (free tier) |
| Final failure | Image not found | pip exit code 1 + quota |

Gemini made more progress but uncovered a second layer of the same fundamental problem. Both failures trace to the same root cause: the Dockerfile spec was not validated against the real image before being written.

**Task 18 hard-fail — correct behavior confirmed again (two runs).**

---

## Model Comparison Summary — T21/T22

| Metric | Gemini T22 | Qwen T21 |
|--------|------------|----------|
| Task set | Revised + infra | Revised + infra |
| Tasks 01–16 | 16/16 ✅ | 16/16 ✅ |
| Task 17 Docker | ⚠️ 27 calls, quota hit | ⚠️ 3 calls, image not found |
| Task 18 Integration | ❌ hard-fail (correct) | ❌ hard-fail (correct) |
| Root cause | Same task doc error; Gemini got further but hit pip/USER constraint + quota | Same task doc error; stopped at image pull |

**Common finding:** Both models confirm the same two upstream skill fixes are needed (issues #9, #10). The task doc is wrong regardless of which model runs it. Once the Dockerfile spec is corrected and validated, both models should pass task 17.

**Standings unchanged:**
- **Gemini 3.1 Flash Lite**: reference model; quota exhaustion on T22 is a free-tier limit artifact, not a reliability regression
- **Qwen 3 Coder 30B**: consistent on service tasks; same Docker degradation as Gemini
- **Codestral 22B**: permanently disqualified

---

## Open Issues

1. **RESOLVED — Wire DAG callable body snippets**
2. **RESOLVED (Chat 5) — UUIDStore SQL E501**
3. **ACTIONABLE — Runner: pre-task file backup + restore on critical export loss**
4. **RESOLVED (Chat 5) — Integration test deferral**
5. **Codestral — permanently disqualified**
6. **Context length floor — 32k (Qwen/MLX)**
7. **RESOLVED (Chat 5) — RabbitMQ `is_closed` mock trap**
8. **RESOLVED (Chat 5) — Docker task test_command / runner redesign**
9. **ACTIONABLE (T21/T22) — Base image tag verification**: `stacks/infra.md` Step 3b must require `docker manifest inspect <tag>` before writing Dockerfile spec. Wrong tag = unrecoverable build failure for any model.
10. **ACTIONABLE (T21/T22) — Dockerfile Layer 0 validation gate**: Must run hadolint AND attempt an actual `docker build` against the spec before embedding in the task doc. Confirmed that hadolint alone is insufficient — the Airflow base image has runtime constraints (root pip blocked) that only surface during a real build. The full pre-flight: (1) `hadolint Dockerfile`; (2) `docker build` the Dockerfile stub; (3) smoke test the resulting container. If any step fails, fix the spec before writing the task doc.

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
| 2026-03-16 (T21/T22, Chat 5) | Open issues logged | Base image tag verification (#9); Dockerfile Layer 0 validation gate upgraded to full build (#10) |
