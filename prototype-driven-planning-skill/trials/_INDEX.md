# Trial Index — Structured Tags

> Find trials by failure pattern, affected component, or root cause.
> Each row is immutable once written.

| Trial | Skill | Model | Result | Tags | Component(s) | Root Cause Summary | Skill Change? |
|-------|-------|-------|--------|------|--------------|-------------------|---------------|
| T01 | implementation | Qwen 3 Coder 30B | ❌ Partial | `circuit-breaker`, `aider-scripting` | verify_task, Aider lint loop | Qwen can't fix I001/F401 ruff errors; burns reflection cycles | Yes — auto-fix step, ecosystem runners |
| T02 | implementation | Gemini Flash | ❌ Stalled | `scaffold-bug`, `aider-scripting` | load_tasks, scaffold prompt | Enum serialization bug + oversized scaffold (19 files) | Yes — model_dump(mode="json"), multi-executor design |
| T03 | implementation | Claude CLI | ❌ Hung | `aider-scripting`, `cwd-selection` | agent_bridge (Claude CLI) | Hardcoded --allowedTools auto-approves not restricts; headless hang | Yes — Phase 1 runtime CLI research |
| T04 | implementation | Qwen+Gemini+Claude | ⚠️ Best | `circuit-breaker`, `context-exhaustion` | escalate_executor, parser task | Qwen repetition loops (no thinking mode); parser too complex; Claude rate limited | Yes — Step 1b model research, test file inclusion, task sizing rules |
| T05 | implementation | Claude CLI | ❌ Stalled | `tdd-violation`, `scaffold-bug` | verify_task, test task stubs | verify_task rejected valid test task; ModuleNotFoundError treated as collection error; no stubs existed for module under test | Yes — stub field in schema, stub-in-test-task design, verify_task rewrite |

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
| `context-exhaustion` | Model ran out of context / OOM / repetition loop |
| `prototype-reference` | Issue with prototype inlining or reference |
| `cwd-selection` | Wrong working directory for task execution |
| `path-rebasing` | File paths not correctly rebased for service root |
| `rate-limit` | Cloud executor hit usage rate limit |
| `enum-serialization` | Pydantic enum not serialized to string |
| `task-sizing` | Task too complex for target model capacity |
| `stub-gap` | Test task imports module with no stub; causes ImportError instead of NotImplementedError |
