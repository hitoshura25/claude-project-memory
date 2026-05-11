# Session Status — 2026-05-10 (update 2)

Picking up from `session-status-2026-05-10.md` (the day's earlier
status). This update documents the prompt-composition skill
structural refactor performed in the late session.

## What this session accomplished

Diagnosed and fixed two coupled bugs in the
`prototype-driven-prompt-composition` skill that were causing
output variation across runs:

1. **Preamble parsing bug** (fixed earlier in session). `_load_preamble`
   used `text.find("# Role")` to locate the start of the preamble
   prose, which matched the inline backtick-quoted reference to
   `# Role` in the meta-commentary at the top of `preamble.md`. Result:
   every generated prompt opened with leaked meta-prose followed by
   the actual preamble. Fix: line-anchored matcher
   (`line.rstrip() == "# Role"`) and tightened meta-commentary that
   names the parsing rule explicitly.

2. **Structural bug** (fixed this update). Claude Code wasn't running
   `scripts/compose_prompts.py` at all — it was reading SKILL.md as
   instructions, simulating the script's logic in a one-off inline
   `/tmp/gen_prompts.py`, and writing the prompts itself. The inline
   script hardcoded `INLINEABLE_EXTS = {".py"}` as a judgment call the
   shipped script doesn't make, which caused dependency lists to omit
   `.txt`, `.yml`, `.toml` files (requirements.txt, docker-compose.yml,
   ruff.toml) that the decomposition declared. Different sessions
   would resolve the ambiguity differently, breaking determinism.

## Four changes landed

### Change 1: Removed the source/non-source filter from the script

`scripts/compose_prompts.py`:
- Deleted `_derive_inlineable_extensions`.
- Removed `inlineable_extensions` parameter from `_inline_dependencies`,
  `_build_prompt`, and the main flow.
- `_inline_dependencies` now lists every file from each dependency
  task's `task.files[]` — no extension filter, no judgment.
- Phase 1 STOP-summary no longer prints "Inlineable extensions" or
  "Extensions" lines.

Rationale: decomposition is the source of truth for what a task
produces; downstream tasks declare dependencies via `depends_on`; the
composition layer shouldn't second-guess by filtering out
"non-source" paths. The filter was both unnecessary (config-file noise
is trivial) and harmful (it introduced ambiguity that broke
determinism).

### Change 2: Added `--phase-1-only` flag

The script's Phase 1 ran inline with Phase 2 — no checkpoint between
input validation and prompt writing. SKILL.md's "STOP and wait for
confirmation" instruction had no clean way to translate to script
invocation. Added `--phase-1-only`: validates inputs, prints the
Phase 1 summary, exits 0 before writing anything. The
output-directory precondition (refuses to run if `prompts/` exists)
is skipped under this flag so the user can run it to inspect inputs
without first deleting an existing prompts directory.

The full run (without the flag) keeps the existing Phase 1→2→3
sequence.

### Change 3: Restructured SKILL.md as a thin invoker

The previous SKILL.md described Phase 1, 2, and 3 as instructional
prose. Claude Code reads that as "here's how to compose prompts,
step by step" and does each step itself, treating the script as
optional infrastructure. The new SKILL.md is short and clear about
what to do:

1. Announce the skill.
2. Run the script with `--phase-1-only`. Surface stdout verbatim.
3. Wait for user confirmation.
4. Re-run without the flag. Surface stdout verbatim.
5. Done.

The "Editing this skill" section explains the why: any prose
describing what to render or how to filter belongs in the script
instead. The Principles section keeps the deterministic-transformation
framing.

The "Phase 1 / Phase 2 / Phase 3" prose moved out of SKILL.md
entirely. The substantive format documentation already lives in
`references/prompt-template.md` and `references/dependency-handling.md`
for editors who need to understand or modify the format.

### Change 4: Added a snapshot test

`tests/verify.sh` runs the script against the canonical test project
(`~/health-data-ai-platform/`, `airflow-gdrive-ingestion` feature)
and diffs the generated prompts against a committed expected
snapshot at `tests/expected/airflow-gdrive-ingestion/prompts/`.

`tests/README.md` documents the workflow, the bootstrap (how to
populate the snapshot on first use), and what the test catches —
specifically including "reimplementation drift: if Claude Code
rewrites the skill in chat instead of running the script, the live
output won't match the snapshot."

The expected snapshot directory ships empty. The bootstrap is
deferred to the user — see the validation steps below.

### Files touched

- `~/claude-devtools/skills/prototype-driven-prompt-composition/scripts/compose_prompts.py` (rewrite)
- `~/claude-devtools/skills/prototype-driven-prompt-composition/SKILL.md` (rewrite)
- `~/claude-devtools/skills/prototype-driven-prompt-composition/references/dependency-handling.md` (rewrite of the inlineable-extensions section + small consistency edits)
- `~/claude-devtools/skills/prototype-driven-prompt-composition/tests/verify.sh` (new)
- `~/claude-devtools/skills/prototype-driven-prompt-composition/tests/README.md` (new)
- `~/claude-devtools/skills/prototype-driven-prompt-composition/tests/expected/airflow-gdrive-ingestion/` (new directory, empty pending bootstrap)

