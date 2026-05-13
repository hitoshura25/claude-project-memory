# R04 — Criticality and verification fields; cliff-edge coverage check

**Date:** 2026-05-11
**Target:** prototype-driven-roadmap skill
**Project context:** airflow-gdrive-ingestion (regenerated; clean sweep)
**Tags:** `criticality-tier`, `verification-form`, `cliff-edge-coverage-validator`,
`schema-extension`, `structural-signal-from-prose-label`
**Sister trials in arc:** P04 (cliff-edge labeling discipline upstream),
D03 (no-prototype-references + task-level cliff-edge coverage),
PC01 (task-type preambles + criticality grouping)
**Result:** Schema extended with two required fields; cliff-edge coverage
check added; airflow roadmap regenerated with 4 cliff-edge scenarios
covering all 4 design-doc labels

---

## Why this iteration

P04 introduced the `**Cliff edge:**` label in the design doc. The
roadmap skill needs to (a) recognize the label and produce scenarios
tagged as `cliff_edge`, (b) enforce that every labeled cliff edge
gets a covering scenario, and (c) record a *verification form* on
every scenario so downstream skills can frame test prompts
consistently.

Before R04, scenarios carried `evidence_kind: "prototype" | "prescribed"`
— two of three criticality tiers were already structurally present.
What was missing was the third tier (`cliff_edge`) and the
verification-form hint. R04 adds both as required fields, plus the
coverage check that completes the structural chain from P04's labels.

## What changed

### Schema — `scripts/roadmap_schema.py`

Two new fields added to both `FunctionalScenario` and `SecurityScenario`,
each backed by a Literal type:

- **`criticality: Literal["cliff_edge", "behavioral", "prescribed"]`**.
  `cliff_edge` is sourced from a `**Cliff edge:**` label in the design
  doc; `behavioral` is the default for prototype-evidence scenarios
  that aren't cliff edges; `prescribed` is a design-doc prescription
  not present in the prototype. The field is independent of
  `evidence_kind`: a prototype-evidence scenario may be cliff-edge
  (boundary tested both ways) or behavioral (proven path only); a
  prescribed scenario typically carries `"prescribed"` but may carry
  `"cliff_edge"` if the prescription describes a boundary with a
  specific failure mode.

- **`verification: Literal["tool_invocation", "unit_test",
  "integration_test", "static_assertion"]`**. A hint to the
  test-writing executor about what *form* the test takes. Not a
  strict contract; some scenarios have two reasonable forms (e.g.,
  "use mkstemp" can be `unit_test` or `static_assertion`). The
  field records the form the model selected so the prompt-composition
  skill (PC01) can frame the prompt consistently.

Both fields are required. The schema does not infer defaults from
`evidence_kind` — the model must write each field explicitly. This
matches the existing discipline (`evidence_kind` is required;
`verified_by` is required; no silent defaults).

The schema's top-of-file invariants docstring gained two new entries
documenting criticality and verification rules.

### Validator — `scripts/validate_roadmap.py`

Three additions:

- **`CLIFF_EDGE_LABEL_RE = re.compile(r"\*\*Cliff edge:\*\*")`** — a
  case-sensitive regex matching the `**Cliff edge:**` label in the
  design doc's markdown. Case-sensitivity is intentional; P04
  prescribes exactly this casing.

- **`count_cliff_edge_labels(design_doc_path)`** — reads the design
  doc and returns the number of label occurrences. Used by the
  cross-file check.

- **`count_cliff_edge_scenarios(roadmap)`** — counts scenarios across
  the entire roadmap with `criticality == "cliff_edge"`. Both
  functional and security scenarios contribute; the count is global,
  not per-component.

The cross-file `check_cross_file()` function gained a new check after
the existing path-resolution check: the number of labels in the
design doc must be ≤ the number of cliff-edge scenarios in the
roadmap. Lower-bound coverage; multiple scenarios per labeled cliff
edge are allowed (e.g., one per failure mode), single scenarios
covering multiple labels are not (the lower bound enforces 1:N or
1:1, not N:1).

