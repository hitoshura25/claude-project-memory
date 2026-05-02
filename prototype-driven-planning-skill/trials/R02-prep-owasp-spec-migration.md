# R02-prep: OWASP Spec Migration & Label Canonicalization

**Date:** 2026-04-30
**Skill:** prototype-driven-roadmap
**Type:** skill rebuild (no project trial run)
**Trigger:** review of R01 output and surrounding skill artifacts

> Note: this is not a trial run against a project. It is a skill-
> level rebuild prompted by review findings. R02 (the next real
> trial) is queued behind this work; the R02 record will reuse this
> file's setup as preconditions.

---

## What was found

Review of R01 artifacts and surrounding skill reference files
surfaced two distinct issues:

1. **Stale spec-version pin.** The skill's reference docs were
   pinned to "ASVS 4.0.3 (last major release as of 2026-04-24)."
   Live verification confirmed ASVS 5.0.0 had been released in May
   2025 — eleven months before the reference doc was authored. The
   "as of" comment was authored without checking the source; nobody
   had ever verified the pin.
2. **Three-way duplicated source of canonical labels.** Category
   labels like "Encoding and Sanitization" (the canonical title of
   ASVS V1) were stored in three places: prose in reference docs,
   the `owasp_category_label` field in roadmap.json security
   scenarios, and (after the migration was planned) dedicated spec
   data files. Three duplicates of one fact across three artifact
   types is a drift surface in three dimensions.

## What was changed

### Architectural changes

| Before | After |
|--------|-------|
| `owasp_category_label` field per security scenario | Field removed; labels derived at runtime from spec data files |
| Hardcoded ASVS regex `^ASVS V\d+\.\d+\.\d+$` (4.0.3 form) | Version-agnostic regex `^v\d+\.\d+\.\d+-\d+\.\d+\.\d+$` (5.0+ form); validator runtime check enforces version against pinned spec |
| Reference docs say "ASVS 4.0.3" verbatim | Reference docs speak abstractly; the version pin lives only in `scripts/owasp-asvs.json` |
| "As of <date>" prose claiming verification | `verified_at` and `verified_against` fields in spec data files |
| ASVS 4.0.3 pinned (stale) | ASVS 5.0.0 pinned (current; verified live 2026-04-30) |
| MASVS unpinned (no spec data file) | MASVS 2.1.0 pinned (current; verified live 2026-04-30) |

### Files changed

| File | Change |
|------|--------|
| `scripts/owasp-asvs.json` (new) | Canonical ASVS 5.0.0 data: 17 chapters with titles, `verified_at`, `verified_against`, `id_format_description` |
| `scripts/owasp-masvs.json` (new) | Canonical MASVS 2.1.0 data: 8 control groups including PRIVACY |
| `scripts/components_schema.py` | ASVS regex updated to version-agnostic 5.0 format |
| `scripts/roadmap_schema.py` | Same regex change; `owasp_category_label` field removed from `SecurityScenario` |
| `scripts/validate_roadmap.py` | Loads spec files at runtime; cross-checks version + category prefix; renders Categories Cited footer with canonical titles |
| `references/owasp-asvs-mapping.md` | Rebuilt for 17-chapter 5.0 structure (V1 Encoding/Sanitization → V17 WebRTC) |
| `references/owasp-masvs-mapping.md` | Added MASVS-PRIVACY data flows and privacy-specific concerns table |
| `references/phase-1-extraction.md` | Stripped version mentions; updated ID format guidance |
| `references/phase-2-generation.md` | Removed `owasp_category_label` instructions; new ID format example; added warnings against reintroducing the label field |
| `references/phase-3-validation.md` | Documents validator's spec-loading behavior, runtime cross-checks, summary footer with category titles |
| `references/components-json-format.md` | Format-only/version-agnostic regex doc; ASVS spec-runtime cross-check rules added |
| `references/roadmap-json-format.md` | `owasp_category_label` removed from schema, anti-patterns, and rationale; new anti-patterns for version drift and stale category prefix |
| `SKILL.md` | Quick Reference updated; spec data files explicitly noted as not shipped; new principle on live verification of spec versions |

## Skill principles added/strengthened

Six new learnings landed in `LEARNINGS.md` under "From OWASP spec
migration (Pre-R02 prep, 2026-04-30)":

- **"As of <date>" is not verification, it's prose pretending to be
  verification.** The structural fix is `verified_at` /
  `verified_against` fields.
- **Live search results are the answer, not a footnote.** When the
  live result and training-data prior disagree on a present-day
  fact, the live result wins.
- **One source of truth for category labels, derived at output
  time.** Spec data file is canonical; reference docs reference
  abstractly; `owasp_category_label` field deleted from the schema.
- **Spec data files belong in the skill, not in project artifacts.**
  Schemas describe artifact shape (so they ship); spec data files
  describe external standards (so they stay with the skill).
- **Version-baked IDs catch a class of drift bare IDs cannot.** The
  ASVS 5.0+ format `v5.0.0-1.2.5` makes version mismatch visible at
  the ID level.
- **"Force visibility" applies to verification too, not just
  reasoning.** Same fix-shape as the planning-skill arc: surface the
  silent work into a structured artifact.

## Why this trial record exists

R02 (a real trial against the airflow-gdrive-ingestion design doc
using the rebuilt skill) is queued. The R02 record will inherit this
file's setup work as preconditions — the spec data files, the
schema changes, the reference rebuilds — so the next trial's
findings stay scoped to "did the rebuilt skill behave correctly on
real input?" without re-litigating the migration's architectural
choices.

This record is also the answer to "why did the migration happen?"
for any future reviewer asking why ASVS 5.0 was adopted, why
`owasp_category_label` was removed, why spec data lives in the skill
and not the project. Without this record, those choices would read
as arbitrary; with it, they read as responses to specific findings
during R01-era review.

## Validation status

- ✅ Skill files coherent: regex format consistent across schemas
  and reference docs; `owasp_category_label` removed from schema +
  reference docs + format docs in lockstep
- ✅ Migration plan filed at
  `~/claude-project-memory/prototype-driven-planning-skill/asvs-5-migration-plan-2026-04-30.md`
- ⏸ R02 trial pending: regenerate
  `~/health-data-ai-platform/docs/roadmap/airflow-gdrive-ingestion/`
  end-to-end with the rebuilt skill, confirm validator passes with
  the new "Categories cited (ASVS 5.0.0):" footer, then file the
  R02 trial record

## Loose ends

- `decomposition-roadmap-refactor-plan-2026-04-26.md` references the
  pre-migration markdown roadmap output format (`.md` files,
  `components.yml`). Sections §4.4, §5.1, §7, and §9.1 need updates
  to point at `components.json`/`roadmap.json` and the JSON schemas.
  This is captured in the migration plan as step 6 item 31 and is
  separate work from the skill rebuild itself.
