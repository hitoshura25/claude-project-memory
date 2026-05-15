# T16 — First pipeline run against the refactored pipeline skill

**Date:** 2026-05-14
**Project:** airflow-gdrive-ingestion
**Pipeline:** `pipelines/airflow-gdrive-ingestion/` (regenerated from
the prompt-consumer pipeline skill)
**Result:** ❌ Pipeline halted at task-03 (test-task for drive-downloader)
**Tags:** `prompt-consumer-pipeline`, `environmental-vs-code-failure-recovery-mismatch`,
`tier-1-timeout-too-tight`, `gemini-tool-calling-bug`,
`executor-output-vs-code-quality-conflation`,
`refactor-architecture-validated`

---

## What this trial validates

This is the first end-to-end pipeline run against the
prompt-consumer pipeline skill (the refactor documented separately
in I01). The headline finding is that **the architectural shift
works as designed**:

- `check_preconditions` validates the prompts directory and per-task
  file presence at startup
- `compose_prompt_node` reads pre-generated prompt files from
  `tasks/<feature>/prompts/<task-id>.md` and passes paths through to
  executors verbatim (no mutation, no augmentation)
- `verify_task` writes per-attempt error logs to the
  `tasks/<feature>/logs/<lint|tests>/<task-id>/attempt-<N>-tier<M>.txt`
  paths that the prompts already reference in their `## Previous
  Attempts` section
- Auto-resume from Phase A correctly skips task-01 (manually executed
  by Claude Code in the conversation that generated this pipeline)
  and starts the pipeline at task-02
- Tier escalation works: task-03 escalated from tier-0 (Gemini) to
  tier-1 (Claude) after retry exhaustion

None of these required changes after generation. The refactor's
structural promises held.

The pipeline still failed, but the failures are at the executor and
orchestration-policy layers — pre-existing concerns that the refactor
neither introduced nor fixed. The structural cleanup just makes them
more visible.

## Run summary

| Task | Status | Executor | Tier | Retries | Notes |
|------|--------|----------|------|---------|-------|
| task-01 | ✅ passed | Claude Code | (Phase A) | — | Scaffold; ran in conversation, not pipeline |
| task-02 | ✅ passed | claude (default) | 0 | 0 | First attempt; hadolint + docker compose config clean |
| task-03 | ❌ failed | gemini → claude | 0 → 1 | 1 each | All 4 attempts (2 tier-0 + 2 tier-1) failed |
| task-04 | ⏭ skipped | — | — | — | Blocked by task-03 failure |
| task-05 .. task-13 | not_run | — | — | — | Pipeline halted before reaching them |

Summary: **2 passed, 1 failed, 1 skipped, 9 not_run.**

## What went wrong on task-03

Task-03 is the test-task for `drive-downloader`: write
`tests/test_download_zip.py` plus a stub
`dags/health_connect_ingestion.py`. The prompt is 13,175 bytes
(13,141 chars after stripping line endings), one of the larger
prompts in this decomposition.

Four execution attempts. Each failed in a different way; together
they expose four distinct orchestration concerns.

### Attempt 1 (tier 0, gemini-2.5-pro): Gemini tool-calling bug → 429 cascade

Two issues compounded:

**Tool-calling bug.** Gemini emitted file-system tool calls with
prompt body fragments as the path argument. The stderr captured:

```
Error stating path daily", start_date=datetime(2026, 1, 1), catchup=False)
    def health_connect_ingestion_dag() -> None:
        zip_path = download_zip()
        ...
```

And:

```
ENAMETOOLONG: name too long, stat '/Users/vinayakmenon/health-data-ai-platform/daily", start_date=datetime(2026, 1, 1), ...
```

This is a Gemini CLI / tool-calling bug — the substring `daily",
start_date=...` is recognizable as the prompt's Objective section
(the DAG definition example). Gemini apparently passed the prompt
text into a `stat` call as a path. ENAMETOOLONG eventually killed the
tool call.