The validator's failure message names what's missing and where to fix
it — adding the scenario or downgrading the design-doc label upstream.

The validator's top-of-file rule list grew from item 28 to item 31 to
incorporate the new fields and the coverage check.

### Reference docs

- **`references/phase-2-generation.md`** — added writing guidance for
  both fields. The criticality subsection documents the three tiers
  with mapping rules: cliff_edge requires a label match, behavioral
  is default for prototype-evidence, prescribed pairs with
  prescribed evidence kind. The verification subsection documents
  the four values with mapping to `verified_by` formats (pytest
  path → unit/integration test, shell command → tool_invocation,
  grep/regex check → static_assertion). The "Common mistakes"
  subsection gained two new entries on cliff-edge under-coverage and
  mismatched verification/verified_by.

- **`references/roadmap-json-format.md`** — added `criticality` and
  `verification` rows to the per-scenario fields table. Added two
  new full sections (`## Criticality`, `## Verification`) analogous
  to the existing `## Evidence kind` section. The validation-rules
  list grew from 28 to 31 items. The "Anti-patterns" section gained
  three new entries (unstructured criticality, cliff-edge under-coverage,
  mismatched verification/verified_by).

JSON examples in both reference docs were updated to show the new
fields. A new cliff-edge example (`airflow-init-single-line-bash`)
was added to phase-2-generation.md to demonstrate the typical
shape.

## Regeneration against airflow-gdrive-ingestion

Roadmap regenerated end-to-end after the skill updates landed. Phase
3 validation ran the new cliff-edge coverage check; it passed.

**Cliff-edge coverage:**

| Design doc label | Roadmap scenario | Component | Verification |
|---|---|---|---|
| Service account URI requires key_path + scope | `key-path-and-scope-required` | drive-downloader | integration_test |
| `airflow-init` single-line bash | `airflow-init-single-line-bash` | project-setup | tool_invocation |
| `pip install` as airflow user | `dockerfile-runs-as-airflow-user` | project-setup | tool_invocation |
| `tempfile.mkstemp()` over `/tmp/` | `tempfile-not-hardcoded-tmp` | drive-downloader | tool_invocation |

4 labels → 4 cliff-edge scenarios. Coverage check passed.

**Other criticality and verification distributions:**

- ~24 behavioral scenarios across 5 components. Verification mostly
  `unit_test` (functional scenarios verified by pytest with mocks)
  with `integration_test` for end-to-end scenarios (Drive download
  with real credentials; MinIO upload with real service; RabbitMQ
  publish with real broker).
- ~12 prescribed scenarios — mostly security (TLS in production,
  credentials not hardcoded, scope restriction) with `tool_invocation`
  (gitleaks, bandit) or `static_assertion` (grep for forbidden
  patterns) verification.

The criticality independence-from-evidence_kind property was exercised:
the `health-message-contains-no-raw-values` security scenario has
`evidence_kind: prototype` (prototype validated this) and
`criticality: behavioral` (proven path, not a tested boundary).
The `tempfile-not-hardcoded-tmp` scenario has `evidence_kind:
prototype` and `criticality: cliff_edge` (boundary tested both ways
via the bandit B108 failure mode).

## Two content notes worth recording for future trials

The regeneration produced two **mixed-criticality scenarios** worth
flagging:

