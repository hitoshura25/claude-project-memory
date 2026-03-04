# Coding Agent Ready Planning Skill — Trial Log

> **Purpose**: Persistent memory across chat sessions for the `devtools:agent-ready-plans` and
> `devtools:implementation-planning` skills. Each entry documents a trial run, findings, and
> any skill/script changes made. Read this at the start of every new chat in this project.
>
> **Skill location**: `~/claude-devtools/skills/agent-ready-plans/`
> **Test project**: `~/health-data-ai-platform` (airflow Google Drive ingestion service)

---

## Skill Overview

Two paired skills:
1. **`devtools:implementation-planning`** — turns a feature idea into a design doc + implementation plan with interface contracts and behavioral specs
2. **`devtools:agent-ready-plans`** — takes those artifacts and produces self-contained task files + scaffold + runner script for local coding agents (Aider + local models via LM Studio)

**Key architectural decision**: Claude Code writes complete, verified tests for each task (TDD approach). The small local model implements the code to make them pass. Claude Code owns test correctness — the small model owns implementation.

---

## Skill File Structure

```
claude-devtools/
  commands/
    agent-ready.md
    plan.md
  skills/
    agent-ready-plans/          <- FLAT under skills/ (nesting causes --plugin-dir failures)
      SKILL.md
      task-template.md
      references/
        writing-guide.md
        tooling.md
      scripts/
        lint-ruff-wrapper.sh
        run-tasks-template.sh
    implementation-planning/
      SKILL.md
      references/
        plan-format.md
        wiring-completeness.md
```

---

## Strategy History

### Strategy 1: Code-Complete Tasks (abandoned)
Claude Code wrote full implementation + tests. Small model transcribed code from plan.

**Result**: Worked well for Codestral 22B (~90% success) because it minimized what the model
had to figure out. Failed when plan had subtle bugs (wrong mock scopes, metaprogramming
patterns) — model exhausted reflections on code it didn't write and couldn't understand.

### Strategy 2: Spec-Based Tasks (abandoned)
Claude Code defines interface contracts + behavioral specs only. Small model writes both
implementation and tests.

**Problem**: Requires a model that can write correct code from specs. Neither Codestral 22B
nor Qwen 30B Q4 clears that bar reliably.

### Strategy 3: TDD — Claude Code Writes Tests (current)
Claude Code writes complete, verified tests per task (Step 3b in SKILL.md). Small model
implements to make them pass. Mutation gate verifies test quality before handoff.

---

## Trial Runs

### Trial Set 1 — Initial Strategy Comparison (2026-02-27 to 2026-03-02)
**Plan**: Airflow Google Drive ingestion service
**Models**: Codestral 22B, Qwen 3 Coder 30B Q4 (via LM Studio)

| Run | Model | Format | Fixtures | Result |
|-----|-------|--------|----------|--------|
| 1 | Codestral 22B | Code-based | None | 12/13 (plan bugs halted) |
| 2 | Codestral 22B | Code-based fixed | None | 6/10 (plan bugs halted) |
| 3 | Codestral 22B | Spec-based | None | 1/15 (wrong imports, cascade) |
| 4 | Qwen 30B Q4 | Spec-based | None | 2/3 (OOM crash) |
| 5 | Qwen 30B Q4 | Spec-based | None | 2/4 (thinking spiral, cascade) |
| 6 | Qwen 30B Q4 | Spec-based | Yes | 1/4 (logic bugs, cascade) |

**Key finding**: Bottleneck is model capability. Codestral reliable as typist (code-based).
Qwen 30B reasons better but fails on non-trivial logic. Spec-based needs ~GPT-4 level model.

---

### Trial Set 2 — TDD Approach (2026-03-03)
**Model**: Qwen 3 Coder 30B Q4
**Tasks**: 18 implementation + 1 deferred
**Result**: 16/18 completed before interruption

**Task 4 (MinioWriter) — DEGRADED**: Model doesn't know `fastavro.writer` API.
Correct: `fastavro.writer(fo, schema, records)`. Model always swapped args 2 and 3.
Recurring bug — also hit by Codestral in Trial 1.

**Tasks 17 + 18 — STUCK (summarizer spiral)**: After task completion, aider fires a
post-task summarization call (~1,557 prompt tokens). Model generates ~25,000 completion
tokens (18-19x ratio). Aider retries every ~10 min indefinitely. Ctrl-C ineffective —
`aider ... | tee` pipeline swallows SIGINT.

---

