# Prototype-Driven Planning Skills — Project Context

> **Purpose**: Persistent memory across chat sessions for the prototype-driven
> skill set (planning → task decomposition → implementation).
>
> **Skill locations**:
> - `~/claude-devtools/skills/prototype-driven-planning/`
> - `~/claude-devtools/skills/prototype-driven-task-decomposition/`
> - `~/claude-devtools/skills/prototype-driven-implementation/`
>
> **Commands**:
> - `/prototype-plan <feature>` → planning skill
> - `/prototype-task-decompose <design-doc>` → decomposition skill
> - `/prototype-implement <feature>` → implementation skill
>
> **Test project**: `~/health-data-ai-platform` (airflow Google Drive ingestion)

---

## Conversation-Start Protocol

Read these files in order:
1. **This file** — orientation, standings, open issues
2. **`LEARNINGS.md`** — distilled principles (always relevant)
3. **`trials/_SUMMARY.md`** — scoreboard

Load on-demand only when needed:
- `references/architecture-rationale.md` — why prototype-first, multi-model design, tool selection
- `references/stack-reference.md` — tool versions, configs, CLI flags, doc links
- `gemini_conversation.txt` — raw Gemini consultation transcript (historical)
- `trials/_INDEX.md` — structured tags per trial (find trials by failure pattern)
- `trials/T<NN>-*.md` — individual trial detail (read when analyzing a specific trial)

---

## Current State (2026-04-09)

### Built and Validated

**prototype-driven-planning** — 3 phases (Discovery → Tracer Bullet → Design Doc)
with mandatory pauses. Design doc template includes Tooling section with lint,
auto-fix, test, bootstrap, and service root fields.

**prototype-driven-task-decomposition** — 3 phases (Analysis → Task Generation →
Validation/Output). Produces `tasks/<feature>/tasks.json` with strict TDD
pairing enforced by PydanticAI schema validators.

### Updated — Implementation Skill (2026-04-09)

**prototype-driven-implementation** — LangGraph pipeline that executes tasks via
configurable coding agent executors.

#### Run 8 Results (2026-04-09)

22 tasks, ~6.9 hours (too long). 19/22 passed, 1 failed (task-20 DAG wiring),
2 skipped. First run with AIDER_LINT_CMD (auto-fix), TeeWriter, and 300s
timeout applied (though timeout was actually 600s due to config drift — see
fixes below).

**Key metrics:**
- Productive work: 22 minutes (5% of runtime)
- Failed retries: 5.6 hours (81%) — dominated by 600s timeouts
- 27 attempts hit 600s timeout, only 4 of those passed
- 12/20 tasks passed on first attempt; 7 needed escalation
- Aider+Qwen: won 2/9 implementation tasks (simplest ones only)
- Gemini: won 12 tasks, but noisy (lint failures, stubs-pass errors)
- Claude: won 5 hardest tasks, 83% success rate

**Root causes of wasted time:**
1. EXECUTOR_TIMEOUT was 600s in generated pipeline despite skill template
   saying 300s — caused by hardcoded `timeout=600` in langgraph-patterns.md
   example code contradicting the config template
2. MAX_RETRIES_PER_TASK=3 meant 4 attempts per tier before escalation —
   Aider+Qwen never benefits from retries on tasks it can't solve
3. No code formatter in auto-fix chain — E501 (line too long) caused 5/14
   lint failures that ruff format would fix mechanically
4. Gemini writes `pytest.raises(NotImplementedError)` in test tasks —
   tests pass against stubs, defeating TDD

**Skill fixes applied (2026-04-09):**
1. `MAX_RETRIES_PER_TASK` reduced from 3 to 1 (all sources updated)
2. Eliminated config value duplication — `phase-2-generation.md` is now the
   single source of truth for all config defaults; other files reference
   `config.*` symbolically, never repeat literal values
3. `DEFAULT_FORMAT_CMD` added to config template — Phase 1 now detects
   project formatter; verify_task runs formatter after lint fix, before
   lint check; AIDER_LINT_CMD becomes "fix && format && check"
4. Test writing rules updated — explicit prohibition on
   `pytest.raises(NotImplementedError)` and language-agnostic equivalents;
   explains WHY this defeats TDD (test would pass against stub)
5. Formatter detection added to Phase 1 analysis guidance with ecosystem table

