"""Command line for the whole repo.

    uv run build                       # every project
    uv run build fishing-rod-mounts    # one project
    uv run verify                      # geometric checks before printing

To add a project: create `src/printing3d/<your_project>/`, give it a module
that can build its parts and (optionally) verify them, then add one entry to
PROJECTS below. Nothing else in this file needs to change.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass

from printing3d.parts import output_dir


@dataclass(frozen=True)
class Project:
    """One 3D-printing project, and how to drive it.

    The callables are looked up lazily by name so that `uv run build` for one
    project does not import every other project's geometry.
    """

    name: str
    summary: str
    build: Callable[[], bool]
    verify: Callable[[], bool] | None = None


def _fishing_rod_mounts() -> Project:
    from printing3d.fishing_rod_mounts import catalog, verify

    return Project(
        name=catalog.PROJECT,
        summary="Low-profile wall mounts for horizontal fishing rod storage",
        build=catalog.build_all,
        verify=verify.verify_all,
    )


PROJECTS: dict[str, Callable[[], Project]] = {
    "fishing-rod-mounts": _fishing_rod_mounts,
}


def build(argv: list[str] | None = None) -> int:
    """Entry point for `uv run build`."""
    return _run(argv, action="build", verb="build")


def verify(argv: list[str] | None = None) -> int:
    """Entry point for `uv run verify`."""
    return _run(argv, action="verify", verb="verify")


def _run(argv: list[str] | None, action: str, verb: str) -> int:
    args = _parse_args(argv, verb)
    ok = True
    for name in args.projects or sorted(PROJECTS):
        project = PROJECTS[name]()
        step = getattr(project, action)
        if step is None:
            print(f"{name}: nothing to {verb}")
            continue
        print(f"\n=== {name} ===")
        ok &= step()
        if action == "build":
            print(f"\nWritten to {output_dir(name)}")
    if not ok:
        print("\nGEOMETRY PROBLEM -- do not print.")
    return 0 if ok else 1


def _parse_args(argv: list[str] | None, verb: str) -> argparse.Namespace:
    known = sorted(PROJECTS)
    parser = argparse.ArgumentParser(
        prog=verb, description=f"{verb.capitalize()} 3D-printing projects."
    )
    parser.add_argument(
        "projects",
        nargs="*",
        metavar="PROJECT",
        help=f"projects to {verb}; defaults to all. One of: {', '.join(known)}",
    )
    args = parser.parse_args(argv)
    for name in args.projects:
        if name not in PROJECTS:
            parser.error(f"unknown project {name!r}; choose from {', '.join(known)}")
    return args
