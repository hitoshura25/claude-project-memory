# Trial Summary — Scoreboard

> Quick-reference table. For full analysis, see the individual trial file.

## Pipeline trials (implementation skill)

| Trial | Date | Skill | Executors | Result | Notes |
|-------|------|-------|-----------|--------|-------|
| T01 | 2026-03-31 | implementation | Aider+Qwen | ❌ Partial | 27 tasks, 20/31 reflection exhaustion from I001/F401 lint loops |
| T02 | 2026-04-01 | implementation | Aider+Gemini Flash | ❌ Stalled | Stalled at task-02; enum bug + oversized scaffold + no escalation |
| T03 | 2026-04-02 | implementation | Claude CLI + Aider+Qwen | ❌ Hung | Hung on task-01; wrong `--allowedTools` semantics |
| T04 | 2026-04-03 | implementation | Aider+Qwen → Gemini → Claude | ⚠️ Best run | 15/18 tasks reached, all impl code produced; Claude rate limited |
| T05 | 2026-04-04 | implementation | Claude CLI | ❌ Stalled | Stalled at task-02; verify_task rejected valid test task (missing stubs) |
| T06 | 2026-04-05 | implementation | Aider+Qwen → Gemini → Claude | ✅ First clean run | 21/21 passed; code quality issues found in post-run review |
| T07 | 2026-04-07 | implementation | Aider+Qwen → Gemini → Claude | ⚠️ Partial | 31 tasks; I001 lint loops, Gemini 429s, DAG field drift, integration test sigs wrong |
| T08 | 2026-04-09 | implementation | Aider+Qwen → Gemini → Claude | ⚠️ 19/22 | I001 fixed; 600s timeout drift; Gemini stubs-pass + E501; task-20 failed all tiers |
| T09 | 2026-04-13 | implementation | Aider+Qwen → Gemini → Claude | ⚠️ 12/17 | 8 passed + 4 degraded; ruff missing from dev deps; task-13 stub import bug; timeout still 600s |
| T10 | 2026-04-16 | implementation | Aider+Qwen → Gemini → Claude | ⚠️ 5/19 | Templating refactor validated; split-file test bug (task-07); mock path inconsistency (task-05) |
| T11 | 2026-04-16 | implementation | Aider+Qwen → newer Gemini → Claude | ⚠️ 6/19 | Gemini upgrade fixed mock drift; stubs-pass failures surfaced (defensive defaults) |
| T12 | 2026-04-16 | implementation | Aider+Qwen → Claude (tests) → Claude (impl) | ❌ 2/19 | Claude-as-test-writer; verify_task rigidity rejected valid partial stub (task-02) |
| T13 | 2026-04-17 | implementation | Aider+Qwen → Gemini → Claude | ⚠️ 5/19 | Tight system prompt + tight task-02 spec; all 3 test tasks passed tier 0 r0; task-05/07 are test over-specification failures |
| T14 | 2026-04-19 | implementation | Aider+Qwen → Gemini → Claude | ⚠️ 16/17 | Tight-task-doc + schema refactors validated; only task-16 (integration test) failed — Docker-wrapped test command embedded in task description never reached TASK_TEST_COMMANDS |

## Planning-skill iterations

These are skill-development iterations against the `prototype-driven-planning`
skill, not pipeline runs. Each identifies failure modes in the skill's design
and records the fixes that landed the same day.

| Trial | Date | Target | Focus | Failure modes found | Skill changes |
|-------|------|--------|-------|---------------------|---------------|
| P01 | 2026-04-23 | airflow-google-drive-ingestion | Security tool selection; scope management | Table read as complete spec; silent scope removal | Surface Coverage Check; Scope-Removal Triage; "Tables are starting points" Principle; "Removals from approved scope are user decisions" Principle |
| P02 | 2026-04-23 | airflow-google-drive-ingestion (re-run) | Design-doc review for residual failure modes | Feasibility questions in Deferred Decisions; judgment stated as observation; Phase 1 deferrals conflated with prototype limitations | Assertion test (2nd triage diagnostic); Scope Deferrals from Phase 1 section; Judgment vs. Observation subsection; "Observation and judgment labeled distinctly" Principle |
| P03 | 2026-04-23 | airflow-google-drive-ingestion (third run) | Security finding handling under real CVEs | Severity-blind deferral; environmental assessment used as shortcut; mitigation space not explored | Severity-indexed handling; Mitigation Ladder (5 options including downgrade); Environmental Risk Assessment rules; "Security findings get severity-indexed handling" Principle |

