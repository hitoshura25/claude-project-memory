# Trial Index — Structured Tags

> Find trials by failure pattern, affected component, or root cause.
> Each row is immutable once written.

## Pipeline trials (implementation skill)

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
| T14 | implementation | Qwen+Gemini+Claude | ⚠️ 16/17 | `lossy-prose-transport`, `test-command-gap`, `integration-test-no-services` | Phase 2 generation, config.py TASK_TEST_COMMANDS, task-16 integration | T13 refactor landed and held (tight task-doc, JSON-only output, expected_test_failure_modes). Only task-16 failed: Docker-compose-wrapped test_command embedded in task description prose but Phase 2 derived plain `pytest <file> -x` with no lifecycle. Tests ran without services; fixtures hard-failed by design. | Yes — refactor plan 2026-04-19: required `test_command: str` schema field + validators |

## Planning-skill iterations

| Trial | Skill | Target | Result | Tags | Section(s) Changed | Root Cause Summary | Skill Change? |
|-------|-------|--------|--------|------|--------------------|-------------------|---------------|
| P01 | planning | airflow-google-drive-ingestion | ⚠️ 2 failure modes | `table-as-complete-spec`, `silent-scope-removal`, `surface-coverage-gap`, `judgment-as-fact` | phase-2-prototype.md (Security Tooling Validation, Scope-Removal Triage), SKILL.md (Phase 2 Step 7, STOP report, Principles) | Security tool selection table read as complete specification (bandit only for a project with Dockerfile + compose); Airflow DB persistence silently dropped from approved Phase 1 scope with "for the prototype, X isn't needed" rationalization | Yes — Surface Coverage Check + Scope-Removal Triage + 2 Principles |
| P02 | planning | airflow-google-drive-ingestion | ⚠️ 3 failure modes | `feasibility-in-disguise`, `judgment-as-fact`, `deferred-decisions-abuse`, `phase-1-scope-ambiguity` | phase-3-design-doc.md (Open Questions Triage adds assertion test, Judgment vs. Observation subsection in Writing Quality), design-doc-template.md (Scope Deferrals from Phase 1 section added), SKILL.md (Principles) | Deferred Decisions contained items passing "difference test" but failing an unstated "assertion test" (the design doc asserts something unobserved, e.g., "boto3 upgrade is API-stable"); judgment-call prose indistinguishable from observation prose; Phase 1 user-approved deferrals conflated with model-designed prototype limitations | Yes — assertion test (2nd triage diagnostic) + Scope Deferrals from Phase 1 section + Judgment vs. Observation + Principle |
| P03 | planning | airflow-google-drive-ingestion | ⚠️ 3 failure modes | `severity-blind-handling`, `environmental-assessment-shortcut`, `transitive-reachability-handwave`, `lesser-evil-tradeoff` | phase-2-prototype.md (Handling findings subsection, Mitigation Ladder subsection, Environmental Risk Assessment subsection), SKILL.md (Phase 2 Step 7, STOP report, Principle) | Critical CVEs proposed for routine deferral (no severity policy); environmental risk assessment finalized unilaterally without user review; only two mitigation options considered (stay-or-upgrade); downgrade/pin/override/exclude not explored; transitive reachability claimed without specific evidence | Yes — Severity-indexed handling + Mitigation Ladder + Environmental Risk Assessment + Principle |

## Roadmap-skill iterations

