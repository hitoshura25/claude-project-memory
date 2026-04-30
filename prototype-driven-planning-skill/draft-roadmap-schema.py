"""Pydantic schema for roadmap.json — per-component content artifact.

Owned by the prototype-driven-roadmap skill. The source of truth for this file
lives at:

    ~/claude-devtools/skills/prototype-driven-roadmap/scripts/roadmap_schema.py

At Phase 3 of the roadmap skill, this file is copied into each project's
roadmap output directory at:

    <project>/docs/roadmap/<feature>/roadmap_schema.py

Downstream skills (e.g., prototype-driven-task-decomposition) import from the
project-shipped copy rather than reaching back into this skill's directory.
This keeps each skill self-contained and avoids cross-skill imports.

roadmap.json holds per-component scenarios and prose: each component's
purpose, prototype evidence, functional scenarios (Gherkin), security
scenarios (Gherkin + OWASP id + Performed-by), out-of-scope items, and
dependency rationales. The component slug is the foreign key joining this
file to components.json (see components_schema.py for the registry shape).

The schema enforces what each file owns alone. Cross-file invariants
(slug set parity between roadmap.json and components.json; depends_on
parity; OWASP id set parity between registry and scenarios) live in
validate_roadmap.py because they require both files loaded.

Trial-earned invariants enforced here:

  - **Performed-by self-match (R01)**: every security scenario's
    performed_by must equal the enclosing component's own slug.
    Scenarios for actions performed by another component belong in
    that other component's content, not here.
  - **Out-of-scope completeness**: out_of_scope and out_of_scope_reason
    are mutually exclusive; one or the other must be present. Silence
    (empty list, no reason) is rejected.
  - **Dependencies completeness**: same pattern for dependencies and
    dependencies_reason.
  - **Verified-by concreteness**: rejects empty / "TBD" / "<unknown>"
    placeholders. Every scenario must name a real verifier.
  - **Evidence-kind labeling (planning skill arc)**: every scenario
    declares whether its verifier is a prototype artifact ("prototype")
    or an implementation-phase prescription ("prescribed"). Replaces
    the prose convention of "Prescribed (not validated)" labels.
  - **Prototype evidence non-empty**: every component must cite at
    least one prototype file. Components without prototype evidence
    indicate either a design-doc component the prototype didn't
    validate, or a Phase 1 mapping error.
"""
from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

# Slugs are kebab-case, start with a lowercase letter, end with a letter or
# digit. Must match the same pattern used in components_schema.py.
SLUG_PATTERN = re.compile(r"^[a-z][a-z0-9-]*[a-z0-9]$")

# OWASP requirement id formats from the ASVS and MASVS specifications.
ASVS_PATTERN = re.compile(r"^ASVS V\d+\.\d+\.\d+$")
MASVS_PATTERN = re.compile(r"^MASVS-[A-Z]+-\d+$")

# Verified-by placeholders that indicate the scenario is not actually done.
# Compared case-insensitively after stripping whitespace.
_VERIFIED_BY_PLACEHOLDERS = frozenset({"", "tbd", "unknown", "<unknown>", "<tbd>", "n/a", "todo"})

EvidenceKind = Literal["prototype", "prescribed"]


def _check_verified_by(v: str) -> str:
    """Reject placeholder values for verified_by; require a concrete artifact."""
    if v.strip().lower() in _VERIFIED_BY_PLACEHOLDERS:
        raise ValueError(
            f"verified_by must name a concrete artifact (test path, tool "
            f"invocation, or named manual check); got {v!r}. A scenario "
            f"that cannot name its verifier is a principle or aspiration, "
            f"not a scenario."
        )
    return v


class PrototypeEvidence(BaseModel):
    """A single prototype-evidence reference: which file demonstrates this
    component's behavior, optionally with a line range, and a one-line note.
    """

    path: str
    note: str
    lines: str | None = None  # e.g., "23-31"; optional

    @field_validator("path")
    @classmethod
    def path_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("prototype_evidence.path must not be empty")
        return v

    @field_validator("note")
    @classmethod
    def note_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("prototype_evidence.note must not be empty")
        return v


