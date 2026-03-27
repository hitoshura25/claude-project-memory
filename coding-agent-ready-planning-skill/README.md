# Coding Agent Ready Planning Skill — Project Context

> **Purpose**: Persistent memory across chat sessions for the `devtools:agent-ready-plans` and
> `devtools:implementation-planning` skills.
>
> **Skill location**: `~/claude-devtools/skills/agent-ready-plans/` and `~/claude-devtools/skills/implementation-planning/`
> **Test project**: `~/health-data-ai-platform` (airflow Google Drive ingestion service)

---

## Conversation-Start Protocol

Read these files in order:
1. **This file** — orientation, standings, open issues
2. **`LEARNINGS.md`** — distilled principles (always relevant)
3. **`trials/_SUMMARY.md`** — scoreboard

Load on-demand only when needed:
- `CHANGELOG.md` — skill changes log (check if a specific fix already landed)
- `RESOLVED_ISSUES.md` — historical closed issues (reference only)
- `trials/_INDEX.md` — structured tags per trial (find trials by failure pattern)
- `trials/T<NN>-*.md` — individual trial detail (read when analyzing a specific trial)

---

## Skill Overview

Two paired skills with distinct responsibilities:
1. **`devtools:implementation-planning`** — turns a feature idea into a design doc + implementation plan + **validated scaffold on disk** (stubs, tests, conftest, Dockerfile, lint/smoke scripts). Owns all scaffolding, test writing, and validation.
2. **`devtools:agent-ready-plans`** — reads validated artifacts from disk and packages them into self-contained task files + manifest + runner script for local coding agents (Aider + local models via LM Studio). Owns only task doc generation and packaging.

**Key architectural decision**: The planning model writes complete, verified tests for each task (TDD approach). The small local model implements the code to make them pass. The planning model owns test correctness — the small model owns implementation.

**Handoff artifact**: Files on disk (stubs, tests, conftest, Dockerfile, scripts), not plan prose. The agent-ready skill reads code from disk, never interprets plan prose for code-level details.

---

## Skill File Structure

```
claude-devtools/
  skills/
    implementation-planning/
      SKILL.md
      references/
        plan-format.md
        wiring-completeness.md
        tooling.md
        test-writing-guide.md
        stacks/
          python-pytest.md
          python-pytest/
            fixture-patterns.md
          typescript-jest.md
          kotlin-junit.md
          infra.md
      scripts/
        lint-ruff-wrapper.sh
        infra-lint-wrapper-template.sh
        docker-smoke-test-template.sh
        validate-stubs.sh
    agent-ready-plans/
      SKILL.md
      task-template.md
      references/
        task-doc-guide.md
      scripts/
        run-tasks-template.sh
```

---

## Strategy (Current)

**Strategy 3: TDD — Planning Model Writes Tests.** The planning model writes complete, verified tests
per task (Step 4). Small model implements to pass them. Strategies 1 (Code-Complete) and
2 (Spec-Based) were abandoned — see `trials/T01-strategy-comparison.md` for rationale.

---

## Model Standings (as of T47 / Chat 10)

- **Gemini 3.1 Flash Lite**: Clean sweeps on T12, T17, T20. T47: 18✅ 1⚠️ (modified test file on integration). All 18 service tasks clean post-refactor.
- **Qwen 3 Coder 30B**: Clean sweeps on T15, T18, T35. T46: 17✅ 1⚠️ (UUIDStore SQL parameterization). Strong but recurring UUIDStore issue.
- **Codestral 22B**: Permanently disqualified (T8, T11, T16). Not fixable at skill level.

Both models validated on the full 19-task pipeline including Docker smoke test and live integration tests.

---

## Open Issues

3. **ACTIONABLE** — Runner: pre-task file backup + restore on critical export loss
22. **INTERMITTENT** — Both models occasionally pass extra kwargs to project-defined dataclasses or fail uuid_filter. Hits different tasks on different runs. Not systematic — grounding rule addresses it but doesn't eliminate non-deterministic model behavior.
23. **SCAFFOLD GAP** — Integration test `test_e2e.py` assumes MinIO bucket exists; test compose doesn't pre-create it. Gemini worked around by modifying test file (T47). Fix: either pre-create bucket in test compose or add bucket creation to conftest/fixture.

> Full historical issue list (including resolved): see `RESOLVED_ISSUES.md`

---

## Context Repository Structure

```
coding-agent-ready-planning-skill/
├── README.md              ← This file (orientation, loaded at conversation start)
├── LEARNINGS.md           ← Distilled principles (loaded at conversation start)
├── CHANGELOG.md           ← Skill changes log (loaded on-demand)
├── RESOLVED_ISSUES.md     ← Historical resolved issues (loaded on-demand)
├── SKILL_CHANGES.md       ← Detailed explanation of the 2026-03-11 fix
└── trials/
    ├── _SUMMARY.md        ← Scoreboard table + model standings
    ├── _INDEX.md           ← Structured tags per trial (find by pattern)
    ├── T01-strategy-comparison.md
    ├── ...
    └── T47-gemini-19-of-19-clean-sweep.md
```

Each trial file is **immutable once written**. New trials add a new file + a row in `_SUMMARY.md` + a row in `_INDEX.md`.
