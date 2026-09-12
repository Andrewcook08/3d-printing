"""What a printable part is, and where its STL lands.

Every project in this repo produces `Part`s. `build_project` writes them into
`output/<project>/`, so the whole repo's printable output sits in one place no
matter which project produced it.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

from manifold3d import Error, Manifold

from printing3d.stl import triangle_count, write_stl

OUTPUT_DIR_ENV = "PRINTING3D_OUTPUT"
DEFAULT_OUTPUT_DIR = "output"


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


def repo_root() -> Path:
    """The directory holding pyproject.toml, found by walking up from here."""
    for directory in Path(__file__).resolve().parents:
        if (directory / "pyproject.toml").is_file():
            return directory
    raise RuntimeError("no pyproject.toml above printing3d/parts.py")


def output_dir(project: str) -> Path:
    """Where `project` writes its STLs. Override the root with PRINTING3D_OUTPUT."""
    root = os.environ.get(OUTPUT_DIR_ENV)
    base = Path(root) if root else repo_root() / DEFAULT_OUTPUT_DIR
    return base / project


def build_project[P: Part](
    project: str, parts: Iterable[P], announce: Callable[[P], str] | None = None
) -> bool:
    """Write every part to the project's output directory. True if all sound.

    `announce` lets a project print its own line about a part -- a derived
    dimension worth seeing at build time -- just above the standard summary.
    """
    destination = output_dir(project)
    destination.mkdir(parents=True, exist_ok=True)
    all_sound = True
    for part in parts:
        if announce is not None:
            print(announce(part))
        write_stl(part.solid, destination / part.filename, part.name)
        print(part.summary())
        all_sound &= part.is_sound
    return all_sound


def existing_stls(project: str) -> Iterator[Path]:
    """The STLs currently on disk for `project`, in a stable order."""
    return iter(sorted(output_dir(project).glob("*.stl")))
