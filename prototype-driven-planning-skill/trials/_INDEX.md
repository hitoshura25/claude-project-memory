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
| T06 | implementation | Qwen+Gemini+Claude | ✅ Clean | `clean-sweep`, `prototype-reference`, `cross-task-drift` | compose_prompt, task descriptions | Prototype code in prompt conflicted with task description; models followed code over prose; field name mismatches and broken integration test signatures found post-run | Yes — removed prototype_references, added inline patterns + output field contracts |
| T07 | implementation | Qwen+Gemini+Claude | ⚠️ Partial | `lint-loop`, `rate-limit`, `cross-task-drift` | Aider lint cmd, DAG wiring, integration tests | I001 lint loops returned; Gemini 429s on escalation; DAG field drift (missing depends_on); integration test signatures wrong | Yes — AIDER_LINT_CMD, TeeWriter, 300s timeout |
| T08 | implementation | Qwen+Gemini+Claude | ⚠️ 19/22 | `config-drift`, `lint-format-gap`, `stub-pass` | config.py, Aider lint chain | Timeout 600s (literal in example code conflicted with template), Gemini stubs-pass, E501 on string literals | Yes — config value dedup, string-literals-as-constants rule |
| T09 | implementation | Qwen+Gemini+Claude | ⚠️ 12/17 | `config-drift`, `bootstrap-gap`, `stub-mock-import` | config.py, scaffold deps, stub writing | 600s timeout persisted (memory contamination); ruff missing from dev deps; task-13 stub missing pika import for mock patch | Yes — pipeline templates refactor, integrated bootstrap, stub mock-import rule |
| T10 | implementation | Qwen+Gemini+Claude | ⚠️ 5/19 | `split-module-tests`, `mock-path-inconsistency`, `test-writing-coherence` | decomposition (parser split), tests/test_drive_downloader.py | Parser split across task-07/task-08 both sharing tests/test_parser.py; Gemini wrote tests with inconsistent mock paths in same file | Queued — tight task-doc template, systemic test-coherence fix |
| T11 | implementation | Qwen+newGemini+Claude | ⚠️ 6/19 | `stubs-pass-defensive`, `split-module-tests` | test-writer output, verify_task logic | Newer Gemini fixed intra-file mock drift but wrote defensive-default tests that pass against partial stubs instead of raising NotImplementedError | Queued — explicit "expected test failure mode" in task spec |
| T12 | implementation | Qwen+Claude-tests+Claude-impl | ❌ 2/19 | `partial-stub-gap`, `verify-rigidity` | verify_task stub-pattern check | Claude produced valid partial stub (Pydantic fields + one NotImplementedError method); verify_task's hardcoded single-pattern check rejected correct output because pytest -x ordering hid the raise | Queued — `expected_test_failure_modes` schema field |
| T13 | implementation | Qwen+Gemini+Claude | ⚠️ 5/19 | `test-over-specification`, `fixture-path-bug`, `system-prompt-bloat-fixed` | compose_prompt system prompt, task-02 spec, Gemini test assertions | Tight system prompt + tight task-02 spec passed all 3 test tasks on first Gemini attempt; remaining failures are test over-specification (task-05) and fixture path resolution (task-07) | Queued — refactor plan 2026-04-17 |

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
| `cross-task-drift` | Field names, signatures, or contracts mismatch across tasks due to no shared validation |
| `lint-loop` | Model burns reflection cycles on auto-fixable lint errors |
| `config-drift` | Config value differs between skill reference (desired) and generated pipeline (actual) due to regeneration from model memory |
| `lint-format-gap` | Linter auto-fix + formatter can't fix a lint error class (e.g., E501 on long string literals) |
| `stub-pass` / `stubs-pass-defensive` | Test passes against a stub instead of raising stub error, because test uses defensive defaults or asserts on placeholder values |
| `stub-mock-import` | Stub missing import of third-party dependency that tests mock at module boundary |
| `split-module-tests` | One module split across multiple tasks, all sharing a single test file; test gate runs whole file so no individual task can pass |
| `mock-path-inconsistency` | Same test file patches the same dependency via multiple different module paths |
| `test-writing-coherence` | Test-writing model produces individually-correct tests that collectively drift |
| `partial-stub-gap` | Component has mixed declarative + stubbed parts; `verify_task`'s single-pattern check can't model this |
| `verify-rigidity` | Pipeline's verification check rejects correct output due to structural gap in what the check can recognize |
| `test-over-specification` | Tests assert on details absent from task spec, blocking any implementation from satisfying them |
| `fixture-path-bug` | Test fixture uses path-resolution logic that resolves wrong under the current project layout |
| `system-prompt-bloat-fixed` | Tightening the per-prompt system-message content eliminated a failure class |
