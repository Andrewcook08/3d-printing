"""Command line for the whole repo.

    build                       # every project
    build <project>             # one project
    verify                      # geometric checks before printing
    relock                      # re-pin what a project ships, after a change

Projects are discovered, not listed here. To add one, declare it in your own
package -- see docs/build/project-contract.md. This file never changes.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable

from printing3d.locks import hashes_of, measurements_from
from printing3d.parts import (
    DEFAULT_OUTPUT_DIR,
    OUTPUT_DIR_ENV,
    output_base,
    output_dir,
    repo_root,
)
from printing3d.registry import Project, discover


def build(argv: list[str] | None = None) -> int:
    """Entry point for `build`."""
    return _run(argv, verb="build", step=lambda project: project.build)


def verify(argv: list[str] | None = None) -> int:
    """Entry point for `verify`."""
    return _run(argv, verb="verify", step=lambda project: project.verify)


def relock(argv: list[str] | None = None) -> int:
    """Entry point for `relock`."""
    if output_base() != repo_root() / DEFAULT_OUTPUT_DIR:
        print(
            f"refusing to re-lock while {OUTPUT_DIR_ENV} is set: the paths "
            f"written into the lock would not be the ones it is read back with"
        )
        return 1
    # Naming a project is required here, unlike build and verify. Those read;
    # this one overwrites two committed records, and the version that defaults
    # to everything re-pins the whole repo for anyone who types it bare.
    return _run(argv, verb="relock", step=_repin, projects_required=True)


def _repin(project: Project) -> Callable[[], bool]:
    """Rebuild one project and pin both records, if it earns them.

    Rebuilding first keeps the lock honest: one taken over whatever happened to
    be sitting in the output directory pins a shape nobody can reproduce.

    Nothing is written unless the build is sound AND its checks pass. A lock
    records something that was right, and a record of a failing run is a record
    of nothing -- worse than nothing, because every gate downstream then agrees
    with it. Re-locking answers a change you meant, never a failure you did not.
    """

    def pin() -> bool:
        if not project.build():
            print("\nnot re-pinned: the build is not sound")
            return False
        passed, measurements = measurements_from(project.verify)
        if not passed:
            print("\nnot re-pinned: the checks do not pass")
            return False
        project.lock.write_text(hashes_of(project.name))
        project.measured.write_text(measurements)
        print(f"\nre-pinned {project.lock.name} and {project.measured.name}")
        return True

    return pin


def _run(argv, verb, step, projects_required=False) -> int:
    projects = discover()
    args = _parse_args(argv, verb, projects, projects_required)
    ok = True
    for name in args.projects or projects:
        project = projects[name]
        print(f"\n=== {name} ===")
        ok &= step(project)()
        if verb == "build":
            print(f"\nWritten to {output_dir(name)}")
    if not ok:
        print("\nGEOMETRY PROBLEM -- do not print.")
    return 0 if ok else 1


def _parse_args(argv, verb: str, projects: dict[str, Project], required=False):
    parser = argparse.ArgumentParser(
        prog=verb,
        description=f"{verb.capitalize()} 3D-printing projects.",
        epilog="\n".join(
            f"  {name}  {project.summary}" for name, project in projects.items()
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "projects",
        nargs="+" if required else "*",
        metavar="PROJECT",
        help=f"projects to {verb}" + ("" if required else "; defaults to all"),
    )
    args = parser.parse_args(argv)
    for name in args.projects:
        if name not in projects:
            parser.error(f"unknown project {name!r}; choose from {', '.join(projects)}")
    return args
