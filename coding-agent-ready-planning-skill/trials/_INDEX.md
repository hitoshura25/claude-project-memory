# Trial Index — Structured Tags

> Find trials by failure pattern, affected component, or root cause.
> Each row is immutable once written.

| Trial | Model | Result | Tags | Component(s) | Root Cause Summary | Skill Change? |
|-------|-------|--------|------|--------------|-------------------|---------------|
| T01 | Mixed | Strategy comparison | `strategy-comparison` | All | Code-complete + spec-based abandoned for TDD | Yes (TDD strategy) |
| T02 | Qwen | 16/18 interrupted | `summarizer-spiral` | DAG Assembly | Aider summarizer consumed context; first TDD trial | No |
| T03 | Qwen | 13✅ 4⚠️ | `timeout-bug`, `git-restore` | Various | --timeout doesn't work with streaming; git restore clobbered stubs | Yes (timeout note) |
| T04 | Qwen | Crashed task 9 | `context-exhaustion` | HeartRate | 12k context → Metal GPU OOM. **Floor: 32k** | No (config) |
| T05 | Qwen | 18 completed | `task-doc-gap` | HeartRate | Contract mismatch | Yes (ABC call site) |
| T06 | Qwen | 11✅ 1⚠️ halted 12 | `sqlite-trap`, `mock-path` | UUIDStore | CREATE TABLE syntax; dotted mock path | Yes (persistence stub) |
| T07 | Qwen | 9✅ 3⚠️ halted 13 | `cascade`, `sqlite-trap` | UUIDStore | Cascade root cause identified; :memory: multi-connection trap | Yes (cascade fix) |
| T08 | Codestral | 5✅ 13⚠️ | `test-corruption`, `lint-spiral` | Various | Test file corruption; first disqualification signal | No (model issue) |
| T09 | Gemini 2.0 FL | 12✅ 1⚠️ halted | `hallucinated-import`, `cascade` | GoogleDriveClient | Hallucinated import; cascade confirmed structural | Yes (import check) |
| T10 | Qwen | 15✅ 2⚠️ | `sqlite-trap`, `e501-spiral` | UUIDStore, ExerciseSession | Post cascade fix; multi-column IN trap; E501 in pre-written test | Yes (SQL trap doc) |
| T11 | Codestral | 7✅ 9⚠️ | `test-corruption`, `lint-spiral`, `abc-incomplete` | Various | Second disqualification: lint loops, test corruption, ABC incomplete | No (model issue) |
| T12 | Gemini 3.1 FL | **17/17 ✅** | `clean-sweep` | All | **First clean sweep** — 27 calls | No (validation) |
| T13 | Qwen | 17✅ 1⚠️ | `e501-spiral`, `ise` | Wire DAG | E501 on DAG callable → ISE; import_integrity validated | Yes (snippet rule) |
| T14 | Qwen | 16✅ 1❌ | `ise`, `context-exhaustion` | Wire DAG | ISE → OOM on Wire DAG; fatal context bloat | Yes (snippet rule) |
| T15 | Qwen | **18/18 ✅** (1⚠️) | `clean-sweep` | All | **First Qwen clean sweep** — snippet fix validated | No (validation) |
| T16 | Codestral | 2✅ 1❌ | `test-corruption` | Various | **Codestral permanently disqualified** (3rd confirmation) | No (model issue) |
| T17 | Gemini 3.1 FL | **18/18 ✅** | `clean-sweep` | All | Second Gemini sweep — 21 calls | No (validation) |
| T18 | Qwen | **18/18 ✅** (1⚠️) | `clean-sweep` | All | Second Qwen sweep — 23 calls; loop closed | No (validation) |
| T19 | Qwen | 17✅ 2⚠️ 1⏭ | `mock-trap`, `runner-bug` | RabbitMQ, Docker | `is_closed` mock trap; empty test_command fallback | Yes (pika trap, runner) |
| T20 | Gemini 3.1 FL | **18/18 ✅** 1⏭ | `clean-sweep` | All | Third Gemini sweep on new task set | No (validation) |
| T21 | Qwen | 16✅ 1⚠️ 1❌ | `docker-lifecycle`, `image-tag` | Docker | Airflow base image tag authoring error (`2.9-python3.11` invalid) | Yes (image verify) |
| T22 | Gemini 3.1 FL | 16✅ 1⚠️ 1❌ | `docker-lifecycle`, `image-tag` | Docker | Same image tag error; pip/USER constraint revealed | Yes (image verify) |
| T23 | Qwen | 0/18 stalled | `sqlite-trap` | Settings | `:memory:` fixture without persistent conn warning | Yes (fixture/behavior pairing) |
| T24 | Qwen | 3/18 stalled | `fixture-interaction` | MinIOWriter | Capture mock + body assertion contradiction | Yes (fixture-patterns.md) |
| T25 | Qwen | 16✅ 1⚠️ | `docker-lifecycle` | Docker | Pinned version fabrication (`boto3==1.29.150`); hadolint DL3013 | Yes (pip freeze flow) |
| T26 | Gemini 3.1 FL | 16✅ 1⚠️ | `docker-lifecycle`, `token-limit` | Docker | hadolint DL3013 + token limit; container exit(1) | Yes (pip freeze flow) |
| T27 | Qwen | 17/19 (14✅ 3⚠️ 1❌) | `docker-lifecycle`, `test-by-ref` | Docker, various | Chat 7: test-by-ref + Dockerfile scaffold validated; Docker exit(1) | Yes (test-by-ref, Dockerfile scaffold) |
| T28 | Gemini 3.1 FL | 17/19 (17✅ 1❌) | `docker-lifecycle`, `test-by-ref` | Docker | Chat 7: 17/17 service tasks clean; Docker exit(1); 26 calls | Yes (test-by-ref) |
| T29 | Qwen | 7✅ 1⚠️ 9⚠️ 1❌ | `sqlite-trap`, `cascade` | UUIDStore (cascade) | Regression: missing persistent conn guidance → 9-task cascade | Yes (fixture pattern enforcement) |
| T30 | Gemini 3.1 FL | 2✅ hard-stop | `sqlite-trap`, `cascade` | UUIDStore | Same regression: both models default to multi-connection SQLite | Yes (fixture pattern enforcement) |
| T31 | Qwen | 8✅ 9⚠️ 1❌ | `task-doc-gap`, `docker-lifecycle` | Various | Clean branch: `:memory:` caught UUIDStore; Docker ✅; 9 task doc gaps | Yes (code-grounding rule) |
| T32 | Gemini 3.1 FL | 16✅ 2⚠️ 1❌ | `task-doc-gap`, `docker-lifecycle` | GDrive, TotalCal | Clean branch: UUIDStore ✅; Docker smoke test ✅; 2 task doc gaps | Yes (code-grounding rule) |
| T33 | Qwen | 12✅ 5⚠️ | `task-doc-gap`, `docker-lifecycle` | ExtractionResult, uuid_filter | Code-grounding rule: +4✅ vs T31; Docker exit(1) | Yes (refined grounding) |
| T34 | Gemini 3.1 FL | 16✅ 1⚠️ | `task-doc-gap`, `docker-lifecycle` | HRV | Code-grounding rule: GDrive+TotalCal fixed; Docker exit(1) | Yes (refined grounding) |
| T35 | Qwen | **18✅** 0⚠️ | `clean-sweep` | All | **Third Qwen clean sweep** — refined grounding rule; Docker ✅ (HTTP 200); 44 calls | No (validation) |
| T36 | Qwen | 18✅ 1⚠️ | `integration-validated`, `task-doc-gap` | DAG Assembly | Three-compose validated; **Integration ✅ 3/3**; DAG mock intermittent; 39 calls | No (validation) |
| T37 | Gemini 3.1 FL | 18✅ 1⚠️ | `integration-validated`, `task-doc-gap` | TotalCal | Three-compose validated; **Integration ✅ 3/3**; ExtractionResult kwargs intermittent; 37 calls | No (validation) |
| T38 | Qwen | 13✅ 2⚠️ OOM | `context-exhaustion` | DAG Assembly | **Regression**: repo map (`--subtree-only`) → Metal GPU OOM on DAG task + 2 uuid_filter failures | No (config revert) |
| T39 | Qwen | 17✅ 1⚠️ | `integration-validated`, `task-doc-gap` | DAG Assembly | Reverted `--no-git`; matches T36 baseline; Integration 3/3 (clock skew on verify) | No (confirmation) |
| T40 | Qwen | 8✅ 1⚠️ halted | `context-exhaustion`, `schema-trap` | Steps, Sleep | Post sys.modules fix; halted task 11 (Metal GPU OOM); Avro schema trap (pre-existing) | Yes (sys.modules fix) |
| T41 | Gemini 3.1 FL | **17✅** Docker ❌ | `sysmodules-mock`, `schema-trap`, `docker-lifecycle` | DAG Assembly, Docker | **sys.modules fix VALIDATED**; Avro self-corrected; Docker exit(1); quota exhausted | Yes (sys.modules fix) |
| T42 | Qwen | **INVALID** 11⚠️ | `scaffold-regression` | Settings (all tasks) | Lint not executable, `uv sync` missing, `./` prefix missing | Yes (scaffold checklist) |
| T43 | Qwen | **INVALID** halted 1 | `interface-contract-gap` | Settings | Interface Contract had comments-as-defaults; Qwen removed actual defaults from stub | Yes (grounding covers IC) |
| T44 | Qwen | 8✅ 3⚠️ (partial) | `scaffold-validation-gap`, `abc-incomplete`, `fixture-gap` | Downloader, HeartRate, Sleep | Post-refactor: Claude Code truncated Layer 2 output; @abstractmethod + missing fixture | Yes (validate-stubs.sh, plan code blocks removed) |
| T45 | Qwen | 16✅ 3⚠️ | `test-writing-bug`, `uuid-format`, `incomplete-test` | BaseExtractor, DriveClient, Integration | T44 fixes validated; 3 planning-model test bugs (UUID format, stub tests, skipif) | Yes (validate-stubs.sh log location) |
| T46 | Qwen | 17✅ 1⚠️ | `sql-parameterization`, `docker-cache` | UUIDStore | SQL double `AND record_type = ?`; Docker smoke ✅; task 19 blocked by Docker cache | No |
| T47 | Gemini 3.1 FL | 18✅ 1⚠️ | `test-file-modified`, `integration-bucket` | Integration | 18/18 service tasks ✅; integration passed but modified test_e2e.py (NoSuchBucket workaround) | No |
| T48 | Qwen | 15✅ 3⚠️ | `module-level-instantiation`, `cascade` | Settings, MinIO, RabbitMQ | UUIDStore ✅ (0 E501); Settings task doc + stub comment told Qwen to instantiate at module level; 3-task cascade | Yes (stub/task doc fix needed) |
