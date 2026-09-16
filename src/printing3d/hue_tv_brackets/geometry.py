"""The parametric solid model of one bracket.

Shape follows reference/Hue LED Strip with Angle straight section.stl: a flat
base plate, an arm carrying a channel out at a lean, and two lips that close
over that channel so the strip clips in and needs no adhesive of its own.
Rebuilt parametrically rather than traced, because the point of the exercise is
a matching corner, and a traced outline cannot be bent.

A bracket is one 2D profile swept three ways -- extruded for a straight run,
revolved about an offset axis for a corner, and lofted through a run of
profiles for a corner the strip turns into rather than meets. There is only
one channel, so no two of them can disagree about it.

Every measured number arrives from the project's config file as a Design. What
this module adds is everything derived from those numbers, and the sweeping.

See README.md for why the channel leans and why the tab stays.
"""

import math
from dataclasses import dataclass, replace
from typing import NamedTuple

import manifold3d as m
import numpy as np

from printing3d.shapes import polygon, rect, signed_area

# Cut past the block's face so the mouth opens cleanly rather than meeting it
# on a coincident edge. Construction, not design: it changes no dimension of
# the finished bracket, so it is not something anyone tunes one with.
SLOT_OVERSHOOT = 1.0

QUARTER_TURN = 90.0  # what a corner of a rectangular TV turns the strip through
CORNER_SEGMENTS = 128  # per full turn, so 32 across the quarter

# How far the lean may move between one station of a turning sweep and the
# next. Construction, not design. The sweep is lofted, so the surface between
# two stations is ruled and carries no step; what is left is only the
# difference between interpolating a profile and leaning it, which falls away
# as the square of this. At this figure that difference is 0.0002 mm, which is
# three orders below what the printer resolves.
LEAN_PER_STATION = 45.0 / 64.0

# How close to vertical counts as vertical. Construction, not design: it only
# decides which of two exact expressions describes the same shape.
UPRIGHT = 1e-9


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

    # What the channel is for. Read only by the pre-print checks -- no
    # dimension of the bracket derives from it, because the channel was
    # measured off the reference rather than sized from the strip.
    strip_width: float

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

    # How far the plate reaches outboard of the strip's centre. Given rather
    # than derived so that it, like the floor height, is the same at every
    # lean: butting each bracket's outer edge to one marked line then puts the
    # strip in the same place whatever the lean.
    pad_outboard: float

    def __post_init__(self) -> None:
        """Refuse a shape that would come apart or leave nothing to stick down.

        Both bounds are about this lean in particular, so they are checked when
        a leaned design is made rather than when the file is read -- an entry
        may name its own lean, and the shipped numbers have to suit all of them.
        """
        if self.block_float > self.plate_thickness:
            raise ValueError(
                f"at {self.tilt:g} degrees the channel floats "
                f"{self.block_float:.4f} mm above where it would rest, which is "
                f"clear of a {self.plate_thickness} mm plate: the block would "
                f"meet the plate along a line rather than sitting into it, and "
                f"the two come out as separate pieces"
            )
        if self.pad_outboard >= self.base_depth:
            raise ValueError(
                f"pad_outboard {self.pad_outboard} mm leaves no tab within a "
                f"base_depth of {self.base_depth} mm: the plate is the footprint "
                f"and the tab is what remains of it inboard of the channel"
            )

    @property
    def mouth_width(self) -> float:
        """The neck the strip has to flex past to be caught."""
        return self.channel_width - 2 * self.lip_reach

    @property
    def block_width(self) -> float:
        """Across the channel block, its walls included."""
        return self.channel_width + 2 * self.wall

    @property
    def resting_height(self) -> float:
        """The height at which the block's outboard-bottom corner would touch.

        What the floor height used to be, and the reason the strip used to move
        when the lean changed. Half the block leans up by the sine while the
        floor's own thickness leans by the cosine -- two different terms, equal
        only at 45 degrees.

        Kept because it is the floor below which a bracket at this lean would
        dip through the TV back, which is what `floor_height` has to clear.
        """
        lean = math.radians(self.tilt)
        return (self.block_width / 2) * math.sin(
            lean
        ) + self.floor_thickness * math.cos(lean)

    @property
    def tallest_resting_height(self) -> float:
        """The tallest `resting_height` any lean can ask for.

        `a*sin + b*cos` is `hypot(a, b)*sin(angle + phase)`, so its maximum over
        every lean is that hypotenuse -- reached near 77 degrees for this
        channel, not at 90. The curve is not monotonic, which is what makes
        reading the value off the steepest bracket in use the wrong answer.
        """
        return math.hypot(self.block_width / 2, self.floor_thickness)

    @property
    def channel_clearing_height(self) -> float:
        """The height at which the channel's low end clears the plate.

        The plate reaches outboard past the strip, so at a steep lean it passes
        underneath the low end of the channel. Too low and it fills the bottom
        of the slot -- the strip's bed measurably shortens rather than anything
        visibly breaking. The low end sits half the channel's width below the
        floor at worst, so clearing the plate's own thickness is the bound.
        """
        return self.plate_thickness + self.channel_width / 2

    @property
    def floor_height(self) -> float:
        """How high the slot floor's centre sits above the TV back.

        Chosen rather than forced, and the same at every lean, so that changing
        the lean does not move the strip. It is the lowest height that clears
        both bounds above at every lean, so no bracket dips through the TV back
        and no plate intrudes into a channel.

        It used to be whatever rested the block's corner on the plane, which
        made the strip's height a consequence of the lean: 7.78 mm at 45
        degrees against 9.00 at 90, so the strip stepped out at every corner.
        """
        return max(self.tallest_resting_height, self.channel_clearing_height)

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
    def block_float(self) -> float:
        """How far the block hangs above where this lean would have rested it.

        Zero at the lean whose resting height the floor was set from, and
        largest at the shallowest lean. The plate has to be at least this thick
        to still overlap the block: below that the two touch along a line, and
        a line of contact is not a join -- the pieces separate.
        """
        return self.floor_height - self.resting_height

    @property
    def to_resting_corner(self) -> float:
        """How far outboard the block's underside corner reaches.

        It no longer decides where the plate ends -- `pad_outboard` does -- but
        the plate still has to reach at least this far, or the block would meet
        the TV back beyond the pad's edge.
        """
        return self.leaned(self.block_width / 2, -self.floor_thickness).u

    @property
    def to_outermost(self) -> float:
        """The furthest outboard the part reaches, at the block's top corner."""
        return self.leaned(self.block_width / 2, self.channel_depth).u

    @property
    def to_tab_edge(self) -> float:
        """How far inboard the plate runs -- the innermost material.

        The pad is the whole plate at every lean now, so the tab is simply what
        is left of the footprint once the outboard reach is taken off it.
        """
        return self.base_depth - self.pad_outboard

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
    return rect(-design.to_tab_edge, 0.0, design.pad_outboard, design.plate_thickness)


