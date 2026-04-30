"""Pydantic schema for components.json — the roadmap registry artifact.

Owned by the prototype-driven-roadmap skill. The source of truth for this file
lives at:

    ~/claude-devtools/skills/prototype-driven-roadmap/scripts/components_schema.py

At Phase 3 of the roadmap skill, this file is copied into each project's
roadmap output directory at:

    <project>/docs/roadmap/<feature>/components_schema.py

Downstream skills (e.g., prototype-driven-task-decomposition) import from the
project-shipped copy rather than reaching back into this skill's directory.
This keeps each skill self-contained and avoids cross-skill imports.

components.json is the registry of components for a feature: which components
exist, what they're called, what they depend on, and which OWASP categories
apply to each. The per-component scenarios and content live in roadmap.json
(see roadmap_schema.py); component slug is the foreign key joining the two
files.

The schema enforces what each file owns alone. Cross-file invariants
(roadmap.json's slug set matches components.json's; depends_on parity between
files; OWASP id set parity between registry and scenarios) live in
validate_roadmap.py because they require both files loaded.

Dependency semantics: `depends_on` represents *structural* dependencies — one
component's code imports from or interfaces with another component's code.
Operational ordering (e.g., "infrastructure must be running before runtime
components can execute") is conveyed by array order, not by depends_on.
A component listed earlier in the array but not in any later component's
depends_on is an upstream precondition; a component in depends_on is a code-
level dependency.
"""
from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator, model_validator

# Slugs are kebab-case, start with a lowercase letter, and end with a letter
# or digit (so "abc-" or "-abc" are rejected). Minimum two characters.
SLUG_PATTERN = re.compile(r"^[a-z][a-z0-9-]*[a-z0-9]$")

# OWASP requirement id formats from the ASVS and MASVS specifications.
# Examples: "ASVS V5.1.3", "MASVS-STORAGE-1".
ASVS_PATTERN = re.compile(r"^ASVS V\d+\.\d+\.\d+$")
MASVS_PATTERN = re.compile(r"^MASVS-[A-Z]+-\d+$")


class ComponentRegistryEntry(BaseModel):
    """A single component's registry entry.

    Carries the structural facts about the component (slug, display name,
    structural dependencies, OWASP categories). Per-component scenarios and
    prose content live in roadmap.json, joined by slug.
    """

    slug: str
    name: str
    depends_on: list[str] = Field(default_factory=list)
    owasp_categories: list[str] = Field(default_factory=list)

    @field_validator("slug")
    @classmethod
    def slug_format(cls, v: str) -> str:
        if not SLUG_PATTERN.match(v):
            raise ValueError(
                f"slug {v!r} does not match kebab-case pattern "
                f"{SLUG_PATTERN.pattern!r}; slugs must start with a lowercase "
                f"letter, contain only lowercase letters, digits, and hyphens, "
                f"and end with a letter or digit"
            )
        return v

    @field_validator("name")
    @classmethod
    def name_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be empty or whitespace-only")
        return v

    @field_validator("depends_on")
    @classmethod
    def depends_on_slug_format(cls, v: list[str]) -> list[str]:
        for entry in v:
            if not SLUG_PATTERN.match(entry):
                raise ValueError(
                    f"depends_on entry {entry!r} does not match kebab-case "
                    f"slug pattern {SLUG_PATTERN.pattern!r}"
                )
        return v

    @field_validator("owasp_categories")
    @classmethod
    def owasp_id_format(cls, v: list[str]) -> list[str]:
        for entry in v:
            if not (ASVS_PATTERN.match(entry) or MASVS_PATTERN.match(entry)):
                raise ValueError(
                    f"owasp_categories entry {entry!r} does not match "
                    f"'ASVS V<n>.<n>.<n>' (e.g. 'ASVS V5.1.3') or "
                    f"'MASVS-<CATEGORY>-<n>' (e.g. 'MASVS-STORAGE-1')"
                )
        return v

    @model_validator(mode="after")
    def no_self_reference(self) -> ComponentRegistryEntry:
        if self.slug in self.depends_on:
            raise ValueError(
                f"component {self.slug!r} lists itself in depends_on; "
                f"depends_on must reference other components"
            )
        return self


class Components(BaseModel):
    """The components.json artifact — registry for a feature's roadmap.

    Phase 1 of the roadmap skill writes this file after user approval of the
    proposed component set, slugs, and OWASP categories. Phase 2 reads it as
    the authoritative input for generating roadmap.json content.
    """

    schema_version: str = Field(pattern=r"^\d+\.\d+$")
    feature: str
    design_doc_path: str
    prototype_path: str
    components: list[ComponentRegistryEntry] = Field(min_length=1)

    @field_validator("feature")
    @classmethod
    def feature_slug_format(cls, v: str) -> str:
        if not SLUG_PATTERN.match(v):
            raise ValueError(
                f"feature {v!r} must match kebab-case slug pattern "
                f"{SLUG_PATTERN.pattern!r}"
            )
        return v

    @field_validator("design_doc_path")
    @classmethod
    def design_doc_path_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("design_doc_path must not be empty")
        return v

    @field_validator("prototype_path")
    @classmethod
    def prototype_path_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("prototype_path must not be empty")
        return v

    @model_validator(mode="after")
    def slugs_unique(self) -> Components:
        seen: set[str] = set()
        for c in self.components:
            if c.slug in seen:
                raise ValueError(
                    f"duplicate slug {c.slug!r}; every component slug must "
                    f"be unique within components.json"
                )
            seen.add(c.slug)
        return self

    @model_validator(mode="after")
    def depends_on_resolves(self) -> Components:
        registered = {c.slug for c in self.components}
        for c in self.components:
            for dep in c.depends_on:
                if dep not in registered:
                    raise ValueError(
                        f"component {c.slug!r} depends_on {dep!r} which is "
                        f"not a registered slug; depends_on must reference "
                        f"other components in this same components.json"
                    )
        return self

    @model_validator(mode="after")
    def topological_order(self) -> Components:
        # Every component's depends_on entries must appear earlier in the
        # array than the component itself. This makes array order convey
        # topological order without an explicit field, and catches cycles
        # naturally — a cycle requires at least one forward reference.
        #
        # depends_on is *structural*: code-level imports / interface
        # dependencies. Operational preconditions (e.g., "infrastructure
        # must be up first") are conveyed by array order alone, with
        # depends_on left empty.
        position = {c.slug: i for i, c in enumerate(self.components)}
        for c in self.components:
            for dep in c.depends_on:
                if position[dep] >= position[c.slug]:
                    raise ValueError(
                        f"component {c.slug!r} at position "
                        f"{position[c.slug]} depends on {dep!r} at position "
                        f"{position[dep]}; components must be listed in "
                        f"topological order, with each component's "
                        f"structural dependencies appearing earlier in the "
                        f"array (a forward or self-reference indicates a "
                        f"cycle or out-of-order entry)"
                    )
        return self
