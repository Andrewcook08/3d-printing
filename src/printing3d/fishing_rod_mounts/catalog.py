"""What actually gets printed.

Generates a matched PAIR per rod: a thin-walled crescent around the thick grip,
and a smaller one carried out from the wall on a wedge for the blank.

Both place the rod's CENTERLINE at the same distance from the wall and the same
height above the part's bottom edge. Align the two parts' bottom edges at one
height and the rod hangs level AND parallel to the wall. The extra standoff the
tip mount needs is derived, not tuned.

Hang each rod rotated so the reel and guides point DOWNWARD. On both spinning
and casting rods the guides sit on the same side as the reel, so this puts bare
blank against the wall. The reel's weight self-rotates the rod into that
position in the cradle.

Print lying on the profile, as exported: the part is a 2D profile extruded
sideways, so it has ZERO overhangs, needs no supports, and its layer lines run
across the cantilever rather than along the plane that would split them.

The shape lives in geometry.py; the numbers live in parts.toml. This module
only says how one becomes the other. See README.md for printing and hanging.
"""

from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from printing3d import config
from printing3d.fishing_rod_mounts import LOCKED, NAME  # noqa: F401  re-exported
from printing3d.fishing_rod_mounts.geometry import (
    Design,
    MountSpec,
    build,
    support_named,
)
from printing3d.parts import Part, build_project

CONFIG = Path(__file__).parent / "parts.toml"


@dataclass(frozen=True, kw_only=True)
class Rod:
    """One rod, measured at the two places a mount will grip it."""

    name: str
    butt_diameter: float
    tip_diameter: float

    def diameter_at(self, kind: str) -> float:
        """The diameter a mount of `kind` has to grip."""
        diameters = {"butt": self.butt_diameter, "tip": self.tip_diameter}
        if kind not in diameters:
            raise ValueError(
                f"unknown mount kind {kind!r}; choose from {', '.join(diameters)}"
            )
        return diameters[kind]


@dataclass(frozen=True, kw_only=True)
class Style:
    """How one end of a rod is held. The rod supplies the diameter."""

    kind: str
    support: str
    lip_rise: float


@dataclass(frozen=True, kw_only=True)
class Catalogue:
    """Everything parts.toml has to say."""

    version: str
    mount: Design
    rod: list[Rod] = field(default_factory=list)
    style: list[Style] = field(default_factory=list)


@dataclass(frozen=True)
class MountPart(Part):
    """A printable mount, carrying the parameters it was built from so that
    verify.py can measure the solid against its own intent."""

    rod: str
    kind: str
    spec: MountSpec


def catalogue() -> Catalogue:
    """The project's configuration, validated."""
    return config.read(CONFIG, into=Catalogue)


def parts(shipping: Catalogue | None = None) -> Iterator[MountPart]:
    """Every mount a catalogue describes, in the order it is printed and listed.

    Defaults to the shipped configuration; a caller may pass its own to see
    what a different set of rods would produce.
    """
    shipping = catalogue() if shipping is None else shipping
    for rod in shipping.rod:
        for style in shipping.style:
            spec = MountSpec(
                rod_dia=rod.diameter_at(style.kind),
                support=support_named(style.support),
                lip_rise=style.lip_rise,
                design=shipping.mount,
            )
            yield MountPart(
                name=f"{rod.name}-{style.kind}-{spec.rod_dia:.2f}mm{shipping.version}",
                solid=build(spec),
                rod=rod.name,
                kind=style.kind,
                spec=spec,
            )


def standoff_line(part: MountPart) -> str:
    """How much material sits behind the rod, and how far the mount projects."""
    cradle = part.spec.cradle
    return (
        f"    {part.kind:<4} standoff behind rod "
        f"{cradle.standoff_behind_rod:5.2f} mm, "
        f"projection {cradle.projection_from_wall:5.2f} mm"
    )


def build_all() -> bool:
    """Write the whole catalog to output/. True if every solid is sound."""
    return build_project(NAME, parts(), announce=standoff_line)
