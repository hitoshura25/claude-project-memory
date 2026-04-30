# Plan — Migrate Roadmap Skill from Markdown + YAML to Two-File JSON Output

> **Status:** Proposal. Not yet implemented. Pick up from this file in a
> fresh session if needed. Re-read the current state pointers in §1
> before touching any skill file.
>
> **Created:** 2026-04-29 (after P05 + R03 confirmed the project-setup
> component lands cleanly under the existing markdown-based skill, and
> the cross-skill code sharing question for the decomposition refactor
> was resolved by changing the upstream artifact format rather than
> sharing a parser).
>
> **Sequencing:** This work goes upstream of the decomposition refactor
> (`decomposition-roadmap-refactor-plan-2026-04-26.md`). When this plan
> lands, the decomposition refactor's §4.4, §5.1, and §7 simplify
> materially — no markdown parsing, no shared-parser question, no
> cross-skill imports.
>
> **Trial code:** R04 (roadmap skill, fourth iteration trial — first
> run after this plan lands).

---

## 1. Where to read in (do this first)

A fresh session must load these before proposing edits.

**Memory repo (always loaded at session start):**

- `~/claude-project-memory/prototype-driven-planning-skill/README.md`
- `~/claude-project-memory/prototype-driven-planning-skill/LEARNINGS.md`
- `~/claude-project-memory/prototype-driven-planning-skill/trials/_SUMMARY.md`

**Memory repo (on demand for this work):**

- `~/claude-project-memory/prototype-driven-planning-skill/trials/R01-roadmap-id-parity-and-actor-misplacement.md`
  (the trial that earned the ID-parity, Performed-by, and Judgment-vs-Observation
  invariants; this migration must preserve them)
- `~/claude-project-memory/prototype-driven-planning-skill/planning-project-setup-component-plan-2026-04-27.md`
  (the most recent landed work — Project Setup component — which this
  migration must continue to support without special-casing)
- `~/claude-project-memory/prototype-driven-planning-skill/decomposition-roadmap-refactor-plan-2026-04-26.md`
  (the downstream plan this work clears the path for; §4.4, §5.1, §7,
  and §9.1 of that plan get simpler after this lands)

**Roadmap skill — full file reads required:**

- `~/claude-devtools/skills/prototype-driven-roadmap/SKILL.md`
- `~/claude-devtools/skills/prototype-driven-roadmap/references/phase-1-extraction.md`
- `~/claude-devtools/skills/prototype-driven-roadmap/references/phase-2-generation.md`
- `~/claude-devtools/skills/prototype-driven-roadmap/references/phase-3-validation.md`
- `~/claude-devtools/skills/prototype-driven-roadmap/references/components-yml-format.md`
- `~/claude-devtools/skills/prototype-driven-roadmap/references/roadmap-item-template.md`
- `~/claude-devtools/skills/prototype-driven-roadmap/scripts/validate_roadmap.py`

**Decomposition skill — read for the shipping pattern this migration mirrors:**