- `minio-credentials-not-hardcoded` and `rabbitmq-credentials-not-hardcoded`
  each blend a validated check (gitleaks running clean against the
  prototype) with a production prescription ("should use short-lived
  STS credentials" / "should use a dedicated vhost"). The scenario's
  `criticality: prescribed` is justified by the production-prescription
  clause; the `verified_by` cites the validated gitleaks check. The
  combination reads coherently in the prompt-composition output
  (PC01) — the prescription flows into framing, the gitleaks check
  flows into the test form. Not a blocker, but a candidate for future
  content cleanup: splitting into two scenarios (one behavioral for
  the gitleaks check, one prescribed for the production discipline)
  would let each one carry a single, clean tier.

Neither blocks downstream consumption; both are documented here for
future iterations to consider.

## Failure modes addressed

The pre-arc decomposition skill could not structurally distinguish
"this scenario is the strongest contract the component carries" from
"this scenario is a normal proven path." The pre-arc prompt-composition
skill rendered every scenario uniformly. Without criticality, every
behavior in an executor prompt reads as equally weighted, and the
cliff-edge boundaries that *should* be non-negotiable get treated
the same as ordinary expectations.

R04's two fields close this gap structurally:

- `criticality` lets downstream skills frame each scenario differently
  (D03 uses it for citation-coverage enforcement; PC01 uses it for
  prompt subsection grouping and instruction framing).
- `verification` lets PC01 hint at the test form the executor should
  produce.

The cliff-edge coverage check makes the chain robust: a roadmap that
silently drops a cliff edge (by marking it behavioral, by failing to
produce a scenario for a labeled boundary) fails validation. The fix
is always upstream (add the scenario; or, if the design doc mis-labeled
something, downgrade the label upstream and regenerate).

## Key findings

1. **`evidence_kind` and `criticality` are orthogonal**. The
   pre-arc roadmap had `evidence_kind` as a single signal blending
   "prototype-validated" and "production-prescribed" with implicit
   "this is the canonical way to do it." Splitting criticality out
   as its own field made the orthogonality explicit and exposed
   useful cases (prototype-evidence + cliff-edge for tested
   boundaries; prescribed + cliff-edge for prescribed boundaries
   with documented failure modes). Independent enums let the schema
   carry richer reality without conditional fields.

2. **Coverage checks should match the upstream signal mechanically**.
   The cliff-edge coverage check counts `**Cliff edge:**` labels via
   regex in the design doc and `criticality == "cliff_edge"`
   scenarios in the roadmap. Both counts are mechanical; neither
   relies on the model to "understand" semantic equivalence. This
   was a deliberate choice — the check is robust to design-doc
   prose changes that don't change the label count, and to roadmap
   regenerations that don't change the scenario count.

3. **Verification as hint, not strict contract**. The verification
   field deliberately avoids consistency enforcement against
   `verified_by`. Some scenarios genuinely have two reasonable test
   forms; some `verified_by` paths name pytest tests that under the
   hood run tool invocations. The field's job is to give the
   prompt-composition skill a consistent framing signal; reviewers
   ensure deeper consistency. This is the same "hint, not contract"
   pattern used for `evidence_kind` in R02-prep.

4. **The schema-driven validator stays small and structural**. R04
   added two enum fields and one cross-file count check — about 50
   lines of Python total. The skill's reference docs grew more
   (writing guidance, examples, format docs, anti-patterns) but the
   load-bearing validation logic is still small and easy to reason
   about. Schemas should carry only what they can enforce; the rest
   lives as model guidance.

5. **The upstream-label discipline produced lower-friction
   regeneration than direct prose changes would have**. The airflow
   roadmap regenerated cleanly on the first try after the skill
   updates landed, with the model correctly tagging cliff-edge
   scenarios based on the design doc's labels. No iteration needed.
   This validates the "label as structural signal" approach: the
   model reads the label and acts on it, rather than re-inferring
   criticality from prose nuance each run.

## Related plan documents

- `session-status-2026-05-11-cliff-edges-and-two-prompt-split.md` —
  arc-level plan
- P04 trial record — upstream label discipline this skill consumes

## Skill change summary

- `scripts/roadmap_schema.py`: `Criticality` + `Verification`
  Literal types; required fields on `FunctionalScenario` and
  `SecurityScenario`; updated invariants docstring
- `scripts/validate_roadmap.py`: `CLIFF_EDGE_LABEL_RE` regex;
  `count_cliff_edge_labels` + `count_cliff_edge_scenarios`
  helpers; cliff-edge coverage check in `check_cross_file()`;
  updated rule-list docstring (28 → 31 rules)
- `references/phase-2-generation.md`: writing guidance for both
  fields; cliff-edge example; two new common-mistakes entries
- `references/roadmap-json-format.md`: per-scenario fields table
  rows; full `## Criticality` and `## Verification` sections;
  validation-rules list 28 → 31; three new anti-patterns