class FunctionalScenario(BaseModel):
    """A functional scenario in Gherkin shape.

    Functional scenarios describe behaviors the prototype demonstrated or
    behaviors the design doc explicitly prescribed for production. The
    evidence_kind field labels which is which: "prototype" for behaviors
    validated by the prototype itself; "prescribed" for behaviors the
    design doc requires that an implementation-phase check will validate.
    """

    name: str
    given: str
    when: str
    then: str
    verified_by: str
    evidence_kind: EvidenceKind

    @field_validator("name", "given", "when", "then")
    @classmethod
    def field_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("scenario field must not be empty")
        return v

    @field_validator("verified_by")
    @classmethod
    def verified_by_concrete(cls, v: str) -> str:
        return _check_verified_by(v)


class SecurityScenario(BaseModel):
    """A security scenario in Gherkin shape, with an OWASP requirement id
    and an explicit Performed-by field naming the component whose code
    performs the action.

    The Performed-by field exists to catch a specific failure (R01): a
    security concern is real, but it gets attached to the file of a
    component that consumes the result of an action rather than the file
    of the component that performs the action. The owning ComponentContent
    enforces that performed_by matches its own slug.
    """

    name: str
    owasp_id: str
    owasp_category_label: str  # human-readable, e.g., "Input Validation"
    performed_by: str
    given: str
    when: str
    then: str
    verified_by: str
    evidence_kind: EvidenceKind

    @field_validator("name", "owasp_category_label", "given", "when", "then")
    @classmethod
    def field_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("scenario field must not be empty")
        return v

    @field_validator("owasp_id")
    @classmethod
    def owasp_id_format(cls, v: str) -> str:
        if not (ASVS_PATTERN.match(v) or MASVS_PATTERN.match(v)):
            raise ValueError(
                f"owasp_id {v!r} does not match 'ASVS V<n>.<n>.<n>' "
                f"(e.g. 'ASVS V5.1.3') or 'MASVS-<CATEGORY>-<n>' "
                f"(e.g. 'MASVS-STORAGE-1')"
            )
        return v

    @field_validator("performed_by")
    @classmethod
    def performed_by_format(cls, v: str) -> str:
        if not SLUG_PATTERN.match(v):
            raise ValueError(
                f"performed_by {v!r} does not match kebab-case slug "
                f"pattern {SLUG_PATTERN.pattern!r}"
            )
        return v

    @field_validator("verified_by")
    @classmethod
    def verified_by_concrete(cls, v: str) -> str:
        return _check_verified_by(v)


