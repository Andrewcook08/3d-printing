"""What a printable part is, and where its STL lands.

Every project in this repo produces `Part`s. `build_project` writes them into
`output/<project>/`, so the whole repo's printable output sits in one place no
matter which project produced it.
"""

from __future__ import annotations

import hashlib
import os
import shutil
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from manifold3d import Error, Manifold

from printing3d.stl import triangle_count, write_stl

OUTPUT_DIR_ENV = "PRINTING3D_OUTPUT"
DEFAULT_OUTPUT_DIR = "output"

# Parts a project has stopped declaring are moved here rather than deleted,
# so a shape can be recovered without going through git. Kept inside the
# output root so that redirecting output redirects the archive with it.
ARCHIVE_DIR = "archive"
TRIALS_DIR = "trials"  # parts being tested; never committed, never locked


@dataclass(frozen=True)
class Part:
    """One printable solid, and the name it ships under.

    The name is used for both the STL filename and the label embedded in the
    file's header, so it is part of the file's bytes -- renaming a part changes
    its hash.
    """

    name: str
    solid: Manifold

    @property
    def filename(self) -> str:
        return f"{self.name}.stl"

    @property
    def is_sound(self) -> bool:
        """Watertight, error-free, and a single connected body."""
        return self.solid.status() == Error.NoError and len(self.solid.decompose()) == 1

    def summary(self) -> str:
        lo_x, lo_y, lo_z, hi_x, hi_y, hi_z = self.solid.bounding_box()
        verdict = "watertight" if self.is_sound else "CHECK GEOMETRY"
        return (
            f"  {self.filename:<40} "
            f"{hi_x - lo_x:5.1f} x {hi_y - lo_y:5.1f} x {hi_z - lo_z:5.1f} mm   "
            f"{self.solid.volume() / 1000:5.2f} cm3   "
            f"{triangle_count(self.solid):5d} tri   {verdict}"
        )


def digest_of(path: Path) -> str:
    """The sha256 of a file, spelled the way `shasum -a 256` spells it."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repo_root() -> Path:
    """The directory holding pyproject.toml, found by walking up from here."""
    for directory in Path(__file__).resolve().parents:
        if (directory / "pyproject.toml").is_file():
            return directory
    raise RuntimeError("no pyproject.toml above printing3d/parts.py")


def output_base() -> Path:
    """The directory every project writes beneath. Override with PRINTING3D_OUTPUT."""
    root = os.environ.get(OUTPUT_DIR_ENV)
    return Path(root) if root else repo_root() / DEFAULT_OUTPUT_DIR


def output_dir(project: str) -> Path:
    """Where `project` writes its STLs."""
    return output_base() / project


def trials_dir(project: str) -> Path:
    """Where `project` writes the parts it is still testing.

    Kept apart from what ships, and out of version control. A trial is a
    question rather than an artifact: it is printed once, it answers something,
    and then it is deleted. Committing it would fill the repo with the shapes
    that lost, and pinning it would make retiring one a change to the record of
    what the project ships.
    """
    return output_base() / TRIALS_DIR / project


def archive_dir(project: str) -> Path:
    """Where `project` keeps parts it has stopped declaring."""
    return output_base() / ARCHIVE_DIR / project


def build_project[P: Part](
    project: str,
    parts: Iterable[P],
    announce: Callable[[P], str] | None = None,
    into: Path | None = None,
) -> bool:
    """Make a directory hold exactly the parts it was given.

    Everything given is written; anything left over from a part no longer
    listed is archived. True if every solid is sound.

    `announce` lets a project print its own line about a part -- a derived
    dimension worth seeing at build time -- just above the standard summary.

    `into` says where, defaulting to what the project ships. A project testing
    shapes it has not committed to passes its trials directory instead, so the
    two sets cannot end up in one pile.
    """
    # The whole catalogue is realised and its names checked before anything is
    # written, so a catalogue that cannot be made sense of fails with the output
    # directory untouched. Writing is not itself all-or-nothing: a part that
    # fails mid-loop leaves the ones before it on disk.
    parts = list(parts)
    _refuse_duplicate_names(project, parts)
    destination = output_dir(project) if into is None else into
    destination.mkdir(parents=True, exist_ok=True)
    all_sound = True
    for part in parts:
        if announce is not None:
            print(announce(part))
        write_stl(part.solid, destination / part.filename, part.name)
        print(part.summary())
        all_sound &= part.is_sound
    declared = {part.filename for part in parts}
    for path in archive_orphans(destination, declared, archive_dir(project)):
        print(f"  archived {path.name}")
    return all_sound


def _refuse_duplicate_names(project: str, parts: list) -> None:
    """Two entries under one name would leave one file where a project asked
    for two, with nothing on disk to say the other had ever existed."""
    seen = set()
    for part in parts:
        if part.filename in seen:
            raise ValueError(
                f"{project} declares {part.name!r} more than once; the second "
                f"would overwrite the first and vanish without a trace"
            )
        seen.add(part.filename)


def archive_orphans(directory: Path, declared: set[str], archive: Path) -> list[Path]:
    """Move the STLs in `directory` that are no longer declared into `archive`.

    The lock is deliberately left alone. A build that could edit its own lock
    could not be a golden master, so retiring a part leaves the lock describing
    a file that is gone -- which fails the contract until it is re-locked on
    purpose, exactly as any other change to a shipped part does.
    """
    orphans = [path for path in existing_stls(directory) if path.name not in declared]
    if orphans:
        archive.mkdir(parents=True, exist_ok=True)
    return [Path(shutil.move(path, _archived_as(path, archive))) for path in orphans]


def _archived_as(path: Path, archive: Path) -> Path:
    """Where `path` lands in the archive without displacing what is there.

    A part retired, brought back at a different size, and retired again would
    otherwise overwrite its own earlier shape -- silently losing the one thing
    the archive exists to keep. An identical shape needs no second copy; a
    different one is kept apart by what is actually different about it.
    """
    settled = archive / path.name
    if not settled.is_file() or settled.read_bytes() == path.read_bytes():
        return settled
    digest = digest_of(path)[:8]
    return archive / f"{path.stem}-{digest}{path.suffix}"


def existing_stls(directory: Path) -> list[Path]:
    """The STLs currently on disk in `directory`, in a stable order."""
    return sorted(directory.glob("*.stl"))
