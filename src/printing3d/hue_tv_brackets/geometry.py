"""The parametric solid model of one bracket.

Shape follows reference/Hue LED Strip with Angle straight section.stl: a flat
base plate, an arm carrying a channel out at a lean, and two lips that close
over that channel so the strip clips in and needs no adhesive of its own.
Rebuilt parametrically rather than traced, because the point of the exercise is
a matching corner, and a traced outline cannot be bent.

A bracket is one 2D profile swept two ways -- extruded for a straight run,
revolved about an offset axis for a corner. There is only one channel, so a
corner and a straight cannot disagree about it.

Every measured number arrives from the project's config file as a Design. What
this module adds is everything derived from those numbers, and the sweeping.

See README.md for why the channel leans and why the tab stays.
"""

import math
from dataclasses import dataclass
from typing import NamedTuple

from printing3d.shapes import polygon, rect

# Cut past the block's face so the mouth opens cleanly rather than meeting it
# on a coincident edge. Construction, not design: it changes no dimension of
# the finished bracket, so it is not something anyone tunes one with.
SLOT_OVERSHOOT = 1.0

QUARTER_TURN = 90.0  # what a corner of a rectangular TV turns the strip through
CORNER_SEGMENTS = 128  # per full turn, so 32 across the quarter


class Point(NamedTuple):
    """A point of the profile: `u` outboard, `v` above the TV back."""

    u: float
    v: float


@dataclass(frozen=True, kw_only=True)
class Design:
    """Every measured or chosen number a bracket is built from.

    Read from the project's config file, so tuning a bracket is an edit to that
    file rather than to this one. Everything derived from these numbers is a
    property or a method below, which is what keeps any of them from being
    written down a second time.
    """

    channel_width: float  # the strip's bed
    channel_depth: float
    wall: float  # slot wall, either side
    floor_thickness: float  # material under the slot

    # Each lip closes `lip_reach` over the slot while climbing `lip_height`,
    # leaving a mouth narrower than the bed. That neck is the clip: the strip
    # flexes past it and is then held mechanically.
    lip_reach: float
    lip_height: float

    # The strip fires out AND back rather than only back: the wall behind this
    # TV is dark, and light thrown along a wall washes further than light
    # thrown at it.
    tilt: float

    plate_thickness: float

    # The adhesive footprint. Also sets the tab -- the plate's overhang past
    # the arm, which is the lever arm resisting the peel that pulled the
    # strip's own adhesive off the TV.
    base_depth: float

    @property
    def mouth_width(self) -> float:
        """The neck the strip has to flex past to be caught."""
        return self.channel_width - 2 * self.lip_reach

    @property
    def block_width(self) -> float:
        """Across the channel block, its walls included."""
        return self.channel_width + 2 * self.wall

    @property
    def floor_height(self) -> float:
        """How high the slot floor's centre sits above the TV back.

        Forced, not chosen: it is what rests the block's outboard-bottom corner
        ON the base plane, and every dimension below follows from it. Half the
        block leans up by the sine while the floor's own thickness leans by the
        cosine -- two different terms, equal only at 45 degrees. Writing it as
        one of them doubled would be right at that lean and wrong at all others.
        """
        lean = math.radians(self.tilt)
        return (self.block_width / 2) * math.sin(
            lean
        ) + self.floor_thickness * math.cos(lean)

    def leaned(self, across: float, up: float) -> Point:
        """A point of the channel's own frame, placed in the profile's frame.

        The channel is described square -- `across` the slot from its centre,
        `up` from its floor -- and then leaned as a whole. Everything the arm
        and the plate need to meet is a point of the channel, so they ask for
        it here rather than restating it at an angle.
        """
        lean = math.radians(self.tilt)
        return Point(
            u=across * math.cos(lean) + up * math.sin(lean),
            v=-across * math.sin(lean) + up * math.cos(lean) + self.floor_height,
        )

    # Outboard is positive, measured from the centre of the slot floor -- the
    # datum a corner's radius is quoted to.

    @property
    def to_base_edge(self) -> float:
        """Where the plate's outboard edge sits: under the block's resting corner."""
        return self.leaned(self.block_width / 2, -self.floor_thickness).u

    @property
    def to_outermost(self) -> float:
        """The furthest outboard the part reaches, at the block's top corner."""
        return self.leaned(self.block_width / 2, self.channel_depth).u

    @property
    def to_tab_edge(self) -> float:
        """How far inboard the plate runs -- the innermost material."""
        return self.base_depth - self.to_base_edge

    @property
    def arm_apex(self) -> Point:
        """Where the arm's wall meets the block, at its inboard-bottom corner."""
        return self.leaned(-self.block_width / 2, -self.floor_thickness)

    @property
    def min_corner_radius(self) -> float:
        """Below this the tab edge reaches the revolve axis and the wedge folds
        through itself: a turn cannot be made by a part reaching past its
        centre."""
        return self.to_tab_edge

    def chord_inset(self, radius: float) -> float:
        """How far a cut between two facets falls inside the true arc.

        The revolve approximates the arc with flat facets, so a section taken
        between two of them sits a chord's sagitta short of the radius. This is
        the most a corner's section can differ from the straight's it was swept
        from.
        """
        half_facet = math.radians(360.0 / CORNER_SEGMENTS / 2.0)
        return (radius + self.to_outermost) * (1.0 - math.cos(half_facet))


