"""The parametric shape: the cradle, the supports, the profile, the bores."""

import math

import pytest
from manifold3d import Manifold

from printing3d.fishing_rod_mounts.catalog import catalogue
from printing3d.fishing_rod_mounts.geometry import (
    ARM_AND_GUSSET,
    WEDGE,
    Cradle,
    MountSpec,
    build,
    profile,
    screw_cut,
    tangent_slope,
)
from printing3d.shapes import signed_area
from tests.support import contour_digest

# The shape these tests measure is the one the project ships, so its numbers
# come from the same place the build gets them.
DESIGN = catalogue().design
AXIS_U = DESIGN.axis_from_wall
AXIS_V = DESIGN.axis_height
PLATE_THK = DESIGN.plate_thickness
RIB = DESIGN.rib
ROD_CLEARANCE = DESIGN.rod_clearance
CSINK_D = DESIGN.screw.countersink_diameter
CSINK_INCLUDED = DESIGN.screw.countersink_included_angle
SCREW_CLEAR_D = DESIGN.screw.clearance_diameter

BUTT_DIA = 26.15
TIP_DIA = 5.80
ALL_DIAMETERS = (5.8, 12.0, 26.15)


def butt_spec(rod_dia=BUTT_DIA):
    return MountSpec(
        rod_dia=rod_dia, support=ARM_AND_GUSSET, lip_rise=5.0, design=DESIGN
    )


def tip_spec(rod_dia=TIP_DIA):
    return MountSpec(rod_dia=rod_dia, support=WEDGE, lip_rise=0.0, design=DESIGN)


SHIPPED_SPECS = pytest.mark.parametrize(
    "spec", [butt_spec(), tip_spec()], ids=["butt", "tip"]
)


# ---------------------------------------------------------------------------
# Cradle
# ---------------------------------------------------------------------------


def test_the_seat_is_the_rod_plus_its_fit_clearance():
    assert Cradle(rod_dia=10.0, design=DESIGN).radius == pytest.approx(
        (10.0 + ROD_CLEARANCE) / 2
    )


def test_the_rib_wraps_the_seat_at_uniform_thickness():
    cradle = Cradle(rod_dia=10.0, design=DESIGN)
    assert cradle.outer_radius - cradle.radius == pytest.approx(RIB)


def test_a_fatter_rod_leaves_less_room_behind_it_and_sticks_out_further():
    thin, thick = (
        Cradle(rod_dia=TIP_DIA, design=DESIGN),
        Cradle(rod_dia=BUTT_DIA, design=DESIGN),
    )
    assert thick.standoff_behind_rod < thin.standoff_behind_rod
    assert thick.projection_from_wall > thin.projection_from_wall


@pytest.mark.parametrize("rod_dia", ALL_DIAMETERS)
def test_every_cradle_seats_the_rod_on_the_shared_axis(rod_dia):
    """This is what lets two mounts built for different diameters hang one rod
    level and parallel to the wall."""
    cradle = Cradle(rod_dia, design=DESIGN)
    assert cradle.standoff_behind_rod + cradle.radius == pytest.approx(AXIS_U)
    assert cradle.floor_v + cradle.radius == pytest.approx(AXIS_V)


# ---------------------------------------------------------------------------
# Supports
# ---------------------------------------------------------------------------


def test_a_low_arm_needs_no_gusset():
    assert len(ARM_AND_GUSSET.pieces(Cradle(rod_dia=BUTT_DIA, design=DESIGN))) == 1


def test_a_high_arm_is_braced_by_a_gusset():
    assert len(ARM_AND_GUSSET.pieces(Cradle(rod_dia=10.0, design=DESIGN))) == 2


def test_the_wedge_is_one_unbroken_strut():
    assert len(WEDGE.pieces(Cradle(rod_dia=TIP_DIA, design=DESIGN))) == 1


def test_the_wedge_reaches_from_the_plate_to_the_cradle():
    (strut,) = WEDGE.pieces(Cradle(rod_dia=TIP_DIA, design=DESIGN))
    lo_u, lo_v, _hi_u, hi_v = strut.bounds()
    assert lo_u == pytest.approx(PLATE_THK)
    assert lo_v == pytest.approx(0.0)
    assert hi_v == pytest.approx(AXIS_V)


# ---------------------------------------------------------------------------
# The wedge angle, which nothing is allowed to set by hand
# ---------------------------------------------------------------------------


def underside_height_at(slope, u, corner_u=PLATE_THK):
    return slope * (u - corner_u)


def distance_from_rod_axis(slope, corner_u=PLATE_THK):
    """Perpendicular distance from the rod's centerline to the wedge's
    underside, written as slope*u - v - slope*corner_u = 0."""
    return abs(slope * AXIS_U - AXIS_V - slope * corner_u) / math.hypot(slope, 1.0)