## Validation required before the changes are usable

I (Claude) couldn't run the script — it lives on the user's host and
the test inputs are there too. The user needs to do three things to
close the loop:

### Step 1: Smoke-test the script with the new flag

```bash
cd ~/health-data-ai-platform
rm -rf tasks/airflow-gdrive-ingestion/prompts

# Phase-1 only — should validate inputs and exit 0 without writing anything.
uv run --with pydantic python \
    ~/claude-devtools/skills/prototype-driven-prompt-composition/scripts/compose_prompts.py \
    airflow-gdrive-ingestion --phase-1-only

# Full run — should generate 12 prompts and exit 0.
uv run --with pydantic python \
    ~/claude-devtools/skills/prototype-driven-prompt-composition/scripts/compose_prompts.py \
    airflow-gdrive-ingestion
```

Expected output for the phase-1-only run: a Phase 1 summary block
with "Tasks: 12, Citations: 56" and a "re-run without
--phase-1-only" message. No "Inlineable extensions" line anymore.

Expected output for the full run: Phase 1 summary, Phase 2 generation
log (12 wrote lines), Phase 3 validation summary, "Done. Next steps"
block.

Spot-check task-04.md's `## Dependencies` section — it should now
list **all** files task-01 produces: requirements.txt, Dockerfile,
docker-compose.yml, ruff.toml, four `__init__.py` files, and
conftest.py. (8 files, not 5 like before.)

If the script errors or the output looks wrong, stop here and surface
the error — don't continue to step 2.

### Step 2: Test the skill end-to-end through Claude Code

```
/devtools:prototype-driven-prompt-composition airflow-gdrive-ingestion
```

What to look for in Claude Code's behavior:

- Should announce "I'm using the prototype-driven-prompt-composition skill…"
- Should run the script with `--phase-1-only` and show its stdout
  verbatim (no unicode tables, no editorial commentary about
  "non-source files").
- Should ask for confirmation.
- After confirmation, should re-run without the flag and show stdout
  verbatim.

The key signal that the structural fix worked: the output shown to
the user should match the script's stdout byte-for-byte, not be
reformatted into a prettier rendering. If Claude Code still
prettifies into tables, SKILL.md needs further iteration.

### Step 3: Bootstrap the snapshot test

Per `tests/README.md`'s "Bootstrap (first time)" section:

```bash
# Generate the canonical prompts (if not already done by step 1/2).
rm -rf ~/health-data-ai-platform/tasks/airflow-gdrive-ingestion/prompts
uv run --with pydantic python \
    ~/claude-devtools/skills/prototype-driven-prompt-composition/scripts/compose_prompts.py \
    airflow-gdrive-ingestion

# Copy as the canonical snapshot.
cp -r ~/health-data-ai-platform/tasks/airflow-gdrive-ingestion/prompts \
      ~/claude-devtools/skills/prototype-driven-prompt-composition/tests/expected/airflow-gdrive-ingestion/prompts

# Verify it now passes.
chmod +x ~/claude-devtools/skills/prototype-driven-prompt-composition/tests/verify.sh
~/claude-devtools/skills/prototype-driven-prompt-composition/tests/verify.sh
```

Expect: `OK: Generated prompts match expected snapshot.`

Then commit the snapshot. After this, every future change to the
script or references gets validated by re-running `verify.sh`.

## Open items

- **Step 2 of the original prompt-composition-skill-plan** (the
  implementation-skill changes described in
  `prompt-composition-skill-plan-2026-05-09.md`) is still pending.
  That work was deferred while the prompt-composition skill was
  stabilized; pick it up next session.
- **T10 / T17 validation run** still pending. The prompt-composition
  fixes mean the pipeline now sees a different (more complete)
  dependency list under `## Dependencies` for some tasks. This may or
  may not affect executor success rates — worth noting in the next
  trial record.

## Alignment with skill-creator best practices

Cross-checked the four changes against
`/mnt/skills/examples/skill-creator/SKILL.md`. Key alignments:

- Progressive disclosure: SKILL.md is now shorter; substantive
  content is in `scripts/` and `references/`.
- Scripts for deterministic tasks: the structural fix aligns SKILL.md
  with the canonical pattern (scripts hold the logic, SKILL.md
  invokes them).
- Lack of surprise: the deterministic-transformation promise is now
  actually true rather than aspirational.
- Test cases for verifiable outputs: snapshot test now exists.

Adjusted from initial draft: softened the "do not reimplement / never
rewrite" language in the new SKILL.md per the doc's guidance
("explain why things are important in lieu of heavy-handed musty
MUSTs"). The new wording explains the reasoning (LLM rendering
breaks the comparison invariant downstream trials rely on) rather
than commanding compliance.
