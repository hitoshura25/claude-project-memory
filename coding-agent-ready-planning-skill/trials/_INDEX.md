# Trial Index — Structured Tags

> Find trials by failure pattern, component, or root cause instead of reading sequentially.
> Load on-demand when investigating a specific pattern.

## Failure Category Vocabulary

- `strategy-eval` — Strategy comparison / approach selection
- `context-exhaustion` — Summarizer spiral, OOM, degenerate output loop
- `sqlite-trap` — `:memory:` multi-connection, persistent conn, SQL patterns
- `e501-cascade` — Line-too-long → reflection exhaustion → ISE/OOM chain
- `cascade` — One task failure propagating to downstream tasks
- `docker-lifecycle` — Image tags, Dockerfile build, compose, smoke test
- `task-doc-gap` — Missing or ambiguous spec in task doc / Behavior section
- `fixture-interaction` — Capture mock + assertion contradiction, mock wiring
- `import-integrity` — Wrong imports, hallucinated modules
- `model-disqualified` — Codestral test-file corruption
- `runner-bug` — Runner script issues (timeout, duplicate launch, service gating)
- `pip-pinning` — Version fabrication, DL3013, freeze flow
- `test-authoring` — Claude Code test quality (embedding divergence, missing guidance)
- `clean-sweep` — All tasks passed
- `grounding-validated` — Code-grounding rule validated (task docs derived from code)
- `integration-validated` — Integration tests passed against live services

## Index