class OutOfScopeItem(BaseModel):
    """A single out-of-scope concern: what's not this component's
    responsibility, optionally which component owns it, optionally why.
    """

    concern: str
    owner: str | None = None  # slug of the component that owns the concern
    reason: str | None = None  # e.g., "deferred per design doc"

    @field_validator("concern")
    @classmethod
    def concern_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("out_of_scope.concern must not be empty")
        return v

    @field_validator("owner")
    @classmethod
    def owner_slug_format(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not SLUG_PATTERN.match(v):
            raise ValueError(
                f"out_of_scope.owner {v!r} does not match kebab-case slug "
                f"pattern {SLUG_PATTERN.pattern!r}"
            )
        return v


class DependencyItem(BaseModel):
    """A single dependency entry: which slug this component depends on,
    and the rationale for the dependency in production terms.
    """

    slug: str
    rationale: str

    @field_validator("slug")
    @classmethod
    def slug_format(cls, v: str) -> str:
        if not SLUG_PATTERN.match(v):
            raise ValueError(
                f"dependency slug {v!r} does not match kebab-case pattern "
                f"{SLUG_PATTERN.pattern!r}"
            )
        return v

    @field_validator("rationale")
    @classmethod
    def rationale_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("dependency rationale must not be empty")
        return v


class ComponentContent(BaseModel):
    """One component's full content: purpose, prototype evidence, scenarios,
    out-of-scope items, and dependency rationales.

    Joined to the registry entry in components.json by slug.
    """

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
                f"slug {v!r} does not match kebab-case pattern "
                f"{SLUG_PATTERN.pattern!r}"
            )
        return v

    @field_validator("purpose")
    @classmethod
    def purpose_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError(
                "purpose must not be empty; describe what this component "
                "does within the feature, scope, and boundaries"
            )
        return v

    @model_validator(mode="after")
    def out_of_scope_completeness(self) -> ComponentContent:
        # Either a non-empty list or a non-null reason. Mutually exclusive.
        # Silence (empty list, no reason) is rejected: an empty Out of Scope
        # reads as "the model didn't think about this" rather than "the
        # model thought about this and it's empty."
        has_items = bool(self.out_of_scope)
        has_reason = self.out_of_scope_reason is not None and self.out_of_scope_reason.strip()
        if not has_items and not has_reason:
            raise ValueError(
                f"component {self.slug!r}: out_of_scope is empty and "
                f"out_of_scope_reason is missing — silence is not allowed; "
                f"either populate out_of_scope or explain why it's empty "
                f"in out_of_scope_reason"
            )
        if has_items and has_reason:
            raise ValueError(
                f"component {self.slug!r}: out_of_scope and "
                f"out_of_scope_reason are mutually exclusive — use the "
                f"reason field only when out_of_scope is empty"
            )
        return self

    @model_validator(mode="after")
    def dependencies_completeness(self) -> ComponentContent:
        # Same pattern as out_of_scope_completeness.
        has_items = bool(self.dependencies)
        has_reason = self.dependencies_reason is not None and self.dependencies_reason.strip()
        if not has_items and not has_reason:
            raise ValueError(
                f"component {self.slug!r}: dependencies is empty and "
                f"dependencies_reason is missing — silence is not allowed; "
                f"either populate dependencies or explain why it's empty "
                f"in dependencies_reason"
            )
        if has_items and has_reason:
            raise ValueError(
                f"component {self.slug!r}: dependencies and "
                f"dependencies_reason are mutually exclusive — use the "
                f"reason field only when dependencies is empty"
            )
        return self

    @model_validator(mode="after")
    def security_performed_by_matches_self(self) -> ComponentContent:
        # R01 fix made structural: every security scenario in this
        # component's content must declare performed_by equal to this
        # component's own slug. Cross-component scenarios belong in the
        # other component's content.
        for s in self.security_scenarios:
            if s.performed_by != self.slug:
                raise ValueError(
                    f"component {self.slug!r}: security scenario "
                    f"{s.name!r} has performed_by={s.performed_by!r} "
                    f"which does not match the component's own slug "
                    f"{self.slug!r}; scenarios for actions performed by "
                    f"another component belong in that component's content"
                )
        return self

    @model_validator(mode="after")
    def dependency_no_self_reference(self) -> ComponentContent:
        for d in self.dependencies:
            if d.slug == self.slug:
                raise ValueError(
                    f"component {self.slug!r}: dependencies entry "
                    f"references itself ({d.slug!r}); a component cannot "
                    f"depend on itself"
                )
        return self


class Roadmap(BaseModel):
    """The roadmap.json artifact — per-component content for a feature.

    Phase 2 of the roadmap skill writes this file. Phase 3 validates it
    against this schema and against components.json (cross-file checks
    live in validate_roadmap.py).
    """

    schema_version: str = Field(pattern=r"^\d+\.\d+$")
    feature: str
    components: list[ComponentContent] = Field(min_length=1)

    @field_validator("feature")
    @classmethod
    def feature_slug_format(cls, v: str) -> str:
        if not SLUG_PATTERN.match(v):
            raise ValueError(
                f"feature {v!r} must match kebab-case slug pattern "
                f"{SLUG_PATTERN.pattern!r}"
            )
        return v

    @model_validator(mode="after")
    def slugs_unique(self) -> Roadmap:
        seen: set[str] = set()
        for c in self.components:
            if c.slug in seen:
                raise ValueError(
                    f"duplicate slug {c.slug!r}; every component slug must "
                    f"be unique within roadmap.json"
                )
            seen.add(c.slug)
        return self