- `~/claude-devtools/skills/prototype-driven-task-decomposition/SKILL.md`
  (specifically Phase 3 step 2: "Copy `task_schema.py` from this skill's
  `scripts/task_schema.py` to `tasks/<feature-name>/task_schema.py`.")
- `~/claude-devtools/skills/prototype-driven-task-decomposition/scripts/task_schema.py`

**Reference output — the markdown roadmap from R03 that this migration replaces:**

- `~/health-data-ai-platform/docs/roadmap/airflow-gdrive-ingestion/components.yml`
- `~/health-data-ai-platform/docs/roadmap/airflow-gdrive-ingestion/project-setup.md`
- (and the four runtime component files alongside)

The user has confirmed the existing roadmap output will be deleted and
regenerated from scratch under the new skill. No data-migration step is
needed.

---

## 2. The decisions this plan locks in

Settled before writing this plan, in conversation:

1. **Output format: JSON, not markdown.** The roadmap is a machine-consumed
   artifact at the middle of a skill chain. Human review at Phase 3
   reads JSON directly; rendered markdown is not produced.
2. **Two files, not one.** `components.json` (registry) and `roadmap.json`
   (per-component content). Component slug is the foreign key joining
   them; no other duplication.
3. **Schemas ship into the project.** `components_schema.py` and
   `roadmap_schema.py` are copied from the skill's `scripts/` into the
   project's `docs/roadmap/<feature>/` at Phase 3, mirroring how
   `task_schema.py` ships from the decomposition skill.
4. **Validator stays in the skill.** `validate_roadmap.py` is a Phase 3
   tool the skill runs, not a project artifact. It imports the schemas
   from the project's shipped copies (validates "the schema as
   shipped," not the master).
5. **Component dependency order = array order.** No explicit `order` field;
   the validator enforces topological order.
6. **Empty `out_of_scope` requires `out_of_scope_reason`.** Mutually
   exclusive: either non-empty list, or empty list with reason. Same
   pattern for empty `dependencies` in `roadmap.json`.
7. **Each file carries its own `schema_version`.** Independent evolution.
8. **No partial-state JSON, no phase field, no discriminated unions.**
   `components.json` is complete after Phase 1; `roadmap.json` is
   complete after Phase 2; each is independently validatable.

These are not re-litigated below. The plan implements them.

---

## 3. The trial-earned invariants this migration must preserve

Every invariant the skill has earned through R01–R03 + P01–P05 maps to
either a Pydantic field validator, a Pydantic model validator, or a
cross-file check in `validate_roadmap.py`. Listed here so the
implementation pass can verify each is covered.

| Invariant | Source trial | Today's enforcement | After migration |
|---|---|---|---|
| Slug format `^[a-z][a-z0-9-]*[a-z0-9]$` | (initial) | regex in validator | Pydantic field validator on `Component.slug` |
| Slug uniqueness within registry | (initial) | validator pass | Pydantic top-level validator on `Components.components` |
| `depends_on` references registered slugs | (initial) | validator pass | Pydantic top-level validator |
| No self-references in `depends_on` | (initial) | validator pass | Pydantic field validator |
| No cycles in `depends_on` graph | (initial) | DFS in validator script | Same DFS, in `validate_roadmap.py` (cross-component) |
| Topological array order | new for migration | n/a | Pydantic top-level validator on `Components.components` |
| OWASP ID format `ASVS V<n>.<n>.<n>` or `MASVS-<CAT>-<n>` | (initial) | regex in validator | Pydantic field validator |
| ID-set parity (registry ↔ scenarios) | R01 | cross-file check in validator | Cross-file check in `validate_roadmap.py` |
| `Performed by` matches own component slug | R01 | cross-file check | Pydantic per-component validator on `Component.security_scenarios` |
| `Performed by` is a registered slug | R01 | cross-file check | Cross-file check in `validate_roadmap.py` |
| Functional scenarios have Given/When/Then/Verified-by | (initial) | markdown structural check | Pydantic schema (each field required, non-empty) |
| Security scenarios have Given/When/Then/Verified-by/Performed-by | R01 | markdown structural check | Pydantic schema |
| Verified-by non-empty / not "TBD" | (initial) | markdown structural check | Pydantic field validator (rejects empty, TBD, `<unknown>`) |
| Out-of-Scope completeness (none-with-reason) | (initial) | markdown structural check | Pydantic top-level validator on `Component` (mutual exclusion of `out_of_scope` and `out_of_scope_reason`) |
| Dependencies completeness (none-with-reason) | (initial) | markdown structural check | Pydantic top-level validator on `Component` |
| Prototype evidence non-empty | (initial) | markdown structural check | Pydantic field validator (`min_length=1`) |
| Judgment vs Observation labeling | planning skill arc | prose convention ("Prescribed (not validated)") | `evidence_kind: "prototype" \| "prescribed"` field on every scenario, Pydantic-validated enum |
| Project Setup as registered component | P05 / R03 | already in components.yml | unchanged; `components.json` carries it as a regular slug |

If any of these can't be cleanly expressed in the new model when
implementation begins, **stop and flag** — the goal is preservation, not
silent loss.

---

## 4. Final shape on disk

### 4.1 In the project after a successful skill run

```
~/<project>/docs/roadmap/<feature>/
├── components.json           # Phase 1 output (registry)
├── components_schema.py      # Pydantic schema for components.json (copied from skill)
├── roadmap.json              # Phase 2 output (per-component content)
└── roadmap_schema.py         # Pydantic schema for roadmap.json (copied from skill)
```

No markdown files. No `components.yml`. The four files above are the
complete roadmap output.

### 4.2 In the skill (source of truth)

```
~/claude-devtools/skills/prototype-driven-roadmap/
├── SKILL.md                  # rewritten to describe the new flow
├── scripts/
│   ├── components_schema.py  # source of truth for the registry shape
│   ├── roadmap_schema.py     # source of truth for the content shape
│   └── validate_roadmap.py   # Phase 3 tool — imports project's shipped schemas
└── references/
    ├── components-json-format.md   # replaces components-yml-format.md
    ├── owasp-asvs-mapping.md       # unchanged
    ├── owasp-masvs-mapping.md      # unchanged
    ├── phase-1-extraction.md       # updated for components.json output
    ├── phase-2-generation.md       # updated for roadmap.json output
    ├── phase-3-validation.md       # updated for two-file validation
    └── roadmap-json-format.md      # replaces roadmap-item-template.md
```

`components-yml-format.md` is replaced by `components-json-format.md`
(rewritten); `roadmap-item-template.md` is replaced by
`roadmap-json-format.md` (rewritten). Old files are deleted at the end
of the migration, not kept as dead references.

---

## 5. Schema specification

The two schemas are sketched here at a level of detail sufficient for
implementation. Field names, types, and validators are normative; phrasing
of error messages is suggestive and can be improved during the implementation
pass.

### 5.1 `components_schema.py` — registry shape

```python
"""Pydantic schema for components.json — the roadmap registry.

Owned by the prototype-driven-roadmap skill. Copied into the project's
docs/roadmap/<feature>/ directory at Phase 3 so downstream consumers
can import it directly without cross-skill paths.
"""
from __future__ import annotations
import re
from pydantic import BaseModel, Field, field_validator, model_validator

SLUG_PATTERN = re.compile(r"^[a-z][a-z0-9-]*[a-z0-9]$")
ASVS_PATTERN = re.compile(r"^ASVS V\d+\.\d+\.\d+$")
MASVS_PATTERN = re.compile(r"^MASVS-[A-Z]+-\d+$")


class ComponentRegistryEntry(BaseModel):
    slug: str
    name: str
    depends_on: list[str] = Field(default_factory=list)
    owasp_categories: list[str] = Field(default_factory=list)

    @field_validator("slug")
    @classmethod
    def slug_format(cls, v: str) -> str:
        if not SLUG_PATTERN.match(v):
            raise ValueError(
                f"slug '{v}' does not match kebab-case pattern "
                f"'{SLUG_PATTERN.pattern}'"
            )
        return v

    @field_validator("owasp_categories")
    @classmethod
    def owasp_id_format(cls, v: list[str]) -> list[str]:
        for entry in v:
            if not (ASVS_PATTERN.match(entry) or MASVS_PATTERN.match(entry)):
                raise ValueError(
                    f"OWASP id '{entry}' does not match ASVS V<n>.<n>.<n> "
                    f"or MASVS-<CAT>-<n>"
                )
        return v

    @model_validator(mode="after")
    def no_self_reference(self):
        if self.slug in self.depends_on:
            raise ValueError(
                f"component '{self.slug}' depends on itself"
            )
        return self


class Components(BaseModel):
    schema_version: str = Field(pattern=r"^\d+\.\d+$")
    feature: str
    design_doc_path: str
    prototype_path: str
    components: list[ComponentRegistryEntry] = Field(min_length=1)

    @model_validator(mode="after")
    def slugs_unique(self):
        seen = set()
        for c in self.components:
            if c.slug in seen:
                raise ValueError(f"duplicate slug '{c.slug}'")
            seen.add(c.slug)
        return self

    @model_validator(mode="after")
    def depends_on_resolves(self):
        registered = {c.slug for c in self.components}
        for c in self.components:
            for dep in c.depends_on:
                if dep not in registered:
                    raise ValueError(
                        f"component '{c.slug}' depends_on '{dep}' "
                        f"which is not a registered slug"
                    )
        return self

    @model_validator(mode="after")
    def topological_order(self):
        # Every component's depends_on must reference components earlier
        # in the array (lower index). Forward references are an error.
        position = {c.slug: i for i, c in enumerate(self.components)}
        for c in self.components:
            for dep in c.depends_on:
                if position[dep] >= position[c.slug]:
                    raise ValueError(
                        f"component '{c.slug}' at position {position[c.slug]} "
                        f"depends on '{dep}' at position {position[dep]} "
                        f"(forward or self reference; components must be "
                        f"listed in topological order, roots first)"
                    )
        return self
```

Cycle detection is a side-effect of `topological_order` — a cycle
implies at least one forward reference, which the topo check catches
with a clearer error than DFS would produce. The `validate_roadmap.py`
script can additionally run a DFS for a redundant "cycle: A → B → A"
diagnostic, but the schema-level check is sufficient by itself.

### 5.2 `roadmap_schema.py` — per-component content shape

```python
"""Pydantic schema for roadmap.json — per-component scenarios and content.

Owned by the prototype-driven-roadmap skill. Copied into the project's
docs/roadmap/<feature>/ directory at Phase 3 so downstream consumers
can import it directly without cross-skill paths.
"""
from __future__ import annotations
import re
from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator

ASVS_PATTERN = re.compile(r"^ASVS V\d+\.\d+\.\d+$")
MASVS_PATTERN = re.compile(r"^MASVS-[A-Z]+-\d+$")
SLUG_PATTERN = re.compile(r"^[a-z][a-z0-9-]*[a-z0-9]$")
EvidenceKind = Literal["prototype", "prescribed"]


class PrototypeEvidence(BaseModel):
    path: str
    note: str
    lines: str | None = None  # e.g., "23-31"; optional


class FunctionalScenario(BaseModel):
    name: str
    given: str
    when: str
    then: str
    verified_by: str
    evidence_kind: EvidenceKind

    @field_validator("verified_by")
    @classmethod
    def verified_by_concrete(cls, v: str) -> str:
        forbidden = {"", "TBD", "<unknown>", "unknown", "tbd"}
        if v.strip() in forbidden:
            raise ValueError(
                f"verified_by must name a concrete artifact "
                f"(test path, tool invocation, named manual check); "
                f"got {v!r}"
            )
        return v


class SecurityScenario(BaseModel):
    name: str
    owasp_id: str
    owasp_category_label: str  # human-readable, e.g., "Input Validation"
    performed_by: str
    given: str
    when: str
    then: str
    verified_by: str
    evidence_kind: EvidenceKind

    @field_validator("owasp_id")
    @classmethod
    def owasp_id_format(cls, v: str) -> str:
        if not (ASVS_PATTERN.match(v) or MASVS_PATTERN.match(v)):
            raise ValueError(
                f"owasp_id '{v}' does not match ASVS V<n>.<n>.<n> "
                f"or MASVS-<CAT>-<n>"
            )
        return v

    @field_validator("performed_by")
    @classmethod
    def performed_by_format(cls, v: str) -> str:
        if not SLUG_PATTERN.match(v):
            raise ValueError(
                f"performed_by '{v}' does not match kebab-case slug pattern"
            )
        return v

    @field_validator("verified_by")
    @classmethod
    def verified_by_concrete(cls, v: str) -> str:
        forbidden = {"", "TBD", "<unknown>", "unknown", "tbd"}
        if v.strip() in forbidden:
            raise ValueError(
                f"verified_by must name a concrete artifact; got {v!r}"
            )
        return v


class OutOfScopeItem(BaseModel):
    concern: str
    owner: str | None = None  # slug of the component that owns the concern
    reason: str | None = None  # e.g., "deferred per design doc"


class DependencyItem(BaseModel):
    slug: str
    rationale: str

    @field_validator("slug")
    @classmethod
    def slug_format(cls, v: str) -> str:
        if not SLUG_PATTERN.match(v):
            raise ValueError(
                f"dependency slug '{v}' does not match kebab-case pattern"
            )
        return v


class ComponentContent(BaseModel):
    slug: str
    purpose: str
    prototype_evidence: list[PrototypeEvidence] = Field(min_length=1)
    functional_scenarios: list[FunctionalScenario] = Field(default_factory=list)
    security_scenarios: list[SecurityScenario] = Field(default_factory=list)
    out_of_scope: list[OutOfScopeItem] = Field(default_factory=list)
    out_of_scope_reason: str | None = None
    dependencies: list[DependencyItem] = Field(default_factory=list)
    dependencies_reason: str | None = None

    @field_validator("slug")
    @classmethod
    def slug_format(cls, v: str) -> str:
        if not SLUG_PATTERN.match(v):
            raise ValueError(
                f"slug '{v}' does not match kebab-case pattern"
            )
        return v

    @model_validator(mode="after")
    def out_of_scope_completeness(self):
        if not self.out_of_scope and not self.out_of_scope_reason:
            raise ValueError(
                f"component '{self.slug}': out_of_scope is empty and "
                f"out_of_scope_reason is missing — silence is not allowed; "
                f"either populate out_of_scope or explain why it's empty"
            )
        if self.out_of_scope and self.out_of_scope_reason:
            raise ValueError(
                f"component '{self.slug}': out_of_scope and "
                f"out_of_scope_reason are mutually exclusive — use the "
                f"reason field only when the list is empty"
            )
        return self

    @model_validator(mode="after")
    def dependencies_completeness(self):
        if not self.dependencies and not self.dependencies_reason:
            raise ValueError(
                f"component '{self.slug}': dependencies is empty and "
                f"dependencies_reason is missing — silence is not allowed"
            )
        if self.dependencies and self.dependencies_reason:
            raise ValueError(
                f"component '{self.slug}': dependencies and "
                f"dependencies_reason are mutually exclusive"
            )
        return self

    @model_validator(mode="after")
    def security_performed_by_matches_self(self):
        for s in self.security_scenarios:
            if s.performed_by != self.slug:
                raise ValueError(
                    f"component '{self.slug}': security scenario "
                    f"'{s.name}' has performed_by='{s.performed_by}' "
                    f"which does not match the component's own slug; "
                    f"scenarios for actions performed by another component "
                    f"belong in that component's content"
                )
        return self


class Roadmap(BaseModel):
    schema_version: str = Field(pattern=r"^\d+\.\d+$")
    feature: str
    components: list[ComponentContent] = Field(min_length=1)

    @model_validator(mode="after")
    def slugs_unique(self):
        seen = set()
        for c in self.components:
            if c.slug in seen:
                raise ValueError(f"duplicate slug '{c.slug}'")
            seen.add(c.slug)
        return self
```

Several invariants intentionally live in `validate_roadmap.py` rather
than the schema:

- **Cross-file slug parity** (every slug in `roadmap.json` is in
  `components.json` and vice versa) — requires both files; not
  expressible in either schema alone.
- **`depends_on` parity between files** — same.
- **OWASP ID parity** (every `owasp_id` cited in a security scenario
  is in that component's registry `owasp_categories`, and every
  registry category is cited in at least one scenario) — same.
- **`performed_by` registered** (the slug exists in `components.json`)
  — same.
- **`out_of_scope.owner` registered** — same.

The Pydantic schemas check what each file owns alone; the validator
script checks what spans both files.

### 5.3 Schema versioning

Both files start at `schema_version: "1.0"`. Bump rules:

- **Additive change** (new optional field, new validator that rejects
  cases that were already buggy): keep the version.
- **Breaking change** (rename/remove field, change required-vs-optional,
  change semantics of an existing field): bump major version.
- The validator script accepts only the major version it ships with
  (initially `1.x`); newer-major roadmaps must be regenerated against
  the matching skill version.

The shipped schema in the project is by definition compatible with the
JSON it shipped alongside, so version drift only matters when (a) the
JSON is hand-edited or (b) a newer skill version reads an older
project's roadmap. Both are real cases worth the few lines of
defensive code.

---

## 6. Validator script (`validate_roadmap.py`) — final shape

Approximate structure, ~150 lines total:

```python
#!/usr/bin/env python3
"""Validate a project's roadmap output (components.json + roadmap.json).

Run:
    uv run --with pydantic python validate_roadmap.py docs/roadmap/<feature>/

Exits:
    0 — all checks passed.
    1 — one or more validation failures.
    2 — precondition failure (directory or files missing).
"""
from __future__ import annotations
import json
import sys
import importlib.util
from pathlib import Path

def load_schema_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_roadmap.py <roadmap_dir>", file=sys.stderr)
        return 2

    roadmap_dir = Path(argv[1]).resolve()
    if not roadmap_dir.is_dir():
        print(f"directory not found: {roadmap_dir}", file=sys.stderr)
        return 2

    components_json = roadmap_dir / "components.json"
    roadmap_json = roadmap_dir / "roadmap.json"
    components_schema = roadmap_dir / "components_schema.py"
    roadmap_schema = roadmap_dir / "roadmap_schema.py"

    for f in (components_json, roadmap_json, components_schema, roadmap_schema):
        if not f.is_file():
            print(f"required file missing: {f}", file=sys.stderr)
            return 2

    cs = load_schema_module(components_schema, "components_schema")
    rs = load_schema_module(roadmap_schema, "roadmap_schema")

    errors: list[str] = []

    # Per-file schema validation
    try:
        components = cs.Components.model_validate_json(components_json.read_text())
    except Exception as e:
        errors.append(f"components.json: {e}")
        components = None

    try:
        roadmap = rs.Roadmap.model_validate_json(roadmap_json.read_text())
    except Exception as e:
        errors.append(f"roadmap.json: {e}")
        roadmap = None

    if components is None or roadmap is None:
        for err in errors:
            print(err)
        return 1

    # Resolve external paths declared in components.json
    # The roadmap dir is at <project>/docs/roadmap/<feature>/, so
    # project root is three levels up.
    project_root = roadmap_dir.parent.parent.parent
    if not (project_root / components.design_doc_path).is_file():
        errors.append(
            f"components.json: design_doc_path '{components.design_doc_path}' "
            f"does not resolve to a file under {project_root}"
        )
    if not (project_root / components.prototype_path).is_dir():
        errors.append(
            f"components.json: prototype_path '{components.prototype_path}' "
            f"does not resolve to a directory under {project_root}"
        )

    # Cross-file: feature name matches
    if components.feature != roadmap.feature:
        errors.append(
            f"feature mismatch: components.json='{components.feature}' "
            f"vs roadmap.json='{roadmap.feature}'"
        )

    # Cross-file: slug sets match
    reg_slugs = {c.slug for c in components.components}
    roadmap_slugs = {c.slug for c in roadmap.components}
    if reg_slugs != roadmap_slugs:
        only_in_reg = reg_slugs - roadmap_slugs
        only_in_roadmap = roadmap_slugs - reg_slugs
        if only_in_reg:
            errors.append(
                f"slugs in components.json but missing from roadmap.json: "
                f"{sorted(only_in_reg)}"
            )
        if only_in_roadmap:
            errors.append(
                f"slugs in roadmap.json but missing from components.json: "
                f"{sorted(only_in_roadmap)}"
            )

    # Cross-file: array order matches
    if [c.slug for c in components.components] != [c.slug for c in roadmap.components]:
        errors.append(
            "component array order in components.json and roadmap.json "
            "must match (both must be in topological order, roots first)"
        )

    # Cross-file: per-component checks
    reg_by_slug = {c.slug: c for c in components.components}
    for content in roadmap.components:
        if content.slug not in reg_by_slug:
            continue  # already reported above
        reg = reg_by_slug[content.slug]

        # depends_on parity
        roadmap_deps = {d.slug for d in content.dependencies}
        if set(reg.depends_on) != roadmap_deps:
            errors.append(
                f"component '{content.slug}': depends_on parity violation. "
                f"components.json depends_on={sorted(reg.depends_on)}; "
                f"roadmap.json dependencies={sorted(roadmap_deps)}"
            )

        # OWASP ID parity
        cited_ids = {s.owasp_id for s in content.security_scenarios}
        registered_ids = set(reg.owasp_categories)
        if cited_ids != registered_ids:
            only_registered = registered_ids - cited_ids
            only_cited = cited_ids - registered_ids
            if only_registered:
                errors.append(
                    f"component '{content.slug}': OWASP ids in components.json "
                    f"but not cited in any scenario: {sorted(only_registered)}"
                )
            if only_cited:
                errors.append(
                    f"component '{content.slug}': OWASP ids cited in scenarios "
                    f"but not registered in components.json: {sorted(only_cited)}"
                )

        # performed_by registration
        for scenario in content.security_scenarios:
            if scenario.performed_by not in reg_slugs:
                errors.append(
                    f"component '{content.slug}', scenario '{scenario.name}': "
                    f"performed_by='{scenario.performed_by}' is not a "
                    f"registered slug"
                )

        # out_of_scope.owner registration
        for ooss in content.out_of_scope:
            if ooss.owner is not None and ooss.owner not in reg_slugs:
                errors.append(
                    f"component '{content.slug}', out_of_scope item "
                    f"'{ooss.concern[:40]}...': owner='{ooss.owner}' is "
                    f"not a registered slug"
                )

    # Schema version check
    if not components.schema_version.startswith("1."):
        errors.append(
            f"components.json schema_version='{components.schema_version}' "
            f"is not in the 1.x range supported by this validator"
        )
    if not roadmap.schema_version.startswith("1."):
        errors.append(
            f"roadmap.json schema_version='{roadmap.schema_version}' "
            f"is not in the 1.x range supported by this validator"
        )

    if errors:
        print(f"Roadmap validation FAILED. {len(errors)} error(s):\n")
        for err in errors:
            print(f"  - {err}")
        return 1

    # Success: print summary table
    print(f"Roadmap Validation: {components.feature} — PASS\n")
    print("| Component | Functional | Security | OWASP categories |")
    print("|-----------|-----------:|---------:|------------------|")
    for content in roadmap.components:
        reg = reg_by_slug[content.slug]
        print(
            f"| {content.slug} "
            f"| {len(content.functional_scenarios)} "
            f"| {len(content.security_scenarios)} "
            f"| {', '.join(reg.owasp_categories) or '—'} |"
        )
    print(f"\nOutput directory: {roadmap_dir}")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

Notes on the validator:

- **Project root derivation.** Computed from `roadmap_dir.parent.parent.parent`,
  matching the roadmap layout convention `<project>/docs/roadmap/<feature>/`.
  This replaces the `Path.cwd()` hack from the existing validator and
  fixes the path-resolution bug discussed in conversation. The argument
  to the script is interpreted as absolute or relative-to-cwd (standard
  shell convention).
- **Schema imports.** The validator dynamically loads the project's
  shipped schema modules via `importlib.util`. This validates "the
  schema as shipped," which is the contract downstream skills will see.
- **Error reporting.** Errors are accumulated and printed together at
  the end so the user sees the full picture per run, not one error at a
  time. Each error names the file, the component slug, and (where
  applicable) the scenario name for trivial fix routing.
- **Summary table.** Mirrors the existing validator's success output,
  with the same columns.

---

## 7. Phase-by-phase changes to the skill

### 7.1 Phase 1 — Extraction

**Stays the same:**
- Precondition check (design doc has Architecture Overview → Components,
  Tooling → Security Tooling, Deferred Decisions sections; rejects
  Open Questions).
- Component extraction from the design doc.
- Slug generation rules.
- Data-flow derivation per component (inputs, outputs, persisted state,
  auth surfaces, cross-process).
- OWASP category mapping using `owasp-asvs-mapping.md` /
  `owasp-masvs-mapping.md`.
- Proposal message format with explicit actor-naming step (R01 fix:
  for each candidate OWASP category, name the component whose code
  performs the action).
- Topological array ordering of components (roots first).
- STOP for user approval before writing anything.

**Changes:**
- Phase 1 ends with writing `components.json` (and copying
  `components_schema.py` into the project) instead of `components.yml`.
  The contents are the same data, in JSON instead of YAML, with
  `schema_version: "1.0"` at the top.
- After writing, Phase 1 runs the components-only portion of the
  validator (schema validation of `components.json` against the
  shipped schema; no cross-file checks since `roadmap.json` doesn't
  exist yet) to confirm the registry is well-formed before Phase 2.
- The reference doc `references/phase-1-extraction.md` is updated to
  reflect the JSON output format and the new validation step. The
  proposal message format and actor-naming step are preserved verbatim.

### 7.2 Phase 2 — Generation

**Stays the same:**
- Reads the registry as the authoritative input (now `components.json`
  instead of `components.yml`).
- Checks for prior-run artifacts and asks before overwriting.
- One component's content per registered slug.
- Content rules: prototype evidence cited per file, Gherkin scenarios
  with all required fields, OWASP ID per security scenario,
  Performed-by per security scenario, Out-of-Scope and Dependencies
  populated (with reason fallback for empty), evidence kind labeled.

**Changes:**
- The output is one file: `roadmap.json`. Per-component markdown files
  are not produced.
- The model produces structured output matching `roadmap_schema.py`.
  Phase 2 reference doc (`references/phase-2-generation.md`) replaces
  the markdown template guide with a JSON-shape guide.
- After writing, Phase 2 runs `validate_roadmap.py` to catch errors
  before Phase 3. (Phase 3 was previously the validation phase; with
  validation also at the end of Phase 1 and Phase 2, Phase 3 becomes
  primarily the user-facing summary step.)
- `roadmap-item-template.md` is replaced by `roadmap-json-format.md`.
  Same role: format reference for the per-component content artifact.
  The new doc presents a JSON example with annotations explaining
  each field, including how the trial-earned invariants
  (Performed-by, evidence_kind, etc.) are expressed in the new shape.

### 7.3 Phase 3 — Validation

**Stays the same:**
- Validator-driven; user does not hand-edit JSON to pass validation
  (rules are intentional; fix the content, not the validator).
- Summary table for sign-off.
- STOP for user review at the end.

**Changes:**
- The validator command is now:
  ```bash
  uv run --with pydantic python \
    ~/claude-devtools/skills/prototype-driven-roadmap/scripts/validate_roadmap.py \
    docs/roadmap/<feature>/
  ```
  (`--with pydantic` instead of `--with pyyaml`).
- The validator does the work of all three previous Phase 3 steps in
  one invocation: per-file schema validation + cross-file invariants +
  summary table.
- `references/phase-3-validation.md` is updated to describe the new
  flow and document the cross-file invariants.

### 7.4 SKILL.md changes

The Quick Reference table changes:

| Phase | Purpose | Output |
|-------|---------|--------|
| 1. Extraction | Parse design doc, extract components, derive data flows, map to OWASP, generate slugs, write registry after user approval | `docs/roadmap/<feature>/components.json` + `components_schema.py` |
| 2. Generation | Read components.json, generate per-component content into roadmap.json | `docs/roadmap/<feature>/roadmap.json` + `roadmap_schema.py` |
| 3. Validation | Run validate_roadmap.py against both files; print summary | Validator exit 0 + summary table |

The Principles section keeps every existing principle. Wording
adjustments only:
- "frontmatter" → "JSON registry fields"
- "markdown structural rules" → "schema validation"
- "`### Scenario:` headings" → "scenario objects"
- The R01 Performed-by principle and the ID-set parity principle are
  preserved verbatim in spirit; phrasing updated to JSON terms.

The Environment Setup section changes from `--with pyyaml` to
`--with pydantic`. The "How to Start" section is unchanged.

---

## 8. JSON examples (for the reference docs)

### 8.1 `components.json`

```json
{
  "schema_version": "1.0",
  "feature": "airflow-gdrive-ingestion",
  "design_doc_path": "docs/design/airflow-gdrive-ingestion-2026-04-28.md",
  "prototype_path": "prototypes/airflow-gdrive-ingestion/",
  "components": [
    {
      "slug": "project-setup",
      "name": "Project Setup",
      "depends_on": [],
      "owasp_categories": ["ASVS V2.10.4", "ASVS V14.2.1"]
    },
    {
      "slug": "drive-downloader",
      "name": "Google Drive Downloader",
      "depends_on": ["project-setup"],
      "owasp_categories": ["ASVS V2.10.4", "ASVS V9.2.1", "ASVS V12.4.2"]
    },
    {
      "slug": "sqlite-parser",
      "name": "SQLite Parser",
      "depends_on": ["drive-downloader"],
      "owasp_categories": ["ASVS V5.1.3", "ASVS V5.1.4", "ASVS V12.2.1"]
    },
    {
      "slug": "minio-uploader",
      "name": "MinIO Uploader",
      "depends_on": ["sqlite-parser"],
      "owasp_categories": ["ASVS V8.1.1", "ASVS V9.1.1", "ASVS V12.3.1"]
    },
    {
      "slug": "rabbitmq-publisher",
      "name": "RabbitMQ Publisher",
      "depends_on": ["minio-uploader"],
      "owasp_categories": ["ASVS V2.10.4", "ASVS V8.3.4", "ASVS V9.1.1"]
    }
  ]
}
```

Note: project-setup is shown with `depends_on: ["project-setup"]` would
be invalid (self-reference). The example here has `depends_on: []` for
project-setup; runtime components depend on project-setup via the array
order and explicit `depends_on`. Whether project-setup should appear in
runtime components' `depends_on` is a content decision the skill makes
during Phase 1 — the schema permits either choice as long as the chain
is acyclic and topologically ordered.

### 8.2 `roadmap.json` (one component for illustration)

```json
{
  "schema_version": "1.0",
  "feature": "airflow-gdrive-ingestion",
  "components": [
    {
      "slug": "project-setup",
      "purpose": "Project Setup establishes the build, test, and runtime infrastructure for the Airflow Google Drive ingestion service. It defines the Python dependency set, the Docker image, the docker-compose stack with all six services (postgres, minio, rabbitmq, airflow-init, airflow-webserver, airflow-scheduler), the lint and test toolchains, and the conftest.py that provides shared test fixtures. Runtime components depend on this scaffolding being in place before their own scenarios can run.",
      "prototype_evidence": [
        {
          "path": "prototypes/airflow-gdrive-ingestion/requirements.txt",
          "note": "direct dependencies with pinned versions"
        },
        {
          "path": "prototypes/airflow-gdrive-ingestion/Dockerfile",
          "note": "airflow user, pip install in user site-packages"
        },
        {
          "path": "prototypes/airflow-gdrive-ingestion/docker-compose.yml",
          "note": "six-service stack with healthcheck dependencies"
        },
        {
          "path": "prototypes/airflow-gdrive-ingestion/ruff.toml",
          "note": "lint configuration with selected rule sets"
        },
        {
          "path": "prototypes/airflow-gdrive-ingestion/conftest.py",
          "note": "session-scoped sample-DB fixture for parser tests"
        }
      ],
      "functional_scenarios": [
        {
          "name": "All six services reach healthy state in order after docker compose up",
          "given": "a host with Docker installed and the service account key file mounted at the configured path",
          "when": "docker compose up -d --wait is run from prototypes/airflow-gdrive-ingestion/",
          "then": "postgres passes its pg_isready healthcheck; minio passes its /minio/health/live check; rabbitmq passes its rabbitmqctl status check; airflow-init exits 0; airflow-webserver and airflow-scheduler enter the running state",
          "verified_by": "docker compose up --wait completing successfully and `docker compose ps` showing all services healthy",
          "evidence_kind": "prototype"
        }
      ],
      "security_scenarios": [
        {
          "name": "Admin credentials and connection URIs are not baked into the Dockerfile or docker-compose.yml",
          "owasp_id": "ASVS V2.10.4",
          "owasp_category_label": "Service Authentication",
          "performed_by": "project-setup",
          "given": "the Dockerfile and docker-compose.yml in prototypes/airflow-gdrive-ingestion/",
          "when": "gitleaks detect --source prototypes/airflow-gdrive-ingestion --no-git is run",
          "then": "no credential values appear in any committed file; all secrets reach the containers via environment variables sourced from a .env file that is gitignored",
          "verified_by": "gitleaks detect exit 0 + manual review of .gitignore for .env coverage",
          "evidence_kind": "prototype"
        }
      ],
      "out_of_scope": [
        {
          "concern": "DAG authoring, task logic, and Airflow connection configuration",
          "owner": "drive-downloader",
          "reason": null
        }
      ],
      "out_of_scope_reason": null,
      "dependencies": [],
      "dependencies_reason": "this component has no dependencies on other components in this feature's roadmap"
    }
  ]
}
```

The full file would have one entry per registered slug, in the same
order as `components.json`.

---

## 9. Implementation order

Steps land in sequence, each gated on the previous passing its smoke check.

### Step 1 — Schemas

1. Write `~/claude-devtools/skills/prototype-driven-roadmap/scripts/components_schema.py`
   per §5.1.
2. Write `~/claude-devtools/skills/prototype-driven-roadmap/scripts/roadmap_schema.py`
   per §5.2.
3. Smoke-test from a Python REPL:
   - Construct a happy-path `Components` and a happy-path `Roadmap`;
     confirm both validate.
   - Construct intentionally-broken instances (duplicate slug, forward
     reference, malformed OWASP ID, empty out_of_scope without reason,
     security scenario performed_by mismatch); confirm each raises with
     a sensible message.
4. **Gate:** all happy-path instances valid; all broken instances
   rejected with messages a reviewer can act on.

### Step 2 — Validator script

5. Rewrite `~/claude-devtools/skills/prototype-driven-roadmap/scripts/validate_roadmap.py`
   per §6.
6. Smoke-test against synthetic JSON fixtures:
   - happy path (both files valid + cross-file invariants hold) → exit 0
   - registry/roadmap slug mismatch → exit 1, error names both files
   - OWASP ID parity miss → exit 1, error names component + ids
   - performed_by unregistered → exit 1, error names component + scenario
   - out_of_scope.owner unregistered → exit 1
   - schema_version out of range → exit 1
   - missing required file → exit 2
7. **Gate:** every smoke test produces the expected exit code and
   error.

### Step 3 — Reference docs

8. Write `references/components-json-format.md` (replaces
   `components-yml-format.md`); content per §5.1 with examples from §8.1.
9. Write `references/roadmap-json-format.md` (replaces
   `roadmap-item-template.md`); content per §5.2 with examples from §8.2.
   Preserve all anti-patterns documented in the original
   `roadmap-item-template.md` (narrative-only files, unverifiable
   security claims, dependency-list drift, wholesale OWASP, etc.) —
   restate them in JSON terms.
10. Update `references/phase-1-extraction.md`. The proposal message
    format and the actor-naming step (R01 fix) stay verbatim. Output
    target changes from `components.yml` to `components.json`. Add the
    "run schema validation on components.json before STOP" step.
11. Update `references/phase-2-generation.md`. Replace the markdown
    template guide with a guide to producing JSON matching
    `roadmap_schema.py`. Preserve the content rules (Gherkin, Performed-by,
    evidence_kind, ID format, no wholesale OWASP).
12. Update `references/phase-3-validation.md`. Document the new
    validator command, the two-file model, and the cross-file invariants.
13. Delete `references/components-yml-format.md` and
    `references/roadmap-item-template.md`.
14. **Gate:** All reference docs read coherently; cross-references
    between docs work; no references to YAML or markdown roadmap files
    remain.

### Step 4 — SKILL.md

15. Rewrite the Quick Reference table per §7.4.
16. Update Environment Setup (`--with pydantic`).
17. Update Phase 1 / Phase 2 / Phase 3 step lists per §7.1–§7.3.
18. Update the Principles section per §7.4 (wording adjustments only).
19. Update the schema-shipping mention to cover both schemas.
20. **Gate:** SKILL.md describes the new flow end-to-end, with no
    YAML/markdown remnants.

### Step 5 — R04 trial

21. **Before invoking the skill,** delete the existing roadmap output
    at `~/health-data-ai-platform/docs/roadmap/airflow-gdrive-ingestion/`
    (the user has confirmed this is intended).
22. Invoke the skill against the existing design doc
    (`docs/design/airflow-gdrive-ingestion-2026-04-28.md`).
23. Walk through Phase 1 to STOP: confirm the proposal message looks
    right, the actor-naming step works, and the user can approve.
24. Walk through Phase 2: confirm `roadmap.json` is generated with the
    correct shape and all components have their content.
25. Walk through Phase 3: confirm the validator passes and the summary
    table renders cleanly.
26. **Eyeball the JSON output as a reviewer would.** Confirm:
    - Each component is readable.
    - Performed-by fields are correctly placed (no R01-class
      misplacement).
    - OWASP IDs match between registry and scenarios.
    - Evidence kind is set per scenario.
    - Out-of-scope and dependencies have either content or reason.
27. **File `R04-roadmap-json-migration.md`** in the trials directory
    documenting:
    - What worked first try
    - What failure modes surfaced (model JSON-emission bugs we haven't
      seen before; missed schema fields; over-quoted strings)
    - Whether any invariants were silently lost in translation
    - Skill-level fixes applied during the trial (if any)
28. **Update `trials/_SUMMARY.md`** and `trials/_INDEX.md` with R04.

### Step 6 — Memory and downstream-plan updates

29. Update `README.md`: Current State section reflects R04 outcome and
    lists the new artifact set.
30. Update `LEARNINGS.md`: add a "From Roadmap-Skill JSON Migration"
    subsection capturing whatever R04 surfaced (if anything new).
31. Update `decomposition-roadmap-refactor-plan-2026-04-26.md`:
    - §4.4 — `components_yml_path` → `roadmap_json_path` and
      `components_json_path` (both inputs now)
    - §5.1 — Phase 1 inputs are JSON only
    - §7 — collapse the validator-implementation-notes section; no
      parser sharing question; just two `json.load()` calls and two
      schema imports
    - §9.1 — note as "resolved upstream by JSON migration"
    - §10 — sequencing updated to reflect the cleaner upstream
32. **Gate:** all memory-repo files reflect post-migration reality;
    next session reads this state cleanly.

---

## 10. Risks and how the trial protocol catches them

**Risk: Model JSON-emission failure modes.** The skill has been tuned
against markdown emission bugs (forgotten Performed-by lines, missing
sections, drifted conventions). JSON emission has different failure
modes: unescaped quotes inside scenario prose, malformed nested arrays,
fields hallucinated that aren't in the schema, missing required fields.

*Catch:* Schema validation rejects structural problems with clear
messages. The R04 trial will surface what content-shape problems
emerge. File new failure modes in the trial record; refine schema or
Phase 2 prompts in response.

**Risk: Trial-earned invariants silently lost in translation.** §3
maps each invariant to its new enforcement. If the implementation pass
finds an invariant that doesn't fit cleanly, the answer is to find a
fit, not to drop it.

*Catch:* §3 is a checklist. R04 trial review explicitly walks each
row: "is this still enforced? Where? Test it."

**Risk: JSON readability is worse than markdown for human review.**
The R04 trial's "eyeball the JSON output" step (Step 5 #26) tests
this directly. If a reviewer cannot catch R01-class semantic issues
when reading JSON, the migration has lost something real.

*Catch:* R04 review is the test. If readability is worse than
expected, evaluate whether to add a separate JSON-to-markdown render
step (option E from the conversation) before completing the
migration. This is a real fallback; the first pass should not
prematurely commit to it.

**Risk: Validator path-resolution still buggy.** §6 fixes the
`Path.cwd()` hack by deriving project root from the roadmap
directory's location. If the roadmap layout convention changes
(e.g., the skill ever decides roadmaps live somewhere other than
`<project>/docs/roadmap/<feature>/`), the derivation breaks.

*Catch:* The convention is explicitly documented in SKILL.md and the
validator script's docstring. Any future move of the convention
forces both updates together.

**Risk: Schema files referenced by absolute paths break across
machines.** The validator dynamically loads schemas via
`importlib.util` from the project's roadmap directory. As long as the
roadmap directory contains the schemas, this works on any machine.

*Catch:* The schema-copy step in Phase 1 / Phase 2 is mandatory; the
validator's preflight (§6 line "for f in (...): if not f.is_file(): ...
return 2") catches missing schemas with a clear precondition error
rather than a confusing import failure.

---

## 11. What's out of scope for this work

- **Changing the design-doc format.** Design docs stay markdown. The
  planning skill is unchanged by this migration.
- **Changing task decomposition's existing JSON output.** Tasks already
  use JSON; this work doesn't touch them.
- **Adding new fields beyond what's needed for the trial-earned
  invariants.** Resist temptation to "since we're rewriting, let's also
  add X." Migration first; refinement in subsequent trials.
- **Generalizing schemas to other domains.** Today's schemas serve
  the airflow-gdrive trial; broader-applicability is something later
  trials will surface and refine.
- **Per-component decomposition in the decomposition skill.** That's
  the downstream refactor's question (§13 of
  `decomposition-roadmap-refactor-plan-2026-04-26.md`); it remains
  open and orthogonal.

---

## 12. Acceptance criteria for this work to be "done"

1. Steps 1–6 complete; each gate has been hit.
2. R04 trial filed with a passing scoreboard.
3. Memory repo reflects post-migration reality (README, LEARNINGS,
   _SUMMARY, _INDEX).
4. Decomposition refactor plan updated.
5. The trial-earned invariants in §3 are all preserved (verified at
   trial time).
6. The roadmap output for airflow-gdrive-ingestion exists in the new
   shape and a reviewer can read and approve it.

When 1–6 hold, this work is done and the decomposition refactor (paused
in the plan from 2026-04-26) is unblocked.
