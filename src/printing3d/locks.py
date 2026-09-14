"""The two records of what a project last shipped.

One pins the bytes of every STL it produced. The other pins what the pre-print
checks measured of those same solids, which the bytes alone do not cover: a
shared helper can change what a check *measures* without moving a single
vertex, and then nothing downstream notices.

They are written together because they are one claim read two ways -- a shape,
and what that shape measures. Nothing here knows what any project makes.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
from collections.abc import Callable
from pathlib import Path

from printing3d.parts import existing_stls, output_base

DIGEST_GAP = "  "  # what `shasum -a 256` puts between a digest and its path


def hashes_of(project: str) -> str:
    """Every STL the project has on disk, as `shasum -a 256` would write them."""
    alongside_output = output_base().parent
    return "".join(
        f"{_digest(path)}{DIGEST_GAP}{path.relative_to(alongside_output)}\n"
        for path in existing_stls(project)
    )


def measurements_from(run_checks: Callable[[], bool]) -> str:
    """What the pre-print checks report, captured instead of printed.

    Takes the checks rather than the project so that the lock and the test that
    compares against it reach the measurements the same way.
    """
    spoken = io.StringIO()
    with contextlib.redirect_stdout(spoken):
        run_checks()
    return spoken.getvalue()


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
