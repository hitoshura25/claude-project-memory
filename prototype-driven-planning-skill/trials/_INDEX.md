# Trial Index — Structured Tags

> Find trials by failure pattern, affected component, or root cause.
> Each row is immutable once written.

| Trial | Skill | Model | Result | Tags | Component(s) | Root Cause Summary | Skill Change? |
|-------|-------|-------|--------|------|--------------|-------------------|---------------|
| — | — | — | — | — | — | — | — |

---

## Tag Glossary

> Add new tags here as they emerge. Keep tags lowercase, hyphenated.

| Tag | Meaning |
|-----|---------|
| `clean-sweep` | All tasks/phases passed |
| `scaffold-bug` | Scaffold task ran from wrong directory or missing config |
| `bootstrap-gap` | Tooling environment not available after scaffold |
| `tdd-violation` | TDD pairing constraint violated |
| `schema-validation` | PydanticAI schema caught an error |
| `circuit-breaker` | Task hit retry limit and escalated or stopped |
| `aider-scripting` | Issue with Aider CLI flags or message file |
| `context-exhaustion` | Model ran out of context / OOM |
| `prototype-reference` | Issue with prototype inlining or reference |
| `cwd-selection` | Wrong working directory for task execution |
| `path-rebasing` | File paths not correctly rebased for service root |
