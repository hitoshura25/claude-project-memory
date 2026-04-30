#!/usr/bin/env python3
"""Validator for prototype-driven-roadmap output directories.

Run:
    uv run --with pydantic python validate_roadmap.py docs/roadmap/<feature>/

Exits:
    0 — all checks passed.
    1 — one or more validation failures (report written to stdout).
    2 — precondition failure (directory or required files missing).

The validator does three things:

  1. **Schema validation per file.** Loads components.json against the
     project's shipped components_schema.py; loads roadmap.json against
     the project's shipped roadmap_schema.py. Per-field and
     per-component invariants enforced by Pydantic surface here.

  2. **Cross-file invariants.** Checks that span both files:
       - feature name matches between files
       - component slug set matches between files
       - component array order matches between files
       - depends_on parity (registry depends_on ↔ roadmap dependencies)
       - OWASP id parity (registry owasp_categories ↔ roadmap
         security_scenarios owasp_id)
       - performed_by slugs are registered in components.json
       - out_of_scope.owner slugs are registered in components.json
       - design_doc_path / prototype_path resolve under the project root

  3. **Summary table on success.** Prints a human-readable scoreboard
     for sign-off (component, functional count, security count, OWASP
     categories).

The validator imports schemas from the project's *shipped copies*
rather than from this skill's source-of-truth scripts directory. This
way the validator validates "the schema as shipped," which is the same
contract downstream skills will see. If the shipped copies are missing,
the validator exits 2 with a precondition error rather than confusing
import failures.

Project root is derived from the roadmap directory's location: the
roadmap layout convention is `<project>/docs/roadmap/<feature>/`, so
project root is three levels up from the roadmap directory passed as
the script argument. The argument itself is interpreted as absolute or
relative-to-cwd per standard shell convention.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


# ---------------------------------------------------------------------------
# Schema loading
# ---------------------------------------------------------------------------

def load_schema_module(path: Path, module_name: str) -> ModuleType:
    """Dynamically import a Pydantic schema module from a project-shipped path.

    The module name is arbitrary (used only by importlib's bookkeeping);
    components_schema and roadmap_schema each get loaded under unique
    names so they don't collide in sys.modules.
    """
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not create import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# Cross-file checks
# ---------------------------------------------------------------------------

def check_cross_file(
    components: Any,  # components_schema.Components
    roadmap: Any,     # roadmap_schema.Roadmap
    project_root: Path,
) -> list[str]:
    """Run cross-file invariants. Returns a list of error strings; empty on
    success.

    Each error string is self-describing: names the file or component
    involved and the rule that was violated.
    """
    errors: list[str] = []

    # External path resolution (registry-only fields)
    design_doc_abs = project_root / components.design_doc_path
    if not design_doc_abs.is_file():
        errors.append(
            f"components.json: design_doc_path "
            f"'{components.design_doc_path}' does not resolve to a file "
            f"under {project_root} (looked at {design_doc_abs})"
        )
    prototype_abs = project_root / components.prototype_path
    if not prototype_abs.is_dir():
        errors.append(
            f"components.json: prototype_path "
            f"'{components.prototype_path}' does not resolve to a directory "
            f"under {project_root} (looked at {prototype_abs})"
        )

    # Feature name parity
    if components.feature != roadmap.feature:
        errors.append(
            f"feature mismatch: components.json='{components.feature}' "
            f"vs roadmap.json='{roadmap.feature}'"
        )

    # Slug-set parity
    reg_slugs = {c.slug for c in components.components}
    roadmap_slugs = {c.slug for c in roadmap.components}
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

    # Array order parity (only meaningful when slug sets match)
    reg_order = [c.slug for c in components.components]
    roadmap_order = [c.slug for c in roadmap.components]
    if set(reg_order) == set(roadmap_order) and reg_order != roadmap_order:
        errors.append(
            f"component array order differs between files. "
            f"components.json: {reg_order}; "
            f"roadmap.json: {roadmap_order}. "
            f"Both must be in topological order, roots first."
        )

    # Per-component cross-file checks
    reg_by_slug = {c.slug: c for c in components.components}
    for content in roadmap.components:
        if content.slug not in reg_by_slug:
            continue  # already reported above as slug-set mismatch
        reg = reg_by_slug[content.slug]

        # depends_on parity (registry depends_on ↔ roadmap dependencies)
        roadmap_dep_slugs = {d.slug for d in content.dependencies}
        registry_dep_slugs = set(reg.depends_on)
        if roadmap_dep_slugs != registry_dep_slugs:
            only_registry = registry_dep_slugs - roadmap_dep_slugs
            only_roadmap = roadmap_dep_slugs - registry_dep_slugs
            if only_registry:
                errors.append(
                    f"component '{content.slug}': depends_on parity "
                    f"violation. components.json lists {sorted(only_registry)} "
                    f"in depends_on but roadmap.json dependencies does not"
                )
            if only_roadmap:
                errors.append(
                    f"component '{content.slug}': depends_on parity "
                    f"violation. roadmap.json dependencies lists "
                    f"{sorted(only_roadmap)} but components.json depends_on "
                    f"does not"
                )

        # OWASP id parity (registry owasp_categories ↔ scenario owasp_ids)
        cited_ids = {s.owasp_id for s in content.security_scenarios}
        registered_ids = set(reg.owasp_categories)
        only_registered = registered_ids - cited_ids
        only_cited = cited_ids - registered_ids
        if only_registered:
            errors.append(
                f"component '{content.slug}': OWASP ids in components.json "
                f"owasp_categories but not cited in any security scenario: "
                f"{sorted(only_registered)}"
            )
        if only_cited:
            errors.append(
                f"component '{content.slug}': OWASP ids cited in security "
                f"scenarios but not registered in components.json "
                f"owasp_categories: {sorted(only_cited)}"
            )

        # performed_by slug must be registered
        for scenario in content.security_scenarios:
            if scenario.performed_by not in reg_slugs:
                errors.append(
                    f"component '{content.slug}', scenario "
                    f"'{scenario.name}': performed_by="
                    f"'{scenario.performed_by}' is not a registered slug "
                    f"in components.json"
                )

        # out_of_scope.owner slug must be registered when present
        for ooss in content.out_of_scope:
            if ooss.owner is not None and ooss.owner not in reg_slugs:
                concern_preview = (
                    ooss.concern[:40] + "…"
                    if len(ooss.concern) > 40
                    else ooss.concern
                )
                errors.append(
                    f"component '{content.slug}', out_of_scope item "
                    f"'{concern_preview}': owner='{ooss.owner}' is not a "
                    f"registered slug in components.json"
                )

    # Schema-version range check
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

    return errors


# ---------------------------------------------------------------------------
# Summary table (success path)
# ---------------------------------------------------------------------------

def print_summary(components: Any, roadmap: Any, roadmap_dir: Path) -> None:
    """Print a markdown-style summary table to stdout."""
    reg_by_slug = {c.slug: c for c in components.components}
    print(f"Roadmap Validation: {components.feature} — PASS\n")
    print("| Component | Functional | Security | OWASP categories |")
    print("|-----------|-----------:|---------:|------------------|")
    for content in roadmap.components:
        reg = reg_by_slug[content.slug]
        owasp = ", ".join(reg.owasp_categories) if reg.owasp_categories else "—"
        print(
            f"| {content.slug} | {len(content.functional_scenarios)} "
            f"| {len(content.security_scenarios)} | {owasp} |"
        )
    print(f"\nOutput directory: {roadmap_dir}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(
            "usage: validate_roadmap.py <roadmap_dir>",
            file=sys.stderr,
        )
        return 2

    # Argument may be absolute or relative-to-cwd; resolve to absolute.
    roadmap_dir = Path(argv[1]).resolve()
    if not roadmap_dir.is_dir():
        print(
            f"directory not found: {roadmap_dir}",
            file=sys.stderr,
        )
        return 2

    components_json = roadmap_dir / "components.json"
    roadmap_json = roadmap_dir / "roadmap.json"
    components_schema_path = roadmap_dir / "components_schema.py"
    roadmap_schema_path = roadmap_dir / "roadmap_schema.py"

    # Preflight: required files
    missing: list[Path] = []
    for f in (components_json, roadmap_json, components_schema_path, roadmap_schema_path):
        if not f.is_file():
            missing.append(f)
    if missing:
        print("Required files missing:", file=sys.stderr)
        for f in missing:
            print(f"  - {f}", file=sys.stderr)
        print(
            "\nThe roadmap directory must contain components.json, "
            "roadmap.json, components_schema.py, and roadmap_schema.py. "
            "The schema files are copied into the project by the roadmap "
            "skill at Phase 3.",
            file=sys.stderr,
        )
        return 2

    # Project root: roadmap dir is at <root>/docs/roadmap/<feature>/.
    # Three levels up gives the project root.
    project_root = roadmap_dir.parent.parent.parent

    # Load schema modules from the project's shipped copies
    try:
        cs_module = load_schema_module(
            components_schema_path, "_proj_components_schema"
        )
    except Exception as e:
        print(
            f"failed to load {components_schema_path}: {e}",
            file=sys.stderr,
        )
        return 2
    try:
        rs_module = load_schema_module(
            roadmap_schema_path, "_proj_roadmap_schema"
        )
    except Exception as e:
        print(
            f"failed to load {roadmap_schema_path}: {e}",
            file=sys.stderr,
        )
        return 2

    # Per-file schema validation
    errors: list[str] = []
    components = None
    roadmap = None

    try:
        components = cs_module.Components.model_validate_json(
            components_json.read_text()
        )
    except Exception as e:
        errors.append(f"components.json validation failed:\n{e}")

    try:
        roadmap = rs_module.Roadmap.model_validate_json(
            roadmap_json.read_text()
        )
    except Exception as e:
        errors.append(f"roadmap.json validation failed:\n{e}")

    if components is None or roadmap is None:
        # Schema-level errors mean we can't run cross-file checks
        # safely. Print what we have and exit 1.
        print(f"Roadmap validation FAILED. {len(errors)} error(s):\n")
        for err in errors:
            print(f"  - {err}\n")
        return 1

    # Cross-file invariants
    errors.extend(check_cross_file(components, roadmap, project_root))

    if errors:
        print(f"Roadmap validation FAILED. {len(errors)} error(s):\n")
        for err in errors:
            print(f"  - {err}\n")
        return 1

    # Success
    print_summary(components, roadmap, roadmap_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
