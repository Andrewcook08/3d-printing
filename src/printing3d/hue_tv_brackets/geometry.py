"""The parametric solid model of one bracket.

Shape follows reference/Hue LED Strip with Angle straight section.stl: a flat
base plate, an arm carrying a channel out at a lean, and two lips that close
over that channel so the strip clips in and needs no adhesive of its own.
Rebuilt parametrically rather than traced, because the point of the exercise is
a matching corner, and a traced outline cannot be bent.

A bracket is one 2D profile swept three ways -- extruded for a straight run,
revolved about an offset axis for a corner, and stacked in slabs for a run that
turns from one lean to another. There is only one channel, so no two of them
can disagree about it.

Every measured number arrives from the project's config file as a Design. What
this module adds is everything derived from those numbers, and the sweeping.

See README.md for why the channel leans and why the tab stays.
"""

import math
from dataclasses import dataclass, replace
from typing import NamedTuple

from printing3d.shapes import polygon, rect

# Cut past the block's face so the mouth opens cleanly rather than meeting it
# on a coincident edge. Construction, not design: it changes no dimension of
# the finished bracket, so it is not something anyone tunes one with.
SLOT_OVERSHOOT = 1.0

QUARTER_TURN = 90.0  # what a corner of a rectangular TV turns the strip through
CORNER_SEGMENTS = 128  # per full turn, so 32 across the quarter

# A twisting run is stacked from slabs, one per this much turn. Construction,
# not design, and measured at both bounds: at two thirds of this step the
# stack stops merging and comes back as three pieces, while at twice it the
# scalloping where one slab meets the next doubles.
TWIST_PER_SLAB = 45.0 / 64.0

# Each slab is extruded this many steps long, so consecutive slabs overlap in
# volume rather than meeting face to face. Solids that only touch do not merge
# -- a stack built without this comes back as one body per slab.
SLAB_SPAN = 2.0

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
    """The void the strip clips into, drawn upright about its own bed.

    Its origin is the middle of the bed, which is where the strip sits. A
    sweep that turns this outline about that origin therefore turns the
    channel around the strip rather than carrying the strip around with it.
    """
    half_bed, half_mouth = design.channel_width / 2, design.mouth_width / 2
    depth = design.channel_depth
    lip_shoulder = depth - design.lip_height
    return polygon(
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


def twisting(design: Design, length: float, to_tilt: float):
    """A straight run of `length` that carries the channel to a new lean.

    Where the strip ends up does not depend on the lean, and must not depend
    on the twist either. That holds by construction rather than by check: the
    channel is one twisted extrusion about the middle of its own bed, which is
    the strip's axis, and it is cut from the body last. So the channel turns
    around the strip instead of carrying the strip around with it, and nothing
    approximate in the body can reach the strip's seat.

    The body is stacked from slabs because there is nothing to sweep it with.
    The profile's outline changes shape as it leans -- features merge and its
    corner count moves -- so there is no correspondence to loft along, and a
    twisted extrusion of the whole profile would turn the plate off the TV.
    Each slab is the profile with its slot left in, which keeps the thin lips
    out of the merges; they are what a stack of slabs fails on.
    """
    turn = to_tilt - design.tilt
    slabs = max(1, math.ceil(abs(turn) / TWIST_PER_SLAB))
    step = length / slabs
    stacked = [_slab(design, turn, index, slabs, step) for index in range(slabs)]
    # Unioned in order, lowest first, because union is not associative in the
    # output mesh and a stack folded the other way tessellates differently.
    stack = stacked[0]
    for slab in stacked[1:]:
        stack = stack + slab
    stack = stack.trim_by_plane((0.0, 0.0, -1.0), -length)
    # Square both ends back to the lean they claim. A slab spans a step of
    # lean but two steps of length, so the first one carries the next lean's
    # outline into the very start and the last one does the same at the end.
    # That surplus is small, but it lands on the lips, and a neighbour joined
    # to a lip at the wrong angle has its mouth roofed over -- the open slot
    # becomes a tunnel. Paring it off is what lets the runs meet the corner.
    stack = stack - _squared_end(design, 0.0, step)
    stack = stack - _squared_end(design, turn, step).translate(
        (0.0, 0.0, length - step)
    )
    upright = stack - _twisted_channel(design, length, turn, slabs)
    # Lying on its base, as a straight run of the same profile comes out.
    return upright.rotate((90.0, 0.0, 0.0)).translate((0.0, length, 0.0))


def _slab(design, turn: float, index: int, slabs: int, step: float):
    """One slab of a twisting run, reaching past the next so the two merge.

    Taken at both ends of the lean it spans rather than at one: a slab built
    on a single lean trails the channel through its own length, and it is the
    lips that the lag shows up on.
    """
    spanned = _leaning_lump(design, turn * index / slabs) + _leaning_lump(
        design, turn * (index + 1) / slabs
    )
    return spanned.extrude(step * SLAB_SPAN).translate((0.0, 0.0, index * step))


def _leaning_lump(design, by: float):
    """The profile leaned further `by`, with the slot left solid."""
    leaned = replace(design, tilt=design.tilt + by)
    block = _block_outline(leaned).rotate(-leaned.tilt)
    return _plate(leaned) + _arm(leaned) + block.translate((0.0, leaned.floor_height))


def _squared_end(design, by: float, depth: float):
    """A prism of everything `depth` deep that the lean `by` does not fill."""
    outline = _leaning_lump(design, by)
    left, bottom, right, top = outline.bounds()
    surround = rect(left - 1.0, bottom - 1.0, right + 1.0, top + 1.0)
    return (surround - outline).extrude(depth)


def _twisted_channel(design, length: float, turn: float, slabs: int):
    """The slot swept along `length` while turning `turn`, about the strip."""
    return (
        _slot(design)
        .rotate(-design.tilt)
        .extrude(length, n_divisions=slabs, twist_degrees=-turn)
        .translate((0.0, design.floor_height, 0.0))
    )


def led_corner(
    design: Design, radius: float, lead: float, twist: float, from_tilt: float
):
    """A quarter turn with a straight run leading into it and out of it.

    Each run meets the strip at `from_tilt`, holds that lean for the first
    `lead - twist` of its length, and turns to the corner's own lean over the
    last `twist`. The twist is measured back from the corner rather than
    forward from the open end, so the channel arrives upright however long
    either is -- lengthening the run moves the straight part, never the turn.

    The exit is the entry mirrored: a corner's two sides are one shape
    approached from either direction.
    """
    if lead <= 0.0 or twist <= 0.0:
        raise ValueError(f"lead {lead} and twist {twist} must both be positive")
    if twist > lead:
        raise ValueError(
            f"twist {twist} is longer than the {lead} mm lead it has to turn "
            f"within: the turn has to finish before the corner starts"
        )
    running = replace(design, tilt=from_tilt)
    # The twisting run finishes its turn at y=0, which is the face the corner
    # presents; mirroring lays it back along the way the lead comes in.
    run = twisting(running, twist, design.tilt).mirror((0.0, 1.0, 0.0))
    run = run.translate((radius, 0.0, 0.0))
    held = lead - twist
    if held > 0.0:
        run = run + straight(running, held).translate((radius, -lead, 0.0))
    # Union order is fixed deliberately, as everywhere else here.
    return corner(design, radius) + run + run.mirror((1.0, -1.0, 0.0))


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
