# T44 — Qwen 30B: Post-Refactor Scaffold Validation Gaps (Chat 10)

**Date**: 2026-03-24
**Model**: Qwen 3 Coder 30B (Q4, 32k context)
**Log**: `run-20260324-100126.log`
**Chat**: 10
**Verdict**: 3 degraded tasks due to planning-model scaffold validation bugs; run still in progress when analyzed

## Result (partial — run still in progress at analysis time)

| Task | Result | Notes |
|------|--------|-------|
| 01 Settings | ✅ | |
| 02 UUIDStore | ✅ | |
| 03 BaseRecordExtractor | ✅ | |
| 04 MinIOWriter | ✅ | |
| 05 RabbitMQPublisher | ✅ | |
| 06 Downloader | ⚠️ DEGRADED | `test_extract_sqlite_returns_path` + `test_extract_sqlite_no_db_raises` fail with FileNotFoundError (credential loading in constructor) |
| 07 BloodGlucose | ✅ | |
| 08 HeartRate | ⚠️ DEGRADED | `TypeError: Can't instantiate abstract class` — `@abstractmethod` on `_row_to_record` in base, HeartRate stub doesn't implement it |
| 09 HRV | ✅ | |
| 10 Steps | ✅ | |
| 11 Sleep | ⚠️ DEGRADED | Same as T08 — `@abstractmethod` prevents instantiation |
| 12–19 | In progress | |

## Context: Major Skill Refactor (Chat 10)

This trial ran after a major structural refactor of the two skills:

**Implementation-planning** absorbed scaffold setup, test writing, and validation from agent-ready-plans. It now owns Steps 3–4: tooling, conftest, stubs, tests, Dockerfile, lint/smoke scripts, and the three-layer validation gate.

**Agent-ready-plans** shrank to packaging only: reads validated artifacts from disk, generates task docs + manifest + runner. No longer interprets plan prose for code-level details.

**Reference files moved** from `agent-ready-plans/references/` to `implementation-planning/references/`: `tooling.md`, `stacks/`, `fixture-patterns.md`. `writing-guide.md` split into `test-writing-guide.md` (impl-planning) and `task-doc-guide.md` (agent-ready).

**Scripts moved**: `lint-ruff-wrapper.sh`, `infra-lint-wrapper-template.sh`, `docker-smoke-test-template.sh` → `implementation-planning/scripts/`. Only `run-tasks-template.sh` stays with agent-ready.

**Plan-format.md lightened**: Interface sections still had code blocks in this run (fix applied after analysis — see Root Causes below).

## Root Cause 1: Downloader constructor loads credentials eagerly

`test_extract_sqlite_returns_path` and `test_extract_sqlite_no_db_raises` construct `HealthConnectDownloader("/fake/sa.json")` without the `mock_drive_service` fixture. These tests only exercise `extract_sqlite` (a pure ZIP operation), but the constructor calls `Credentials.from_service_account_file("/fake/sa.json")` which hits the real filesystem. The `mock_drive_service` fixture patches `Credentials`, but only the download tests use it.

**Why validation didn't catch it:** The stub's `__init__` raises `NotImplementedError`, so the real credential loading never fires during Layer 2 validation. Tests "correctly" fail with `NotImplementedError` against the stub, masking the fact that the real constructor has side effects the tests don't account for.

## Root Cause 2: `@abstractmethod` prevents subclass instantiation

`BaseRecordExtractor._row_to_record` is decorated with `@abstractmethod`. `HeartRateExtractor` and `SleepExtractor` intentionally skip `_row_to_record` (they override `extract` directly for multi-table joins). But Python refuses to instantiate a class with an unimplemented `@abstractmethod`, even if the subclass overrides a different method.

**Previous occurrence:** T11 (Codestral) had the exact same error: "ABC not implemented — overrode `extract()` but omitted `_row_to_record()` stub." That was attributed to Codestral's model-level deficiency, but the underlying issue was the same. In previous clean sweeps (T12, T18), the base class stub used `raise NotImplementedError` without `@abstractmethod`, which Python doesn't enforce at instantiation time.

**Why validation didn't catch it:** Same as Root Cause 1 — the stub's `_row_to_record` body (`raise NotImplementedError`) satisfies ABC enforcement. The real HeartRate/Sleep implementations will skip it, but stubs don't.

**Dedup failure (secondary):** After Qwen added a dummy `_row_to_record` to satisfy the ABC, its `extract` override didn't properly call `uuid_store.filter_new`, resulting in `assert 2 == 1` on dedup tests.

## Root Cause 3: Claude Code truncated validation output

Investigation of Claude Code logs (session `fdcfe3a4`) revealed the planning model ran Layer 2 validation using:
```bash
uv run pytest tests/ -q 2>&1 | tail -20
uv run pytest tests/ -q 2>&1 | grep -E "(PASSED|ERROR|FAILED)" | grep -v "NotImplemented" | head -20
```

The `head -20` and `tail -20` pipes truncated the output, hiding HeartRate, Sleep, and downloader failures entirely. Claude Code saw the first 20 filtered lines (UUIDStore setup errors + some extractor failures), investigated 3 specific test files (downloader + 2 minio writer), saw `NotImplementedError`, and declared "Layer 2 is clean" without checking the remaining test files.

The existing Layer 2 rule ("verify all fail for the right reason") was correct but was implemented as a manual check that the planning model executed incompletely.

## Skill Fixes Applied

### Fix 1: Automated Layer 2 validation script

New `implementation-planning/scripts/validate-stubs.sh` replaces the manual Layer 2 check. The script:
- Runs each test file individually (no batch `pytest tests/` with truncated output)
- Parses every `FAILED` and `ERROR` line programmatically
- Accepts only `NotImplementedError` and `AssertionError` as valid failure types
- Rejects `TypeError`, `FileNotFoundError`, `ImportError`, setup errors, etc.
- Exits non-zero with clear per-test diagnostics if any invalid failure is found

`SKILL.md` Step 4 updated: "Run `scripts/validate-stubs.sh` — do NOT use `pytest | tail` or any manual/truncated approach. Do NOT proceed until this script exits 0."

`test-writing-guide.md` Layer 2 updated to reference the script with specific examples of rejected error types.

### Fix 2: Interface code blocks removed from plan-format.md

Plan task template `Interface:` section changed from code blocks to prose bullet points. `Writing Interface Descriptions` section explicitly prohibits code blocks and explains why: code blocks look authoritative but are unvalidated, causing the planning model to copy them into stubs without thinking through implications (like `@abstractmethod` breaking subclass instantiation).

The planning model now makes code-level decisions during Step 3 (stub writing) where they're caught by the validation script in Step 4.

## Outcome

Not a clean trial. Three failures trace to planning-model scaffold validation gaps, not Qwen's implementation ability. The refactored skill structure (impl-planning owns scaffold, agent-ready owns packaging) is sound — the Settings task doc correctly had actual defaults from the on-disk stub, confirming the T43 fix works. The remaining issues are in validation thoroughness, addressed by the validation script.