## Roadmap-skill iterations

These are skill-development iterations against the `prototype-driven-roadmap`
skill, not pipeline runs.

| Trial | Date | Target | Focus | Failure modes found | Skill changes |
|-------|------|--------|-------|---------------------|---------------|
| R01 | 2026-04-26 | airflow-gdrive-ingestion | First real trial after design pass; structural-rule completeness | Cross-component category misplacement (parser V8.1.1 described orchestrator's temp-dir step); validator gap on registry-vs-scenario ID-set parity | Required `**Performed by** <slug>` field on every security scenario with hard exit on file-slug mismatch / registry mismatch / missing field; ID-set parity check between `components.yml` `owasp_categories` and per-file security-scenario headings (hard exit on either-direction mismatch); Phase 1 "Naming the actor for each category" subsection + updated proposal message; Phase 2 "Performed-by-grounded" rule + updated example; new template subsection + new anti-patterns; 2 new Principles in SKILL.md |
| R02-prep | 2026-04-30 | (skill rebuild; no project run) | OWASP spec migration + label canonicalization triggered by R01-era review | Stale spec-version pin (ASVS 4.0.3 instead of 5.0.0) with "as of <date>" prose claiming verification that was never done; canonical category labels duplicated across 3 artifact types (reference doc prose, per-scenario `owasp_category_label` field, dedicated spec data files) — three drift surfaces for one fact | New `scripts/owasp-asvs.json` and `scripts/owasp-masvs.json` spec data files with `verified_at` / `verified_against` provenance fields; ASVS regex made version-agnostic and pin moved to JSON; `owasp_category_label` field removed from schema; validator loads spec files at runtime, cross-checks version + category prefix, renders Categories Cited footer with canonical titles; reference docs rebuilt for ASVS 5.0's 17-chapter structure and made abstract about version pin; 6 new principles in LEARNINGS.md (live-verification discipline, single-source-of-truth for labels, force-visibility-applies-to-verification, etc.) |
| R02 | 2026-05-01 | airflow-gdrive-ingestion | First project trial against rebuilt skill (post-OWASP-migration) | None — clean sweep | None |
| R03 | 2026-05-02 | airflow-gdrive-ingestion | Validate scenario `id` field addition (step 1 of three-skill decomposition refactor) | None — clean sweep | Required `id: str` on FunctionalScenario + SecurityScenario; kebab-case format validator; `scenario_ids_unique_within_component` model validator; reference doc updates (Scenario IDs subsection, Phase 2 writing guidance, JSON example, validation rules); schema smoke-tested against 7 cases all pass; regenerated airflow-gdrive-ingestion roadmap with 33 scenarios across 5 components |

## Decomposition-skill iterations

These are skill-development iterations against the
`prototype-driven-task-decomposition` skill, not pipeline runs.

| Trial | Date | Target | Focus | Failure modes found | Skill changes |
|-------|------|--------|-------|---------------------|---------------|
| D01 | 2026-05-04 | airflow-gdrive-ingestion | Validate roadmap consumption (step 3 of three-skill decomposition refactor); first decomposition-skill iteration trial | None — clean sweep | 3 new task fields (`roadmap_component`, `roadmap_functional_scenarios`, `roadmap_security_scenarios`) + 2 new top-level fields (`components_json_path`, `roadmap_json_path`) + 1 field validator + 3 decomposition-level model validators + 4 helper functions (project-shipped schema imports, Levenshtein "Did you mean" hints, three-case unresolved-citation error builder); reference docs rewritten end-to-end (analysis-guide rewritten roadmap-primary, task-writing-guide gained Roadmap-Driven Task Authoring section + `Behaviors to test:` removed, output-format gained new fields + summary table reshape + Integration with Roadmap subsection); SKILL.md updated (Quick Reference, How to Start, Phase 1 renamed, Phase 2 step renumbering, Phase 3 step 4, schema reference table, 3 new Principles); schema smoke-tested against 8 cases all pass; regenerated airflow-gdrive-ingestion decomposition with 13 tasks across 5 components, 60 scenario citations all resolve |
| D02 | 2026-05-06 | airflow-gdrive-ingestion (T15 first attempt) | CWD-relative path resolution surfaced when pipeline ran from its own directory — schema's `Path(self.components_json_path).resolve()` resolved against pipeline CWD, not project root | `cwd-relative-path-resolution` (new tag), `validator-gap` | decomposition: `_PROJECT_ROOT` constant inferred from `__file__` location + `_resolve_project_path` helper + 4 call sites updated (2 in `_load_roadmap_schemas`, 1 each in `validate_roadmap_component_registered` / `validate_roadmap_scenarios_resolve`) + field-description prose updated to make the resolution rule explicit. Implementation: parallel `_resolve_project_path` helper in `compose_prompt.py.template` (sourced from `config.PROJECT_ROOT`, same name+shape as schema's), inline absolute/relative guard in `_load_roadmap` replaced with helper call. Phase 3: Smoke Test section added to phase-3-handoff.md between Syntax Check and Precondition Validation, runs from pipeline directory and exercises both `_resolve_project_path` implementations transitively (`load_tasks_node` for schema-side, `_inline_roadmap_scenarios` for implementation-side); SKILL.md Phase 3 step list renumbered, smoke test as step 3. Project-side artifacts unchanged per directive; user regenerates decomposition + pipeline from fixed skills before retrying T15. |


