# Coding Agent Ready Planning Skill — Project Context

> **Purpose**: Persistent memory across chat sessions for the `devtools:agent-ready-plans` and
> `devtools:implementation-planning` skills.
>
> **Skill location**: `~/claude-devtools/skills/agent-ready-plans/`
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

Two paired skills:
1. **`devtools:implementation-planning`** — turns a feature idea into a design doc + implementation plan with interface contracts and behavioral specs
2. **`devtools:agent-ready-plans`** — takes those artifacts and produces self-contained task files + scaffold + runner script for local coding agents (Aider + local models via LM Studio)

**Key architectural decision**: The planning model writes complete, verified tests for each task (TDD approach). The small local model implements the code to make them pass. The planning model owns test correctness — the small model owns implementation.

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
            fixture-patterns.md
          typescript-jest.md
          kotlin-junit.md
          infra.md
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

**Strategy 3: TDD — Planning Model Writes Tests.** The planning model writes complete, verified tests
per task (Step 3b). Small model implements to pass them. Strategies 1 (Code-Complete) and
2 (Spec-Based) were abandoned — see `trials/T01-strategy-comparison.md` for rationale.

---

## Model Standings (as of T41 / Chat 9)

- **Qwen 3 Coder 30B**: Clean sweeps on T15, T18, T35. Baseline: 17–18✅ + integration 3/3 with `--no-git`. Repo map (T38) causes regression — do not use. T40 halted early (Metal GPU OOM).
- **Gemini 3.1 Flash Lite**: Clean sweeps on T12, T17, T20. T37: 18✅ + integration 3/3 ✅. T41: 17✅ service tasks, Docker exit(1). Stronger self-correction on Avro schemas.
- **Codestral 22B**: Permanently disqualified (T8, T11, T16). Not fixable at skill level.

Both models validated on the full 19-task pipeline including Docker smoke test and live integration tests (T36, T37).

---

## Open Issues

3. **ACTIONABLE** — Runner: pre-task file backup + restore on critical export loss
22. **INTERMITTENT** — Both models occasionally pass extra kwargs to project-defined dataclasses or fail uuid_filter. Hits different tasks on different runs. Not systematic — grounding rule addresses it but doesn't eliminate non-deterministic model behavior.
23. **CLOSED (T38)** — Aider repo map regression. Reverted to `--no-git`.
24. **CLOSED (T41)** — DAG Assembly `sys.modules` mock constructor trap. Fix validated — explicit attribute assignments after constructor.

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
    └── T41-gemini-post-sysmodules-fix.md
```

Each trial file is **immutable once written**. New trials add a new file + a row in `_SUMMARY.md` + a row in `_INDEX.md`.
