# Skill Change Log — 2026-03-11

## Root Cause

The generated task docs in `health-data-ai-platform` still used old inline wiring patterns
because `SKILL.md` and `task-template.md` were never updated. The 2026-03-10 fix updated
`writing-guide.md` and `plan-format.md` correctly, but Claude Code reads `SKILL.md` and
`task-template.md` as the primary instruction source during task doc generation. The
discrepancy caused the generated output to follow the old pattern despite the reference
docs being correct.

## Files Fixed

### `skills/agent-ready-plans/SKILL.md` — Step 5
- **Removed**: `Test scope` bullet (old narrow-scope workaround — test_command covers only created files, omit modified files)
- **Removed**: `Wiring steps` bullet (instructed Claude Code to add wiring to component task docs)
- **Added**: `Component tasks create files only` — explicit rule with reference to writing-guide.md
- **Added**: Explicit test_command scoping rule (run only the task's own test file)
- **Updated**: `Deferred tasks` note now names wiring tasks as the primary deferred case
- **Updated**: Manifest example now includes a wiring task entry to show correct structure
- **Updated**: Bundled Resources row for writing-guide.md updated to mention task scope rules

### `skills/agent-ready-plans/task-template.md`
- **Added**: Warning at top — component tasks have no `## Files to Modify` or `## Wiring` section
- **Removed**: `## Files to Modify` section from template body
- **Removed**: `## Wiring` section from template body (including registry example)
- **Added**: `### Why there is no Wiring or Files to Modify section` — explains cascade failure rationale so future readers understand the rule is intentional

## Principle

Skill changes must propagate to ALL files Claude Code reads during execution, not just
reference docs. SKILL.md is the entry point; task-template.md is the structural template.
If either contains old patterns, the generated output will follow those patterns regardless
of what the reference docs say.