def _arm(design):
    """The wedge carrying the channel up off the plate.

    Its long face is the channel block's own underside, so the arm meets the
    block flush however the block is dimensioned. Four corners rather than
    three: the floor sits above what would rest the block on the plane, so the
    arm has to climb from the plane to the block's underside corner before it
    can follow that underside inboard. A triangle straight to the corner leaves
    a notch under the block -- one that reads as solid, because it is open to
    the outside rather than enclosed.

    At a right angle the underside stands vertical and the four corners fall on
    one line. The arm contributes nothing there, which is correct: the plate
    reaches past the block and carries it directly.
    """
    apex = design.arm_apex
    resting = design.leaned(design.block_width / 2, -design.floor_thickness)
    beneath = polygon([(resting.u, 0.0), resting, apex, (apex.u, 0.0)])
    # Never outboard of the plate. At a shallow lean the block's resting corner
    # reaches past the plate's edge, and an arm that followed it there would
    # put its own foot on the TV outboard of the pad -- which is the thing the
    # fixed reach exists to stop. The block overhangs instead, in the air.
    inboard = min(apex.u, resting.u)
    tallest = max(apex.v, resting.v)
    return beneath ^ rect(inboard, 0.0, design.pad_outboard, tallest)


def _channel_block(design):
    """The slot and its two lips, described square and then leaned."""
    block = _block_outline(design) - _slot(design)
    return block.rotate(-design.tilt).translate((0.0, design.floor_height))


def _slot(design):
    """The void the strip clips into, drawn upright about its own bed."""
    return polygon(_slot_points(design))


