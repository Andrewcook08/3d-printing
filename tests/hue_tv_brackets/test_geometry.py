"""The parametric shape: the channel, the lean, and the two sweeps."""

import pytest

from printing3d.hue_tv_brackets.catalog import LADDER_RADII
from printing3d.hue_tv_brackets.geometry import (
    BASE_DEPTH,
    BLOCK_W,
    CHANNEL_D,
    CHANNEL_W,
    CORNER_SEGMENTS,
    FLOOR,
    MIN_CORNER_RADIUS,
    MOUTH,
    TO_BASE_EDGE,
    TO_OUTERMOST,
    TO_TAB_EDGE,
    chord_inset,
    corner,
    leaned,
    profile,
    straight,
)
from printing3d.hue_tv_brackets.verify import slot_width_at, upright_section
from printing3d.shapes import signed_area
from tests.support import contour_digest

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
    assert MOUTH < CHANNEL_W


def test_the_lips_are_what_narrow_it():
    bed = slot_width_at(profile(), 0.05)
    mouth = slot_width_at(profile(), CHANNEL_D - 0.05)
    assert mouth < bed


# ---------------------------------------------------------------------------
# The channel rests on the plate, and everything else follows
# ---------------------------------------------------------------------------


def test_the_channel_block_rests_on_the_base_plane():
    """The one constraint the rest of the profile is derived from."""
    _, resting_height = leaned(BLOCK_W / 2, -FLOOR)
    assert resting_height == pytest.approx(0.0, abs=1e-9)


def test_the_plate_reaches_from_the_tab_edge_to_under_the_block():
    assert TO_TAB_EDGE + TO_BASE_EDGE == pytest.approx(BASE_DEPTH)


def test_the_arm_overhangs_the_pad_it_stands_on():
    """The channel leans out past the plate, which is why it aims off the TV."""
    assert TO_OUTERMOST > TO_BASE_EDGE


def test_the_profile_sits_on_the_mounting_plane():
    _, low_v, _, _ = profile().bounds()
    assert low_v == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# The profile is printable as drawn
# ---------------------------------------------------------------------------


def test_the_profile_encloses_no_pocket():
    assert [c for c in profile().to_polygons() if signed_area(c) < 0] == []


def test_the_profile_is_one_connected_outline():
    assert profile().num_contour() == 1


# ---------------------------------------------------------------------------
# One profile, swept two ways
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("radius", LADDER_RADII)
@pytest.mark.parametrize("degrees", WHERE_FACETS_MEET)
def test_a_corner_is_the_straight_bent(radius, degrees):
    """The design in one assertion: cut a corner where its facets meet and the
    straight's cross-section comes back, exactly."""
    cut = upright_section(corner(radius), degrees).translate((-radius, 0.0))
    reference = profile()
    assert cut.area() == pytest.approx(reference.area(), abs=1e-6)
    assert cut.bounds() == pytest.approx(reference.bounds(), abs=1e-6)


@pytest.mark.parametrize("radius", LADDER_RADII)
@pytest.mark.parametrize("degrees", BETWEEN_FACETS)
def test_between_facets_a_corner_falls_short_by_a_chord_and_no_more(radius, degrees):
    """Cut between two facets and the outline sits a sagitta inside the true
    arc. That inset is the revolve's whole error, and it is bounded."""
    cut = upright_section(corner(radius), degrees).translate((-radius, 0.0))
    assert cut.bounds() == pytest.approx(profile().bounds(), abs=chord_inset(radius))


@pytest.mark.parametrize("radius", LADDER_RADII)
def test_the_facets_are_finer_than_the_printer_can_resolve(radius):
    """Which is what makes the inset above a curiosity rather than a defect."""
    assert chord_inset(radius) < NOZZLE_WIDTH / 10.0


def test_the_chosen_angles_really_do_sit_where_they_claim():
    """Guards the two tests above from swapping their meanings silently."""
    assert all(abs(d / FACET - round(d / FACET)) < 1e-9 for d in WHERE_FACETS_MEET)
    assert all(abs(d / FACET - round(d / FACET)) > 0.1 for d in BETWEEN_FACETS)


@pytest.mark.parametrize("radius", LADDER_RADII)
def test_a_wider_corner_puts_the_same_profile_further_out(radius):
    _, _, _, far_x, _, _ = corner(radius).bounding_box()
    assert far_x == pytest.approx(radius + TO_OUTERMOST)


def test_a_longer_straight_is_the_same_profile_for_longer():
    short, long = straight(25.0), straight(125.0)
    assert long.volume() == pytest.approx(short.volume() * 5.0)


# ---------------------------------------------------------------------------
# A corner cannot be tighter than the part reaching into it
# ---------------------------------------------------------------------------


def test_a_corner_tighter_than_the_profile_is_refused():
    """Below this the tab edge reaches the axis and the wedge folds through
    itself -- a turn a part reaching past its own centre cannot make."""
    with pytest.raises(ValueError, match="reaches the revolve axis"):
        corner(MIN_CORNER_RADIUS)


def test_the_refusal_starts_exactly_where_the_profile_does():
    assert MIN_CORNER_RADIUS == pytest.approx(TO_TAB_EDGE)
    assert corner(MIN_CORNER_RADIUS + 0.01).volume() > 0.0


# ---------------------------------------------------------------------------
# Characterization: the shipped outline, pinned
# ---------------------------------------------------------------------------


# Pinned so a change to the outline names itself here, before the golden master
# reports it as a difference in bytes.
PINNED_VERTICES = 13
PINNED_AREA = 150.544156
PINNED_DIGEST = "5724aa42ecc9a950"


def test_the_shipped_profile_is_unchanged():
    cross_section = profile()
    assert cross_section.num_vert() == PINNED_VERTICES
    assert cross_section.area() == pytest.approx(PINNED_AREA, abs=1e-6)
    assert contour_digest(cross_section) == PINNED_DIGEST
