# P04 — Cliff-edge labeling discipline

**Date:** 2026-05-11
**Target:** prototype-driven-planning skill
**Project context:** airflow-gdrive-ingestion (one-time design-doc hand-update)
**Tags:** `cliff-edge-discipline`, `breadcrumb-elicitation`, `labeling-as-signal`,
`upstream-vs-downstream-fix`
**Sister trials in arc:** R04 (criticality + verification fields),
D03 (no-prototype-references + cliff-edge coverage), PC01 (task-type
preambles + criticality grouping)
**Result:** Skill changes landed; airflow design doc gained four
`**Cliff edge:**` labels; downstream skills (R04) successfully
consumed the labeled output

---

## Why this iteration

Session-status-2026-05-10 update-3 documented a three-executor
failure on task-01: Pi+Gemma, Pi+Qwen, and Claude Code all produced
`tests/conftest.py` missing the `all_records` fixture and (for Claude
Code) `requirements.txt` missing `apache-airflow[celery]==2.10.5`. The
diagnosis was that decomposition-skill prose ambiguity — `files[].
description` paragraphs combining "mirror prototype" with "include X
that prototype doesn't have" — caused models to resolve the
contradiction inconsistently.

The first proposed fix was to drop the prose and lean on the
prototype as a path-only reference. Session-status-2026-05-11 refined
this: the *real* fix is upstream. Critical patterns are BDD scenarios;
the roadmap is the right encoding layer; what was missing was a
structural way for the design doc to *tag* observations that document
specific failure modes, so the roadmap skill could mechanically
identify which scenarios deserve the `cliff_edge` criticality tier.

The planning skill already produces these breadcrumbs in
observation-with-evidence form (the airflow design doc said "GoogleDriveHook
authenticates [...] omitting `key_path` causes a `DefaultCredentialsError`").
What it did not do was *label* them as cliff edges in a way the roadmap
could pick up structurally. P04 adds that labeling discipline.

A second piece this iteration adds: **deliberate cliff-edge probing**
during prototype iteration. The previous Phase 2 guidance captured
breadcrumbs *incidentally* — only when iteration happened to fail with
a specific error. For new integration boundaries (auth field names,
container init formats, package install user), this iteration adds a
rule to deliberately probe at least one wrong configuration to capture
the failure mode. Without this, future planning runs produce design
docs that say "X is correct" without evidence that not-X is wrong, and
downstream cliff-edge labeling has nothing to consume.

## What changed

Four files updated, no project-side artifact regeneration required
(planning skill produces design docs; the airflow design doc was
updated by hand as a one-time bridging step).

### 1. `references/phase-3-design-doc.md`

Added **Rule 3** to the Judgment vs. Observation discipline. The three
previously-documented label types — *observation with evidence*,
*speculation labeled "Not observed"*, *prescription labeled "Prescribed
(not validated)"* — gained a fourth: *cliff-edge observation labeled
"Cliff edge:"*. Format:

```
**Cliff edge:** <Behavior description>. Omitting <what> causes
<specific failure>. Validated in `<prototype file>`.
```

Distinguished from ordinary observation-with-evidence by the requirement
that both sides are documented: the working pattern *and* a specific
failure mode for the alternative. If only one side is captured, the
observation stays plain.

Added a "Good (cliff edge labeled)" example and a "Bad (cliff edge
missing the failure mode)" anti-example using the airflow project's
service-account connection URI as the concrete case. Also added the
single-location labeling discipline: each cliff edge gets labeled
once, in the most semantically-natural section (Prototype Reference
for auth boundaries, Tooling Notes for build-script boundaries, etc.).
Other sections may reference the same boundary in prose without
re-labeling — multiple labels for the same boundary would risk
confusing the downstream validator's coverage check.

### 2. `references/phase-2-prototype.md`

Two additions to the prototype-iteration phase.

