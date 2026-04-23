# P02 — Feasibility in Disguise; Judgment Rendered as Observation

> **Date:** 2026-04-23
> **Skill:** prototype-driven-planning (Part A + Part C iteration 2)
> **Target:** health-data-ai-platform (second re-plan of airflow-google-drive-ingestion)
> **Outcome:** Two additional failure modes identified and fixed. Scope-Removal Triage and Surface Coverage Check from P01 held. Design doc is now significantly higher-quality but still has identifiable gaps at the judgment-vs-observation boundary.

## Context

Second iteration of the planning skill after P01's Scope-Removal Triage and
Surface Coverage Check fixes landed. Same target feature. The design doc
this trial produced was reviewed section-by-section for residual failure
modes.

## What went well (P01 fixes held)

- **Surface Coverage Check fired.** The Security Tooling Validation step
  produced a multi-tool SAST selection: `bandit` for Python code AND
  `semgrep` with `p/dockerfile`, `p/secrets` (and effectively `p/python`)
  rulesets. The design doc's Security Tooling subsection lists both with
  exact commands.
- **No silent scope removals.** The Phase 2 STOP report's new "Removals
  from Phase 1 scope" bullet appears to have prevented the drop-volume
  failure mode from recurring. (Inferred: no user-flagged removal during
  review.)
- **Prototype grounding remains strong.** Most design-doc statements cite
  specific prototype files or observations. The "Observe, don't predict"
  principle continues to hold.

## Observations during review of the generated design doc

### Observation 1 — Deferred Decisions contains feasibility-in-disguise items

The design doc's `## Deferred Decisions` section contained items that
passed the "difference test" (framed as operational) but failed an
implicit "assertion test" (the design doc makes claims that depend on
unobserved behavior).

Specifically:

- **"boto3/botocore upgrade"** — deferred with rationale "the boto3 API
  surface used by the service is stable across versions." But earlier in
  the doc, the known-vulnerability disclosure states "upgrade must be
  retested." The model simultaneously asserts stability (to justify
  deferral) and asserts uncertainty (when documenting the known
  vulnerability). The assertion that the upgrade will work is unobserved
  speculation.

- **"Drive file staleness detection"** — deferred with rationale "what
  to do when the Android device has not exported a new ZIP is an
  operational policy." But if the answer is "alert after N days of stale
  data," that's a new architectural component. Different answers yield
  different designs; the "operational" framing masks the architectural
  question.

These are both feasibility questions dressed in operational-decision
language.

### Observation 2 — Behavioral claims stated as facts without prototype evidence

The design doc contains statements that read like observations but are
model assertions. Examples from the generated doc:

- "This is the correct behavior: a failed run will re-process from the
  last known good watermark on retry."
  — No prototype test simulated a mid-loop failure. This is a model
  prediction about behavior, not an observation.

- "should be refactored to a single connection per process_records
  invocation in production"
  — Prescription. The prototype didn't validate that a single long-lived
  connection would work across the full batch.

- "is acceptable for a daily DAG"
  — Judgment call about what "acceptable" means. No observation supports
  this.

- Testing Strategy section prescribes integration tests against MinIO and
  RabbitMQ, but the prototype only ran unit tests with mocked boto3/pika.
  The design doc is prescribing tests the prototype did not run.

None of these are wrong per se — they're reasonable judgments. But they're
indistinguishable from observations in the prose, which misleads a future
implementer.

### Observation 3 — No explicit record of Phase 1 deferrals in the design doc

The Prototype Reference's "Limitations of the prototype" subsection
conflates two things: design choices about minimum viable validation
(limited by design) and items the user agreed to defer during Phase 1
(deferred by decision). The doc lists items like "no retry logic," "no
multi-user support," "no alerting" as prototype limitations — but without
distinguishing whether the user explicitly approved deferring these or
the model made those scope calls.

## Root cause analysis

The common pattern across all three observations: **the model turns
uncertain judgments into fact-shaped output.**

- Observation 1: the judgment is "this version bump is safe"; the output
  is "Deferred to implementation" (a routine categorization).
- Observation 2: the judgment is "this is the correct behavior"; the output
  is a bare assertion with no hedge.
- Observation 3: the judgment is "this was never in scope" or "this is a
  prototype design limit"; the output is a single undifferentiated list.

The Open Questions Triage added in Part A catches one narrow case of this
(feasibility questions outright) but isn't strong enough to catch items
that pass a surface-level "is this operational?" test.

## Skill fixes

Three edits landed the same day as the trial.

### Fix 1 — Strengthen triage with an assertion test (Edit A)

Added to `references/phase-3-design-doc.md`'s Open Questions Triage
section. The existing "difference test" (does the answer change the
design?) is joined by a second diagnostic, the **assertion test**:

> Does accepting this item as deferred require the design doc to *assert*
> something the prototype didn't observe?

If yes, it's a feasibility question regardless of how operational it
sounds. Worked examples include version bumps (the "boto3 stability"
case), staleness detection, retry policy (split into existence-of-retry
vs. policy-of-retry), and credential rotation (the only one that cleanly
passes the test).

Triage output template now requires a "Passes assertion test: ..."
field on Q-bucket items so the model has to explicitly confirm the check
ran.

### Fix 2 — Scope Deferrals from Phase 1 as its own section (Edit B)

New section `## Scope Deferrals from Phase 1` in the design-doc template,
slotted between Prototype Reference and Architecture Overview. Captures
items the user explicitly approved as out-of-scope during Phase 1, with
each entry carrying the user's rationale.

The Prototype Reference section's "Limitations" subsection intro is now
explicit: "design choices about minimum viable validation — distinct
from Scope Deferrals from Phase 1 below."

If nothing was deferred in Phase 1, the section says so explicitly:
"None — all Phase 1 scope was validated by the prototype." Silence is
not an allowed outcome.

### Fix 3 — Judgment vs. Observation labeling (Edit C)

New subsection in `references/phase-3-design-doc.md`'s Writing Quality
section. Two rules:

1. **Behavioral claims cite evidence or admit speculation.** Any statement
   of the form "the system does X" / "Y handles Z correctly" must either
   cite a prototype file and observation, or be labeled "*Not observed —
   based on inference.*"

2. **Prescriptive claims are labeled.** "Should be refactored to X" /
   "should be upgraded to Y" carries the "**Prescribed (not validated)**"
   label.

Four worked examples in the subsection: one Good (observation with
evidence), two Good (speculation and prescription properly labeled), one
Bad (judgment stated as fact). All examples are generic (no
project-specific names).

New Principle in SKILL.md: "Observation and judgment are labeled distinctly
in the design doc."

## Known remaining risks (for P03)

- The assertion test catches one class of feasibility-in-disguise but
  relies on the model correctly applying the test. A model that doesn't
  recognize an assertion as an assertion will still miss it.
- The Judgment vs. Observation rule is prose-level discipline. It
  doesn't have a mechanical enforcement mechanism the way the assertion
  test has the triage-output template.
- Security findings handling was not tested in this trial. The design doc
  named the security tools correctly (thanks to P01's Surface Coverage
  Check) but did not exercise the handling of actual findings.

## Tags

`feasibility-in-disguise`, `judgment-as-fact`, `deferred-decisions-abuse`,
`phase-1-scope-ambiguity`
