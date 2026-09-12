"""The parametric solid model of one wall mount.

Shape follows stl/wall_hook_for_3mm_screw(2).stl: a thin backplate, a curved
rib that wraps the load, and a triangular gusset -- open sides rather than a
solid block. Rebuilt parametrically rather than scaled, because scaling the
reference mesh to the 5.80 mm blank (0.22x) would shrink its 3 mm screw hole
to 0.66 mm and the backplate to 11 x 3.3 mm.

A mount is a 2D profile extruded sideways, with the screw bores drilled
afterwards. Everything is measured from two shared anchors, AXIS_U and AXIS_V,
which fix where the rod's centerline sits; every other dimension follows from
the rod's diameter. That is what lets a butt mount and a tip mount built for
very different diameters hang the same rod level and parallel to the wall.
"""

import math
from dataclasses import dataclass
from typing import Protocol

import manifold3d as m

from printing3d.shapes import (
    polygon,
    rect,
    rounded_convex_corners,
    without_enclosed_voids,
)

# ---------------------------------------------------------------------------
# Shared anchors -- every mount agrees on these, so every mount interchanges
# ---------------------------------------------------------------------------

# Where the rod's centerline sits. Every mount agrees on these two.
AXIS_U = 18.0  # distance from the wall face
AXIS_V = 17.5  # height above the part's bottom edge

# Backplate thickness. Also the removal-channel limit: nothing above the cradle
# may sit further from the wall than this, or the rod -- a long cylinder that
# cannot dodge sideways -- is trapped.
PLATE_THK = 4.0

# Backplate height. Screws must sit ABOVE the rod: the load always tries to
# peel the TOP off the wall.
PLATE_H = 35.0

RIB = 4.0  # thickness of the curved rib and the arm
LIP_RISE = 5.0  # how far the rib rises past the rod centerline
LIP_CHAMFER = 1.2  # 45-degree lead-in so the rod drops in easily
ROD_CLEARANCE = 0.6  # added to rod diameter -> cradle diameter
FILLET = 0.8  # softening on convex corners

DEFAULT_SCREW_HEIGHTS = (27.5,)
SCREW_CLEAR_D = 4.2  # through-hole: clears #6, #8 and M4

# Countersunk on the FRONT face, so the back stays a flat unbroken pad for tape.
CSINK_D = 8.4
CSINK_INCLUDED = 90.0

# Tuning that only affects tessellation and the size of throwaway cutting
# bodies -- named so the geometry above reads as design intent, not arithmetic.
CIRCLE_SEGMENTS = 192  # facets around the cradle and the rib
CLIP_MARGIN = 1.0  # overshoot when halving the rib's annulus
CHANNEL_OVERSHOOT = 20.0  # how far the lift-out channel runs past the plate
MIN_GUSSET_HEIGHT = 2.0  # below this the arm reaches the bottom edge anyway
FLUSH_LIP_CHAMFER = 0.4  # chamfer scale where there is no lip to lead into
BORE_START_U = -5.0  # screw bores start behind the wall face...
BORE_LENGTH = 60.0  # ...and run well past the front of any mount
CSINK_OVERCUT = 4.0  # countersink cone continues past the front face
BORE_SEGMENTS = 64  # facets around a screw bore


# ---------------------------------------------------------------------------
# Cradle: the circles and key points that one rod diameter implies
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Cradle:
    """Where the rod sits, and the geometry the rest of the mount hangs off."""

    rod_dia: float

    @property
    def radius(self):
        """Inner radius of the cradle: the rod plus its fit clearance."""
        return (self.rod_dia + ROD_CLEARANCE) / 2.0

    @property
    def outer_radius(self):
        """Outer radius of the curved rib wrapped around the cradle."""
        return self.radius + RIB

    @property
    def floor_v(self):
        """Height of the lowest point of the cradle -- where the arm meets it."""
        return AXIS_V - self.radius

    @property
    def wall_side_u(self):
        """Outer face of the cradle's wall-side wall."""
        return AXIS_U - self.radius - RIB

    @property
    def standoff_behind_rod(self):
        """Material between the wall face and the rod's nearest surface."""
        return AXIS_U - self.radius

    @property
    def projection_from_wall(self):
        """How far the finished mount stands out from the wall."""
        return AXIS_U + self.radius + RIB


