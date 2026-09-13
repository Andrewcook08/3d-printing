"""The parametric shape: the channel, the lean, and the two sweeps."""

from dataclasses import replace

import pytest

from printing3d.hue_tv_brackets.catalog import shipping
from printing3d.hue_tv_brackets.geometry import (
    CORNER_SEGMENTS,
    corner,
    profile,
    straight,
)
from printing3d.hue_tv_brackets.verify import (
    PROBE_BAND,
    slot_width_at,
    upright_section,
)
from printing3d.shapes import signed_area
from tests.support import contour_digest

# The shape these tests measure is the one the project ships, so its numbers
# come from the same place the build gets them.
DESIGN = shipping().design
RADII = [30.0, 55.0, 101.0]

# A section taken where two facets meet is the profile itself; one taken
# between them is a chord short of it. Both claims are worth asserting.
FACET = 360.0 / CORNER_SEGMENTS
WHERE_FACETS_MEET = (22.5, 45.0, 67.5)
BETWEEN_FACETS = (15.0, 75.0)
NOZZLE_WIDTH = 0.4


# ---------------------------------------------------------------------------
# The channel clips
# ---------------------------------------------------------------------------


def test_the_mouth_is_narrower_than_the_bed_it_opens_onto():
    """Without this the channel is a trough and the strip lifts straight out."""
    assert DESIGN.mouth_width < DESIGN.channel_width


def test_the_lips_are_what_narrow_it():
    bed = slot_width_at(profile(DESIGN), PROBE_BAND, DESIGN)
    mouth = slot_width_at(profile(DESIGN), DESIGN.channel_depth - PROBE_BAND, DESIGN)
    assert mouth < bed


# ---------------------------------------------------------------------------
# The channel rests on the plate, and everything else follows
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("tilt", (25.0, 30.0, 35.0, DESIGN.tilt, 55.0, 65.0))
def test_the_channel_block_rests_on_the_base_plane_at_any_lean(tilt):
    """The one constraint the rest of the profile is derived from.

    Asserted across the range rather than at the angle we ship: the height is a
    sine term plus a cosine term, and those agree only at 45 degrees, so a
    version of this that held for the wrong reason would still pass there.
    """
    assert replace(DESIGN, tilt=tilt).leaned(
        DESIGN.block_width / 2, -DESIGN.floor_thickness
    ).v == pytest.approx(0.0, abs=1e-9)


def test_the_plate_reaches_from_the_tab_edge_to_under_the_block():
    assert DESIGN.to_tab_edge + DESIGN.to_base_edge == pytest.approx(DESIGN.base_depth)


def test_the_arm_overhangs_the_pad_it_stands_on():
    """The channel leans out past the plate, which is why it aims off the TV."""
    assert DESIGN.to_outermost > DESIGN.to_base_edge


def test_the_profile_sits_on_the_mounting_plane():
    _, low_v, _, _ = profile(DESIGN).bounds()
    assert low_v == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# The profile is printable as drawn
# ---------------------------------------------------------------------------


def test_the_profile_encloses_no_pocket():
    assert [c for c in profile(DESIGN).to_polygons() if signed_area(c) < 0] == []


def test_the_profile_is_one_connected_outline():
    assert profile(DESIGN).num_contour() == 1


# ---------------------------------------------------------------------------
# One profile, swept two ways
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("radius", RADII)
@pytest.mark.parametrize("degrees", WHERE_FACETS_MEET)
def test_a_corner_is_the_straight_bent(radius, degrees):
    """The design in one assertion: cut a corner where its facets meet and the
    straight's cross-section comes back, exactly."""
    cut = upright_section(corner(DESIGN, radius), degrees).translate((-radius, 0.0))
    reference = profile(DESIGN)
    assert cut.area() == pytest.approx(reference.area(), abs=1e-6)
    assert cut.bounds() == pytest.approx(reference.bounds(), abs=1e-6)


@pytest.mark.parametrize("radius", RADII)
@pytest.mark.parametrize("degrees", BETWEEN_FACETS)
def test_between_facets_a_corner_falls_short_by_a_chord_and_no_more(radius, degrees):
    """Cut between two facets and the outline sits a sagitta inside the true
    arc. That inset is the revolve's whole error, and it is bounded."""
    cut = upright_section(corner(DESIGN, radius), degrees).translate((-radius, 0.0))
    assert cut.bounds() == pytest.approx(
        profile(DESIGN).bounds(), abs=DESIGN.chord_inset(radius)
    )


@pytest.mark.parametrize("radius", RADII)
def test_the_facets_are_finer_than_the_printer_can_resolve(radius):
    """Which is what makes the inset above a curiosity rather than a defect."""
    assert DESIGN.chord_inset(radius) < NOZZLE_WIDTH / 10.0


def test_the_chosen_angles_really_do_sit_where_they_claim():
    """Guards the two tests above from swapping their meanings silently."""
    assert all(abs(d / FACET - round(d / FACET)) < 1e-9 for d in WHERE_FACETS_MEET)
    assert all(abs(d / FACET - round(d / FACET)) > 0.1 for d in BETWEEN_FACETS)


@pytest.mark.parametrize("radius", RADII)
def test_a_corner_reaches_its_radius_plus_the_profile(radius):
    _, _, _, far_x, _, _ = corner(DESIGN, radius).bounding_box()
    assert far_x == pytest.approx(radius + DESIGN.to_outermost)


def test_a_wider_corner_puts_the_same_profile_further_out():
    """Widening moves the profile; it does not reshape it."""
    narrow, wide = min(RADII), max(RADII)
    _, _, _, near_reach, _, _ = corner(DESIGN, narrow).bounding_box()
    _, _, _, far_reach, _, _ = corner(DESIGN, wide).bounding_box()
    assert far_reach - near_reach == pytest.approx(wide - narrow)


def test_a_longer_straight_is_the_same_profile_for_longer():
    short, long = straight(DESIGN, 25.0), straight(DESIGN, 125.0)
    assert long.volume() == pytest.approx(short.volume() * 5.0)


# ---------------------------------------------------------------------------
# A corner cannot be tighter than the part reaching into it
# ---------------------------------------------------------------------------


def test_a_corner_tighter_than_the_profile_is_refused():
    """Below this the tab edge reaches the axis and the wedge folds through
    itself -- a turn a part reaching past its own centre cannot make."""
    with pytest.raises(ValueError, match="reaches the revolve axis"):
        corner(DESIGN, DESIGN.min_corner_radius)


def test_a_corner_just_wider_than_the_profile_is_built():
    """The refusal is a floor, not a margin: one hundredth wider is fine."""
    assert corner(DESIGN, DESIGN.min_corner_radius + 0.01).volume() > 0.0


# ---------------------------------------------------------------------------
# Characterization: the shipped outline, pinned
# ---------------------------------------------------------------------------


# Pinned so a change to the outline names itself here, before the golden master
# reports it as a difference in bytes.
PINNED_VERTICES = 13
PINNED_AREA = 150.544156
PINNED_DIGEST = "5724aa42ecc9a950"


def test_the_shipped_profile_is_unchanged():
    cross_section = profile(DESIGN)
    assert cross_section.num_vert() == PINNED_VERTICES
    assert cross_section.area() == pytest.approx(PINNED_AREA, abs=1e-6)
    assert contour_digest(cross_section) == PINNED_DIGEST
