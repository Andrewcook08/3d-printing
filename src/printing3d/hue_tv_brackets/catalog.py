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
    TO_OUTERMOST,
    TO_TAB_EDGE,
    corner,
    straight,
)
from printing3d.parts import Part, build_project

VERSION_SUFFIX = "-v1"

STRAIGHT_LENGTHS = [125.0]

# Print all three, thread the strip through each, keep the sharpest that does
# not put it in a bind. The losing rungs are then deleted and the survivors
# re-locked.
LADDER_RADII = [30.0, 40.0, 55.0]


@dataclass(frozen=True)
class StraightBracket(Part):
    """A straight run, carrying the length it was built from."""

    length: float

    def footprint_line(self) -> str:
        """The adhesive pad this lands on the TV, and the strip it covers."""
        pad = self.length * BASE_DEPTH / 100.0
        return f"    straight  pad {pad:6.1f} cm2 over {self.length:5.1f} mm of strip"


@dataclass(frozen=True)
class CornerBracket(Part):
    """A quarter turn, carrying the radius it was built from."""

    radius: float

    @property
    def inner_radius(self) -> float:
        """Where the tab edge sweeps -- the innermost material."""
        return self.radius - TO_TAB_EDGE

    @property
    def outer_radius(self) -> float:
        """Where the arm's outer edge sweeps."""
        return self.radius + TO_OUTERMOST

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


Bracket = StraightBracket | CornerBracket


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


def straights(brackets: list[Bracket]) -> list[StraightBracket]:
    """The straight runs among `brackets`."""
    return [part for part in brackets if isinstance(part, StraightBracket)]


def corners(brackets: list[Bracket]) -> list[CornerBracket]:
    """The corners among `brackets`."""
    return [part for part in brackets if isinstance(part, CornerBracket)]


def build_all() -> bool:
    """Write the whole catalog to output/. True if every solid is sound."""
    return build_project(NAME, parts(), announce=lambda part: part.footprint_line())
