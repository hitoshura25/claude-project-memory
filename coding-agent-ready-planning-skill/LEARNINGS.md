# Key Learnings & Principles

> Distilled from 41 trials across 9 chat sessions. These are the rules that govern
> skill development. Always loaded at conversation start alongside `README.md`.

---

## Upstream-Only Fixes

- **Fixes must be generic and upstream** in the skill files, never band-aids on individual task docs.
- **Skill content must not reference trial numbers or chat-specific history**. Trial references are meaningless to the planning model. Skill guidance should explain the *principle* and *why*, not cite historical incidents.

## Context & Model Constraints

- **Context length floor**: Do not reduce LM Studio context below 32k. MLX pre-allocates a fixed GPU KV cache; reducing to 12k causes Metal GPU OOM segfaults mid-run.

## SQLite Patterns

- **`:memory:` is the quality standard for SQLite fixtures**: Faster than file-backed, perfect isolation, and enforces correct implementation (persistent `self._conn`). `tmp_path` masks the multi-connection bug — do not use it for SQLite fixtures. See `python-pytest.md` § Trap 1 and `fixture-patterns.md` Pattern 3.
- **SQL Constants Pattern**: All SQL strings must be assigned to named module-level constants, never inlined in method bodies (eliminates E501 surface).

## Test & Lint Quality Gates

- **Layer 0 lint gate**: Linter must return zero errors against pre-written test files before they can be embedded in task docs.
- **Tests referenced by path, not embedded**: Task docs point to on-disk test files rather than embedding copies. Embedding creates a second source of truth that diverges due to LLM non-determinism.

## Task Structure

- **Import integrity pattern**: Wiring task docs must enumerate exact class names with explicit instruction not to import anything not listed.
- **Cascade isolation**: Component tasks create files only; wiring is always a separate task. Component test_commands never include shared files.
- **Deferred vs Service-Gated**: Integration tests are service-gated (runner skips when services unavailable), not deferred (which halts the runner).
- **Long literals must be multi-line in Behavior sections**: SQL queries, Avro schemas, and nested dicts shown in task docs must be broken across lines. The model copies whatever form it reads.

## Fixture Patterns

- **Fixture interaction rules**: Capture mocks block downstream side effects. Never combine a capture mock with an assertion on the captured function's output. See `python-pytest/fixture-patterns.md`.

## Mock Traps

- **sys.modules mock constructor trap**: When a framework class is loaded from a `sys.modules` MagicMock entry, constructor kwargs are silently discarded. `FrameworkClass(name="x")` returns a MagicMock whose `.name` is another MagicMock, not `"x"`. Task docs must include explicit attribute assignments after the constructor for every attribute that tests assert on. See `python-pytest.md` § "sys.modules Mock Constructor Trap".

## Schema Validation

- **Include validated schemas when tests check parsing**: If a test validates schema structure (Avro `parse_schema`, JSON Schema, protobuf descriptors), the planning model must construct the exact schema during Step 3b, validate it against the library, and include it verbatim in the task doc. Small models cannot reliably construct schemas with library-specific constraints (named type deduplication, reference rules). Pre-existing intermittent failure — seen in T31 and T40 on Avro schemas with shared nested record types.

## Docker & Infrastructure

- **Docker scaffold requires technology-specific research, not templates**: Before writing any Dockerfile, the planning model must research the base image's official Docker documentation — entrypoint behavior, built-in initialization mechanisms, environment variables, and volume/permission requirements. Templates cannot substitute for this because every framework has unique entrypoint behavior. See `stacks/infra.md` § "Step 0: Research the base image's Docker setup".
- **Pip version pinning in Dockerfiles**: The planning model must build unpinned first, capture resolved versions via `pip freeze`, pin them in the Dockerfile, and rebuild.
- **Dockerfile is scaffold, not a task deliverable**: The planning model writes, builds, pins versions, and validates the Dockerfile with hadolint during Step 3. It stays on disk — the small model only creates compose files.
- **Test compose is scaffold too**: The planning model writes the test compose and verifies the full stack starts healthy via `docker compose up --wait`.

## Regeneration Hygiene

- **Always regenerate from a clean branch**: When regenerating scaffold and task docs after skill changes, use a branch with no prior committed scaffold. The planning model's brainstorming skill references git history — prior committed task docs contaminate fresh regenerations, causing non-determinism that looks like compliance issues but is actually historical artifact copying.
