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

    Continuous integration here has exactly one trigger -- a pull request to
    `main` -- so the marker it sets is the question, not a proxy for it.
    Nothing local sets it.

    Only two kinds of run exist, and they want different things. A working copy
    is where a project is still being worked out, and a rule that stops the
    suite running while that is true costs more than it protects. `main` is
    where the same rule has to hold without exception, because that is what
    anyone cloning gets.
    """
    return os.environ.get("CI") == "true"


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