def _slot_points(design):
    """That void's corners, in the channel's own frame.

    Its origin is the middle of the bed, which is where the strip sits. A
    sweep that turns this outline about that origin therefore turns the
    channel around the strip rather than carrying the strip around with it.
    """
    half_bed, half_mouth = design.channel_width / 2, design.mouth_width / 2
    depth = design.channel_depth
    lip_shoulder = depth - design.lip_height
    return [
        (-half_bed, 0.0),
        (half_bed, 0.0),
        (half_bed, lip_shoulder),
        (half_mouth, depth),
        (half_mouth, depth + SLOT_OVERSHOOT),
        (-half_mouth, depth + SLOT_OVERSHOOT),
        (-half_mouth, depth),
        (-half_bed, lip_shoulder),
    ]


def _block_outline(design):
    """The block the slot is cut from, upright and about the same origin."""
    return rect(
        -design.block_width / 2,
        -design.floor_thickness,
        design.block_width / 2,
        design.channel_depth,
    )


# ---------------------------------------------------------------------------
# Solids: the profile swept
# ---------------------------------------------------------------------------


def straight(design: Design, length: float):
    """A straight run of bracket, `length` along the strip."""
    upright = profile(design).extrude(length)
    # Exported lying on its base, which is how it prints and how the corner
    # comes out of the revolve. The profile is authored standing up.
    return upright.rotate((90.0, 0.0, 0.0)).translate((0.0, length, 0.0))


class Station(NamedTuple):
    """Where the profile sits along a sweep, and how it leans there.

    `origin` is a point of the strip's own centre line and `outboard` the
    direction the profile's `u` runs in from it, both in the mounting plane.
    Together they say where to put a profile; `tilt` says which one to put.
    """

    origin: tuple[float, float]
    outboard: tuple[float, float]
    tilt: float


def led_corner(
    design: Design, radius: float, lead: float, twist: float, from_tilt: float
):
    """A quarter turn with a straight run leading into it and out of it.

    Each run meets the strip at `from_tilt`, holds that lean for the first
    `lead - twist` of its length, and turns to the corner's own lean over the
    last `twist`. The turn is measured back from the corner rather than
    forward from the open end, so the channel arrives upright however long
    either is -- lengthening the run moves the straight part, never the turn.

    Swept in one piece rather than assembled from three. A run, the turn and
    the run out are stations of one sweep, so there is no seam between them to
    take or to show, and the channel is one cut along the whole of it.
    """
    if lead <= 0.0 or twist <= 0.0:
        raise ValueError(f"lead {lead} and twist {twist} must both be positive")
    if twist > lead:
        raise ValueError(
            f"twist {twist} is longer than the {lead} mm lead it has to turn "
            f"within: the turn has to finish before the corner starts"
        )
    body = _along(design, radius, lead, twist, from_tilt, 0.0)
    # The channel is cut from a sweep that runs past both ends, so it opens
    # out rather than meeting the end faces on a coincident plane.
    cut = _along(design, radius, lead, twist, from_tilt, SLOT_OVERSHOOT)
    # Union order fixed deliberately, matching profile(): the pad, then what
    # it carries. Union is not associative in the resulting mesh.
    outer = _swept(design, body, _plate_points) + _swept(design, body, _lump_points)
    return outer - _swept(design, cut, _leaning_slot_points)


def _along(design, radius, lead, twist, from_tilt, overshoot):
    """Every station of a led corner: in along one run, round, and out.

    `overshoot` carries the first and last stations past the ends of the part,
    which is what the channel is cut with.
    """
    held = lead - twist
    turning = max(1, math.ceil(abs(design.tilt - from_tilt) / LEAN_PER_STATION))
    arc = max(1, round(CORNER_SEGMENTS * QUARTER_TURN / 360.0))

    def entering(along):
        share = 0.0 if along <= held else (along - held) / twist
        lean = from_tilt + (design.tilt - from_tilt) * share
        return Station((radius, along - lead), (1.0, 0.0), lean)

    def leaving(along):
        share = min(along, twist) / twist
        lean = design.tilt - (design.tilt - from_tilt) * share
        return Station((-along, radius), (0.0, 1.0), lean)

    def turned(step):
        about = math.radians(QUARTER_TURN * step / arc)
        reach = (math.cos(about), math.sin(about))
        return Station((radius * reach[0], radius * reach[1]), reach, design.tilt)

    # The lean holds until `held`, so one station at each end of that stretch
    # describes it exactly however long it is.
    places = [entering(mark) for mark in sorted({-overshoot, 0.0, held})]
    places += [entering(held + twist * k / turning) for k in range(1, turning + 1)]
    places += [turned(k) for k in range(1, arc + 1)]
    places += [leaving(twist * k / turning) for k in range(1, turning + 1)]
    places += [leaving(mark) for mark in sorted({lead, lead + overshoot})]
    return _once_each(places)