#### All features:
1. `EXECUTORS` + `EXECUTOR_ROLES` config with type-based dispatch
2. Multi-executor dispatch via `agent_bridge.py`
3. Lint auto-fix as a post-executor step in `verify_task`
4. Executor escalation via `escalate_executor` node
5. Phase 1 live CLI research + test prompt verification
6. Phase 1 Step 1b: Aider model settings research for local models
7. Prompt composition with dependency inlining and test-task guidance
8. Enum serialization fix (`model_dump(mode="json")`)
9. Aider test file inclusion for implementation tasks
10. `AIDER_MODEL_EXTRA_ARGS` per-model config
11. Stub files in test tasks with `stub: true` schema field
12. `validate_stub_on_test_tasks_only` and `validate_stub_to_modify` validators
13. verify_task test-task logic: NotImplementedError = pass, collection error = fail
14. Stub writing rules in test-task prompt composition
15. Prototype references removed — task descriptions are sole source of truth
16. Inline patterns and output field contracts in decomposition skill
17. Implementation pipeline no longer reads prototype directory or design doc
18. `AIDER_LINT_CMD` — auto-fix before check in Aider's `--lint-cmd`
19. `TeeWriter` stdout capture in `run.py` for run log completeness
20. `EXECUTOR_TIMEOUT` default reduced from 600s to 300s
21. Integration test Docker lifecycle in test commands (compose up/test/down)
22. Docker availability validation at startup when integration tests present
23. Scaffold task creates `services.compose.yml` for dependency services
24. Integration test task descriptions require exact function signatures
25. Orchestrator/wiring tasks must depend on scaffold if they import config/settings

---

## Pipeline Run History

### Run 1 (2026-03-31) — Single-tier Aider + Qwen

27 tasks, all attempted. 20/31 invocations hit reflection exhaustion.
Dominant failure: I001/F401 lint loops. See LEARNINGS.md for analysis.

### Run 2 (2026-04-01) — Aider + Gemini Flash (model roles, no CLI research)

18 tasks. Stalled at task-02 (4 attempts). Causes: empty stubs from oversized
scaffold task, enum serialization bug, single-tier test role. Positive: test
file had real assertions (model roles concept validated).

### Run 3 (2026-04-02) — Claude CLI as scaffold/test executor (pre-research fix)

Pipeline hung on task-01 (scaffold via claude CLI). Cause: hardcoded
`--allowedTools "Read,Write,Edit,Bash"` was wrong — `--allowedTools` in Claude
CLI auto-approves listed tools but doesn't prevent Claude from trying to use
other tools that then hang waiting for approval in headless mode. The correct
flags need to be determined by researching the CLI's official docs.

**Fix:** Updated skill to research CLI docs during Phase 1 executor detection
rather than relying on hardcoded patterns. Next run will regenerate the pipeline
with researched, verified invocation commands.

### Run 4 (2026-04-03) — Full escalation: Aider+Qwen → Gemini → Claude

18 tasks, ~2.5 hours. Best run yet — all implementation code produced.

**Results:** All 6 plugin modules implemented, all 7 test files written, DAG
complete. Tasks 16-18 (Dockerfile, Docker Compose, integration tests) not
reached. Claude CLI rate limit hit after ~1 hour.

**Executor performance:**
- Aider+Qwen: Succeeded on small tasks (avro_writer, watermark_store), timed
  out on complex ones (parser). 3 degenerate repetition loops (27K tokens).
- Gemini: Rescued drive_downloader and minio_uploader. Hit 429 capacity errors
  but internal retry handled them. Produced working code.
- Claude: Rescued parser. Rate limited after ~5 tasks.

**Root causes identified:**
1. Qwen 3 Coder running without thinking mode (temperature 0, no reasoning
   config) caused repetition loops
2. Aider couldn't read test files (not in --file list), so implementation
   attempts were blind to test expectations
3. Parser task too complex for local models (270 lines, 6 parsers in 1 file)

**Fixes applied:** Step 1b model research, test file inclusion, task sizing rules.

### Run 5 (2026-04-04) — Re-decomposed with task sizing

21 tasks (re-decomposed with updated task sizing). Stalled at task-02 after 4
attempts. Claude CLI produced empty output on all retries. Root cause: test
task imports module under test (`from config.settings import Settings`), but
the module doesn't exist yet — `verify_task` treated the `ModuleNotFoundError`
as a collection error instead of recognizing it as expected TDD behavior.

**Fix:** Stub-in-test-task design across both decomposition and implementation
skills. Test tasks now create stub files alongside test files.

### Run 6 (2026-04-05) — First clean run: Aider+Qwen → Gemini → Claude

21 tasks, ~2h 19m. First clean 21/21 run. Qwen improved significantly with
`/no_think` + `temperature: 0.7`. One repetition loop (task-09) recovered via
escalation. Post-run manual review found field name mismatches, wrong function
signatures in integration tests, and prototype-over-prose copying. Led to
`prototype_references` removal from the pipeline.

### Run 7 (2026-04-07) — Re-decomposed with inline patterns

31 tasks (re-decomposed). Field name drift and structlog issues from T06 are
fixed. But Aider+Qwen hit I001 lint loops on every implementation task
(reflection exhaustion), Gemini 429 blocked escalation for tasks 3, 27, 29.
DAG has cross-file field name drift (wrong Settings attributes). Integration
tests still have wrong function signatures. Run log empty (stdout not captured).

**Fixes applied:** AIDER_LINT_CMD (auto-fix before check), TeeWriter stdout
capture, EXECUTOR_TIMEOUT reduced to 300s.

### Run 8 (2026-04-09) — Auto-fix + TeeWriter + 300s timeout