---

## Progression

### Pipeline trials (T01–T14)

T01 → T02: Introduced model roles (validated test quality). Exposed enum bug and scaffold sizing.
T02 → T03: Introduced Claude CLI as executor. Exposed hardcoded flag assumptions.
T03 → T04: Runtime CLI research, multi-executor escalation. First run to produce all implementation code.
T04 → T05: Re-decomposed with task sizing. Exposed TDD stub gap in verify_task. Led to stub-in-test-task design.
T05 → T06: Stub workflow validated, /no_think + model settings applied, test file inclusion for Aider. First complete run. Post-run review revealed cross-task field name drift, leading to prototype_references removal.
T06 → T07: Re-decomposed with inline patterns + output field contracts. Field drift fixed, structlog everywhere. But I001 lint loops returned as #1 failure mode (unchanged since T01). Led to AIDER_LINT_CMD (auto-fix before check), TeeWriter stdout capture, 300s timeout.
T07 → T08: AIDER_LINT_CMD fixed I001 loops. TeeWriter captured full log. But timeout was still 600s due to config drift (hardcoded literal in example code). Led to config value deduplication.
T08 → T09: MAX_RETRIES=1 cut runtime from 6.9h to 1.8h. But timeout still drifted to 600s (Claude Code memory contamination). ruff missing from dev deps caused early lint failures. Task-13 stub import bug. Led to pipeline templates refactor.
T09 → T10: Templating refactor held (300s timeout stable). Split-file test bug (task-07) and mock path inconsistency (task-05) exposed test-writing quality as a coherence problem, not a generation problem.
T10 → T11: Gemini upgrade improved intra-file consistency; new stubs-pass failure class surfaced where tests with defensive defaults pass against partial stubs instead of failing with NotImplementedError.
T11 → T12: Claude-as-test-writer experiment exposed `verify_task` rigidity for partial stubs — correct output rejected by hardcoded single-pattern check.
T12 → T13: System prompt tightening + per-task tight template eliminated prompt contradictions and noise. All 3 test tasks passed tier 0 retry 0. Remaining failures are test over-specification (task-05) and fixture path bugs (task-07) — a different failure class from prompt-structure issues. Led to skill refactor plan: drop .md outputs from decomposition, tighten task-doc template, bake compose_prompt.py changes into implementation skill templates, add `expected_test_failure_modes` schema field.
T13 → T14: All T13 refactor items landed (tight template, JSON-only output, compose_prompt.py template, `expected_test_failure_modes` field + verify_task wiring). 16/17 passed — jump from T13's 5/19. task-05 (test over-spec) and task-07 (fixture path) both passed this run. Only task-16 failed: integration test's Docker-wrapped `test_command` was embedded in prose in the task description but the Phase 2 generator ignored it, producing a bare `pytest tests/test_integration.py -x` in TASK_TEST_COMMANDS. Services were never started; fixtures hard-failed by design. Led to refactor-plan-2026-04-19: required `test_command: str` schema field, validators for non-empty and integration-lifecycle-wrapping, scaffold also gets test_command (exit-5-tolerant pytest), `TASK_TEST_COMMANDS` populated verbatim from schema. Refactor landed same day pending T15 validation.