def _once_each(places):
    """The same stations with any repeat of the one before it dropped.

    Where a run holds its lean, or spends none of itself turning, two of the
    marks above land on the same place. A sweep through a station twice would
    carry a ring of zero-length edges.
    """
    kept = [places[0]]
    for place in places[1:]:
        if place != kept[-1]:
            kept.append(place)
    return kept


def _swept(design, places, points_of):
    """`points_of` swept along `places`, lofted rather than stacked.

    The outline is asked for again at every station, so a sweep is not limited
    to shapes that merely rotate: what changes as the lean changes -- which
    corner of the block the pad reaches, whether the arm is there at all -- is
    described once, by the outline, and the sweep follows it.
    """
    rings = []
    for place in places:
        points = points_of(replace(design, tilt=place.tilt))
        # Wound against the way the sweep runs, so the loft faces outwards.
        if signed_area(points) > 0.0:
            points = points[::-1]
        (across, along), (out_u, out_v) = place.origin, place.outboard
        rings.append([(across + out_u * u, along + out_v * u, v) for u, v in points])
    return _lofted(rings)


def _lofted(rings):
    """A solid through `rings`, each a closed loop of the same length.

    The surface between one ring and the next is ruled. That is the whole
    point of lofting rather than stacking: a stack of prisms leaves a ledge
    wherever two of them meet, and no number of prisms turns a ledge into a
    smooth surface -- it only makes it smaller.
    """
    width = len(rings[0])
    points = [list(point) for ring in rings for point in ring]
    faces = []
    for index in range(len(rings) - 1):
        near, far = index * width, (index + 1) * width
        for here in range(width):
            after = (here + 1) % width
            corners = (
                points[near + here],
                points[near + after],
                points[far + after],
                points[far + here],
            )
            # A quad spanning a change of lean is not planar, and cutting it
            # along one diagonal leaves its middle standing off the surface it
            # stands for -- by a quarter of how much the edge moved, which is
            # a ledge again by another name. A centre point keeps all four
            # triangles on the ruled patch.
            points.append([sum(c[axis] for c in corners) / 4.0 for axis in range(3)])
            middle = len(points) - 1
            faces.append((near + here, near + after, middle))
            faces.append((near + after, far + after, middle))
            faces.append((far + after, far + here, middle))
            faces.append((far + here, near + here, middle))
    last = (len(rings) - 1) * width
    for here in range(1, width - 1):
        faces.append((0, here + 1, here))
        faces.append((last, last + here, last + here + 1))
    mesh = m.Mesh64(
        np.array(points, dtype=np.float64), np.array(faces, dtype=np.uint64)
    )
    return m.Manifold(mesh)


def _plate_points(design):
    """The flat pad, as four corners."""
    return [
        (-design.to_tab_edge, 0.0),
        (design.pad_outboard, 0.0),
        (design.pad_outboard, design.plate_thickness),
        (-design.to_tab_edge, design.plate_thickness),
    ]


def _lump_points(design):
    """The arm and the channel block as one outline, seven corners.

    One outline rather than two solids because the arm's top face is the
    block's underside: swept apart and unioned, those two coincident faces
    leave the channel roofed over in places. Swept together there is no seam
    between them at all.

    Seven corners at every lean, which is what lets one ring be lofted to the
    next. Where the block's underside does not reach outboard of the pad, two
    of them land on each other and the corner is simply not there.
    """
    half, deep = design.block_width / 2, design.channel_depth
    floor = -design.floor_thickness
    out, inboard = design.leaned(half, floor), design.leaned(-half, floor)
    over, under = design.leaned(half, deep), design.leaned(-half, deep)
    if out.u > design.pad_outboard:
        # The arm may not stand on the TV outboard of the pad, so it stops at
        # the pad's edge and the block overhangs it, in the air.
        share = (out.u - design.pad_outboard) / (out.u - inboard.u)
        reached = (design.pad_outboard, out.v + share * (inboard.v - out.v))
    else:
        reached = (out.u, out.v)
    return [
        (reached[0], 0.0),
        reached,
        (out.u, out.v),
        (over.u, over.v),
        (under.u, under.v),
        (inboard.u, inboard.v),
        (inboard.u, 0.0),
    ]


def _leaning_slot_points(design):
    """The slot's corners, leaned into the profile's frame."""
    return [tuple(design.leaned(across, up)) for across, up in _slot_points(design)]


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
