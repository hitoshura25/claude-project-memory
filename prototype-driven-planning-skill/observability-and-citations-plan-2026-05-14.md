# Planning Skill — Observability and Citations Expansion Plan

**Status:** proposed, 2026-05-14
**Author:** Claude session 2026-05-14
**Skill targeted:** `prototype-driven-planning`
**Validation trial:** P05 (next planning-skill trial slot)

> **Revision history**
> - 2026-05-14 (initial draft): used static ecosystem-to-tool tables for
>   telemetry SDKs, performance APIs, and per-ecosystem strong/weak
>   verdicts.
> - 2026-05-14 (this version): rewritten to use the runtime-research
>   pattern from the implementation skill's Runtime-Isolation Research
>   protocol (LEARNINGS.md "Static ecosystem-to-tool tables are
>   stop-thinking instructions"). The skill specifies *responsibility*
>   and *signals*; the model researches the *realization* at use time.

## Why this exists

The user requested four additions to the planning skill, plus
clarification on a fifth (security validation of the prototype) which
the P01–P03 arc already covers:

1. **Prototype security validation** — already covered by Phase 2
   Step 7 (Surface Coverage Check, severity-indexed handling,
   Mitigation Ladder, Environmental Risk Assessment). No changes
   needed. Confirmed in pre-plan discussion.
2. **Telemetry instrumentation validation in Phase 2** (new).
   OpenTelemetry-preferred where mature; applicability-gated;
   demonstrated viewing path required; test or verification
   recorded; tool selection comes from live research at skill
   runtime, not from a table in the skill.
3. **Performance measurement validation in Phase 2** (new).
   Type-of-project applicability gates (UI vs backend vs CLI);
   demonstrated viewing path; test or recorded measurement;
   explicit overlap-with-telemetry handling for backend; tool
   selection comes from live research at skill runtime, not from
   a table in the skill.
4. **Tech-selection bias toward observability-friendly frameworks
   in Phase 1** (new). Stronger form per user decision: picking a
   weak-observability tech requires explicit justification. The
   strong/weak verdict per candidate × dimension comes from live
   research at skill runtime, not from a table in the skill.
5. **External-source citation discipline in the design doc** (new).
   Inline `**External:**` label per Judgment-vs-Observation pattern
   plus a consolidated `## References` section at the end of the
   design doc.

The expansion sits within two established patterns from this skill
set:

- **Force visibility** (P01–P03, R01, R02-prep, R04, D03). Each
  addition forces reasoning into a visible artifact: telemetry as
  exported data, performance as a measurement, tech selection as a
  documented comparison, citations as URLs.
- **Responsibility + signals + research-protocol** (Phase A/B
  runtime-isolation in the implementation skill). The skill specifies
  *what the output must accomplish* and *what evidence to look for*;
  the model researches the *realization* at runtime. Static
  ecosystem-to-tool tables in skill references are a documented
  anti-pattern (LEARNINGS.md "Static ecosystem-to-tool tables are
  stop-thinking instructions") and are not introduced here.

## User decisions (locked)

- **Telemetry and performance** ship as two separate Phase 2
  subsections (not one combined). Separate applicability gates per
  topic. Overlap on backend (a single OTel span satisfies both) is
  declared explicitly via a field in the Performance subsection.
- **Citations** use inline `**External:**` label *plus* a
  consolidated `## References` section. Parallel to the existing
  four-label discipline (Cliff edge / Not observed / Prescribed /
  External — fifth label added).
- **Tech-selection bias** is the stronger form: choosing a tech with
  weak observability support requires explicit justification surfaced
  to the user in the Phase 1 proposal.
- **Tool selection is researched at runtime, not prescribed by the
  skill.** Confirmed in pre-plan discussion. No ecosystem-to-tool
  tables for telemetry, performance, or observability verdicts.

## What's changing

### Architectural fit

The expansion adds three new sections to Phase 2 (one of which —
security — is already there), one new step to Phase 1, and one new
label-plus-section to the design doc. The shape mirrors the existing
Security Tooling Validation work plus the implementation skill's
Runtime-Isolation Research protocol:

| Existing pattern (security tooling) | New parallel (telemetry) | New parallel (performance) |
|----|----|----|
| Phase 2 step validates tools work in prototype's ecosystem | Phase 2 step validates instrumentation works in prototype's ecosystem | Phase 2 step validates measurement works in prototype's ecosystem |
| Surface Coverage Check forces enumeration of every surface | Applicability gate forces explicit not-applicable rationale | Type-of-project applicability gate forces explicit category selection |
| **Ecosystem table** (carried over from P01–P03 era; this skill's only remaining static tooling table) | **No ecosystem table** — signals + research protocol | **No ecosystem table** — signals + research protocol |
| Severity-indexed handling | Three signals (traces / metrics / logs) — subset gated by applicability | Type-specific demonstration (rendering perf for UI, latency for backend) — category gated by applicability |
| Demonstrated handling of findings | Demonstrated viewing path required | Demonstrated viewing path required |
| Recorded outcome in design doc | Recorded outcome in design doc, plus URLs consulted | Recorded outcome in design doc, plus URLs consulted |

**On the existing Security Tooling ecosystem table.** Phase 2's
Security Tooling Validation still carries an ecosystem table (Python
→ pip-audit, Node → npm audit, etc.). This expansion doesn't change
it — the security table predates the Phase A/B refactor and the
LEARNINGS.md anti-pattern note, and removing it is out of scope for
this expansion. The skill notes mention the table is a "starting
point" and pairs it with the Surface Coverage Check forcing function,
which partially mitigates the stop-thinking risk. A future expansion
may rewrite the security tooling section using the same research-
protocol pattern adopted here; tracked as an open question in §
"Risks and open questions."

### Files touched

| File | Change |
|------|--------|
| `SKILL.md` | Phase 1 step list (new step for observability-tech check); Phase 2 step list (two new steps after current 7); Quick Reference table; Principles list (3 new principles); How-to-Start unchanged |
| `references/phase-1-discovery.md` | New "Observability-Friendly Tech Selection" section under Research, structured as responsibility + signals + research protocol (no static tables). New "Source citations" subsection under Research output with `verified_at` / `accessed` discipline. Updated proposal template to surface comparison + justification + sources |
| `references/phase-2-prototype.md` | Two new major subsections after Security Tooling Validation: "Telemetry Instrumentation Validation" and "Performance Measurement Validation". Each structured as responsibility + signals + research protocol + demonstrated viewing path + test-or-example + what-to-capture (no static SDK/API tables). Updated Cross-Cutting Research section to mention citation discipline |
| `references/phase-3-design-doc.md` | Add **External:** as the fifth label in Judgment vs. Observation. New `## References` rule. Section-by-section guidance: Telemetry, Performance subsections under Tooling; new `## References` section at end |
| `references/design-doc-template.md` | Two new subsections under `## Tooling`: "Telemetry" and "Performance Measurement", paralleling the existing "Security Tooling" subsection (template fields don't pin specific tools — fields are for the research output to populate). New `## References` section at end. Meta-commentary updated to enumerate five labels (was four) |

No template-doc file additions; everything fits in existing structure.

## Detailed design — Phase 2 additions

Both new Phase 2 subsections share the same structural shape, modeled
on the implementation skill's Runtime-Isolation Research protocol:

1. **Responsibility** — what the output must accomplish.
2. **Applicability gate** — when this step runs vs. when it's
   skipped with a recorded reason.
3. **Signals** — what evidence in the project / ecosystem informs
   tool choice.
4. **Research protocol** — inspect signals → if convention exists,
   use it → if not, web-search current best-practice for the
   detected ecosystem → verify the chosen tool by running it →
   record URLs consulted with `accessed` dates.
5. **Demonstrated viewing path** — proof the data is observable.
6. **Test or verification** — captured in code or in the prototype
   README.
7. **What to capture for the design doc** — field-by-field, all
   fields populated by research output (no pre-pinned defaults).

### Telemetry Instrumentation Validation

**Responsibility.** The prototype demonstrates that observability
instrumentation works in its ecosystem: instrumentation code is
present, data is exported to some collector, the data is viewable,
and a test or recorded verification proves the data was produced.
The design doc's Telemetry subsection records what was validated;
production may extend it but cannot contradict it.

**Applicability gate.** Telemetry validation is required when the
feature ships:

- A runtime service (API server, worker, daemon)
- A scheduled job (cron, Airflow DAG, queue consumer)
- A mobile app that does meaningful work
- Any other long-running or repeatedly-invoked process

Not applicable for:

- Pure libraries with no I/O (no runtime context to instrument)
- Codegen tools / one-shot CLI utilities that run <1s and exit
- Pure configuration changes
- Infrastructure-as-code only

If not applicable, the design doc's Telemetry subsection records
"Not applicable — <one-sentence reason>." Same shape as the
existing SAST not-applicable rule. Silence is not allowed.

**Signals.** For the chosen tech, look for:

- **Existing instrumentation in the project.** Imports of
  observability SDKs (OpenTelemetry, vendor SDKs like Datadog or
  New Relic, framework-built-in tracers). If the project is already
  instrumented, the prototype extends the existing stack rather
  than introducing a new one.
- **CI / deployment config that implies a backend.** A
  `prometheus.yml` scrape config, a Datadog API key in CI secrets,
  a Honeycomb dashboard URL in a README — these are evidence of an
  existing observability backend the prototype should target.
- **Lockfile / dependency manifest entries.** Observability
  libraries already pinned in `pyproject.toml`, `package.json`,
  `build.gradle`, etc. The project's existing choice takes
  precedence.
- **Framework conventions.** Some frameworks have built-in
  instrumentation primitives (Spring Boot Actuator, Django's
  `django-prometheus`, Airflow's StatsD integration). The
  prototype builds on the framework's conventions when they exist.
- **Production target signals.** If the design doc or
  infrastructure repo names a backend (Datadog, Grafana Cloud,
  Honeycomb, self-hosted OTel Collector + Jaeger), the prototype's
  validation aligns with what production will use.

**Research protocol.**

1. **Inspect the project for existing observability signals** (above).
   The project's existing convention takes precedence. Record what
   was found and which signals support the conclusion.

2. **If the project has no existing instrumentation**, web-search for
   current best-practice telemetry tooling for the detected
   ecosystem. Search queries should be ecosystem-shaped and
   year-stamped (per the skill's web-search guidance):
   - "<ecosystem-name> opentelemetry instrumentation <current-year>"
   - "<framework-name> distributed tracing <current-year>"
   - "<language-name> observability libraries <current-year>"

   OpenTelemetry is the strong default where it has mature support;
   read the OTel project's current docs to confirm maturity for the
   detected ecosystem. If OTel is alpha/beta/unavailable for the
   ecosystem, the search surfaces the alternatives (vendor SDKs,
   framework-built-in, etc.). Record the URLs consulted and which
   tool was selected.

3. **Determine signals to capture.** The prototype validates whatever
   subset of traces / metrics / logs is meaningful for the feature.
   Don't require all three. A single trace span over the core
   operation is often the simplest valid demonstration. The
   research from step 2 surfaces which signals the chosen SDK
   supports — record the subset selected.

4. **Determine an export target the prototype can use** for the
   demonstrated viewing path. The choice is research-informed:

   - If the project already has a backend in use (signal step 1),
     export to it.
   - If not, the chosen SDK's docs typically describe a simplest-
     possible local exporter (a console exporter that prints to
     stdout, or a docker-compose snippet for a local collector).
     Read the docs and pick the lowest-friction option that proves
     the data flows.
   - For mature OTel ecosystems, a local OTel Collector receiving
     OTLP plus Jaeger/Zipkin/Prometheus visualizers is a common
     pattern; the SDK's docs will name the current canonical
     setup.

   Record the demonstrator and the command/URL that proves the data
   was viewed.

5. **Verify instrumentation works.** Either:

   - Write a unit test that asserts spans/metrics are produced
     using an in-memory exporter, if the SDK supports one (most
     mature SDKs do; the SDK's docs name the type).
   - Or run the prototype against the chosen demonstrator and
     record the observed output in the README, with the command
     used and a quote/screenshot-description of what was visible.

   The test path is preferred; the manual path is acceptable when
   the test path adds disproportionate complexity for a small
   feature (e.g., mobile app testing infra is heavy for a one-span
   proof).

6. **Record what was researched.** The Phase 2 STOP report includes:

   - Existing project observability signals found, if any
   - Tool chosen (if research was needed) and the URLs consulted,
     each with an `accessed <YYYY-MM-DD>` timestamp
   - Signals captured (traces / metrics / logs subset)
   - Demonstrator used and the viewing-path output
   - Verification artifact (test file path or README section
     reference)
   - Any ecosystem maturity caveats discovered

**What to capture for the design doc's Tooling section.** The
template field names are fixed so downstream skills can parse them.
Field *values* come from the research output:

- **Instrumentation SDK**: tool + version (from research, not from a
  skill table)
- **Exporter**: tool + version, or "built into SDK"
- **Signals captured**: subset of traces / metrics / logs
- **Demonstrator (prototype-time)**: what was used during prototype
  validation; how the data was viewed
- **Verification**: test file path or README section reference
- **Production target (proposed)**: backend the production
  deployment is expected to use. Labeled
  **Prescribed (not validated)** unless the prototype actually
  exported to that backend.
- **Sources consulted**: list of URLs cited during tool research,
  each with `accessed <YYYY-MM-DD>`. These flow into the design
  doc's `## References` section.
- **Notes**: any ecosystem maturity caveats discovered

### Performance Measurement Validation

**Responsibility.** The prototype demonstrates that performance
measurement works in its ecosystem: a relevant timing or rendering
metric is captured for the type of project, the measurement is
observable, and a test or recorded measurement proves the data was
produced. The design doc's Performance subsection records what was
validated.

**Applicability gate.** Always applicable for:

- Runtime services with user-facing latency requirements
- UI applications (mobile, web frontend, desktop, native apps)
- Batch jobs with SLA or budget concerns

Conditionally applicable for:

- Internal jobs where timing affects scheduling (validate if
  Phase 1 surfaced a timing concern)

Not applicable for:

- Pure libraries with no I/O
- One-shot CLI tools with no meaningful work
- Configuration changes / IaC-only features

If not applicable, the design doc records "Not applicable —
<one-sentence reason>." Silence is not allowed.

**Type-of-project category as research input, not prescription.**
Different project types call for fundamentally different measurement
approaches. The skill names the categories so the research is
focused, but does not prescribe specific tools or APIs per category.
The categories are:

- **UI rendering performance.** Frame timing, rendering pipeline
  cost, jank tracking, frontend load metrics.
- **Backend latency / throughput.** Operation duration, request
  latency, queue processing rate.
- **Batch / job timing.** End-to-end runtime, per-record
  processing time, throughput budgets.

The model determines which category applies (often more than one for
features that span UI and backend) and researches measurement tools
for *that* category. The tool that wins depends on the project's
framework, the platform's conventions at the time of research, and
existing project tooling — none of which the skill encodes.

**Signals.** For the chosen project type, look for:

- **Existing perf tooling in the project.** Imports of perf
  libraries, profiler scripts in the repo, CI workflow steps that
  run benchmarks (e.g., a `make bench` target or a Lighthouse CI
  job). If the project already measures performance, the prototype
  uses the same approach.
- **Framework conventions.** Some frameworks have built-in perf
  primitives (mobile platforms expose frame-timing APIs, web
  browsers expose `performance.*` APIs, backend frameworks often
  expose latency histograms). The prototype builds on framework
  conventions when they exist.
- **CI / deployment config that implies a target.** A Lighthouse CI
  workflow, a load-test harness in the repo, a perf SLO
  documented in a runbook.
- **Overlap with telemetry instrumentation.** If the Telemetry step
  above selected an SDK that natively captures timings (e.g., OTel
  spans are timing measurements), the same artifact may satisfy
  both steps. Record the overlap explicitly.

**Research protocol.**

1. **Determine project category.** UI rendering / backend latency /
   batch timing / N/A. A feature may span multiple categories — a
   web app's frontend has UI rendering concerns and the backend
   has latency concerns; both validate independently.

2. **Inspect the project for existing perf signals** (above). The
   project's existing convention takes precedence. Record what was
   found.

3. **If the project has no existing perf tooling**, web-search for
   current best-practice perf measurement for the detected category
   and framework. Search queries should be category-shaped and
   year-stamped:
   - For UI: "<framework-name> rendering performance measurement
     <current-year>" / "<mobile-platform> frame timing API
     <current-year>"
   - For backend: "<framework-name> request latency instrumentation
     <current-year>" / "<language-name> histogram metrics
     <current-year>"
   - For batch: "<runtime-name> job timing measurement
     <current-year>"

   Read the top results to identify the current community-
   recommended tool or API. The "stop-thinking instructions"
   anti-pattern applies — even though a single canonical tool may
   exist for some categories today, encode the research step, not
   the tool name.

4. **Check for telemetry overlap.** If the Telemetry step's chosen
   SDK natively captures timings, evaluate whether the same SDK
   satisfies this step too. For backend services this is common
   (OTel spans). For UI apps, telemetry and rendering perf are
   typically different artifacts (an OTel exporter call versus a
   platform frame-timing API). Record the overlap explicitly.

5. **Determine a demonstration approach.** The choice is
   research-informed:

   - For UI: a single screen rendered with a perf trace captured;
     command and one-line summary of the result in the README
   - For backend: a histogram bucket or span captured during the
     prototype's end-to-end run; actual numbers recorded in the
     README
   - For batch: a wall-clock measurement of the prototype's
     end-to-end run; numbers recorded

6. **Verify measurement works.** Either:

   - A test that asserts on a timing or measurement (e.g., the
     core operation completes in under X ms, render achieves
     target FPS)
   - A manual measurement recorded in the prototype README

   The test path is preferred; the manual path is acceptable when
   the test path is disproportionately heavy.

7. **Record what was researched.** The Phase 2 STOP report
   includes:

   - Project category determined
   - Existing project perf signals found, if any
   - Tool / API chosen (from research) and the URLs consulted with
     `accessed <YYYY-MM-DD>` timestamps
   - Demonstrator and the captured output
   - Baseline measurement numbers (concrete, not "fast enough")
   - Overlap-with-telemetry status (yes/no, citing the shared
     artifact if yes)
   - Verification artifact (test file path or README section)
   - Any maturity caveats

**What to capture for the design doc's Tooling section.** Field
names are fixed; values come from research:

- **Measurement category**: UI rendering / backend latency /
  batch timing / multiple (list)
- **Library or API**: tool/version or platform-API-name (from
  research, not from a skill table)
- **Demonstrator (prototype-time)**: what was used; how the data
  was viewed
- **Verification**: test file path or README section reference
- **Baseline measurement(s)**: concrete numbers (e.g., "core
  operation 142ms p50, 380ms p99 over 100 samples")
- **Overlap with telemetry**: yes/no; if yes, cite the shared
  artifact
- **Sources consulted**: list of URLs cited during tool research,
  each with `accessed <YYYY-MM-DD>`. These flow into the design
  doc's `## References` section.
- **Notes**: anything surprising (e.g., "first-render is 3x
  slower than steady-state due to JIT warmup; documented in
  production considerations")

## Detailed design — Phase 1 additions

### Observability-Friendly Tech Selection (stronger form, runtime-researched)

Add a research criterion to Phase 1 Step 5 ("Research") and to the
proposal template. The criterion is structured as
responsibility + signals + research protocol, not as an ecosystem
strong/weak table.

**Responsibility.** When Phase 1 is choosing among candidate
technologies for a greenfield feature (or evaluating the parent
project's tech for an extending feature), evaluate each candidate
against three observability dimensions and surface the verdict to
the user before approving the prototype scope. Weak verdicts on any
dimension require explicit justification + workaround.

**Applicability gate.**

- **Greenfield features:** the check applies in full. The model
  produces a verdict per candidate × dimension based on live
  research.
- **Extending features:** the check inherits the parent project's
  tech, but the model still produces an observability verdict for
  the parent's tech, so the user sees what they're inheriting. If
  the parent has weak observability, the design doc records the
  inheritance; the user can opt to add observability work as
  scope.
- **Single-candidate Phase 1 features** (where the tech is fixed
  by the project or business context — e.g., "this must be an
  Airflow DAG"): the check runs against the single candidate
  rather than a comparison. Weak dimensions still need
  justification.

**Three dimensions:**

1. **Security tooling support.** Are the dep scanner, secrets
   scanner, and SAST tools needed for Phase 2 available and mature
   for this tech? Existing project-level signals (if extending) or
   live research (if greenfield).
2. **Telemetry support.** Is there mature instrumentation
   available (OpenTelemetry or otherwise)? Live research.
3. **Performance measurement support.** Is there proven tooling
   for the relevant performance category? Live research.

**Signals.** For each candidate × dimension:

- **Project / inheritance signals** (for extending features): is
  the parent project already using observability tooling on this
  tech that works? Existing tooling is the strongest signal of
  "support exists" — it's already proven in this org's context.
- **Vendor / project documentation.** Does the candidate tech's
  official docs name observability integrations? A framework with
  a dedicated "Observability" docs section is a strong signal;
  silence on the topic is a weak signal.
- **Community-recommended-tool maturity.** For greenfield candidates,
  what does current best-practice say? Searching turns up either
  established patterns (OTel SDK at GA for ecosystem X) or signals
  of immaturity (alpha/beta status, low GitHub activity, sparse
  Stack Overflow coverage).
- **Cross-references.** If the tech is well-supported by major
  observability vendors (Datadog, New Relic, Grafana Cloud have
  integrations for it), that's evidence of an active ecosystem.

**Research protocol.**

For each candidate × dimension pair (e.g., 2 candidates × 3
dimensions = 6 research targets), do the following. Multiple
searches per dimension may be needed; this is acceptable given the
weight of the decision.

1. **Check project signals first.** If extending, the parent
   project's existing observability tooling answers the dimension.
   If greenfield with no existing context, proceed to step 2.

2. **Web-search current state.** Year-stamped queries per
   dimension:
   - Security: "<candidate-tech> SAST tools <current-year>",
     "<candidate-tech> dependency vulnerability scanner
     <current-year>"
   - Telemetry: "<candidate-tech> opentelemetry support
     <current-year>", "<candidate-tech> distributed tracing
     <current-year>"
   - Performance: "<candidate-tech> performance measurement
     <current-year>" (adapt to the perf category — UI vs backend
     vs batch)

3. **Read the candidate's official docs.** Whatever the search
   surfaces, verify against the candidate tech's own current docs
   for the dimension. The docs are the most authoritative source.

4. **Produce a verdict.** Each candidate × dimension gets one of:
   - **Strong** — mature, well-documented support exists; specific
     tool or pattern can be named
   - **Adequate** — usable support exists but has limitations
     (alpha/beta status, limited features, requires custom work)
   - **Weak** — no usable support; would require vendor lock-in,
     custom instrumentation, or accepting an observability gap

5. **For any Weak verdict**, name:
   - What specifically is weak
   - The alternative the prototype will use (vendor SDK, custom
     instrumentation, framework built-in, or "none — accept the
     gap")
   - The workaround for the limitation (e.g., "ship a wrapper
     that exports to OTLP from the framework's built-in metrics;
     to be validated in Phase 2")
   - The acknowledgment that the design doc will record what was
     actually validated, not vendor roadmap

6. **Record what was researched.** Each verdict carries its
   evidence — URLs consulted, with `accessed <YYYY-MM-DD>`
   timestamps. The user can audit the research before approving.

**Stronger-form rule.** Choosing a tech with any Weak verdict
requires explicit justification in the Phase 1 proposal. The user
sees the verdicts and justification before approving the scope —
same surface-it-first pattern as deferred risks. The user can
override by saying "use the tech anyway" or by saying "pick a
stronger-observability alternative."

**Hard veto avoided.** This is not a hard veto on tech choices.
Sometimes the feature requires a specific framework (the project
already runs on Airflow, the mobile platform is fixed, etc.). The
stronger form is about *visibility*: if the chosen tech has
observability gaps, the model surfaces them before the prototype
is built, so the user can decide whether to accept them or pick an
alternative.

**Proposal template addition.** The Phase 1 proposal gains a
section:

```
**Tech selection observability check** (each verdict backed by
live research at the URLs cited in the Sources block below):

| Candidate | Security tooling | Telemetry | Performance measurement |
|-----------|------------------|-----------|-------------------------|
| <candidate A> | <Strong | Adequate | Weak> — <one-line reason> | <Strong | Adequate | Weak> — <one-line reason> | <Strong | Adequate | Weak> — <one-line reason> |
| <candidate B> | <…> | <…> | <…> |

**Selection:** <chosen candidate>
**Justification (required when any column shows Adequate or Weak):**
<prose>
**Workarounds for Adequate/Weak dimensions:** <prose; to be
validated in Phase 2>

**Sources consulted** (each will flow into the design doc's
References section):
- <source-label> — <title> — <URL> — accessed <YYYY-MM-DD>
- <source-label> — …
```

When all dimensions are Strong, the justification line reads "All
dimensions Strong — no workaround needed." Silence is not allowed.

### Source citations under Research output

Tighten the existing "Links to relevant documentation (if web search
was used)" line. New rule:

Every external claim that influences the prototype scope or design
must cite a source URL with an `accessed <YYYY-MM-DD>` timestamp.
Citations are collected during Phase 1 and Phase 2 research and
carried into the design doc.

Format for Phase 1 / Phase 2 research output:

```
- <claim> [<source-label>] — <URL> — accessed <YYYY-MM-DD>
```

Where `<source-label>` is a short identifier (e.g., `otel-docs`,
`gdrive-api-ref`, `apache-airflow-2.10-release-notes`) the design
doc uses in inline citations.

**The `accessed` field is required, not optional.** External pages
drift — a URL that documents OTel Python at version 1.25 today may
document version 1.40 in six months, and the claim derived from the
old version may no longer be true. The timestamp tells a future
reader "this URL pointed to X content on this date; if it now
points to different content, the claim may have drifted." This is
the same shape as the OWASP spec migration's `verified_at` /
`verified_against` discipline — a banned-anti-pattern fix applied
proactively here rather than reactively.

The model is expected to use the web_search and web_fetch tools to
verify claims rather than rely on training-data priors for external
specs, library APIs, framework behavior, or version-pinned facts.
The "as of <date>" anti-pattern from the OWASP spec migration
applies here too: prose pretending to be verification ("the OTel
Python SDK is mature as of 2026") is banned. Verification claims
must point at a URL with an `accessed` date.

## Detailed design — Phase 3 / design-doc additions

### `**External:**` label (fifth label in Judgment vs. Observation)

Add `**External:**` to the existing four-label set
(`**Cliff edge:**`, `**Not observed:**`,
`**Prescribed (not validated):**`, plus the default unlabeled
observation-with-evidence). The new label marks claims derived from
external sources — documentation, vendor specs, RFCs, third-party
blogs — rather than from prototype observation or model judgment.

Rule shape (parallel to Rule 3 — Cliff-edge):

**Rule 4: External-source claims are labeled and cited.**

When the doc says "X behaves this way" / "Y supports Z" / "the
specification defines W" and the claim's source is external
documentation (not the prototype), label it `**External:**` and
include an inline citation pointing to a `<source-label>` in the
`## References` section:

```
**External:** The OAuth 2.0 device-flow grant requires the
authorization server to poll the token endpoint at the interval
specified in the `interval` field of the device authorization
response [oauth-rfc8628].
```

The label tells the reader "this claim came from a document, not
from running code." The citation gives the reader the source. The
`## References` section gives the full URL with the `accessed`
date.

If a claim is *both* observed in the prototype *and* documented
externally, the prototype observation takes precedence — cite the
prototype file. External citations are for claims the prototype did
not validate.

**Why this matters.** Design docs accumulate reader trust. Without
the External label, claims from documentation are indistinguishable
from claims from prototype observation — and documentation can be
wrong (out-of-date, ambiguous, or specifying behavior the actual
library doesn't implement). The label tells the implementer "verify
this against the actual library at implementation time" in a way
"see the docs" never does.

#### Good examples

> **External:** Apache Airflow's `apache-airflow-providers-google`
> package version 10.x documents service-account authentication via
> the `key_path` URI parameter [airflow-google-provider-docs].

> **External:** The OpenTelemetry semantic conventions specify that
> HTTP server spans should set `http.request.method` (not the older
> `http.method` attribute, which was deprecated in OTel semconv
> 1.20) [otel-semconv-http].

#### Bad examples

Bad (claim from external docs but no label or citation):
> The provider package supports service-account authentication via
> `key_path` URI parameter.

Bad (External label without a citation):
> **External:** OAuth device flow requires interval-based polling.

Bad (External label on something the prototype actually validated):
> **External:** Connection URI uses `key_path=` (validated in
> `prototypes/foo/docker-compose.yml`).

The third bad case is more subtle: the prototype validated this, so
the citation should be the prototype file, not an External label.
The External label is for the residual class — claims the prototype
didn't validate but documentation supports.

### `## References` section (new, at end of design doc)

A flat list of every external source cited in the doc. Section
template:

```markdown
## References

External sources cited throughout this document. Sources are listed
in alphabetical order by label.

- `<source-label>` — <title> — <URL> — accessed <YYYY-MM-DD>
- `<source-label>` — <title> — <URL> — accessed <YYYY-MM-DD>
```

Examples:

```
- `airflow-google-provider-docs` — Google Cloud Operators —
  https://airflow.apache.org/docs/apache-airflow-providers-google/stable/operators/cloud/index.html
  — accessed 2026-05-14
- `oauth-rfc8628` — OAuth 2.0 Device Authorization Grant —
  https://datatracker.ietf.org/doc/html/rfc8628 — accessed 2026-05-14
- `otel-semconv-http` — Semantic Conventions for HTTP Spans —
  https://opentelemetry.io/docs/specs/semconv/http/http-spans/ —
  accessed 2026-05-14
```

The `accessed` field is required (per the Phase 1 / Phase 2 citation
discipline above). It carries the same role as `verified_at` /
`verified_against` in the OWASP spec data files: a structural
record that the verification work was done at a specific time, so a
future reader can challenge it.

If no external sources were cited, the section reads:

```markdown
## References

None — all design-doc claims are grounded in prototype observation,
user decisions during Phase 1, or labeled as **Not observed** /
**Prescribed (not validated)** per Judgment vs. Observation.
```

(Silence-not-allowed rule.)

### Design-doc-template.md updates

Two new subsections under `## Tooling`, parallel to "Security
Tooling". The template fields are fixed so downstream skills parse
them reliably; **the field values come from the Phase 2 research
output, not from a default-fills list in the template**.

```markdown
### Telemetry
Validated during prototype build. See `references/phase-2-prototype.md`
§ "Telemetry Instrumentation Validation" for the responsibility +
signals + research protocol.

- **Instrumentation SDK**: <tool + version from Phase 2 research>
  or "Not applicable — <one-sentence reason>"
- **Exporter**: <tool + version, or "built into SDK">  or "N/A"
- **Signals captured**: <e.g., "traces only", "traces + custom
  metrics">
- **Demonstrator (prototype-time)**: <what was used; how data was
  viewed>
- **Verification**: <test file path or README section reference>
- **Production target (proposed)**: <backend; label
  **Prescribed (not validated)** if not actually exported to
  during prototype>
- **Sources consulted**: <flows into `## References`>
- **Notes**: <any ecosystem maturity caveats>

### Performance Measurement
Validated during prototype build. See `references/phase-2-prototype.md`
§ "Performance Measurement Validation" for the responsibility +
signals + research protocol.

- **Measurement category**: <UI rendering / backend latency /
  batch timing / multiple / N/A>
- **Library or API**: <from Phase 2 research> or "N/A"
- **Demonstrator (prototype-time)**: <what was used; how data was
  viewed>
- **Verification**: <test file path or README section reference>
- **Baseline measurement(s)**: <concrete numbers>
- **Overlap with telemetry**: <yes — cites <shared-artifact> | no>
- **Sources consulted**: <flows into `## References`>
- **Notes**: <any surprises>
```

The template's meta-commentary at the top of the file is updated to
enumerate five labels (Cliff edge / Not observed / Prescribed (not
validated) / External / default unlabeled observation-with-evidence)
and to note that field *values* in the new subsections come from
Phase 2 research output. The template doesn't pin specific tools.

A new `## References` section is added at the end:

```markdown
## References

External sources cited throughout this document. Sources are listed
in alphabetical order by label.

- `<source-label>` — <title> — <URL> — accessed <YYYY-MM-DD>

(If no external sources were cited, render the explicit "None —
all design-doc claims are grounded in prototype observation, ..."
form per the silence-not-allowed rule.)
```

## Order of operations

1. ✅ Plan landed in memory repo (this file)
2. Draft Phase 2 telemetry subsection (largest single piece;
   includes responsibility + signals + research protocol)
3. Draft Phase 2 performance subsection (parallel structure)
4. Draft Phase 1 observability-tech-selection step (parallel
   structure; six-pair research protocol)
5. Draft Phase 1 source-citation rule with `accessed <YYYY-MM-DD>`
   discipline
6. Draft Phase 3 External-label rule + References section guidance
7. Update design-doc template (Telemetry + Performance + References)
8. Update SKILL.md (Phase step lists, Quick Reference, Principles)
9. P05 trial against airflow-gdrive-ingestion (or new feature) to
   surface failure modes
10. Distill principles into `LEARNINGS.md`
11. Mark this plan superseded

Each step is its own discussion / approval round per the project
rules ("Discuss before changing"). The plan as a whole is one
proposal; individual file edits are separate approval gates.

## Risks and open questions

- **Risk: Phase 2 becomes very long.** Phase 2 already has Lint /
  Test / Dockerfile / Security; adding Telemetry and Performance
  makes seven distinct toolchain steps. Mitigation: the applicability
  gates fast-exit irrelevant cases (a pure library skips telemetry,
  performance, AND Dockerfile, ending up with Lint + Test + Security
  only). The reference doc gets longer but the per-prototype work
  doesn't.

- **Risk: Phase 1 tech-selection research adds latency.** The
  protocol naturally requires multiple web searches (e.g., 2
  candidates × 3 dimensions = 6 research targets, each potentially
  requiring 2–3 search queries to get current state + verify
  against vendor docs). For an extending feature this drops to
  inheriting the parent's verdicts. The implementation skill's
  runtime-isolation step has comparable search-count overhead
  (multiple CLI flag researches, runtime version verification)
  without issue, so this is acceptable. Confirmed in pre-plan
  discussion.

- **Risk: backend telemetry-vs-performance overlap confuses
  decomposition.** A single OTel span satisfies both subsections;
  the decomposition skill needs to handle "this Tooling field
  references the same artifact as that one" without double-counting.
  Mitigation: explicit "Overlap with telemetry: yes/no" field in
  the Performance subsection; downstream skills read it.

- **Risk: tech-selection bias triggers Phase 1 rework on mature
  projects.** A project already running on a tech with weak
  observability (e.g., a legacy framework) shouldn't have to
  rejustify the tech every time a new feature is added. Mitigation:
  the stronger-form rule only fires on greenfield tech selection.
  Extending features inherit the parent's verdicts; the model still
  records them so the user sees what they're inheriting, but no
  justification is required for the inherited choice.

- **Risk: model researches at runtime but lands on the same defaults
  every time, making the research feel performative.** True for
  some ecosystems where one tool dominates (OTel SDK for Python at
  most points in time). The research protocol is still valuable
  because: (a) the research output records URLs the user can audit,
  (b) when the dominant tool *changes* (alpha→GA, or community
  shifts), the protocol surfaces the change automatically without
  a skill update, (c) the protocol catches non-default cases
  (project already uses vendor SDK X, framework has built-in
  observability Y) that a default-table-with-override pattern would
  miss. Same trade-off as the implementation skill's runtime-
  isolation research — sometimes the model lands on `uv`; sometimes
  it lands on `poetry`; the protocol surfaces which signal made the
  decision, which the table-with-override pattern doesn't.

- **Open question: should the existing Security Tooling ecosystem
  table be rewritten using the same research-protocol pattern?**
  The Phase 2 security tooling section still carries a static
  table (Python → pip-audit, Node → npm audit, etc.). It predates
  the LEARNINGS.md anti-pattern note and the Phase A/B refactor
  that established the research-protocol pattern. The table is
  partially mitigated by the Surface Coverage Check forcing
  function, but the underlying pattern is the same one this
  expansion explicitly avoids. Out of scope for this expansion;
  worth a separate plan once P05 validates the new pattern works
  for telemetry and performance. Tracked as a future-work item.

- **Open question: does telemetry validation apply to the
  prototype's own code or to production?** The prototype
  demonstrates that the instrumentation works in the chosen
  ecosystem; the design doc prescribes what production should
  instrument. The prototype is the proof-of-concept; the design
  doc is the prescription. This is the same shape as the existing
  security tooling validation (Phase 2 proves the tools work; the
  design doc prescribes what production should run). Documented
  explicitly in the new Phase 2 subsection.

- **Open question: P05 will surface whether models actually do the
  research or fake it.** A model could theoretically write
  plausible-sounding verdicts ("OTel Python: Strong — mature SDK")
  without doing the search, with the URLs invented or pointing at
  unrelated pages. The `accessed <YYYY-MM-DD>` discipline is the
  forcing function — a fake URL with no real `accessed` provenance
  can be caught at user review. P05 should specifically check that
  cited URLs resolve to relevant content. If models fake citations
  systematically, the fix is a validator step (the same shape as
  the OWASP spec migration's structural fix).

## Acceptance criteria (P05 trial)

The P05 trial regenerates the airflow-gdrive-ingestion design doc
with the expanded planning skill. Acceptance:

- Phase 1 proposal includes a tech-selection observability check
  table with verdicts per candidate × dimension, each backed by
  cited URLs with `accessed <YYYY-MM-DD>` timestamps. URLs resolve
  to relevant content.
- Phase 2 STOP report includes telemetry validation outcome
  (either applicability gate fired with reason, or instrumentation
  worked with the demonstrator named) AND performance validation
  outcome (same shape). Both name the tools chosen and the URLs
  consulted.
- Generated design doc has Telemetry and Performance subsections
  in `## Tooling`, each populated with the validated artifact
  details from research output or an explicit Not applicable.
  Field values are concrete (not "TBD" or template-leftover).
- At least one `**External:**` label appears in the design doc
  (airflow-gdrive-ingestion's existing claims about apache-airflow,
  google-provider, etc. should have external sources behind them).
- `## References` section exists at the end with at least the
  observability sources from Phase 1 / Phase 2 research and any
  external claims cited inline. Each entry has `accessed
  <YYYY-MM-DD>`.
- Existing four-label discipline (Cliff edge / Not observed /
  Prescribed / observation-with-evidence) is preserved — no
  regressions.
- No static ecosystem-to-tool tables introduced in any of the new
  reference doc content. The skill's only remaining static tooling
  table is the pre-existing security tooling table, and it's
  unchanged.

If P05 surfaces failure modes (the model picks weak-observability
tech without justifying, the prototype skips telemetry validation
silently, External-label gets confused with Cliff-edge or vice
versa, citations are fake or stale, models default to a tool
without doing the research), each gets a same-day fix in the
planning skill before P06, following the P01–P03 cadence.

---

## Why the format mirrors the asvs-5-migration plan

This plan follows the same shape as `asvs-5-migration-plan-2026-04-30.md`:
a "Why this exists" + "What's changing" + per-file change table +
"Order of operations" + "Risks and open questions" structure. Plan
docs in this repo are persistent context for future sessions;
following the established format means a session-limit cutoff
doesn't lose the thread.
