# Trial Set 3 — After Runner Fixes

**Date**: 2026-03-04 morning
**Log**: `run-20260304-114920.log`
**Model**: Qwen 3 Coder 30B Q4
**Result**: 13 completed, 4 degraded

---

## Analysis

**`--timeout` ineffective with streaming**: Aider's `--timeout` caps HTTP connection setup
but LM Studio uses `stream: true`. Once streaming starts, timeout never triggers regardless
of generation length. Summarizer spiral still ran (25,439 tokens at 12:02, 25,536 at 12:12).

**`timeout` shell wrapper tried and reverted**: Wrapping aider in `timeout 600 aider ...`
broke Ctrl-C entirely — `tee` pipeline kept pipe alive after timeout killed aider.

**Git restore bug**: Claude Code saw deleted task files in git HEAD, ran
`git checkout HEAD --` and stopped — never re-reading updated skill files. Step 0 added
to SKILL.md to prevent this.

---

## Skill Changes

- `SKILL.md`: Added Step 0 — prohibit `git checkout HEAD` restoration of stale artifacts
- `SKILL.md` Step 7: Always copy runner from template, not git
- `run-tasks-template.sh`: Reverted `timeout` shell wrapper; kept `--timeout` aider flag
