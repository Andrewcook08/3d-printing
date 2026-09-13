"""The parametric solid model of one bracket.

Shape follows reference/Hue LED Strip with Angle straight section.stl: a flat
base plate, an arm carrying a channel out at 45 degrees, and two lips that
close over that channel so the strip clips in and needs no adhesive of its own.
Rebuilt parametrically rather than traced, because the point of the exercise is
a matching corner, and a traced outline cannot be bent.

A bracket is one 2D profile swept two ways -- extruded for a straight run,
revolved about an offset axis for a corner. There is only one channel, so a
corner and a straight cannot disagree about it.

See README.md for why the channel leans, why the tab stays, and why the corner
radius ships as a ladder.
"""

import math
from typing import NamedTuple

from printing3d.shapes import polygon, rect

# ---------------------------------------------------------------------------
# The channel -- the only part of the bracket the strip touches
# ---------------------------------------------------------------------------

CHANNEL_W = 15.0  # the strip's bed
CHANNEL_D = 4.0
WALL = 1.5  # slot wall, either side
FLOOR_THK = 2.0  # material under the slot

# Each lip closes LIP_REACH over the slot while climbing LIP_RISE, leaving a
# mouth narrower than the bed. That neck is the clip: the strip flexes past it
# and is then held mechanically.
LIP_REACH = 1.5
LIP_RISE = 2.0

MOUTH_W = CHANNEL_W - 2 * LIP_REACH
BLOCK_W = CHANNEL_W + 2 * WALL

# Cut past the block's face so the mouth opens cleanly rather than meeting it
# on a coincident edge.
SLOT_OVERSHOOT = 1.0

# ---------------------------------------------------------------------------
# How the channel is carried
# ---------------------------------------------------------------------------

# The strip fires out AND back rather than only back: the wall behind this TV
# is dark, and light thrown along a wall washes further than light thrown at it.
TILT = 45.0

PLATE_THK = 2.0

# The adhesive footprint. Also sets the tab -- the plate's overhang past the
# arm, which is the lever arm resisting the peel that pulled the strip's own
# adhesive off the TV.
BASE_DEPTH = 22.0


def floor_height(tilt):
    """How high the slot floor's centre sits above the TV back.

    Forced, not chosen: it is what rests the block's outboard-bottom corner ON
    the base plane, and every dimension below follows from it. Half the block
    leans up by the sine while the floor's own thickness leans by the cosine --
    two different terms, equal only at 45 degrees. Writing it as one of them
    doubled would be right at the angle we ship and wrong at every other.
    """
    lean = math.radians(tilt)
    return (BLOCK_W / 2) * math.sin(lean) + FLOOR_THK * math.cos(lean)


FLOOR_HEIGHT = floor_height(TILT)

QUARTER_TURN = 90.0  # what a corner of a rectangular TV turns the strip through
CORNER_SEGMENTS = 128  # per full turn, so 32 across the quarter


class Point(NamedTuple):
    """A point of the profile: `u` outboard, `v` above the TV back."""

    u: float
    v: float


def leaned(across, up, tilt=TILT):
    """A point of the channel's own frame, placed in the profile's frame.

    The channel is described square -- `across` the slot from its centre,
    `up` from its floor -- and then leaned as a whole. Everything the arm and
    the plate need to meet is a point of the channel, so they ask for it here
    rather than restating it at an angle.
    """
    lean = math.radians(tilt)
    return Point(
        u=across * math.cos(lean) + up * math.sin(lean),
        v=-across * math.sin(lean) + up * math.cos(lean) + floor_height(tilt),
    )


# Outboard is positive, measured from the centre of the slot floor -- the datum
# a corner's radius is quoted to. The plate runs inboard from the block's
# outboard-bottom corner; the arm's wall drops from its inboard-bottom one.
# Each is a function of the lean, with a constant for the lean we ship.


def to_base_edge(tilt):
    """Where the plate's outboard edge sits: under the block's resting corner."""
    return leaned(BLOCK_W / 2, -FLOOR_THK, tilt).u


def to_outermost(tilt):
    """The furthest outboard the part reaches, at the block's top corner."""
    return leaned(BLOCK_W / 2, CHANNEL_D, tilt).u


