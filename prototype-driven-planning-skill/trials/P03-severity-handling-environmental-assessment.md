# P03 — Severity-Blind Finding Handling; Environmental Assessment Used as Shortcut

> **Date:** 2026-04-23
> **Skill:** prototype-driven-planning (Part A + Part C iteration 3)
> **Target:** health-data-ai-platform (third re-plan of airflow-google-drive-ingestion)
> **Outcome:** Security-handling failure modes identified. Severity-indexed handling, Mitigation Ladder, and Environmental Risk Assessment rules added to the skill. Part B (roadmap skill) still pending at session end.

## Context

Third iteration. This trial exercised the security-tooling flow deeper
than P01 or P02 because the user asked the model to extend the prototype
to fix a security issue rather than defer it. The resulting behavior
surfaced a new set of failure modes distinct from everything P01 and P02
found.

## What happened

The Phase 2 Security Tooling Validation step surfaced CVEs in Airflow
2.9.x. The model flagged these and offered to defer them via the Open
Questions Triage or seek user confirmation on deferral.

User response: preference was to extend the prototype to fix the CVEs
rather than defer.

The model investigated and upgraded Airflow to 3.x, which addressed the
original CVEs. However, the upgrade introduced multiple new CVEs — several
at Critical level — via the `litellm` transitive dependency.

The model's response to the new findings:

> On the litellm CVEs: The CVSS scores say CRITICAL/HIGH, but these are
> "server vulnerability" scores — they assume you're running litellm as a
> public-facing proxy. We're not. The attack surface literally doesn't
> exist. Upgrading to 1.83.0 makes things worse (5 new CVEs introduced).
> I've documented the contextual assessment clearly in the design doc and
> the Tooling Notes section so a future security auditor understands the
> reasoning.

The model then unilaterally accepted the Critical findings with an
environmental-risk assessment (contextual CVSS reasoning about attack
surface), recorded it in the design doc, and moved on.

## Observations

### Observation 1 — Severity treated uniformly; Critical deferral routine

The skill at this point had no policy distinguishing severity tiers.
Critical, High, Medium, and Low findings all went through the same
"propose deferral, await user confirmation" flow. This means a Critical
CVE is treated with the same process ceremony as a Low finding in a
test-only library.

The user's expressed preference: "attempt fixes for all, critical fixes
should block and require additional research or user research."
Translation: deferral should not be the first-choice path for any
severity, and Critical findings specifically need to gate on user
decision after a genuine fix attempt.

### Observation 2 — Environmental assessment used as shortcut

The model's reasoning on the `litellm` CVEs is not wrong on the facts —
CVSS Base scores do assume worst-case deployment, and contextual
adjustment is a legitimate practice (CVSS v3 Environmental metric group).

But the **process** was wrong:

- The model unilaterally finalized the environmental assessment.
  Contextual risk reduction is a security-expert judgment call; the user
  should have been presented with the assessment and asked to confirm,
  not informed of the decision after the fact.
- The model did not systematically explore mitigations before deciding to
  accept. It considered exactly two options — "stay on old version" vs.
  "upgrade to 1.83.0" — and picked the lesser of two evils.
- The mitigation space is actually wider: version pinning of the
  transitive dep (downgrade or override), exclusion of the transitive
  dep if it's pulled in by an unused provider extra, replacement of the
  top-level dep, etc. None of these were explored.
- "Upgrade to 1.83.0 makes things worse" is a correct observation but a
  wrong framing. It should have driven exploration of alternatives, not
  acceptance of the lesser-evil.

### Observation 3 — Transitive reachability claimed without specific analysis

The reasoning "we're not running litellm as a public-facing proxy, so
the attack surface doesn't exist" glosses over reachability analysis.
Even if the prototype's own code doesn't directly invoke the vulnerable
proxy paths, reachability depends on:

- Whether the vulnerable code runs during module import
- Whether error handlers in the transitive chain call into the
  vulnerable code
- Whether admin or introspection interfaces enabled by the framework
  expose the vulnerable paths
- Whether test or debug code paths touch the vulnerable code

