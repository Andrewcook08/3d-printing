"""Command line for the whole repo.

    build                       # every project
    build <project>             # one project
    verify                      # geometric checks before printing

Projects are discovered, not listed here. To add one, declare it in your own
package -- see docs/build/project-contract.md. This file never changes.
"""

from __future__ import annotations

import argparse

from printing3d.parts import output_dir
from printing3d.registry import Project, discover


def build(argv: list[str] | None = None) -> int:
    """Entry point for `build`."""
    return _run(argv, verb="build", step=lambda project: project.build)


def verify(argv: list[str] | None = None) -> int:
    """Entry point for `verify`."""
    return _run(argv, verb="verify", step=lambda project: project.verify)


def _run(argv, verb, step) -> int:
    projects = discover()
    args = _parse_args(argv, verb, projects)
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


def _parse_args(argv, verb: str, projects: dict[str, Project]):
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
        nargs="*",
        metavar="PROJECT",
        help=f"projects to {verb}; defaults to all",
    )
    args = parser.parse_args(argv)
    for name in args.projects:
        if name not in projects:
            parser.error(f"unknown project {name!r}; choose from {', '.join(projects)}")
    return args
