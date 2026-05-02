# ASVS 5.0 Migration Plan

**Status:** in progress, 2026-04-30
**Author:** Claude session 2026-04-30 (this session)

## Why this exists

The roadmap skill was authored this month with a reference doc
(`owasp-asvs-mapping.md`) pinned to ASVS 4.0.3. That pin was never
verified live — it was based on training-data assumptions and stamped
with a misleading "as of 2026-04-24" comment. ASVS 5.0.0 was actually
released May 2025, eleven months before the reference was written.

The skill author (a previous Claude session) saw search results
mentioning 5.0 but rationalized staying on 4.0.3 to "preserve R04
compatibility" — a non-existent compatibility concern, since R04 was
about to be regenerated anyway. Same failure pattern caught again in
this session at the start of step 1; this time live verification was
done and the migration is proceeding.

## What's changing

### Architectural shift (single source of truth)

| Before | After |
|--------|-------|
| `owasp_category_label` field in roadmap.json | Field removed; labels derived at runtime from spec files |
| Category labels embedded in `owasp-asvs-mapping.md` and `owasp-masvs-mapping.md` | Labels live in `scripts/owasp-asvs.json` and `scripts/owasp-masvs.json`; reference docs point at JSON |
| Hardcoded ASVS regex `^ASVS V\d+\.\d+\.\d+$` (4.0.3 form) | Version-agnostic regex `^v\d+\.\d+\.\d+-\d+\.\d+\.\d+$` (5.0+ form); validator cross-checks version against pinned spec |
| Reference docs say "ASVS 4.0.3" verbatim | Reference docs speak abstractly; version pin lives only in the JSON |
| Misleading "as of <date>" verification claims | Explicit `verified_at` and `verified_against` fields in JSON |

### Version pins

- **ASVS:** 4.0.3 → **5.0.0** (May 2025, current)
- **MASVS:** new pin → **2.1.0** (January 2024, current)

### File-by-file changes

