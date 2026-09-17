"""Clip brackets that carry a Hue gradient lightstrip around a TV.

See README.md in this folder for the design, printing and assembly.
"""

from pathlib import Path

from printing3d.registry import Project

NAME = "hue-tv-brackets"
SUMMARY = "Adhesive-free clip brackets for a Hue gradient lightstrip around a TV"
LOCKED = Path(__file__).parent / "LOCKED.txt"
MEASURED = Path(__file__).parent / "MEASURED.txt"
CONFIG = Path(__file__).parent / "parts.toml"


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
        verify_trials=lambda: _checks().verify_trials(),
        lock=LOCKED,
        measured=MEASURED,
        config=CONFIG,
    )


def _catalog():
    from printing3d.hue_tv_brackets import catalog

    return catalog


def _checks():
    from printing3d.hue_tv_brackets import verify

    return verify