### Planning-skill iterations (P01–P03)

P01 → P02: Scope-Removal Triage and Surface Coverage Check held in P02 — multi-tool SAST selection (bandit + semgrep with dockerfile/secrets/python rulesets) appeared in the design doc, and no silent scope removals were flagged. But section-by-section review of the generated design doc revealed two new failure classes: items in Deferred Decisions that passed the "difference test" but required unobserved assertions (e.g., "boto3 upgrade is API-stable"), and judgment-call prose that read as observation ("this is the correct behavior," "should be refactored," "is acceptable"). Also surfaced a conflation between user-approved Phase 1 deferrals and model-designed prototype limitations.

P02 → P03: The assertion test, Scope Deferrals from Phase 1 section, and Judgment vs. Observation rules landed. Third trial exercised security-finding handling under real CVEs (Airflow 2.9.x → 3.x upgrade introducing critical litellm CVEs). The model unilaterally finalized an environmental risk assessment ("we're not running litellm as a public-facing proxy, so attack surface doesn't exist"), chose between only two options (stay or go to 1.83.0), and accepted the new CVEs as the lesser evil without exploring pinning/downgrading/exclusion. This is the same silent-judgment failure pattern as P01/P02 but in the security domain, where the consequences of wrong judgment can be invisible until exploited. Led to severity-indexed handling, Mitigation Ladder (5 options including downgrade), and Environmental Risk Assessment rules.

The three trials share a single underlying failure pattern: **an LLM can reliably do reasoning it has to make visible; it cannot reliably do reasoning it can internalize and shortcut.** The fixes across P01–P03 all share the same shape — force the model's reasoning into visible artifacts (Surface Coverage Check output, Scope-Removal Triage message, assertion-test field, Mitigation Ladder attempt log, Environmental assessment proposal) rather than allowing it to appear as fact-shaped prose.

### Roadmap-skill iterations (R01 → R02-prep → R02)

R01 → R02-prep: R01 surfaced two structural fixes (Performed-by field, ID-set parity check) that landed same-day. Subsequent review of the resulting skill artifacts surfaced two architectural issues that R01's findings didn't directly cover but the surrounding-doc review revealed: a stale OWASP version pin (ASVS 4.0.3 — ASVS 5.0.0 had been out 11 months) and a triple-source-of-truth for category labels (reference doc prose + `owasp_category_label` field + dedicated spec data files in the migration plan). The fix package — separate spec data files in the skill, removed `owasp_category_label`, version-baked ID format, runtime version cross-check, `verified_at`/`verified_against` provenance — landed before R02 ran so R02's findings stay scoped to "did the rebuilt skill behave correctly?" not "are the architectural choices correct?" The same "force visibility" pattern from P01–P03 applies: silent verification ("as of <date>") is the same failure shape as silent judgment, and the structural fix is the same — surface the work into a typed artifact that can be inspected and challenged.

R02-prep → R02: The migration's structural fixes (single source of truth for labels, version-baked IDs, runtime version cross-checks, `verified_at`/`verified_against` provenance) held against the airflow-gdrive-ingestion design doc on first run. R01's Performed-by field and ID-set parity validator carried through unchanged. No new failure modes surfaced. The trial implicitly exercised the Project Setup component (landed via P05) as a registered first component, satisfying the structural part of what would have been R03's acceptance bar.