The "Common failure patterns" subsection gained a **Cliff-edge breadcrumbs**
bullet documenting the pattern explicitly: when iteration follows the
shape "tried X, got error E, switched to Y," that's a cliff-edge
candidate. Capture both sides in the prototype README's Toolchain notes:
working pattern, failing alternative, exact error message. Without the
explicit failure mode captured, Phase 3 cannot produce a `**Cliff edge:**`
label and downstream skills lose the criticality signal.

A new **Cliff-Edge Probing for New Integration Boundaries** subsection
was added between "What counts as 'working'" and "Toolchain Validation."
This codifies *deliberate* probing of boundaries that incidental
iteration may not surface. The subsection names four common probe
categories (authentication, container init, permission/user, connection
field names with similar alternatives), three non-probe categories
(already-documented boundaries, hypothetical wrong configurations,
destructive setups), and the record-keeping format for captured
results. The rationale paragraph at the end ties this back to the
roadmap's `criticality: cliff_edge` requirement.

### 3. `references/design-doc-template.md`

Added a single-line reference at the top of the meta-commentary
pointing at the four-label convention in `phase-3-design-doc.md`:

> Within sections, label claims using the conventions in
> `phase-3-design-doc.md` § Judgment vs. Observation — observation
> with evidence (the default for prototype-validated claims),
> **Cliff edge:** (observation with a specific failure mode for the
> alternative), **Not observed:** (speculation), or **Prescribed
> (not validated):** (production prescription not in the prototype).
> The four labels are the discipline; the template shows the
> structural shape.

The template itself was *not* littered with cliff-edge examples in
every component block — that would conflict with the template's role
as structural shape. The reference doc owns the labeling discipline;
the template owns the structure.

### 4. `SKILL.md`

Updated the "Observation and judgment are labeled distinctly in the
design doc" principle to enumerate all four labels (was three):
observation, "not observed," "prescribed (not validated)," and
**Cliff edge:**. A future implementer must be able to tell
observation from judgment from cliff edge without re-reading the
prototype.

## One-time airflow design doc update

Per the plan, the airflow design doc at
`docs/design/airflow-gdrive-ingestion-2026-04-28.md` was hand-updated
to add `**Cliff edge:**` labels to existing observations that
qualified under the new rule. This is a one-time bridging step; future
planning-skill runs against fresh projects will produce labeled output
automatically.

Four cliff-edge labels added:

1. **Service account connection URI** (Prototype Reference section).
   Both failure modes documented: `DefaultCredentialsError` for
   omitting `key_path`, `HttpError 403 insufficientPermissions` for
   omitting `scope`.
2. **`airflow-init` single-line bash** (Tooling Notes section). Failure
   mode: multi-line YAML block scalars cause Bash to split continuation
   lines, breaking the `--username admin` flags.
3. **`pip install` as airflow user** (Containerization section).
   Failure mode: "You are running pip as root" bootstrap error from
   the apache/airflow base image.
4. **`tempfile.mkstemp()` over `/tmp/`** (Components > Project Setup >
   Production considerations). Failure mode: bandit B108 severity-medium
   findings; the `mkstemp` form passes clean.

Items considered but **not** labeled, per the both-sides rule:

- **pytest version pin** (`8.4.2 → 9.0.3` for CVE-2025-71176) — not a
  boundary the implementer crosses on each piece of code; one-time
  pin justified by a CVE
- **MinIO endpoint scheme handling** — only the working side documented
- **`_upload_timestamp_utc` shared capture** — only the working side
  documented; the alternative-fails-with-specific-error breadcrumb is
  absent from this doc
- **`pika.BlockingConnection` over `aio_pika`** — design decision with
  rationale, not a tested boundary
- **pip-audit resolution divergence** — known tool behavior, not a
  user-code boundary

The "items not labeled" set highlights what future planning-skill
runs should capture more rigorously via the new Cliff-Edge Probing
subsection: each of these is a real boundary, but the prototype
iteration didn't capture both sides explicitly enough to support a
cliff-edge label.

## Validation

End-to-end via the arc's downstream trials:

