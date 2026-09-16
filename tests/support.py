"""Helpers shared by every project's tests.

Plain functions rather than fixtures, so they read as ordinary calls at the
point of use. Fixtures belong in conftest.py.
"""

import hashlib
import os
from pathlib import Path

from printing3d.parts import digest_of

# The kit already spells this, and a second spelling is a second thing that can
# drift from what the lock actually holds.
sha256_of = digest_of


def locked_hashes(locked_file: Path) -> dict[str, str]:
    """Parse a `shasum -a 256` file into {filename: digest}."""
    hashes = {}
    for line in locked_file.read_text().splitlines():
        if line.strip():
            digest, path = line.split()
            hashes[Path(path).name] = digest
    return hashes


def guarding_main() -> bool:
    """Is this the run that stands between a change and `main`?

    Reads the target branch of the pull request being checked, which the
    automation sets on that event and no other. The generic "this is
    automation" marker will not do: the scheduled upgrade check runs the same
    suite and sets it too, and that run guards nothing -- failing it there
    would report a project mid-design as though a dependency had broken.

    Only two kinds of run matter here and they want different things. A working
    copy is where a project is still being worked out, and a rule that stops
    the suite running while that is true costs more than it protects. `main` is
    where the same rule holds without exception, because that is what anyone
    cloning gets.
    """
    return os.environ.get("GITHUB_BASE_REF") == "main"


def contour_digest(cross_section) -> str:
    """A fingerprint of every vertex in a 2D profile, in order."""
    fingerprint = hashlib.sha256()
    for contour in cross_section.to_polygons():
        for u, v in contour:
            fingerprint.update(f"{u:.9g},{v:.9g};".encode())
    return fingerprint.hexdigest()[:16]


def objections_to(check, *arguments):
    """What a check complains about when handed `arguments`.

    Shared because both projects' negative suites need exactly this and wrote
    it identically. The architecture test would have failed on that in `src/`;
    it does not look at `tests/`, so it was noticed by a sweep instead.
    """
    from printing3d.checks import CheckRunner

    runner = CheckRunner()
    check(runner, *arguments)
    return runner.failures