R02 → R03 (retargeted): R03 was originally queued for Project Setup component validation (which R02-rerun implicitly satisfied). Retargeted per the 2026-05-02 three-skill refactor plan to validate the scenario `id` field addition. Schema gains required, kebab-case, unique-within-component `id` field on every functional and security scenario. Schema smoke-tested against 7 cases (happy + 6 edge); all pass. Regenerated airflow-gdrive-ingestion roadmap: 33 scenarios across 5 components. R03 unblocks D01 (and step 2 of the refactor, which is the implementation skill's `compose_prompt.py.template` change — validated end-to-end by T15 once D01 lands).

### Decomposition-skill iterations (D01)

R03 → D01: First decomposition-skill iteration trial; validates step 3 (the bulk) of the three-skill decomposition refactor. Decomposition consumes the roadmap as primary input — component boundaries come from `components.json`, testable behaviors from `roadmap.json` scenario IDs. The decomposer's freedom narrows to per-component task counts and scenario assignments. Schema gains 3 task fields + 2 top-level fields + 4 validators + helper functions for project-shipped schema imports and Levenshtein "Did you mean" hints. Reference docs rewritten end-to-end. Schema smoke-tested against 8 cases (5 plan-mandated + 3 edge); all pass. Regenerated airflow-gdrive-ingestion decomposition: 13 tasks across 5 components, 60 scenario citations all resolve, `Behaviors to test:` section absent everywhere, stub-import discipline preserved, T14 invariants hold under extended schema. The pattern from T14 ("prose is a lossy transport — promote to typed field") generalized cleanly across the chain: roadmap scenarios got stable IDs (R03), decomposition cites them (D01), implementation pipeline inlines them (already landed; T15 validates). D01 unblocks T15 — the implementation pipeline can now be regenerated against the new tasks.json.

D01 → D02: T15 first attempt surfaced a schema-side CWD-relative-path-resolution bug. The user ran `python run.py` from `pipelines/airflow-gdrive-ingestion/` (the natural directory for a generated pipeline); the schema's `Path(self.components_json_path).resolve()` calls resolved against the pipeline-dir CWD instead of the project root. D01 didn't catch this because validation ran from project root — schema and CWD coincidentally agreed. Fix: `_PROJECT_ROOT` constant + `_resolve_project_path` helper in `task_schema.py`, sourced from `__file__` location; parallel helper in `compose_prompt.py.template` sourced from `config.PROJECT_ROOT`. Two helpers share name + shape; their roots differ because each has access to a different concrete answer. Phase 3 of the implementation skill gains a smoke test that runs from the pipeline directory and exercises both helpers transitively, catching this bug class structurally rather than discovering it at first runtime. Project-side artifacts (`task_schema.py` shipped to the project, regenerated pipeline) unchanged per directive — user regenerates from fixed skills. T15 stays blocked until that regeneration happens.

---

## Model Standings

| Model | Strengths | Weaknesses |
|-------|-----------|------------|
| Qwen 3 Coder 30B | Simplest tasks only (minio_uploader in T09, task-08 in T14 tier-0) | Complex tasks |
| Gemini Flash | Reliable for tests and mid-complexity impl tasks; T14 escalation survived a stray SSL/TLS error mid-run | E501 on string literals; occasional `write_file:` markdown blob output (T14 task-16) |
| Claude CLI | Handles most complex tasks, high code quality; T14 cleaned up several tier-0 Gemini misses | Pro plan rate limit (~1hr active use) |

---

## Skill Standings

| Skill | Status | Last Validated |
|-------|--------|----------------|
| prototype-driven-planning | ✅ Built; Part A + Part C landed 2026-04-23 after 3-iteration refinement arc (P01–P03) | P03 (2026-04-23) |
| prototype-driven-task-decomposition | ✅ Built; D02 landed 2026-05-06 (`_resolve_project_path` helper + 4 updated call sites in `task_schema.py`) on top of D01 (2026-05-04, roadmap consumption); CWD-relative-path-resolution bug surfaced at T15 first attempt and structurally fixed | D02 (2026-05-06) |
| prototype-driven-roadmap | ✅ Built; R03 landed 2026-05-02 (scenario `id` field for stable downstream citation); R02 re-run 2026-05-01 validated rebuilt skill | R03 (2026-05-02) |
| prototype-driven-implementation | ✅ Built; T14-refactor landed 2026-04-19 (TASK_TEST_COMMANDS verbatim from schema; scaffold runs test_command); compose_prompt.py.template gained `_inline_roadmap_scenarios` 2026-05-03; D02-parallel changes landed 2026-05-06 (`_resolve_project_path` helper hoisted from inline guard, Phase 3 smoke test added) | D02 (2026-05-06) |