def to_tab_edge(tilt):
    """How far inboard the plate runs -- the innermost material."""
    return BASE_DEPTH - to_base_edge(tilt)


def arm_apex(tilt):
    """Where the arm's wall meets the block, at its inboard-bottom corner."""
    return leaned(-BLOCK_W / 2, -FLOOR_THK, tilt)


def min_corner_radius(tilt):
    """Below this the tab edge reaches the revolve axis and the wedge folds
    through itself: a turn cannot be made by a part reaching past its centre."""
    return to_tab_edge(tilt)


TO_BASE_EDGE = to_base_edge(TILT)
TO_OUTERMOST = to_outermost(TILT)
TO_TAB_EDGE = to_tab_edge(TILT)
ARM_APEX = arm_apex(TILT)
MIN_CORNER_RADIUS = min_corner_radius(TILT)


# ---------------------------------------------------------------------------
# Profile: plate + arm + channel block
# ---------------------------------------------------------------------------


def profile(tilt=TILT):
    """The 2D cross-section every bracket is swept from."""
    # Union order is fixed deliberately. Union is not associative in the output
    # mesh, so re-ordering these would re-tessellate every shipped part.
    part = _plate(tilt)
    part = part + _arm(tilt)
    part = part + _channel_block(tilt)
    return part


def _plate(tilt):
    """The flat pad the adhesive holds, running inboard from under the arm."""
    return rect(-to_tab_edge(tilt), 0.0, to_base_edge(tilt), PLATE_THK)


def _arm(tilt):
    """The wedge carrying the channel up off the plate.

    Its hypotenuse is the channel block's own underside, so the arm meets the
    block flush however the block is dimensioned.
    """
    apex = arm_apex(tilt)
    return polygon([(to_base_edge(tilt), 0.0), apex, (apex.u, 0.0)])


def _channel_block(tilt):
    """The slot and its two lips, described square and then leaned."""
    lip_shoulder = CHANNEL_D - LIP_RISE
    slot = polygon(
        [
            (-CHANNEL_W / 2, 0.0),
            (CHANNEL_W / 2, 0.0),
            (CHANNEL_W / 2, lip_shoulder),
            (MOUTH_W / 2, CHANNEL_D),
            (MOUTH_W / 2, CHANNEL_D + SLOT_OVERSHOOT),
            (-MOUTH_W / 2, CHANNEL_D + SLOT_OVERSHOOT),
            (-MOUTH_W / 2, CHANNEL_D),
            (-CHANNEL_W / 2, lip_shoulder),
        ]
    )
    block = rect(-BLOCK_W / 2, -FLOOR_THK, BLOCK_W / 2, CHANNEL_D) - slot
    return block.rotate(-tilt).translate((0.0, floor_height(tilt)))


# ---------------------------------------------------------------------------
# Solids: the profile swept
# ---------------------------------------------------------------------------


def straight(length, tilt=TILT):
    """A straight run of bracket, `length` along the strip."""
    upright = profile(tilt).extrude(length)
    # Exported lying on its base, which is how it prints and how the corner
    # comes out of the revolve. The profile is authored standing up.
    return upright.rotate((90.0, 0.0, 0.0)).translate((0.0, length, 0.0))


def corner(radius, tilt=TILT):
    """A quarter turn, `radius` measured to the centre of the slot floor."""
    floor = min_corner_radius(tilt)
    if radius <= floor:
        raise ValueError(
            f"radius {radius} reaches the revolve axis: the profile extends "
            f"{floor:.2f} mm inboard of the channel, so a corner "
            f"must be wider than that"
        )
    # revolve() spins a profile about its own Y axis and takes no axis
    # argument, so the radius is applied by moving the profile out to it.
    return profile(tilt).translate((radius, 0.0)).revolve(CORNER_SEGMENTS, QUARTER_TURN)


def chord_inset(radius):
    """How far a cut between two facets falls inside the true arc.

    The revolve approximates the arc with flat facets, so a section taken
    between two of them sits a chord's sagitta short of the radius. This is the
    most a corner's section can differ from the straight's it was swept from.
    """
    half_facet = math.radians(360.0 / CORNER_SEGMENTS / 2.0)
    return (radius + TO_OUTERMOST) * (1.0 - math.cos(half_facet))
