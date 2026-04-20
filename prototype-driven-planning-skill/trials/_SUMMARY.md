# Trial Summary — Scoreboard

> Quick-reference table. For full analysis, see the individual trial file.

| Trial | Date | Skill | Executors | Result | Notes |
|-------|------|-------|-----------|--------|-------|
| T01 | 2026-03-31 | implementation | Aider+Qwen | ❌ Partial | 27 tasks, 20/31 reflection exhaustion from I001/F401 lint loops |
| T02 | 2026-04-01 | implementation | Aider+Gemini Flash | ❌ Stalled | Stalled at task-02; enum bug + oversized scaffold + no escalation |
| T03 | 2026-04-02 | implementation | Claude CLI + Aider+Qwen | ❌ Hung | Hung on task-01; wrong `--allowedTools` semantics |
| T04 | 2026-04-03 | implementation | Aider+Qwen → Gemini → Claude | ⚠️ Best run | 15/18 tasks reached, all impl code produced; Claude rate limited |
| T05 | 2026-04-04 | implementation | Claude CLI | ❌ Stalled | Stalled at task-02; verify_task rejected valid test task (missing stubs) |
| T06 | 2026-04-05 | implementation | Aider+Qwen → Gemini → Claude | ✅ First clean run | 21/21 passed; code quality issues found in post-run review |
| T07 | 2026-04-07 | implementation | Aider+Qwen → Gemini → Claude | ⚠️ Partial | 31 tasks; I001 lint loops, Gemini 429s, DAG field drift, integration test sigs wrong |
| T08 | 2026-04-09 | implementation | Aider+Qwen → Gemini → Claude | ⚠️ 19/22 | I001 fixed; 600s timeout drift; Gemini stubs-pass + E501; task-20 failed all tiers |
| T09 | 2026-04-13 | implementation | Aider+Qwen → Gemini → Claude | ⚠️ 12/17 | 8 passed + 4 degraded; ruff missing from dev deps; task-13 stub import bug; timeout still 600s |
| T10 | 2026-04-16 | implementation | Aider+Qwen → Gemini → Claude | ⚠️ 5/19 | Templating refactor validated; split-file test bug (task-07); mock path inconsistency (task-05) |
| T11 | 2026-04-16 | implementation | Aider+Qwen → newer Gemini → Claude | ⚠️ 6/19 | Gemini upgrade fixed mock drift; stubs-pass failures surfaced (defensive defaults) |
| T12 | 2026-04-16 | implementation | Aider+Qwen → Claude (tests) → Claude (impl) | ❌ 2/19 | Claude-as-test-writer; verify_task rigidity rejected valid partial stub (task-02) |
| T13 | 2026-04-17 | implementation | Aider+Qwen → Gemini → Claude | ⚠️ 5/19 | Tight system prompt + tight task-02 spec; all 3 test tasks passed tier 0 r0; task-05/07 are test over-specification failures |
| T14 | 2026-04-19 | implementation | Aider+Qwen → Gemini → Claude | ⚠️ 16/17 | Tight-task-doc + schema refactors validated; only task-16 (integration test) failed — Docker-wrapped test command embedded in task description never reached TASK_TEST_COMMANDS |

---

## Progression

T01 → T02: Introduced model roles (validated test quality). Exposed enum bug and scaffold sizing.
T02 → T03: Introduced Claude CLI as executor. Exposed hardcoded flag assumptions.
T03 → T04: Runtime CLI research, multi-executor escalation. First run to produce all implementation code.
T04 → T05: Re-decomposed with task sizing. Exposed TDD stub gap in verify_task. Led to stub-in-test-task design.
T05 → T06: Stub workflow validated, /no_think + model settings applied, test file inclusion for Aider. First complete run. Post-run review revealed cross-task field name drift, leading to prototype_references removal.
T06 → T07: Re-decomposed with inline patterns + output field contracts. Field drift fixed, structlog everywhere. But I001 lint loops returned as #1 failure mode (unchanged since T01). Led to AIDER_LINT_CMD (auto-fix before check), TeeWriter stdout capture, 300s timeout.
T07 → T08: AIDER_LINT_CMD fixed I001 loops. TeeWriter captured full log. But timeout was still 600s due to config drift (hardcoded literal in example code). Led to config value deduplication.
T08 → T09: MAX_RETRIES=1 cut runtime from 6.9h to 1.8h. But timeout still drifted to 600s (Claude Code memory contamination). ruff missing from dev deps caused early lint failures. Task-13 stub import bug. Led to pipeline templates refactor.
T09 → T10: Templating refactor held (300s timeout stable). Split-file test bug (task-07) and mock path inconsistency (task-05) exposed test-writing quality as a coherence problem, not a generation problem.
T10 → T11: Gemini upgrade improved intra-file consistency; new stubs-pass failure class surfaced where tests with defensive defaults pass against partial stubs instead of failing with NotImplementedError.
T11 → T12: Claude-as-test-writer experiment exposed `verify_task` rigidity for partial stubs — correct output rejected by hardcoded single-pattern check.
T12 → T13: System prompt tightening + per-task tight template eliminated prompt contradictions and noise. All 3 test tasks passed tier 0 retry 0. Remaining failures are test over-specification (task-05) and fixture path bugs (task-07) — a different failure class from prompt-structure issues. Led to skill refactor plan: drop .md outputs from decomposition, tighten task-doc template, bake compose_prompt.py changes into implementation skill templates, add `expected_test_failure_modes` schema field.
T13 → T14: All T13 refactor items landed (tight template, JSON-only output, compose_prompt.py template, `expected_test_failure_modes` field + verify_task wiring). 16/17 passed — jump from T13's 5/19. task-05 (test over-spec) and task-07 (fixture path) both passed this run. Only task-16 failed: integration test's Docker-wrapped `test_command` was embedded in prose in the task description but the Phase 2 generator ignored it, producing a bare `pytest tests/test_integration.py -x` in TASK_TEST_COMMANDS. Services were never started; fixtures hard-failed by design. Led to refactor-plan-2026-04-19: required `test_command: str` schema field, validators for non-empty and integration-lifecycle-wrapping, scaffold also gets test_command (exit-5-tolerant pytest), `TASK_TEST_COMMANDS` populated verbatim from schema. Refactor landed same day pending T15 validation.

---

## Model Standings

| Model | Strengths | Weaknesses |
|-------|-----------|------------|
| Qwen 3 Coder 30B | Simplest tasks only (minio_uploader in T09, task-08 in T14 tier-0) | Complex tasks |
| Gemini Flash | Reliable for tests and mid-complexity impl tasks; T14 escalation survived a stray SSL/TLS error mid-run | E501 on string literals; occasional `write_file:` markdown blob output (T14 task-16) |
| Claude CLI | Handles most complex tasks, high code quality; T14 cleaned up several tier-0 Gemini misses | Pro plan rate limit (~1hr active use) |

---

## Skill Standings

| Skill | Status | Last Validated |
|-------|--------|----------------|
| prototype-driven-planning | ✅ Built | 2026-03-28 (2 test runs) |
| prototype-driven-task-decomposition | ✅ Built; T14-refactor landed 2026-04-19 (test_command required field + validators) | T14 (2026-04-19) |
| prototype-driven-implementation | ✅ Built; T14-refactor landed 2026-04-19 (TASK_TEST_COMMANDS verbatim from schema; scaffold runs test_command) | T14 (2026-04-19) |
