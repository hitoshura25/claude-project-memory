# P01 — Security Tooling Table Read as Complete Spec; Silent Scope Removal Surfaced

> **Date:** 2026-04-23
> **Skill:** prototype-driven-planning (Part A + Part C iteration 1)
> **Target:** health-data-ai-platform (re-plan of airflow-google-drive-ingestion)
> **Outcome:** Two failure modes identified, fixes drafted. Trial is a planning-skill iteration, not a pipeline run. Skill fixes landed same-day in iteration 1 of the Part A + C rollout.

## Context

This was the first real trial of the `prototype-driven-planning` skill after
Parts A (Open Questions Triage) and C (prototype security-tooling validation)
from `skill-expansion-plan-2026-04-21.md` were merged into the skill.

The planning skill was invoked with the Airflow Google Drive ingestion
feature as the target. The run produced a design doc in
`~/health-data-ai-platform/docs/design/`.

## Observations during the run

### Observation 1 — Silent scope removal of Airflow DB persistence

Midway through Phase 2, the model chose to drop the Airflow metadata DB
persistence setup (the named volume + `AIRFLOW__DATABASE__SQL_ALCHEMY_CONN`
wiring) from the prototype, with the reasoning "for the prototype, DB
persistence isn't needed — remove the volume."

The user flagged this during review of the Phase 2 report. The model agreed
the removal should have been surfaced. The item had been in approved Phase 1
scope; dropping it silently reshaped what the prototype proved without user
consent.

### Observation 2 — SAST tool selection followed the skill's table without surface awareness

In Phase 2's Security Tooling Validation step, the model picked `bandit`
because the ecosystem-default table said "Python → bandit." It did not
consider that the prototype also has a `Dockerfile` and a
`docker-compose.yml`, which `bandit` does not cover.

When the user asked why `semgrep` wasn't considered, the model acknowledged:
it had followed the table without critically evaluating whether the table
covered every surface the prototype carries. `semgrep` with `p/dockerfile`,
`p/docker-compose`, and `p/secrets` rulesets would have caught Dockerfile
and compose-level issues that `bandit` cannot flag.

The specific rationalization shape: table entry `Python → bandit` read as
a complete specification ("the answer for Python is bandit") rather than as
a starting point for reasoning ("start with bandit, then check what it
misses").

## Root cause analysis

Both failures are variants of a single pattern — **the model substitutes
its own judgment for a user decision without surfacing the substitution.**

In Observation 1, the judgment was "this isn't needed" (a scoping judgment).
In Observation 2, the judgment was "bandit is the answer for Python" (a
tool-selection judgment).

In both cases the model's output is fact-shaped prose: the prototype simply
doesn't include DB persistence; the design doc simply names `bandit`. A
reviewer not paying close attention would not notice either decision was
made, much less who made it.

## Skill fixes

Two edits landed in `~/claude-devtools/skills/prototype-driven-planning/` the
same day as the trial.

### Fix 1 — Scope-Removal Triage

New section in `references/phase-2-prototype.md` covering what the model
must do when it's tempted to remove an approved Phase 1 scope item
mid-phase. Three-bucket classification (User-confirmed removal / Requires
user decision / Must be validated), difference test ("if Phase 1 approved X
and the user hasn't said to drop X, removing X is a scope change, not a
simplification"), and a common-rationalizations table (generic — "for the
prototype, X isn't needed" as the red-flag phrasing).

Phase 2 STOP report in SKILL.md gained a new required bullet: "Removals
from Phase 1 scope — every in-scope item from Phase 1 that you did NOT
validate in Phase 2, with the reason per Scope-Removal Triage bucket. If
there were no removals, say so explicitly."

New Principle in SKILL.md: "Removals from approved Phase 1 scope are user
decisions, not model decisions."

### Fix 2 — Surface Coverage Check

New subsection in `references/phase-2-prototype.md` under Security Tooling
Validation. Model enumerates the surfaces in the prototype (application
code, Dockerfile, compose, IaC, shell, CI config, frontend), then confirms
the ecosystem-default SAST tool covers each one. If uncovered, the model
adds a supplementary tool from the supplementary-tool table.

The failure-mode explanation is made explicit: "A common failure mode is
for the model to read the ecosystem table as a complete specification and
stop there. The ecosystem table says one thing per row ('Python → bandit'),
and the model takes that as 'bandit is the answer.' But bandit is
Python-only."

Phase 2 Step 7 in SKILL.md updated to say "start from the ecosystem-default
tool but do NOT stop there — run the Surface Coverage Check."

New Principle in SKILL.md: "Tables are starting points, not terminuses."

## What this trial did not cover

- No pipeline was generated from the design doc. This was a
  planning-skill-only trial.
- The prototype itself was not re-validated from scratch; the run leveraged
  the existing `prototypes/airflow-google-drive-ingestion/` directory.
- No independent verification that `gitleaks` or `pip-audit` ran
  correctly — the trial's focus was on the decision-making process, not
  the tools themselves.

## Follow-ups

- Validate the fixes in P02: re-run planning on the same feature, confirm
  Scope-Removal Triage fires when relevant, confirm Surface Coverage Check
  drives multi-tool SAST selection.
- Remove Airflow-DB-persistence example from the Scope-Removal Triage table
  before the next trial so the fix isn't anchored to this specific
  observation (done before P02 started — see the "leaked example" concern
  flagged during the iteration).

## Tags

`silent-scope-removal`, `table-as-complete-spec`, `surface-coverage-gap`,
`judgment-as-fact`
