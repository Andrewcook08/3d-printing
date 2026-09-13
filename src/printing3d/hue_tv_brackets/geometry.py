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

# Height of the channel above the TV back. Forced, not chosen: it is what rests
# the block's outboard-bottom corner ON the base plane. Every dimension below
# follows from it, which is why none of them is measured off the reference.
FLOOR_HEIGHT = (BLOCK_W / 2 + FLOOR_THK) * math.sin(math.radians(TILT))

QUARTER_TURN = 90.0  # what a corner of a rectangular TV turns the strip through
CORNER_SEGMENTS = 128  # per full turn, so 32 across the quarter


class Point(NamedTuple):
    """A point of the profile: `u` outboard, `v` above the TV back."""

    u: float
    v: float


def leaned(across, up):
    """A point of the channel's own frame, placed in the profile's frame.

    The channel is described square -- `across` the slot from its centre,
    `up` from its floor -- and then leaned as a whole. Everything the arm and
    the plate need to meet is a point of the channel, so they ask for it here
    rather than restating it at an angle.
    """
    lean = math.radians(TILT)
    return Point(
        u=across * math.cos(lean) + up * math.sin(lean),
        v=-across * math.sin(lean) + up * math.cos(lean) + FLOOR_HEIGHT,
    )


# Outboard is positive, measured from the centre of the slot floor -- the datum
# a corner's radius is quoted to. The plate runs inboard from the block's
# outboard-bottom corner; the arm's wall drops from its inboard-bottom one.
TO_BASE_EDGE = leaned(BLOCK_W / 2, -FLOOR_THK).u
TO_OUTERMOST = leaned(BLOCK_W / 2, CHANNEL_D).u
TO_TAB_EDGE = BASE_DEPTH - TO_BASE_EDGE
ARM_APEX = leaned(-BLOCK_W / 2, -FLOOR_THK)

# Below this the tab edge reaches the revolve axis and the wedge folds through
# itself: a turn cannot be made by a part reaching past its own centre.
MIN_CORNER_RADIUS = TO_TAB_EDGE


# ---------------------------------------------------------------------------
# Profile: plate + arm + channel block
# ---------------------------------------------------------------------------


def profile():
    """The 2D cross-section every bracket is swept from."""
    # Union order is fixed deliberately. Union is not associative in the output
    # mesh, so re-ordering these would re-tessellate every shipped part.
    part = _plate()
    part = part + _arm()
    part = part + _channel_block()
    return part


def _plate():
    """The flat pad the adhesive holds, running inboard from under the arm."""
    return rect(-TO_TAB_EDGE, 0.0, TO_BASE_EDGE, PLATE_THK)


def _arm():
    """The wedge carrying the channel up off the plate.

    Its hypotenuse is the channel block's own underside, so the arm meets the
    block flush however the block is dimensioned.
    """
    return polygon([(TO_BASE_EDGE, 0.0), ARM_APEX, (ARM_APEX.u, 0.0)])


def _channel_block():
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
    return block.rotate(-TILT).translate((0.0, FLOOR_HEIGHT))


# ---------------------------------------------------------------------------
# Solids: the profile swept
# ---------------------------------------------------------------------------


def straight(length):
    """A straight run of bracket, `length` along the strip."""
    upright = profile().extrude(length)
    # Exported lying on its base, which is how it prints and how the corner
    # comes out of the revolve. The profile is authored standing up.
    return upright.rotate((90.0, 0.0, 0.0)).translate((0.0, length, 0.0))


def corner(radius):
    """A quarter turn, `radius` measured to the centre of the slot floor."""
    if radius <= MIN_CORNER_RADIUS:
        raise ValueError(
            f"radius {radius} reaches the revolve axis: the profile extends "
            f"{MIN_CORNER_RADIUS:.2f} mm inboard of the channel, so a corner "
            f"must be wider than that"
        )
    # revolve() spins a profile about its own Y axis and takes no axis
    # argument, so the radius is applied by moving the profile out to it.
    return profile().translate((radius, 0.0)).revolve(CORNER_SEGMENTS, QUARTER_TURN)


def chord_inset(radius):
    """How far a cut between two facets falls inside the true arc.

    The revolve approximates the arc with flat facets, so a section taken
    between two of them sits a chord's sagitta short of the radius. This is the
    most a corner's section can differ from the straight's it was swept from.
    """
    half_facet = math.radians(360.0 / CORNER_SEGMENTS / 2.0)
    return (radius + TO_OUTERMOST) * (1.0 - math.cos(half_facet))
