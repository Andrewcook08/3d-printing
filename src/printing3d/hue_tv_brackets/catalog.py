"""What actually gets printed.

Two shapes, swept from the one profile in geometry.py: straight runs for the
sides of the TV, and 90-degree corners. Straights are long on purpose -- a
125 mm section covers what five of the original 25 mm clips would, and the
brackets are universal, so how many of each a TV needs is the TV's business,
not this catalog's.

Corners currently ship as a ladder of three radii. The strip's tolerance for
bending in its own plane cannot be derived, only measured, so the sharpest
usable radius is settled by printing all three. See README.md.
"""

import math
from collections.abc import Iterator
from dataclasses import dataclass

from printing3d.hue_tv_brackets import LOCKED, NAME  # noqa: F401  re-exported
from printing3d.hue_tv_brackets.geometry import (
    BASE_DEPTH,
    QUARTER_TURN,
    TILT,
    corner,
    straight,
    to_outermost,
    to_tab_edge,
)
from printing3d.parts import Part, build_project

VERSION_SUFFIX = "-v1"

MM2_PER_CM2 = 100.0

STRAIGHT_LENGTHS = [125.0]

# Print all three, thread the strip through each, keep the sharpest that does
# not put it in a bind. The losing rungs are then deleted and the survivors
# re-locked.
LADDER_RADII = [30.0, 40.0, 55.0]

# TEMPORARY -- trial parts, to be deleted once a configuration is chosen.
#
# The 45-degree ladder above bound solid: a corner at that lean forces the strip
# to bend in its own plane, which flat strips refuse. Rolling the channel up
# cuts that demand, since it falls with the cosine of the lean.
#
# Listed sharpest first, which is also cheapest first -- a tighter corner is a
# smaller print. Print in this order and stop at the first that threads: that
# radius is the answer, and the gentler ones never need making. The strains run
# 6.0 / 4.5 / 3.0 / 2.0 / 1.54%, against the 9.0% that bound.
#
# The last pair sit at the same 1.54% at different leans. If those two behave
# alike, strain really is the only thing that matters and the winning value can
# be spent at whatever lean looks best.
TRIAL_CORNERS = [
    (65.0, 51.0),
    (70.0, 41.0),
    (70.0, 55.0),
    (70.0, 82.0),
    (65.0, 68.0),
    (65.0, 101.0),
    (65.0, 152.0),
    (65.0, 197.0),
    (70.0, 160.0),
]

# A one-inch sample of each lean, to feel the twist from a 45-degree straight.
TRIAL_STRAIGHT_LENGTH = 25.4
TRIAL_LEANS = [65.0, 70.0]


@dataclass(frozen=True)
class Bracket(Part):
    """A printable bracket. Each shape reports its own footprint."""

    def footprint_line(self) -> str:
        """One line about what this bracket lands on the TV, for build output."""
        raise NotImplementedError


@dataclass(frozen=True)
class StraightBracket(Bracket):
    """A straight run, carrying the length and lean it was built from."""

    length: float
    tilt: float = TILT

    def footprint_line(self) -> str:
        """The adhesive pad this lands on the TV, and the strip it covers."""
        pad = self.length * BASE_DEPTH / MM2_PER_CM2
        return f"    straight  pad {pad:6.1f} cm2 over {self.length:5.1f} mm of strip"


@dataclass(frozen=True)
class CornerBracket(Bracket):
    """A quarter turn, carrying the radius and lean it was built from."""

    radius: float
    tilt: float = TILT

    @property
    def inner_radius(self) -> float:
        """Where the tab edge sweeps -- the innermost material."""
        return self.radius - to_tab_edge(self.tilt)

    @property
    def outer_radius(self) -> float:
        """Where the arm's outer edge sweeps."""
        return self.radius + to_outermost(self.tilt)

    @property
    def strip_spent(self) -> float:
        """Strip consumed by the turn, which the straight runs then go without."""
        return math.radians(QUARTER_TURN) * self.radius

    def footprint_line(self) -> str:
        """The arc this turns the strip through, and what it costs in strip."""
        return (
            f"    corner    r{self.radius:<5.1f} inner {self.inner_radius:5.2f} mm, "
            f"outer {self.outer_radius:5.2f} mm, spends {self.strip_spent:5.1f} mm "
            f"of strip"
        )


def parts() -> Iterator[Bracket]:
    """Every bracket this catalog ships, in the order it is listed and printed."""
    for length in STRAIGHT_LENGTHS:
        yield StraightBracket(
            name=f"straight-{length:g}mm{VERSION_SUFFIX}",
            solid=straight(length),
            length=length,
        )
    for radius in LADDER_RADII:
        yield CornerBracket(
            name=f"corner-r{radius:g}{VERSION_SUFFIX}",
            solid=corner(radius),
            radius=radius,
        )
    for tilt, radius in TRIAL_CORNERS:
        yield CornerBracket(
            name=f"trial-corner-{tilt:g}deg-r{radius:g}{VERSION_SUFFIX}",
            solid=corner(radius, tilt),
            radius=radius,
            tilt=tilt,
        )
    for tilt in TRIAL_LEANS:
        yield StraightBracket(
            name=f"trial-straight-{tilt:g}deg-{TRIAL_STRAIGHT_LENGTH:g}mm{VERSION_SUFFIX}",
            solid=straight(TRIAL_STRAIGHT_LENGTH, tilt),
            length=TRIAL_STRAIGHT_LENGTH,
            tilt=tilt,
        )


def straights(brackets: list[Bracket]) -> list[StraightBracket]:
    """The straight runs among `brackets`."""
    return [part for part in brackets if isinstance(part, StraightBracket)]


def corners(brackets: list[Bracket]) -> list[CornerBracket]:
    """The corners among `brackets`."""
    return [part for part in brackets if isinstance(part, CornerBracket)]


def build_all() -> bool:
    """Write the whole catalog to output/. True if every solid is sound."""
    # Called through a lambda rather than passed as Bracket.footprint_line: the
    # latter binds the base class's version and never reaches the subclass.
    return build_project(NAME, parts(), announce=lambda part: part.footprint_line())
