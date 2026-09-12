"""Dependency direction: the shared kit must not know about any project.

The kit is reusable only as long as it carries no project's assumptions. A
single import from a project package is how that erodes, so it is checked
rather than left to discipline.
"""

import ast
import pkgutil
from pathlib import Path

import printing3d

CORE = Path(printing3d.__file__).parent
PROJECT_PACKAGES = {
    module.name for module in pkgutil.iter_modules(printing3d.__path__) if module.ispkg
}


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


def test_project_packages_are_discovered():
    """Guards the check below from passing because nothing was found."""
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