# ---------------------------------------------------------------------------
# Supports: the two ways a cradle is carried out from the wall
# ---------------------------------------------------------------------------


class Support(Protocol):
    """Structure between the backplate and the cradle.

    Returns its pieces in the order they are unioned into the profile, rather
    than one combined shape, so that adding a piece never disturbs the ones
    already placed.
    """

    def pieces(self, cradle: Cradle) -> list: ...


class ArmAndGusset:
    """A short floor under the cradle, braced by a triangular gusset.

    Used where the cradle is wide enough to reach most of the way to the wall
    on its own -- the thick grip at the butt of the rod. The gusset is skipped
    when the arm sits so low that the crescent already meets the bottom edge.
    """

    def pieces(self, cradle):
        arm_base_v = cradle.floor_v - RIB
        arm = rect(0.0, arm_base_v, AXIS_U, cradle.floor_v)
        if arm_base_v <= MIN_GUSSET_HEIGHT:
            return [arm]
        return [arm, self._gusset(arm_base_v)]

    @staticmethod
    def _gusset(arm_base_v):
        return polygon(
            [(PLATE_THK, 0.0), (AXIS_U, arm_base_v), (PLATE_THK, arm_base_v)]
        )


class Wedge:
    """A single tapered strut, replacing the arm and gusset entirely.

    Used where the cradle is far too small to span the gap on its own -- the
    skinny blank at the tip, which has to be kicked out to match the grip.

    The strut's top and bottom faces are PARALLEL. The top face is pinned to
    the top of the cradle's wall-side wall (which is what removes the nub); the
    bottom face is pinned to the plate's bottom corner and runs tangent to the
    crescent's outer circle, so it merges into the curve without a kink.
    Requiring those two lines to be parallel fully determines the angle --
    there is nothing to tune.
    """

    def pieces(self, cradle):
        slope = tangent_slope_from_corner(cradle.outer_radius, PLATE_THK)
        tangent_u, tangent_v = self._tangent_point(cradle.outer_radius, slope)
        top_face_rise = slope * (cradle.wall_side_u - PLATE_THK)
        return [
            polygon(
                [
                    (PLATE_THK, 0.0),
                    (tangent_u, tangent_v),
                    (tangent_u, AXIS_V),
                    (cradle.wall_side_u, AXIS_V),
                    (PLATE_THK, AXIS_V - top_face_rise),
                ]
            )
        ]

    @staticmethod
    def _tangent_point(outer_radius, slope):
        normal = math.sqrt(slope * slope + 1.0)
        return (AXIS_U + outer_radius * slope / normal, AXIS_V - outer_radius / normal)


ARM_AND_GUSSET = ArmAndGusset()
WEDGE = Wedge()


def tangent_slope_from_corner(outer_radius, corner_u):
    """Slope of the line from (corner_u, 0) tangent to the crescent's outer
    circle from below.

    Lets the wedge's underside diagonal and the diagonal above it be parallel
    while each stays pinned to the feature it must meet.
    """
    run = AXIS_U - corner_u
    a = run * run - outer_radius * outer_radius
    b = -2.0 * run * AXIS_V
    c = AXIS_V * AXIS_V - outer_radius * outer_radius
    return (-b - math.sqrt(b * b - 4.0 * a * c)) / (2.0 * a)


# ---------------------------------------------------------------------------
# One mount, as parameters
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MountSpec:
    """Everything that distinguishes one mount from another."""

    rod_dia: float
    width: float
    support: Support
    lip_rise: float
    screw_heights: tuple = DEFAULT_SCREW_HEIGHTS
    plate_h: float = PLATE_H

    @property
    def cradle(self):
        return Cradle(self.rod_dia)


