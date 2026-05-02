# R02 — Roadmap Skill: OWASP Spec Migration Re-validation

**Date**: 2026-05-01
**Skill**: prototype-driven-roadmap
**Target**: airflow-gdrive-ingestion (existing design doc, post-P05 with
Project Setup component already present)
**Result**: ✅ Clean sweep — validates the 2026-04-30 OWASP spec migration
end-to-end

## What was tested

Re-running the rebuilt roadmap skill against the airflow-gdrive-ingestion
design doc, with the cached pre-migration output cleared. The rebuilt
skill ships ASVS 5.0.0 + MASVS 2.1.0 spec data files, the version-baked
ID format, runtime version cross-checks, and the `verified_at` /
`verified_against` provenance fields that landed in the 2026-04-30
migration (R02-prep).

This run is the first project trial against the rebuilt skill. The
original R02 (2026-04-27, with markdown / ASVS 4.0.3 output format) was
rendered invalid by the migration; its placement and parity fixes had to
survive the rebuild.

## Acceptance bar

| Criterion | Result |
|---|---|
| `components.json` and `roadmap.json` written | ✅ |
| ASVS IDs converted to `v5.0.0-X.Y.Z` form across both files | ✅ — every ID matches the version-baked regex; no 4.0.3-form `V<n>.<n>.<n>` remains |
| No `owasp_category_label` field anywhere | ✅ — field absent from all security scenarios |
| Validator exits 0 with the new "Categories cited (ASVS 5.0.0):" footer | ✅ — confirmed by user run |
| R01 placement fix survives | ✅ — drive-downloader owns mkstemp/temp-file (`v5.0.0-5.3.1`); MinIO uploader owns at-rest encryption (`v5.0.0-14.2.1`); RabbitMQ publisher owns AMQP TLS (`v5.0.0-12.3.1`); no consumer-side misplacement recurs |
| Existing structural rules (Performed-by, ID-set parity, depends_on parity) fire correctly | ✅ |

## Structural verification

**Performed-by field present on every security scenario**: 10/10 scenarios
across the five components carry the `performed_by` slug; every value
matches the slug of the component whose file the scenario lives in.

**ID-set parity (registry ↔ scenarios)** — exact match per component:

| Component | Registry IDs | Scenario IDs |
|---|---|---|
| project-setup | 13.3.1, 15.2.1 | 13.3.1, 15.2.1 |
| drive-downloader | 12.2.1, 13.3.1, 5.3.1 | 12.2.1, 13.3.1, 5.3.1 |
| sqlite-parser | 1.5.3, 2.2.2, 5.2.4 | 1.5.3, 2.2.2, 5.2.4 |
| minio-uploader | 12.2.1, 13.2.1, 14.2.1 | 12.2.1, 13.2.1, 14.2.1 |
| rabbitmq-publisher | 12.3.1, 13.3.1, 14.2.1 | 12.3.1, 13.3.1, 14.2.1 |

**`depends_on` ↔ `dependencies` parity**: registry slug sets match prose
entries across all five components.

**Component ordering**: identical between `components.json` and
`roadmap.json` — `project-setup` → `drive-downloader` → `sqlite-parser` →
`minio-uploader` → `rabbitmq-publisher`. Roots-first; project-setup is the
common dependency.

**Silence-not-allowed**: empty lists carry explicit `*_reason` prose
(e.g., `project-setup.dependencies_reason`: "project-setup has no
code-level dependencies on other components in this feature; it is the
operational precondition within which all other components execute").

## Notable: implicit Project Setup component validation

The design doc that drove this run includes a Project Setup component
(landed via P05). This run therefore exercises the roadmap skill's
handling of project-setup as a registered first component — `depends_on:
[]`, `owasp_categories` drawn from V13/V14/V15, all downstream components
listing `project-setup` in their `depends_on`. This satisfies the
structural part of R03's acceptance bar; a dedicated R03 trial is no
longer strictly required unless something in project-setup-specific
scenarios surfaces a failure mode that didn't appear here.

## Failure modes surfaced

None. This is the first roadmap-skill trial since R01 to surface no new
failure modes. The 2026-04-30 migration's structural fixes (single source
of truth for labels, version-baked IDs, runtime version cross-checks,
verification provenance) hold against a real feature run.

## Skill changes

None required. R02 is a validation run.

## Implications

- R02 re-run completes the queued work from the README Next Steps.
- The `decomposition-roadmap-refactor-plan-2026-04-26.md` plan-doc update
  (§4.4, §5.1, §7, §9.1 — markdown/YAML references → JSON) is now the top
  of the queue.
- After the plan-doc update lands, the decomposition-roadmap refactor work
  can resume.
- R03 as a separate trial is no longer strictly required given Project
  Setup was implicitly exercised here.
