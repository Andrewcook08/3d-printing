"""Low-profile wall mounts for horizontal fishing rod storage.

See README.md in this folder for printing and hanging instructions.
"""

from pathlib import Path

from printing3d.registry import Project

NAME = "fishing-rod-mounts"
SUMMARY = "Low-profile wall mounts for horizontal fishing rod storage"
LOCKED = Path(__file__).parent / "LOCKED.txt"


def project() -> Project:
    """This project's declaration.

    Identity is available without importing any geometry; the callables pull
    their modules in only when something actually asks for parts.
    """
    return Project(
        name=NAME,
        summary=SUMMARY,
        parts=lambda: _catalog().parts(),
        build=lambda: _catalog().build_all(),
        verify=lambda: _checks().verify_all(),
        lock=LOCKED,
    )


def _catalog():
    from printing3d.fishing_rod_mounts import catalog

    return catalog


def _checks():
    from printing3d.fishing_rod_mounts import verify

    return verify