def test_the_undersides_line_leaves_the_plates_bottom_corner():
    slope = tangent_slope(PLATE_THK, *Cradle(TIP_DIA, design=DESIGN).outer_circle)
    assert underside_height_at(slope, PLATE_THK) == pytest.approx(0.0)


@pytest.mark.parametrize("rod_dia", ALL_DIAMETERS)
def test_the_underside_just_touches_the_crescents_outer_circle(rod_dia):
    """Tangent, not merely close: that is what removes the kink where the
    strut meets the curve."""
    cradle = Cradle(rod_dia, design=DESIGN)
    slope = tangent_slope(PLATE_THK, *cradle.outer_circle)
    assert distance_from_rod_axis(slope) == pytest.approx(cradle.outer_radius)


def test_the_wedge_passes_below_the_rod():
    slope = tangent_slope(PLATE_THK, *Cradle(TIP_DIA, design=DESIGN).outer_circle)
    assert underside_height_at(slope, AXIS_U) < AXIS_V


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------


@SHIPPED_SPECS
def test_no_shipped_profile_encloses_a_pocket(spec):
    assert [c for c in profile(spec).to_polygons() if signed_area(c) < 0] == []


@SHIPPED_SPECS
def test_the_profile_is_one_connected_outline(spec):
    assert len(profile(spec).to_polygons()) == 1


# Vertex-level characterization, so a geometry change names itself here before
# it shows up as an opaque hash mismatch in the golden master.
PINNED_PROFILES = {
    "butt": (butt_spec(), 399, 358.536789825, "9b7e4b38c240b0ba"),
    "tip": (tip_spec(), 341, 333.206225380, "b61ad284cab97e31"),
}


@pytest.mark.parametrize("kind", sorted(PINNED_PROFILES))
def test_the_shipped_profile_is_unchanged(kind):
    spec, points, area, digest = PINNED_PROFILES[kind]
    cross_section = profile(spec)
    assert sum(len(c) for c in cross_section.to_polygons()) == points
    assert cross_section.area() == pytest.approx(area, abs=1e-6)
    assert contour_digest(cross_section) == digest


# ---------------------------------------------------------------------------
# Screw bores
#
# The plate's back face (u = 0) lies against the wall and must stay a flat
# unbroken pad for tape; the countersink opens out on the front face
# (u = PLATE_THK), where the screw head finishes flush.
# ---------------------------------------------------------------------------

OFF_AXIS = CSINK_D / 2.0 - 1.0  # inside the countersink, outside the bore


class BoreProbe:
    """Samples a built mount along one screw bore."""

    def __init__(self, spec):
        self.solid = build(spec)
        self.height = spec.design.screw.heights[0]
        self.mid_width = spec.design.slab_width / 2.0

    def material_at(self, u, off_axis=0.0, size=0.1):
        cube = Manifold.cube((size, size, size), True).translate(
            (u, self.height, self.mid_width + off_axis)
        )
        return (self.solid ^ cube).volume() > 1e-9

    def open_radius_at(self, u, step=0.05):
        """How far off the bore's axis the hole is still open, at depth u."""
        offset = 0.0
        while not self.material_at(u, offset):
            offset += step
        return offset


@pytest.fixture(scope="module")
def bore():
    return BoreProbe(tip_spec())


@pytest.mark.parametrize("u", [0.2, PLATE_THK / 2.0, PLATE_THK - 0.2])
def test_the_bore_runs_clear_through_the_backplate(bore, u):
    assert not bore.material_at(u)


def test_the_back_face_stays_a_flat_unbroken_pad(bore):
    assert bore.material_at(0.3, OFF_AXIS)


def test_the_countersink_opens_out_on_the_front_face(bore):
    assert not bore.material_at(PLATE_THK - 0.3, OFF_AXIS)


def test_the_bore_is_a_plain_through_hole_at_the_back(bore):
    assert bore.open_radius_at(0.3) == pytest.approx(SCREW_CLEAR_D / 2, abs=0.2)


def test_the_countersink_tapers_at_the_screw_heads_own_angle(bore):
    shallow, deep = 2.5, PLATE_THK - 0.3
    taper = (bore.open_radius_at(deep) - bore.open_radius_at(shallow)) / (
        deep - shallow
    )
    assert taper == pytest.approx(math.tan(math.radians(CSINK_INCLUDED) / 2), abs=0.05)


def test_the_cut_is_centered_on_the_screw_and_across_the_slab():
    spec = tip_spec()
    _lo_u, lo_v, lo_w, _hi_u, hi_v, hi_w = screw_cut(
        spec.design.screw.heights[0], DESIGN
    ).bounding_box()
    assert (lo_w + hi_w) / 2 == pytest.approx(spec.design.slab_width / 2)
    assert (lo_v + hi_v) / 2 == pytest.approx(spec.design.screw.heights[0])