### Trial Set 3 — After Runner Fixes (2026-03-04)
**Log**: `run-20260304-114920.log`
**Result**: 13 completed, 4 degraded

**`--timeout` ineffective with streaming**: Aider's `--timeout` caps HTTP connection setup
but LM Studio uses `stream: true`. Once streaming starts, timeout never triggers regardless
of generation length. Summarizer spiral still ran (25,439 tokens at 12:02, 25,536 at 12:12).

**`timeout` shell wrapper tried and reverted**: Wrapping aider in `timeout 600 aider ...`
broke Ctrl-C entirely — `tee` pipeline kept pipe alive after timeout killed aider.

**Git restore bug**: Claude Code saw deleted task files in git HEAD, ran
`git checkout HEAD --` and stopped — never re-reading updated skill files. Step 0 added
to SKILL.md to prevent this.

---

## Generated Code Quality Assessment (2026-03-04)

### Infrastructure — Good
- `UUIDStore`: correct (schema, INSERT OR IGNORE, connection lifecycle)
- `GoogleDriveClient`: correct (streaming download loop, right error types)
- `RabbitmqPublisher`: mostly correct (hardcoded timestamp placeholder minor issue)
- `Settings`: correct (pydantic v2, env_prefix, extra="ignore")

### Extractors — Inconsistent

| Extractor | Status | Issue |
|-----------|--------|-------|
| StepsExtractor | OK | Correct if/else for empty seen set |
| BloodGlucoseExtractor | OK | Correct mmol conversion and null guards |
| HRVExtractor | Fragile | Builds `NOT IN ()` before checking empty set; SQLite accepts it accidentally |
| ActiveCaloriesExtractor | Fragile | Same empty-set issue as HRV |
| DistanceExtractor | Bug | `seen_uuid_hexes` ignored entirely — re-ingests all records every run |
| SleepExtractor | Crash | `row["key"]` access requires row_factory not set in DAG; also `row[0]` is int not uuid |
| HeartRateExtractor | Crash | Override `extract()` uses `row["uuid"]` by name — requires row_factory |
| ExerciseSessionExtractor | OK | Only extractor using correct `bytes.fromhex()` BLOB comparison |

5 different UUID dedup strategies across 8 extractors — no canonical approach enforced.

### DAG — Multiple Call-Site Bugs
1. `RabbitmqPublisher(rabbitmq_host, rabbitmq_port, ...)` — class takes `(rabbitmq_url,
   exchange, exchange_type)`, Settings has `rabbitmq_url` not host/port → AttributeError
2. `download_file_by_name(file_name, zip_path)` — method takes only `file_name`, returns
   bytes; DAG ignores return value → zip never written to disk
3. 6 of 11 extractors missing from `EXTRACTORS` list (generated after DAG task ran)
4. `TaskGroup.add()` invalid — tasks join groups via `with` context manager

### MinioWriter — Wrong fastavro Arg Order
`fastavro.writer(buffer, records, schema)` — correct is `fastavro.writer(fo, schema, records)`.
Every write fails. Recurring across all models tested.

---

## Open Issues

1. **Summarizer spiral**: `--timeout` doesn't work with streaming. Real fix: `stream: false`
   in aider config, or server-side `max_tokens` cap in LM Studio. Not yet resolved.
2. **fastavro arg order**: Recurring across models. Add explicit example to `writing-guide.md`.
3. **row_factory assumption**: SleepExtractor and HeartRateExtractor assume `sqlite3.Row`.
   Fix: set `row_factory` in `base.extract()` or enforce positional access in `_to_avro_dict`.
4. **DAG wiring split**: DAG task (12) ran before extractors 13-17 existed. Consider
   splitting into structure task (early) + wiring task (deferred, after all components exist).
5. **UUID dedup**: Add canonical dedup example to `writing-guide.md`.

---

## Skill Changes Log

| Date | File | Change |
|------|------|--------|
| 2026-03-03 | `run-tasks-template.sh` | Added `--timeout 600` to aider invocation |
| 2026-03-03 | `references/writing-guide.md` | Added ABC call site rule |
| 2026-03-04 | `SKILL.md` | Added Step 0: prohibit `git checkout HEAD` restoration of stale artifacts |
| 2026-03-04 | `SKILL.md` Step 7 | Added: do not restore `run-tasks.sh` from git, always copy from template |
| 2026-03-04 | `run-tasks-template.sh` | Reverted `timeout` shell wrapper; kept `--timeout` aider flag |