- **R04** consumed the labeled design doc and produced exactly four
  scenarios with `criticality: cliff_edge`, one per label. The
  roadmap-skill validator's cliff-edge coverage check (added in R04)
  enforced this structurally.
- **D03** consumed the criticality-tagged roadmap and produced a
  decomposition where every cliff-edge scenario is cited by at least
  one task. The decomposition-skill validator's parallel coverage
  check (added in D03) enforced this.
- **PC01** rendered the resulting prompts with cliff-edge subsections
  front-and-center, framed as non-negotiable.

The full chain — design doc labels → roadmap scenarios → task
citations → prompt framing — is structurally enforced at each step.

## Failure modes addressed

The session-status-2026-05-10 update-3 failure mode (task-01
contradictory prose) is addressed structurally via the chain:

- P04 makes cliff edges a typed signal in the design doc
- R04 turns them into typed scenarios with criticality and
  verification
- D03 requires task citations for every cliff edge
- PC01 frames them as non-negotiable in executor prompts

No single change is sufficient; each layer in the chain depends on
the previous. P04 is the upstream anchor — without explicit labels,
downstream layers either have to infer criticality from prose
(unreliable) or treat all observations uniformly (drops the
signal entirely).

## Key findings

1. **Labels as structural signal**, not just documentation. The
   `**Cliff edge:**` label is not for human readers (though it works
   for that too) — it's a mechanical pickup point for the roadmap
   skill's coverage check. The discipline survives because the
   downstream validator enforces it: a labeled cliff edge that
   doesn't produce a roadmap scenario fails validation. This is the
   same "force visibility" pattern from P01–P03 applied at a
   structural rather than reasoning layer.

2. **Breadcrumb capture is a Phase 2 responsibility, not Phase 3.**
   Phase 3's labeling discipline is only as good as the prototype
   README's Toolchain Notes section. Phase 2 must capture
   "tried X, got error E, switched to Y" iteration breadcrumbs, and
   the deliberate-probing rule extends this to boundaries that
   incidental iteration didn't surface. Without the breadcrumb,
   Phase 3 has nothing to label.

3. **The both-sides rule prevents speculation creep.** A label
   format that requires *both* the working pattern *and* the specific
   failure mode prevents the design doc from accumulating
   prescriptive-shaped cliff edges that lack evidence. If only one
   side is documented, the observation stays plain. This forces
   real probing work upstream rather than letting the cliff-edge
   label become a vague "this is important" marker.

4. **Single-location labeling avoids validator confusion.** The
   discipline of labeling each cliff edge once, in the most
   semantically-natural section, keeps the validator's coverage
   count clean (one label → at least one scenario). Multiple labels
   for the same boundary would inflate the count and either cause
   spurious validation failures or require deduplication logic the
   skill chain doesn't want.

5. **The planning skill's existing breadcrumb-elicitation discipline
   carried this work.** A meaningful share of P04's load-bearing work
   was already in the skill — Phase 2's "Common failure patterns"
   bullets, Phase 3's Judgment vs. Observation discipline, the
   observation-with-evidence rule. What was missing was the label as
   structural signal. Earlier in the session I considered whether
   planning needed a larger consultation update; reviewing the existing
   skill showed it didn't. The change is additive on top of solid
   foundations.

## Related plan documents

- `session-status-2026-05-11-cliff-edges-and-two-prompt-split.md` —
  arc-level plan covering this iteration and its sisters
- `session-status-2026-05-10-update-3.md` — diagnosis that triggered
  the arc

## Skill change summary

- `references/phase-3-design-doc.md`: Rule 3 (cliff-edge labeling) +
  good/bad examples + single-location guidance
- `references/phase-2-prototype.md`: cliff-edge breadcrumb bullet in
  Common failure patterns; new Cliff-Edge Probing subsection
- `references/design-doc-template.md`: four-label reference in
  meta-commentary
- `SKILL.md`: principle extended to enumerate four labels
