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
import io
from collections.abc import Callable

from printing3d.parts import digest_of, existing_stls, output_base

DIGEST_GAP = "  "  # what `shasum -a 256` puts between a digest and its path


def hashes_of(project: str) -> str:
    """Every STL the project has on disk, as `shasum -a 256` would write them."""
    alongside_output = output_base().parent
    return "".join(
        f"{digest_of(path)}{DIGEST_GAP}{path.relative_to(alongside_output)}\n"
        for path in existing_stls(project)
    )


def measurements_from(run_checks: Callable[[], bool]) -> tuple[bool, str]:
    """Whether the pre-print checks passed, and what they reported.

    Both halves, because a caller writing a lock needs the verdict as much as
    the text: a record of a failing run is not a record of anything. Takes the
    checks rather than the project so that the lock and the test comparing
    against it reach the measurements by the same path.
    """
    spoken = io.StringIO()
    with contextlib.redirect_stdout(spoken):
        passed = run_checks()
    return passed, spoken.getvalue()
