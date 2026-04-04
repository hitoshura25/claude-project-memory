# T03 — Claude CLI as Scaffold/Test Executor (Pre-Research Fix)

| Field | Value |
|-------|-------|
| **Date** | 2026-04-02 |
| **Skill** | prototype-driven-implementation |
| **Executors** | Claude CLI (scaffold/test), Aider + Qwen (implementation) |
| **Escalation** | Planned but never reached |
| **Test project** | health-data-ai-platform / airflow-google-drive-ingestion |
| **Result** | ❌ Hung on task-01 — pipeline never progressed |

---

## Setup

- 18 tasks
- Claude CLI introduced as executor for scaffold and test tasks
- Aider + Qwen for implementation tasks
- Hardcoded CLI flags: `--allowedTools "Read,Write,Edit,Bash"`

## Results

- **Tasks attempted:** 1 (task-01 scaffold via Claude CLI)
- **Duration:** Hung indefinitely
- **Output:** None — pipeline stuck waiting for Claude CLI subprocess

### What Happened

The pipeline invoked Claude CLI with `--allowedTools "Read,Write,Edit,Bash"`.
The assumption was that `--allowedTools` restricts which tools Claude can use.
In reality, `--allowedTools` **auto-approves** the listed tools but doesn't
prevent Claude from trying to use other tools. In headless/non-interactive mode,
when Claude attempts an unapproved tool, it hangs waiting for user approval
that never comes.

The subprocess call blocked indefinitely. No timeout was configured for this
executor type, so the pipeline never progressed.

## Root Cause

**Hardcoded CLI flags based on wrong assumptions.** The `--allowedTools` flag
semantics were different from what was assumed. The skill had hardcoded patterns
in `executor-integration.md` without validating them against the actual CLI
documentation.

## Skill Changes

1. **Phase 1 now researches CLI docs at runtime:** Web search for official
   documentation, then test prompt verification, instead of hardcoded flag patterns
2. **Step 1 updated in `phase-1-analysis.md`:** Detect CLIs on PATH → search
   for official docs → run test prompt → record verified pattern
3. `executor-integration.md` updated to use research-driven patterns

## Key Learnings

- Never hardcode CLI flags — CLI semantics change and assumptions go stale
- Runtime research (search docs + test prompt) is more robust than static patterns
- Headless CLI execution needs explicit timeout handling