| File | Change |
|------|--------|
| `scripts/owasp-asvs.json` (new) | Canonical ASVS 5.0.0 data: 17 chapters with titles |
| `scripts/owasp-masvs.json` (new) | Canonical MASVS 2.1.0 data: 8 control groups including PRIVACY |
| `scripts/components_schema.py` | ASVS regex updated to version-agnostic 5.0 format |
| `scripts/roadmap_schema.py` | Same regex change; `owasp_category_label` field removed |
| `scripts/validate_roadmap.py` | Loads spec files at runtime; cross-checks version + category; renders Categories Cited footer |
| `references/owasp-asvs-mapping.md` | Rebuilt for 17-chapter 5.0 structure (this plan's biggest single piece) |
| `references/owasp-masvs-mapping.md` | Add MASVS-PRIVACY data flows; remove version mentions |
| `references/phase-1-extraction.md` | Strip version mentions; point at JSON |
| `references/phase-2-generation.md` | Strip version mentions; remove `owasp_category_label` instructions |
| `references/phase-3-validation.md` | Document that validator copies needed spec files into project |
| `references/components-json-format.md` | Describe regex format; remove version mentions |
| `references/roadmap-json-format.md` | Remove `owasp_category_label` field; describe regex format |
| `SKILL.md` | Update Quick Reference; strip version mentions |

## Order of operations

1. ✅ Spec files (`owasp-asvs.json`, `owasp-masvs.json`) shipped
2. ✅ Schemas updated (`components_schema.py`, `roadmap_schema.py`)
3. ✅ Validator updated (`validate_roadmap.py`)
4. 🔄 Rebuild `owasp-asvs-mapping.md` for 17-chapter 5.0 structure (this step)
5. Update `owasp-masvs-mapping.md` (add PRIVACY, remove version mentions)
6. Update phase docs and SKILL.md (strip version mentions, point at JSON)
7. Update format docs (strip `owasp_category_label`, describe regex format)
8. File this migration plan (this file — being written before step 4 starts so the plan survives any context boundary)
9. Update LEARNINGS.md with the verify-spec-versions-live discipline
10. Regenerate R04 against the rebuilt skill

## What "step 4" specifically requires

`owasp-asvs-mapping.md` carries data-flow-to-category mapping tables.
Five tables: Inputs, Outputs, Persisted state, Auth surfaces,
Cross-process communication. Each table has columns: kind, implicated
categories, top requirement IDs.

ASVS 5.0 is a **reorganization**, not a renumbering, of 4.0.3:

- V1 was "Architecture, Design, Threat Modeling" → now "Encoding and
  Sanitization"
- V12 was "Files and Resources" → now "Secure Communication"
- V14 was "Configuration" → now "Data Protection"
- File handling moved from V12 (4.0.3) to V5 (5.0)
- Configuration moved from V14 (4.0.3) to V13 (5.0)
- New chapters with no 4.0.3 counterpart: V3 (Web Frontend), V9
  (Self-contained Tokens), V10 (OAuth/OIDC), V15 (Secure Coding &
  Architecture), V16 (Logging & Error Handling), V17 (WebRTC)

The mapping cannot be translated mechanically. Each new chapter
requires reading the actual section structure to decide which data
flows implicate it.

### Section structure verified live (2026-04-30) from
### cheatsheetseries.owasp.org/IndexASVS.html

- **V1 Encoding and Sanitization:** 1.1 Architecture, 1.2 Injection
  Prevention, 1.3 Sanitization, 1.4 Memory/String/Unmanaged Code, 1.5
  Safe Deserialization
- **V2 Validation and Business Logic:** 2.1 Doc, 2.2 Input Validation,
  2.3 Business Logic Security, 2.4 Anti-automation
- **V3 Web Frontend Security:** 3.1 Doc, 3.2 Unintended Content
  Interpretation, 3.3 Cookie Setup, 3.4 Browser Security Headers, 3.5
  Origin Separation, 3.6 External Resource Integrity, 3.7 Other
- **V4 API and Web Service:** 4.1 Generic Web Service, 4.2 HTTP
  Message Structure, 4.3 GraphQL, 4.4 WebSocket
- **V5 File Handling:** 5.1 Doc, 5.2 File Upload and Content, 5.3 File
  Storage, 5.4 File Download
- **V6 Authentication:** 6.1 Doc, 6.2 Password Security, 6.3 General
  Auth, 6.4 Auth Lifecycle, 6.5 MFA, 6.6 Out-of-band, 6.7 Crypto auth,
  6.8 IdP
- **V7 Session Management:** 7.1–7.6
- **V8 Authorization:** 8.1–8.4
- **V9 Self-contained Tokens:** 9.1 Token source/integrity, 9.2 Token
  content
- **V10 OAuth and OIDC:** 10.1–10.7 sections
- **V11 Cryptography:** 11.1–11.7 sections
- **V12 Secure Communication:** 12.1 General TLS, 12.2 HTTPS External,
  12.3 Service-to-Service
- **V13 Configuration:** 13.1 Doc, 13.2 Backend Comm Config, 13.3
  Secret Management, 13.4 Unintended Info Leakage
- **V14 Data Protection:** 14.1 Doc, 14.2 General Data Protection,
  14.3 Client-side
- **V15 Secure Coding and Architecture:** 15.1 Doc, 15.2
  Architecture/Dependencies, 15.3 Defensive Coding, 15.4 Safe
  Concurrency
- **V16 Security Logging and Error Handling:** 16.1 Doc, 16.2 General
  Logging, 16.3 Security Events, 16.4 Log Protection, 16.5 Error
  Handling
- **V17 WebRTC:** 17.1 TURN, 17.2 Media, 17.3 Signaling

This list is the working data for step 4. The new mapping doc puts
these into the data-flow tables based on which kinds of inputs,
outputs, persisted state, auth, and cross-process flows each chapter
covers.

## R04 implications

R04 already passed validation against the 4.0.3-pinned skill. With
the 5.0 migration, R04's IDs (`ASVS V5.1.3`, `V14.1.1`, etc.) are
invalid against the new skill (wrong format AND wrong chapter
numbering). R04 will be regenerated as the final step, producing
`v5.0.0-X.Y.Z`-form IDs against the new chapter structure.

The R04 trial record will document both improvements together: the
JSON migration (the larger architectural change) and the spec-version
canonicalization (this plan).
