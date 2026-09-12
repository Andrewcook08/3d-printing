"""
Low-profile wall mounts for horizontal fishing rod storage.

Generates a matched PAIR per rod:
  - butt mount: thin-walled crescent around the thick grip
  - tip mount:  small crescent carried out from the wall on a wedge

Both place the rod's CENTERLINE at the same distance from the wall (AXIS_U)
and the same height above the part's bottom edge (AXIS_V). Align the two
parts' bottom edges at one height and the rod hangs level AND parallel to the
wall. The extra standoff the tip mount needs is derived, not tuned.

Hang each rod rotated so the reel and guides point DOWNWARD. On both spinning
and casting rods the guides sit on the same side as the reel, so this puts
bare blank against the wall. The reel's weight self-rotates the rod into that
position in the cradle.

Print lying on the profile, as exported: the part is a 2D profile extruded
sideways, so it has ZERO overhangs, needs no supports, and its layer lines run
across the cantilever rather than along the plane that would split them.

The shape itself lives in geometry.py; this module is the catalog of what
actually gets printed. See README.md for printing and hanging instructions.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from printing3d.fishing_rod_mounts.geometry import (
    ARM_AND_GUSSET,
    WEDGE,
    MountSpec,
    Support,
    build,
)
from printing3d.parts import Part, build_project

PROJECT = "fishing-rod-mounts"
LOCKED = Path(__file__).parent / "LOCKED.txt"


# ---------------------------------------------------------------------------
# MEASURE THESE FOR EACH ROD
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Rod:
    """One rod, measured at the two places a mount will grip it."""

    name: str
    butt_dia: float  # grip diameter at the butt mount
    tip_dia: float  # blank diameter at the tip mount

    def diameter_at(self, kind: str) -> float:
        return {"butt": self.butt_dia, "tip": self.tip_dia}[kind]


RODS = [
    Rod(name="spinning-85in", butt_dia=26.15, tip_dia=5.80),
    # Rod(name="baitcaster", butt_dia=0.0, tip_dia=0.0),
]


# ---------------------------------------------------------------------------
# THE SHIPPING PAIR
# ---------------------------------------------------------------------------

# One screw per mount, not two: the second was overkill for this load, and
# dropping it lets the plate come down from 46 to 35 mm, which is where the
# visual saving actually is. A single tightened screw resists rotation by
# friction between plate and wall with a wide margin over the ~96 N.mm the
# hanging rod applies.
VERSION_SUFFIX = "-v3"

# Both mounts are 11 mm wide. The butt was narrowed from 15 mm to match the
# tip: same slab thickness, same 1.3 mm of margin around the countersink. That
# costs 27% of the rib's section modulus, which leaves roughly 7x margin on
# PETG at this load.
SLAB_WIDTH = 11.0


@dataclass(frozen=True)
class MountStyle:
    """How one end of a rod is held. The rod supplies the diameter."""

    kind: str
    support: Support
    lip_rise: float
    width: float = SLAB_WIDTH

    def spec_for(self, rod: Rod) -> MountSpec:
        return MountSpec(
            rod_dia=rod.diameter_at(self.kind),
            width=self.width,
            support=self.support,
            lip_rise=self.lip_rise,
        )


MOUNT_STYLES = [
    MountStyle(kind="butt", support=ARM_AND_GUSSET, lip_rise=5.0),
    MountStyle(kind="tip", support=WEDGE, lip_rise=0.0),
]


@dataclass(frozen=True)
class MountPart(Part):
    """A printable mount, carrying the parameters it was built from so that
    verify.py can measure the solid against its own intent."""

    kind: str
    spec: MountSpec


def parts(rods: list[Rod] | None = None) -> Iterator[MountPart]:
    """Every mount this catalog ships, in the order it is printed and listed."""
    for rod in RODS if rods is None else rods:
        for style in MOUNT_STYLES:
            spec = style.spec_for(rod)
            name = f"{rod.name}-{style.kind}-{spec.rod_dia:.2f}mm{VERSION_SUFFIX}"
            yield MountPart(name=name, solid=build(spec), kind=style.kind, spec=spec)


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
    all_sound = True
    for rod in RODS:
        print(f"\n{rod.name}   grip {rod.butt_dia:.2f} mm / blank {rod.tip_dia:.2f} mm")
        all_sound &= build_project(PROJECT, parts([rod]), announce=standoff_line)
    return all_sound
