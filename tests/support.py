"""Helpers shared by every project's tests.

Plain functions rather than fixtures, so they read as ordinary calls at the
point of use. Fixtures belong in conftest.py.
"""

import hashlib
from pathlib import Path


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def locked_hashes(locked_file: Path) -> dict[str, str]:
    """Parse a `shasum -a 256` file into {filename: digest}."""
    hashes = {}
    for line in locked_file.read_text().splitlines():
        if line.strip():
            digest, path = line.split()
            hashes[Path(path).name] = digest
    return hashes


def contour_digest(cross_section) -> str:
    """A fingerprint of every vertex in a 2D profile, in order."""
    fingerprint = hashlib.sha256()
    for contour in cross_section.to_polygons():
        for u, v in contour:
            fingerprint.update(f"{u:.9g},{v:.9g};".encode())
    return fingerprint.hexdigest()[:16]