| Trial | Model | Result | Categories | Components | Root Cause | Skill Change? |
|-------|-------|--------|------------|------------|------------|---------------|
| T01 | Codestral, Qwen | Strategy comparison | `strategy-eval` | all | Strategy 1+2 abandoned | Yes (adopted TDD) |
| T02 | Qwen | 16/18 interrupted | `context-exhaustion` | — | Summarizer spiral | Yes (timeout) |
| T03 | Qwen | 13✅ 4⚠️ | `runner-bug` | — | --timeout ineffective; git restore | Yes (runner fixes) |
| T04 | Qwen | Crashed task 9 | `context-exhaustion` | — | 12k context → Metal GPU OOM | No (reverted; floor=32k) |
| T05 | Qwen | 18 completed | `task-doc-gap` | HeartRate | Contract mismatch | Yes (ABC call site) |
| T06 | Qwen | 11✅ halted 12 | `sqlite-trap`, `fixture-interaction` | UUIDStore, RabbitMQ | CREATE TABLE; dotted mock | Yes (tooling.md) |
| T07 | Qwen | 9✅ halted 13 | `cascade`, `sqlite-trap` | UUIDStore, conftest | Cascade root cause identified | Yes (redesign) |
| T08 | Codestral | 5✅ 13⚠️ | `model-disqualified` | all | Test file corruption | No (model issue) |
| T09 | Gemini 2.0 FL | 12✅ halted 14 | `cascade`, `import-integrity` | — | Hallucinated import; cascade confirmed | No (structural) |
| T10 | Qwen | 15✅ 2⚠️ | `sqlite-trap` | UUIDStore | Multi-column IN trap | Yes (python-pytest.md) |
| T11 | Codestral | 7✅ 9⚠️ | `model-disqualified` | all | Second disqualification signal | No |
| T12 | Gemini 3.1 FL | **17/17 ✅** | `clean-sweep` | — | — | No |
| T13 | Qwen | 17✅ 1⚠️ | `e501-cascade` | Wire DAG | E501 spiral + ISE | Yes (import_integrity) |
| T14 | Qwen | 16✅ 1❌ | `e501-cascade`, `context-exhaustion` | Wire DAG | ISE → OOM; fatal context bloat | No (same root as T13) |
| T15 | Qwen | **18/18 ✅** | `clean-sweep` | — | — | No (validated snippet fix) |
| T16 | Codestral | 2✅ 1❌ | `model-disqualified` | — | **Permanently disqualified** | No |
| T17 | Gemini 3.1 FL | **18/18 ✅** | `clean-sweep` | — | — | No |
| T18 | Qwen | **18/18 ✅** | `clean-sweep` | — | — | No |
| T19 | Qwen | 17✅ 2⚠️ | `fixture-interaction`, `runner-bug` | RabbitMQ, Docker | `is_closed` mock; empty test_command | Yes (Chat 5) |
| T20 | Gemini 3.1 FL | **18/18 ✅** | `clean-sweep` | — | — | No |
| T21 | Qwen | 16✅ 1⚠️ 1❌ | `docker-lifecycle` | Docker | Image tag authoring error | Yes (Issue #9) |
| T22 | Gemini 3.1 FL | 16✅ 1⚠️ 1❌ | `docker-lifecycle`, `pip-pinning` | Docker | Same image tag error; pip/USER constraint | Yes (Issue #10) |
| T23 | Qwen | 0/18 stalled | `sqlite-trap`, `test-authoring`, `context-exhaustion` | UUIDStore | `:memory:` without persistent conn warning | Yes (fixture/Behavior pairing) |
| T24 | Qwen | 3/18 stalled | `fixture-interaction`, `test-authoring` | MinIO Writer | Capture mock + body assertion contradiction | Yes (fixture-patterns.md) |
| T25 | Qwen | 16✅ 1⚠️ | `pip-pinning`, `docker-lifecycle` | Docker | Version fabrication (`boto3==1.29.150`) | Yes (pip freeze flow) |
| T26 | Gemini 3.1 FL | 16✅ 1⚠️ | `pip-pinning`, `docker-lifecycle` | Docker | hadolint DL3013 + token limit | Yes (pip freeze flow) |
| T27 | Qwen | 14✅ 3⚠️ 1❌ | `docker-lifecycle`, `task-doc-gap` | Docker, various | Docker exit(1); test-by-ref validated | No (validated Chat 7) |
| T28 | Gemini 3.1 FL | 17✅ 1❌ | `docker-lifecycle` | Docker | Docker exit(1) | No (validated Chat 7) |
| T29 | Qwen | 7✅ 9⚠️ 1❌ | `sqlite-trap`, `test-authoring` | UUIDStore, cascade | Missing persistent conn guidance → 9-task cascade | Yes (`:memory:` enforcement) |
| T30 | Gemini 3.1 FL | 2✅ hard-stop | `sqlite-trap`, `test-authoring` | UUIDStore | Same regression: both models default multi-conn | Yes (`:memory:` enforcement) |
| T31 | Qwen | 8✅ 9⚠️ 1❌ | `task-doc-gap`, `sqlite-trap` | UUIDStore, GDrive, Calories, Avro, DAG | Clean branch; `:memory:` caught; 9 task doc gaps | Pending |
| T32 | Gemini 3.1 FL | 16✅ 2⚠️ 1❌ | `task-doc-gap`, `docker-lifecycle` | GDrive, Calories, Docker | Clean branch; Docker full pass; 2 task doc gaps | Pending |
| T33 | Qwen | 12✅ 5⚠️ | `grounding-validated`, `task-doc-gap`, `docker-lifecycle` | HRV, O2Sat, ExSession, RabbitMQ, TotalCal, Docker | Grounding fixed 5 gaps; ExtractionResult kwargs + uuid_filter remain | Yes (Step 5 grounding) |
| T34 | Gemini 3.1 FL | 16✅ 1⚠️ | `grounding-validated`, `task-doc-gap`, `docker-lifecycle` | HRV, Docker | Grounding fixed both T32 gaps; ExtractionResult kwargs on HRV only | Yes (Step 5 grounding) |
| T35 | Qwen | **18✅** 0⚠️ | `clean-sweep`, `grounding-validated` | — | Refined grounding rule; Docker HTTP 200; all Issue #19/#20 gaps resolved | Yes (refined grounding) |
| T36 | Qwen | 18✅ 1⚠️ | `grounding-validated`, `integration-validated`, `task-doc-gap` | DAG Assembly | Three-compose validated; Integration 3/3 ✅; DAG mock intermittent | Yes (three-compose + service_compose) |
| T37 | Gemini 3.1 FL | 18✅ 1⚠️ | `grounding-validated`, `integration-validated`, `task-doc-gap` | Total Calories | Three-compose validated; Integration 3/3 ✅; ExtractionResult kwargs intermittent | Yes (three-compose + service_compose) |