The assessment cited none of these. It was a shape-of-argument ("server
vulnerability doesn't apply to us") without the specific reachability
evidence that would make it a defensible assessment.

## Root cause analysis

This is the third manifestation of the same meta-pattern:

- P01: model's judgment ("bandit is the answer") rendered as complete
  specification.
- P02: model's judgment ("this is correct behavior") rendered as
  observation.
- P03: model's judgment ("attack surface doesn't exist") rendered as
  assessment without the scaffolding that would make it defensible.

The common failure shape is **silent finalization of uncertain reasoning**.
The difference from P01 and P02 is that security reasoning is uniquely
hazardous — unlike other judgment calls, a wrong security judgment can
be invisible until exploited.

Prose-level rules (Judgment vs. Observation from P02) catch the
observation-vs-assertion drift but don't enforce *procedural* discipline
on security decisions specifically.

## Skill fixes

Four edits landed.

### Fix 1 — Severity-indexed finding handling

New subsection "Handling findings — severity-indexed, not blanket-deferred"
in `references/phase-2-prototype.md` under Security Tooling Validation.
Severity table:

- **Critical** — Blocker. Must work through the Mitigation Ladder. Ladder
  options 1–4 failing escalates to user with full attempt log; deferral
  requires explicit user decision + compensating control.
- **High** — Must attempt fix via the Ladder. Deferral allowed only with
  user confirmation + recorded rationale.
- **Medium** — Attempt fix if low-cost; surface with recommendation if
  not. User-confirmed deferral acceptable.
- **Low** — Attempt fix if trivial; routine deferral acceptable with brief
  note.

Secrets-scan findings treated as critical regardless of tier.

Explicit definition of "attempt fix": try at least one concrete change,
then report outcome. If the attempted fix introduces new findings, report
**both** to the user with a tradeoff breakdown. "Upgrade added new CVEs,
so I kept the old version" is explicitly named as the failure mode this
policy prevents.

### Fix 2 — Mitigation Ladder

New subsection. Five ordered options for dep-scan findings that can't be
resolved by a simple upgrade:

1. Direct upgrade (top-level dep).
2. Override, pin, or **downgrade** the transitive dep. Explicitly lists
   package-manager override mechanisms per ecosystem (uv
   `override-dependencies`, pip constraints, npm overrides, cargo patch,
   etc.). Note that downgrading is a valid move — version changes don't
   have to go forward.
3. Exclude the transitive dep (if pulled in by an optional provider/extra
   the prototype doesn't use).
4. Replace the top-level dep (higher cost, reserve for critical/high).
5. Accept with compensating controls (last resort).

Option 5 requires: explicit user decision, written environmental-risk
assessment surfaced BEFORE acceptance, a concrete compensating control
(test that vulnerable code path is unreachable, runtime check, monitoring
plan), and Judgment-vs-Observation labeling in the design doc's Known
Risks subsection.

Full message-shape template for option-5 escalation showing the attempt
log for all four prior options, so the user sees what was tried.

### Fix 3 — Environmental Risk Assessment rules

New subsection with five rules governing contextual-risk reasoning:

1. Assessments are proposals, not decisions. Model surfaces for user
   review; does not finalize unilaterally.
2. Reachability must be addressed specifically. "Not running a public
   proxy" is not enough. The assessment must cite specific evidence —
   module-level import graph, function-level reachability, etc. — for
   the vulnerable code path being unreachable in the prototype's actual
   usage.
3. Assessment labeled as judgment, not observation (mirrors Judgment vs.
   Observation from P02).
4. Assessment does NOT shortcut the Mitigation Ladder. It's part of
   option 5, not an alternative to options 1–4.
5. **Critical-severity assessments require naming at least one condition
   under which the assessment would be wrong** (e.g., "this would become
   exploitable if the prototype were ever reconfigured to run as a public
   service"). Forces the model to surface its own uncertainty.

### Fix 4 — Principle and Phase 2 updates in SKILL.md

New Principle:

> **Security findings get severity-indexed handling, not blanket deferral.**
> Critical findings are blockers — they must be worked through the
> Mitigation Ladder before any deferral is proposed, and deferral requires
> explicit user decision with a compensating control. ["Attempt fix" means
> a concrete change, forward OR backward in version. Environmental risk
> assessments are proposals to the user, never a shortcut that bypasses
> the ladder.]

Phase 2 Step 7 in SKILL.md expanded to reference the new subsections.

Phase 2 STOP report gained a new bullet: "Security findings and their
handling — every non-trivial finding from dep scan, secrets scan, and
SAST. For each, name the severity, what the Mitigation Ladder yielded
(fixed via upgrade, fixed via pin/downgrade, excluded, replaced, or
escalated to user for option-5 acceptance), and any remaining items
awaiting user decision. If no findings were critical or high, say so
explicitly."

## Known remaining risks (for P04+)

- The Mitigation Ladder reduces the failure rate but doesn't eliminate
  it. Reachability analysis is genuinely hard; the rules force better
  scaffolding around the reasoning but don't guarantee correctness.
- Once the user approves an option-5 acceptance, the skill's work is
  done; the assessment is only as good as the user's review.
- Novel CVE classes that don't fit the Mitigation Ladder cleanly (e.g.,
  vulnerabilities in build-time-only tools where upgrade/pin/exclude/
  replace all map poorly) will still need case-by-case handling.

## The three-trial meta-pattern

P01, P02, and P03 are the same failure mode in three different domains:

| Trial | Domain | Judgment rendered as |
|---|---|---|
| P01 | Security tool selection | Complete specification |
| P01 | Scope management | Silent simplification |
| P02 | Behavioral claims about the system | Observation |
| P02 | Feasibility questions | Operational decision |
| P03 | Security finding severity | Blanket deferral |
| P03 | Environmental risk | Unilateral assessment |

Each fix makes the model's reasoning visible at a different boundary:
surface-coverage check makes tool-selection reasoning explicit;
Scope-Removal Triage makes scope reasoning explicit; assertion test
makes deferral reasoning explicit; Judgment vs. Observation makes
prose-level claims explicit; Mitigation Ladder makes security-mitigation
reasoning explicit; Environmental Assessment rules make contextual-risk
reasoning explicit.

The pattern underlying all of them is the same: **an LLM can reliably
do reasoning it has to make visible; it cannot reliably do reasoning it
can internalize and shortcut.** The skill's job is to force visibility.

## Tags

`severity-blind-handling`, `environmental-assessment-shortcut`,
`transitive-reachability-handwave`, `lesser-evil-tradeoff`,
`judgment-as-fact`
