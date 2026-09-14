"""What a 3D-printing project must declare, and how they are found.

A project is discovered by existing: any subpackage that declares itself is
picked up, so adding one touches only that project's own files. Nothing here
knows what any particular project makes.

Declarations are cheap on purpose. A project's package exposes its descriptor
with callables that import lazily, so listing every project does not import
every project's geometry -- only the one actually being built.
"""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

DECLARATION = "project"  # the attribute a project package exposes


@dataclass(frozen=True)
class Project:
    """One 3D-printing project, and everything the repo needs from it.

    Every field is required. A project that cannot say what it ships, pin what
    it has shipped, pin what its parts measured, check that they are sound, or
    point at the file its numbers come from has no business shipping them, so
    there is no way to declare a partial one.
    """

    name: str
    summary: str
    parts: Callable[[], Iterator]
    build: Callable[[], bool]
    verify: Callable[[], bool]
    lock: Path
    measured: Path
    config: Path


def discover() -> dict[str, Project]:
    """Every declared project, by name."""
    import printing3d

    found = {}
    for module in pkgutil.iter_modules(printing3d.__path__):
        if not module.ispkg:
            continue
        package = importlib.import_module(f"printing3d.{module.name}")
        declaration = getattr(package, DECLARATION, None)
        if declaration is None:
            continue
        project = declaration() if callable(declaration) else declaration
        found[project.name] = project
    return dict(sorted(found.items()))