# ---------------------------------------------------------------------------
# Profile: plate + crescent + support, then the rod's space carved back out
# ---------------------------------------------------------------------------


def profile(spec):
    """The 2D cross-section that gets extruded into a mount."""
    cradle = spec.cradle
    part = rect(0.0, 0.0, PLATE_THK, spec.plate_h)
    part = part + _crescent(cradle, spec.lip_rise)
    for piece in spec.support.pieces(cradle):
        part = part + piece
    part = part - _rod_space_and_lift_channel(cradle, spec.plate_h)
    part = part - _lip_lead_in(cradle, spec.lip_rise)
    return rounded_convex_corners(without_enclosed_voids(part), FILLET)


def _crescent(cradle, lip_rise):
    """The curved rib around the rod: the lower half of an annulus, plus the
    outer lip that rises past the centerline so the rod must be lifted
    deliberately before it can roll forward."""
    ring = m.CrossSection.circle(
        cradle.outer_radius, CIRCLE_SEGMENTS
    ) - m.CrossSection.circle(cradle.radius, CIRCLE_SEGMENTS)
    reach = cradle.outer_radius + CLIP_MARGIN
    lower_half = ring ^ rect(-reach, -reach, reach, 0.0)
    if lip_rise > 0:
        lip = rect(cradle.radius, 0.0, cradle.outer_radius, lip_rise)
        lower_half = lower_half + lip
    return lower_half.translate((AXIS_U, AXIS_V))


def _rod_space_and_lift_channel(cradle, plate_h):
    """The rod's seat plus the channel it travels up through on its way out.

    Subtracting this explicitly -- rather than relying on every member added
    above to stay clear of it -- keeps the cradle and the removal channel
    correct by construction no matter what else is unioned in.
    """
    seat = m.CrossSection.circle(cradle.radius, CIRCLE_SEGMENTS).translate(
        (AXIS_U, AXIS_V)
    )
    channel = rect(
        AXIS_U - cradle.radius,
        AXIS_V,
        AXIS_U + cradle.radius,
        plate_h + CHANNEL_OVERSHOOT,
    )
    return seat + channel


def _lip_lead_in(cradle, lip_rise):
    """A 45-degree chamfer off the top of the lip, so the rod drops in rather
    than catching on the edge."""
    chamfer = LIP_CHAMFER if lip_rise > 0 else LIP_CHAMFER * FLUSH_LIP_CHAMFER
    leg = chamfer * 2
    lip_top = AXIS_V + lip_rise
    outer_u = AXIS_U + cradle.radius
    return polygon(
        [
            (outer_u, lip_top),
            (outer_u + leg, lip_top),
            (outer_u, lip_top - leg),
        ]
    )


# ---------------------------------------------------------------------------
# Solid: the profile extruded, then drilled
# ---------------------------------------------------------------------------


def build(spec):
    """The finished mount as a solid, ready to export."""
    solid = profile(spec).extrude(spec.width)
    for height in spec.screw_heights:
        solid = solid - screw_cut(height, spec.width)
    return solid


def screw_cut(height, width):
    """Through-hole plus front-face countersink, drilled horizontally."""
    half_angle = math.radians(CSINK_INCLUDED) / 2.0
    depth = (CSINK_D - SCREW_CLEAR_D) / 2.0 / math.tan(half_angle)
    shank_r = SCREW_CLEAR_D / 2.0

    shank = (
        m.Manifold.cylinder(BORE_LENGTH, shank_r, shank_r, BORE_SEGMENTS, False)
        .rotate((0.0, 90.0, 0.0))
        .translate((BORE_START_U, height, width / 2.0))
    )

    cone_h = depth + CSINK_OVERCUT
    cone = (
        m.Manifold.cylinder(
            cone_h,
            shank_r,
            shank_r + cone_h * math.tan(half_angle),
            BORE_SEGMENTS,
            False,
        )
        .rotate((0.0, 90.0, 0.0))
        .translate((PLATE_THK - depth, height, width / 2.0))
    )
    return shank + cone
