"""Architecture rules about the boundary between the shared kit and projects.

Three rules. The kit is reusable only as long as it carries no project's
assumptions, so it may not import one. A helper that two projects both need
belongs in the kit rather than in each of them. And a helper the kit already
offers should be called, not rewritten beside it.

All three erode silently -- the first with a single import, the others with a
single forgotten copy -- so all three are checked rather than left to
discipline.

Detection is by name, which has a known blind spot: a copy that arrives under a
different name passes. The docstring marker described in CLAUDE.md is what
covers that case, and these tests are the backstop for when it is missed.
"""

import ast
import pkgutil
from pathlib import Path

import printing3d

CORE = Path(printing3d.__file__).parent
PROJECT_PACKAGES = {
    module.name for module in pkgutil.iter_modules(printing3d.__path__) if module.ispkg
}

# The names the registry wires up. Every project must define these, so two
# projects sharing one is the contract being met, not duplication.
CONTRACT_ROLES = frozenset({"project", "parts", "build_all", "verify_all"})

# Words every project uses for the same idea: the shape it describes, the solid
# it builds from that shape, the checks it runs, and the two shapes its config
# file takes -- the measured numbers, and the parts asked for. Sharing one of
# these is the house style, not duplication: two projects' Designs hold entirely
# different fields, so there is nothing to promote and nothing being hidden.
#
# `build` is also what the shared command is called, so a project's own build
# function is expected to sit alongside it rather than clash with it.
SHARED_VOCABULARY = frozenset({"profile", "build", "verify", "Design", "Catalogue"})
ROLE_PREFIXES = ("check_",)

ROLES = CONTRACT_ROLES | SHARED_VOCABULARY


def imported_modules(source: Path):
    """Every module name imported by a source file."""
    tree = ast.parse(source.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


def core_modules():
    """The shared kit: every module directly under the package root."""
    return sorted(CORE.glob("*.py"))


def plays_a_role(name):
    """Is this a name every project is expected to define?"""
    return name in ROLES or name.startswith(ROLE_PREFIXES)


def public_helpers(source: Path):
    """Top-level functions and classes a module offers under a public name.

    Constants are left out on purpose: two projects naming a dimension the same
    thing is a shared vocabulary, not a shared helper.
    """
    tree = ast.parse(source.read_text())
    return {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
        and not node.name.startswith("_")
        and not plays_a_role(node.name)
    }


def helpers_by_project():
    """Every project's helper names, by project."""
    return {
        package: {
            name
            for source in sorted((CORE / package).glob("*.py"))
            for name in public_helpers(source)
        }
        for package in sorted(PROJECT_PACKAGES)
    }


def shared_names(by_project):
    """Names defined by more than one project, each with the projects defining it."""
    owners: dict[str, list[str]] = {}
    for package, names in sorted(by_project.items()):
        for name in names:
            owners.setdefault(name, []).append(package)
    return {name: packages for name, packages in owners.items() if len(packages) > 1}


def test_project_packages_are_discovered():
    """Guards the checks below from passing because nothing was found."""
    assert PROJECT_PACKAGES


def test_the_shared_kit_never_imports_a_project():
    offenders = []
    for source in core_modules():
        for name in imported_modules(source):
            leaf = name.removeprefix("printing3d.").split(".")[0]
            if leaf in PROJECT_PACKAGES:
                offenders.append(f"{source.name} imports {name}")
    assert not offenders, "the shared kit must not depend on a project: " + "; ".join(
        offenders
    )


def test_a_helper_defined_by_two_projects_is_reported():
    """Guards the rule below from passing because nothing was ever compared."""
    duplicated = shared_names(
        {"alpha": {"radial_section"}, "beta": {"radial_section", "fillet"}}
    )
    assert duplicated == {"radial_section": ["alpha", "beta"]}


def test_a_helper_defined_by_one_project_is_left_alone():
    assert shared_names({"alpha": {"radial_section"}, "beta": {"fillet"}}) == {}


def test_the_names_every_project_plays_are_not_helpers():
    assert plays_a_role("build_all")
    assert plays_a_role("check_solid_is_printable")
    assert not plays_a_role("radial_section")


def test_no_helper_is_defined_by_two_projects():
    duplicated = shared_names(helpers_by_project())
    assert not duplicated, (
        "the same helper in two projects belongs in the shared kit: "
        + "; ".join(
            f"{name} in {' and '.join(owners)}" for name, owners in duplicated.items()
        )
    )


def kit_helpers():
    """Helper names the shared kit already offers."""
    return {name for source in core_modules() for name in public_helpers(source)}


def test_the_kit_offers_helpers_to_collide_with():
    """Guards the rule below from passing because nothing was found."""
    assert kit_helpers()


def test_no_project_rewrites_a_helper_the_kit_already_has():
    offenders = {
        f"{package}.{name}"
        for package, names in helpers_by_project().items()
        for name in names & kit_helpers()
    }
    assert not offenders, (
        "the shared kit already offers these; call them rather than rewriting "
        "them beside it: " + ", ".join(sorted(offenders))
    )