After this, Gemini did manage to write a file matching
`services/airflow-ingestion/dags/health_connect_ingestion.py` (since
attempt 2's lint found `DTZ001` at line 58:16 of that file), but
**never created `tests/test_download_zip.py`** — verify_task's pytest
run reported:

```
ERROR: file or directory not found: tests/test_download_zip.py
```

Notably: the DAG file Gemini wrote contained `start_date=datetime(2026,
1, 1)` — copied verbatim from the *prompt's example code*, not derived
from the task description. Evidence of literal-copying behavior when
the model is degraded.

**429 cascade.** After the file partially-existed state, Gemini hit
`429 RESOURCE_EXHAUSTED: No capacity available for model
gemini-2.5-pro on the server`. The Gemini CLI's internal
retry-with-backoff fired ten times in a row, all returning the same
429, before exhausting its internal retry and exiting non-zero.

From the pipeline's perspective, this looked like a normal
executor exit with non-zero status → kick off normal retry/escalation
flow. **But this is environmental, not code-quality.** The model was
unavailable; there was no executor output to verify.

### Attempts 2 (tier 0 retry), 3 + 4 (tier 1): each failed differently but uniformly

Attempt 2 (Gemini retry within tier 0): timed out at 300s. No output
captured beyond `gemini timed out after 300s`.

Attempt 3 (Claude tier-1, first try): timed out at 300s. Same
no-output failure.

Attempt 4 (Claude tier-1 retry): timed out at 300s. Same.

In all three, verify_task ran against whatever was on disk from
attempt 1 (Gemini's partial DAG file). Lint found `DTZ001` on
`datetime(2026, 1, 1)`; pytest failed with collection error because
`test_download_zip.py` still didn't exist.

The error logs captured at each attempt are identical because **the
underlying disk state never changed** — the executor never produced
output to change it.

## Root causes

### RC-1: Environmental-vs-code-failure recovery mismatch

Status: **known pattern from the trial-record glossary**
(`environmental-vs-code-failure-recovery-mismatch`). The retry/
escalation loop is shaped for code-quality failures (executor wrote
wrong code → run verifier → write error log → retry with same
input). When the failure is environmental (model unavailable,
network issue, rate-limit, daemon down), retrying with the same
input changes nothing, but the pipeline still burns retry budget.

In this run: the 429s from Gemini consumed 1 tier-0 retry slot
*and* triggered tier escalation. Tier 1's timeouts then consumed 2
more slots. Four attempts burned on a problem no executor could
recover from.

The structural fix: distinguish failure classes earlier. A 429 from
the model provider should retry-with-backoff at the
executor-bridge layer (`agent_bridge._execute_gemini` or similar),
not in the pipeline retry loop. A timeout with no captured output
should be classified separately from a timeout with partial output.

### RC-2: 300-second timeout too tight for tier-1 Claude on test-task prompts

The default `EXECUTOR_TIMEOUT = 300` was sized for Aider invocations
in earlier trials. Aider's prompt-cycle pattern (per-edit chat
exchange, immediate file diff application) fits comfortably in 300s
for typical tasks.

Claude CLI in non-interactive `-p` mode has a different cycle: a
single prompt → planning → multiple tool calls → file writes →
verification. For a 13KB test-task prompt that needs to mock
GoogleDriveHook with multiple test cases, 300s is realistically
not enough.

Reference points from the manual three-way comparison earlier in
this session:
- Manual Claude Code on task-01 (scaffold, smaller prompt): ~1:28
- Manual Claude Code on task-02 (infrastructure, mid-sized): ~2:04
- Pi+Qwen on task-01 with verification: ~2:35 (including tool
  installs)

A 13KB test-task prompt with mock setup is ≥5 minutes of work even
for a strong executor. Pipeline timeout needs to scale with prompt
size and task complexity, or be configurable per tier.

### RC-3: Timeout failures produce no diagnostic output

When `subprocess.run(...)` is killed at timeout, the pipeline
captures only `<executor> timed out after Ns`. No partial stdout,
no partial stderr. We can't tell whether the executor was making
progress and just slow, or completely stuck.

Fix: stream stdout/stderr to log files during execution (rather than
capturing only at termination). On timeout, the partial output is
already on disk.

### RC-4: E902 (file not found) treated as a lint error

After Gemini's partial output, ruff's lint command targeted specific
files from `task.files[]`. Two of those files didn't exist:

```
E902 No such file or directory (os error 2)
--> services/airflow-ingestion/dags/health_connect_ingestion.py:1:1

E902 No such file or directory (os error 2)
--> services/airflow-ingestion/tests/test_download_zip.py:1:1
```

This is classified as a lint failure in verify_task and routed to
retry/escalation. But it's really an executor-output failure —
the executor didn't produce the files it was asked to. The retry
loop is shaped for "fix the lint errors"; the right action here is
"executor produced nothing, retry from scratch."

Pipeline could detect `E902 No such file or directory` (or the
equivalent in other linters) as an executor-output signal and route
it differently from code-quality lint failures.

### RC-5: Cosmetic — skipped tasks reported as `lint=✗`

Skipped tasks (task-04, which was correctly skipped due to task-03's
failure) showed `lint=✗` and `test=-` in the summary. Should be
`lint=-` and `test=-` — neither was attempted.

`task_status.json` for task-04 records `lint_passed: false`,
`test_passed: null`. The boolean default for `lint_passed` is wrong
for non-attempted tasks; should be `None` and the summary renderer
should distinguish.

## What the refactor delivered (validation)

Cross-reference against the I01 refactor plan:

- **`compose_prompt_node` reads pre-generated prompts.** Verified by
  log lines like `[compose_prompt] task-02: using prompt (12753
  bytes) at /Users/vinayakmenon/health-data-ai-platform/tasks/
  airflow-gdrive-ingestion/prompts/task-02.md`. Same byte count
  every time the same task is composed — no mutation.

- **Error logs at the new paths.** Verified by log lines like
  `[verify_task] full lint output → tasks/airflow-gdrive-ingestion/
  logs/lint/task-03/attempt-1-tier0.txt`. Filesystem confirms files
  exist at `tasks/airflow-gdrive-ingestion/logs/lint/task-03/`.

- **`check_preconditions` validates prompts directory and per-task
  files.** Verified by log lines:
  ```
  [check_preconditions] ✓ prompts directory: tasks/airflow-gdrive-ingestion/prompts
  [check_preconditions] ✓ prompts present for all 13 tasks
  ```

- **No prompt mutation between retry attempts.** All four task-03
  attempts logged the same prompt byte count (13175 bytes). The
  pipeline never rewrote the prompt file or appended retry context.

- **The `## Previous Attempts` framing in the prompt is the
  retry-context vehicle.** The prompt directs the executor to read
  the most-recent attempt log. The pipeline writes those logs at
  the paths the prompt references. The contract holds.

- **Auto-resume works.** task-01 was correctly skipped from
  `task_status.json`; pipeline started at task-02.

- **Tier escalation triggered correctly.** After task-03 tier-0
  exhausted retries, the pipeline escalated to tier 1 with the
  Claude executor as configured in `EXECUTOR_ROLES["test"]`.

The refactor is sound. No refactor-introduced bugs surfaced in this
run.

## What the refactor did NOT fix (and was not intended to)

Orchestration-layer issues — retry policy, tier escalation triggers,
timeout sizing, executor-bridge robustness, failure-class detection
— were out of scope for the refactor. They surfaced in this run
because the structural cleanup made the orchestration's behavior
more legible. Previously, runtime prompt composition added noise to
the failure signal; now the failure signal is clean and the
orchestration's response to it is visible.

The orchestration concerns are sequenced separately. None of them
require touching the prompt-composition skill or the
decomposition skill.

## Observations on executor capability

Beyond the orchestration concerns, this run produced executor-
specific findings worth recording:

### Gemini CLI tool-calling bug

Gemini's tool-calling implementation appears to take very long
prompts and use parts of the prompt text as tool arguments. The
`ENAMETOOLONG` error captured a literal substring of the prompt's
Objective section being passed as a `stat` path. This is a Gemini
CLI bug, not something the pipeline can fix.

Mitigation: rule out Gemini as the test-task tier-0 executor for
prompts above some size threshold (TBD). Use Claude or Aider+local
model instead.

### Gemini-2.5-pro capacity-exhaustion frequency

The 429s came back ten times in a row from a single CLI invocation,
with Google's own internal retry exhausted. Gemini-2.5-pro is
demonstrably an unreliable tier-0 executor at present; capacity
issues will recur until Google resolves the underlying capacity
problem.

Mitigation: configure tier-0 for test tasks to use Aider+local model
(Qwen 3 Coder 30B via LM Studio) instead of Gemini. The trial-record
arc has shown Aider+Qwen produces reasonable content depth on test
tasks when the prompt provides enough framing (PC01's task-type
preambles + verification framing).

### Claude `-p` timeout behavior

Claude CLI invoked with `-p` (non-interactive) hangs to timeout
without producing output when given a 13KB prompt. Two possibilities:

1. The CLI itself is slow on prompts this size (Claude is processing
   but not finishing within 300s)
2. The CLI is silently failing (e.g., a tool permission prompt
   that's not surfacing in non-interactive mode)

Either way, the pipeline can't tell because output isn't streamed.
The timeout-streams-output fix (RC-3) will distinguish these cases.

## What to do next

Three independent workstreams emerge:

**Workstream A: Orchestration robustness.** Address RC-1 through
RC-5. This is pipeline-internal work — no upstream skill changes.
Likely scope:
- Stream executor stdout/stderr during execution
- Detect environmental failures (429, network, missing daemon) at
  the executor-bridge layer; retry-with-backoff there before the
  pipeline retry loop sees them
- Distinguish "executor produced nothing" from "executor produced
  wrong code" in `verify_task`
- Per-tier or per-prompt-size timeout configuration
- Fix the `lint=✗` cosmetic issue for skipped tasks

**Workstream B: Executor tier reassessment.** Recompose
`EXECUTOR_ROLES` for the airflow project to use Aider+Qwen on the
`test` role instead of Gemini-2.5-pro. This is project-side, not
skill-side. Run T17 against this configuration to see how the
manual three-way comparison's Pi+Qwen behavior holds up in pipeline
context.

**Workstream C: Pipeline retry policy.** Reconsider the
`MAX_RETRIES_PER_TASK = 1` setting (which is per-tier, so total
attempts are 2 tier-0 + 2 tier-1 = 4). This is enough for
code-quality failures but burns all four on environmental failures.
Workstream A's failure-class detection would let this stay at 1
without budget loss; but if A doesn't land first, B might warrant
raising retries to 2.

I recommend A before C. The right structural fix is to not waste
retries on environmental failures, not to raise the retry budget.

## Related trial records

- I01 — pipeline-as-prompt-consumer refactor (the architectural
  change this trial validates)
- T15 — last pipeline run; environmental-vs-code-failure-recovery-
  mismatch was the dominant failure mode there too, and motivated
  the Phase A/B scaffold split
- T10–T13 — earlier pipeline runs documenting the tightening arc
  for the older prompt-composition-in-pipeline architecture

## Run logs

- `pipelines/airflow-gdrive-ingestion/logs/runs/run-20260514_103856.log`
  (this trial)
- `pipelines/airflow-gdrive-ingestion/logs/runs/run-20260514_100416.log`
  (earlier run today; superseded)
- `pipelines/airflow-gdrive-ingestion/logs/runs/run-20260514_100401.log`
  (earlier run today; superseded)

Per-attempt error logs at
`tasks/airflow-gdrive-ingestion/logs/lint/task-03/` and
`.../tests/task-03/`. Filenames follow the
`attempt-<N>-tier<M>.txt` convention from the prompt-composition
skill's `references/log-conventions.md`.