22 tasks, ~6.9 hours. 19/22 passed, 1 failed (task-20), 2 skipped. I001 lint
loops resolved by AIDER_LINT_CMD. TeeWriter captured full log. But timeout
was still 600s due to config drift (literal in example code overrode template).
Aider+Qwen won only 2/9 impl tasks; Claude rescued 5 hardest. Gemini had
5 stubs-pass failures (wrote pytest.raises(NotImplementedError)) and 5 E501
lint failures (no formatter in auto-fix chain).

**Fixes applied:** MAX_RETRIES=1, single source of truth for config values,
DEFAULT_FORMAT_CMD (ruff format in auto-fix chain), test writing rules
updated to prohibit asserting on stub placeholder errors.

---

## Next Steps

- **Run T09** with updated config (MAX_RETRIES=1, EXECUTOR_TIMEOUT=300,
  DEFAULT_FORMAT_CMD, updated test writing rules) and measure improvement
- **Task-20 (DAG wiring)**: Still the hardest task — exhausted all tiers in
  T08. May need decomposition into smaller pieces (e.g., separate
  _download_zip wiring from _parse_records wiring)
- **Gemini 429 mitigation**: Gemini hit 429 rate limits on 20+ attempts.
  Consider adding backoff delay between Gemini retries, or switching to
  API key auth instead of CLI OAuth
- **Aider+Qwen value**: Won only 2/9 impl tasks. Consider whether it's
  worth keeping as tier-0 for implementation, or promoting Gemini to tier-0

---

## Test Run Results

### Planning Skill
- Session `f75b5f43-fd52-4138-87ad-c7c18589fa07` — First test run
- Session `a7c48f00-b614-4086-a640-b623a00f5a97` — Second test run

### Decomposition Skill
- Session `6d471491-32b7-4f74-a720-8fdbf0060023` — First run (8 tasks)
- Session `b2354707-0024-45db-bb9a-7ff872e39271` — Second run (11 tasks)
- Session `64052f92-5393-4425-8286-1389124c6feb` — Third run (27 tasks)

### Implementation Skill
- **2026-03-31**: Run 1 — 27 tasks, Aider+Qwen. Reflection exhaustion dominant.
- **2026-04-01**: Run 2 — 18 tasks, Aider+Gemini Flash. Enum bug + empty stubs.
- **2026-04-02**: Run 3 — Claude CLI as executor. Hung on task-01 (wrong CLI flags).
- **2026-04-03**: Run 4 — 18 tasks, Aider+Qwen/Gemini/Claude. All impl code produced.
  Claude rate limited after ~1hr. 3 Qwen repetition loops. Tasks 16-18 not reached.
- **2026-04-04**: Run 5 — 21 tasks (re-decomposed). Stalled at task-02.
  verify_task rejected valid test task due to ModuleNotFoundError from missing
  stub. Led to stub-in-test-task design across both skills.
- **2026-04-05**: Run 6 — 21 tasks, Aider+Qwen/Gemini/Claude. First clean
  21/21 run. Post-run review found field name drift, wrong signatures, and
  prototype-over-prose copying. Led to prototype_references removal.
- **2026-04-07**: Run 7 — 31 tasks (re-decomposed). I001 lint loops on all
  Aider+Qwen tasks, Gemini 429 on escalation. Field drift and structlog fixed.
  Led to AIDER_LINT_CMD, TeeWriter, 300s timeout.

---

## File Map

```
~/claude-project-memory/prototype-driven-planning-skill/
├── README.md                              # This file (read first)
├── LEARNINGS.md                           # Distilled principles (read second)
├── gemini_conversation.txt                # Raw Gemini consultation (historical)
├── references/
│   ├── architecture-rationale.md
│   └── stack-reference.md
└── trials/
    ├── _SUMMARY.md                        # Scoreboard (read third)
    ├── _INDEX.md
    └── T<NN>-<slug>.md

~/claude-devtools/skills/prototype-driven-planning/
├── SKILL.md
└── references/
    ├── design-doc-template.md             # Includes Tooling section
    ├── phase-1-discovery.md
    ├── phase-2-prototype.md               # Includes auto-fix discovery
    └── phase-3-design-doc.md

~/claude-devtools/skills/prototype-driven-task-decomposition/
├── SKILL.md
├── scripts/
│   └── task_schema.py
└── references/
    ├── analysis-guide.md
    ├── task-writing-guide.md
    └── output-format.md

~/claude-devtools/skills/prototype-driven-implementation/
├── SKILL.md                     # Multi-executor, research-based
└── references/
    ├── phase-1-analysis.md      # Updated: live CLI research + test prompt
    ├── phase-2-generation.md    # EXECUTORS/EXECUTOR_ROLES, enum fix
    ├── langgraph-patterns.md    # escalate_executor node
    ├── executor-integration.md  # Research-driven patterns (no hardcoded flags)
    └── phase-3-handoff.md

~/claude-devtools/commands/
├── prototype-plan.md
└── prototype-task-decompose.md
```
