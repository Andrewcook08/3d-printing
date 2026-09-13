"""Architecture rules about the boundary between the shared kit and projects.

The kit is reusable only as long as it carries no project's assumptions, so it
may not import one. And a helper that two projects both need belongs in the
kit rather than in each of them, so the same helper name appearing in two
projects is read as a promotion that has not happened yet.

Both erode silently -- the first with a single import, the second with a
single forgotten copy -- so both are checked rather than left to discipline.
"""

import ast
import pkgutil
from pathlib import Path

import printing3d

CORE = Path(printing3d.__file__).parent
PROJECT_PACKAGES = {
    module.name for module in pkgutil.iter_modules(printing3d.__path__) if module.ispkg
}

# Names every project is expected to offer: how a project plugs into the build,
# and the checks it runs. Two projects sharing one of these is the design
# working, not duplication.
ROLES = frozenset(
    {"project", "parts", "profile", "build", "build_all", "verify", "verify_all"}
)
ROLE_PREFIXES = ("check_",)


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