| Trial | Skill | Target | Result | Tags | Section(s) Changed | Root Cause Summary | Skill Change? |
|-------|-------|--------|--------|------|--------------------|-------------------|---------------|
| R01 | roadmap | airflow-gdrive-ingestion | ⚠️ 2 failure modes | `cross-component-misplacement`, `id-set-drift-class`, `validator-gap`, `silent-actor-assumption` | scripts/validate_roadmap.py (check 17 ID-set parity, Performed-by field check), roadmap-item-template.md (Performed-by subsection, scenario-structure rule, anti-patterns), components-yml-format.md (rules 17+18), phase-1-extraction.md (Naming the actor subsection, proposal-message template), phase-2-generation.md (Performed-by-grounded bullet, example), SKILL.md (2 Principles) | Output passed all existing structural rules. Review surfaced (a) parser V8.1.1 scenario described work the orchestrator performs, not the parser — a category-placement misalignment invisible to a structural validator; (b) registry-vs-scenario ID-set drift was mechanically possible because the validator only format-checked IDs, never compared sets | Yes — ID-set parity validator check (A) + required `Performed by` field with file-slug + registry checks (B3) + reference doc updates |
| R02-prep | roadmap | (skill rebuild; no project run) | ⚠️ 2 architectural issues | `stale-spec-pin`, `pseudo-verification`, `triple-source-of-truth`, `version-baked-id-missing` | scripts/owasp-asvs.json (new), scripts/owasp-masvs.json (new), scripts/components_schema.py (regex), scripts/roadmap_schema.py (regex + remove `owasp_category_label`), scripts/validate_roadmap.py (spec-loading + runtime cross-checks + Categories Cited footer), references/owasp-asvs-mapping.md (rebuilt for 17 chapters), references/owasp-masvs-mapping.md (PRIVACY data flows added), references/phase-1-extraction.md, references/phase-2-generation.md, references/phase-3-validation.md, references/components-json-format.md, references/roadmap-json-format.md, SKILL.md (live-verification principle added) | Reference docs pinned to ASVS 4.0.3 with "as of <date>" prose claiming verification that was never done — ASVS 5.0.0 had been out 11 months. Category labels duplicated across reference doc prose, per-scenario `owasp_category_label` field, and (planned) spec data files — three sources of one fact, three drift surfaces | Yes — `verified_at`/`verified_against` fields + spec data files as single source of truth + `owasp_category_label` removed from schema + version-baked ID format + 6 new principles in LEARNINGS |
| R02 | roadmap | airflow-gdrive-ingestion (post-P05 design doc) | ✅ Clean sweep | `clean-sweep`, `validation-run` | (none — validation run) | First project trial against the rebuilt skill (post-OWASP-migration). All 6 acceptance criteria green: JSON output written, ASVS 5.0.0 version-baked IDs across all scenarios, `owasp_category_label` absent, validator exits 0 with Categories Cited footer, R01 placement fix survives (mkstemp on drive-downloader; at-rest encryption on minio-uploader; AMQP TLS on rabbitmq-publisher), structural rules (Performed-by, ID-set parity, `depends_on` parity) fire correctly. Project Setup component implicitly exercised. | No |

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
| `lossy-prose-transport` | Task description prose contains a specific command, contract, or value that the downstream skill has no schema field to read; information is lost in translation |
| `test-command-gap` | Per-task verification command lives only in prose; generator substitutes a generic default that doesn't meet the task's actual needs |
| `integration-test-no-services` | Integration test runs without the external services it depends on being started; fixtures fail by design |
| `silent-scope-removal` | Model drops an approved-scope item mid-phase without surfacing the removal to the user (often framed as "for the prototype, X isn't needed") |
| `table-as-complete-spec` | Model reads a reference table in the skill as an exhaustive specification (one cell per question) rather than as a starting point for reasoning about additional surfaces or options |
| `surface-coverage-gap` | Security tooling runs only against the primary language surface (e.g., bandit on Python) and misses additional file surfaces carried by the prototype (Dockerfile, docker-compose, IaC, shell) |
| `judgment-as-fact` | Model states a judgment call in observation-shaped prose, without citing evidence or labeling it as inference — makes the claim indistinguishable from prototype observation to a future reader |
| `feasibility-in-disguise` | An open question framed as an operational decision (passes the "difference test" of not changing architecture) but requires the design doc to assert something the prototype didn't observe (fails the "assertion test") |
| `deferred-decisions-abuse` | Items placed in Deferred Decisions that should have required user decision or prototype extension, masked by "implementation-phase decision" framing |
| `phase-1-scope-ambiguity` | Design doc conflates user-approved Phase 1 scope deferrals with model-designed prototype minimum-viable-validation limitations; downstream readers can't distinguish the two |
| `severity-blind-handling` | Security findings treated uniformly regardless of Critical/High/Medium/Low severity; routine deferral path offered for Critical findings that should block |
| `environmental-assessment-shortcut` | Model uses contextual CVSS reasoning ("this doesn't apply to us because we're not running a public proxy") to accept findings without first exploring mitigations; environmental assessment finalized unilaterally without user review |
| `transitive-reachability-handwave` | Assessment that vulnerable code is unreachable lacks specific evidence (module-level import graph, reachability analysis) — relies on shape-of-argument rather than concrete observation |
| `lesser-evil-tradeoff` | Model presents two options and picks the less-bad one without exploring the fuller option space (pinning, downgrading, overriding, excluding, replacing) |
| `cross-component-misplacement` | A security scenario is attached to the file of a component that consumes the result of an action rather than the file of the component whose code performs the action; valid format and real concern, but wrong placement |
| `id-set-drift-class` | Set of OWASP IDs in `components.yml` and the set cited in per-file scenario headings can drift independently because the validator only format-checks IDs, never compares sets |
| `validator-gap` | A failure class is mechanically preventable (sets must match, fields must be present) but the validator doesn't check it; closing the gap is a structural fix, not a model-behavior fix |
| `silent-actor-assumption` | A security scenario assumes the file's component is the actor; reviewer cannot tell whether the model considered other components without an explicit Performed-by field |
| `stale-spec-pin` | Skill reference doc pins to an outdated version of an external standard (e.g., OWASP ASVS) without verifying current state; the pin reads as authoritative but no verification was done |
| `pseudo-verification` | Prose in a skill or doc claims verification that didn't happen (e.g., "as of <date>"); the parenthetical reads as evidence of a check, but the check was never performed |
| `triple-source-of-truth` | Same canonical fact (e.g., a category label) stored across three artifact types (reference doc prose, per-scenario field, dedicated data file) — three drift surfaces for one fact |
| `version-baked-id-missing` | Standard's older ID format omits version (e.g., ASVS 4.x's `V<n>.<n>.<n>`); citations across spec versions become ambiguous and version-mismatch is invisible at the ID level |
| `validation-run` | Run that exercises a previously-built skill against a real feature with no skill changes intended; success means no new failure modes surface |