# ---------------------------------------------------------------------------
# Profile: plate + arm + channel block
# ---------------------------------------------------------------------------


def profile(design: Design):
    """The 2D cross-section every bracket is swept from."""
    # Union order is fixed deliberately. Union is not associative in the output
    # mesh, so re-ordering these would re-tessellate every shipped part.
    part = _plate(design)
    part = part + _arm(design)
    part = part + _channel_block(design)
    return part


def _plate(design):
    """The flat pad the adhesive holds, running inboard from under the arm."""
    return rect(-design.to_tab_edge, 0.0, design.to_base_edge, design.plate_thickness)


def _arm(design):
    """The wedge carrying the channel up off the plate.

    Its hypotenuse is the channel block's own underside, so the arm meets the
    block flush however the block is dimensioned.
    """
    apex = design.arm_apex
    return polygon([(design.to_base_edge, 0.0), apex, (apex.u, 0.0)])


def _channel_block(design):
    """The slot and its two lips, described square and then leaned."""
    half_bed, half_mouth = design.channel_width / 2, design.mouth_width / 2
    depth = design.channel_depth
    lip_shoulder = depth - design.lip_height
    slot = polygon(
        [
            (-half_bed, 0.0),
            (half_bed, 0.0),
            (half_bed, lip_shoulder),
            (half_mouth, depth),
            (half_mouth, depth + SLOT_OVERSHOOT),
            (-half_mouth, depth + SLOT_OVERSHOOT),
            (-half_mouth, depth),
            (-half_bed, lip_shoulder),
        ]
    )
    block = (
        rect(
            -design.block_width / 2,
            -design.floor_thickness,
            design.block_width / 2,
            depth,
        )
        - slot
    )
    return block.rotate(-design.tilt).translate((0.0, design.floor_height))


# ---------------------------------------------------------------------------
# Solids: the profile swept
# ---------------------------------------------------------------------------


def straight(design: Design, length: float):
    """A straight run of bracket, `length` along the strip."""
    upright = profile(design).extrude(length)
    # Exported lying on its base, which is how it prints and how the corner
    # comes out of the revolve. The profile is authored standing up.
    return upright.rotate((90.0, 0.0, 0.0)).translate((0.0, length, 0.0))


def corner(design: Design, radius: float):
    """A quarter turn, `radius` measured to the centre of the slot floor."""
    floor = design.min_corner_radius
    if radius <= floor:
        raise ValueError(
            f"radius {radius} reaches the revolve axis: the profile extends "
            f"{floor:.2f} mm inboard of the channel, so a corner "
            f"must be wider than that"
        )
    # revolve() spins a profile about its own Y axis and takes no axis
    # argument, so the radius is applied by moving the profile out to it.
    return (
        profile(design).translate((radius, 0.0)).revolve(CORNER_SEGMENTS, QUARTER_TURN)
    )
