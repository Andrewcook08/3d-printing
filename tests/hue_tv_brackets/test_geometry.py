"""The parametric shape: the channel, the lean, and the two sweeps."""

import math
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
from printing3d.shapes import polygon, signed_area
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


# The leans the shipped outboard reach covers. Below about 45 degrees the
# block's resting corner lands outside the pad and the design refuses itself,
# which the test below this one pins.
@pytest.mark.parametrize("tilt", (DESIGN.tilt, 55.0, 65.0, 77.5, 85.0, 90.0))
def test_the_channel_block_clears_the_base_plane_at_any_lean(tilt):
    """It used to rest on the plane, and that was the whole problem.

    Resting on it made the floor height a consequence of the lean, so the strip
    moved whenever the lean changed. The block now floats, by however much the
    fixed floor height exceeds what this lean would have rested at -- never
    below, which is what this asserts.

    Asserted across the range rather than at the angle we ship: the resting
    height is a sine term plus a cosine term whose sum peaks in the middle of
    the range, so a version of this that held at both ends could still fail
    between them.
    """
    leaning = replace(DESIGN, tilt=tilt)
    corner = leaning.leaned(leaning.block_width / 2, -leaning.floor_thickness)
    assert corner.v >= -1e-9, f"{tilt} degrees dips {corner.v} mm through the plane"


# Every lean the shipped outboard reach covers, including the one where the
# resting height peaks (the old derivation's worst case) and the one where the
# arm closes to nothing.
EVERY_LEAN = (45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 77.5, 80.0, 85.0, 90.0)


def chord_inset(design, radius):
    """How far a cut between two facets falls inside the true arc.

    The revolve approximates the arc with flat facets, so a section taken
    between two of them sits a chord's sagitta short of the radius. It is the
    bound on how much a corner's section may differ from the straight's it was
    swept from -- an error budget for the two tests below, which is why it
    lives with them rather than on the shape they measure.
    """
    half_facet = math.radians(360.0 / CORNER_SEGMENTS / 2.0)
    return (radius + design.to_outermost) * (1.0 - math.cos(half_facet))


def profile_at(tilt):
    return profile(replace(DESIGN, tilt=tilt))


def edges_of(cross_section):
    """Every edge of a profile, as (length, midpoint)."""
    for contour in cross_section.to_polygons():
        for index in range(len(contour)):
            start, end = contour[index], contour[(index + 1) % len(contour)]
            length = math.hypot(end[0] - start[0], end[1] - start[1])
            midpoint = ((start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0)
            yield length, midpoint


def bed_midpoint(cross_section, width):
    """Where the strip sits, read off the built profile.

    The bed is the edge as long as the channel is wide whose midpoint sits on
    the strip's centreline -- the datum everything outboard is measured from.
    Both halves are needed: upright, the block embeds itself in the plate and
    splits the plate's top edge into a piece that is also exactly that long.

    Found by measuring rather than by asking the design where it put the strip,
    so this cannot agree with a derivation that is wrong.
    """
    found = [
        mid
        for length, mid in edges_of(cross_section)
        if abs(length - width) < 1e-6 and abs(mid[0]) < 1e-9
    ]
    assert len(found) == 1, f"expected one bed {width} mm wide, found {len(found)}"
    return found[0]


def resting_on_the_plane(cross_section):
    """How far outboard the profile still touches the TV back."""
    return max(
        u
        for contour in cross_section.to_polygons()
        for u, v in contour
        if abs(v) < 1e-9
    )


# ---------------------------------------------------------------------------
# The strip's place does not depend on the lean
# ---------------------------------------------------------------------------


def test_the_strip_sits_at_one_height_whatever_the_lean():
    """The point of the whole arrangement.

    Compared across leans rather than against a number, so it never reads back
    the derivation it is testing: whatever the height turns out to be, every
    lean has to agree on it.
    """
    heights = {
        tilt: bed_midpoint(profile_at(tilt), DESIGN.channel_width)
        for tilt in EVERY_LEAN
    }
    first = heights[EVERY_LEAN[0]]
    for tilt, place in heights.items():
        assert place == pytest.approx(first, abs=1e-9), (
            f"{tilt} degrees puts the strip at {place}"
        )


def test_the_plate_reaches_the_same_distance_from_the_strip_whatever_the_lean():
    """Butting every bracket to one marked line has to put the strip in one
    place, which it only does while this is the same at every lean."""
    reaches = {tilt: resting_on_the_plane(profile_at(tilt)) for tilt in EVERY_LEAN}
    for tilt, reach in reaches.items():
        assert reach == pytest.approx(DESIGN.pad_outboard, abs=1e-9), f"{tilt} degrees"


@pytest.mark.parametrize("tilt", EVERY_LEAN)
def test_no_part_of_the_profile_hangs_below_the_tv_back(tilt):
    """Anything below the plane is plastic the bracket would rock on."""
    lowest = min(v for contour in profile_at(tilt).to_polygons() for _, v in contour)
    assert lowest == pytest.approx(0.0, abs=1e-9), f"{tilt} degrees reaches {lowest} mm"


@pytest.mark.parametrize("tilt", EVERY_LEAN)
def test_the_profile_is_one_piece_with_its_bed_full_width(tilt):
    """A plate reaching under the channel fills the bottom of the slot, which
    shortens the bed without breaking anything visible."""
    section = profile_at(tilt)
    assert len(section.to_polygons()) == 1
    bed_midpoint(section, DESIGN.channel_width)


@pytest.mark.parametrize("tilt", EVERY_LEAN)
def test_nothing_is_hollow_beneath_the_channel(tilt):
    """The floor stands above what would rest the block on the plane, so the
    space underneath has to be filled rather than spanned.

    Counting enclosed voids does not catch this. The gap an arm leaves when it
    runs straight to the apex instead of climbing the block's outboard face
    first is open to the outside, so the profile stays one contour with no void
    in it and the bed keeps its width -- it is simply missing plastic where the
    channel needs carrying.

    The region is built from the block's own corners rather than from the arm,
    so it describes what must be solid without assuming how.
    """
    leaning = replace(DESIGN, tilt=tilt)
    resting = leaning.leaned(leaning.block_width / 2, -leaning.floor_thickness)
    apex = leaning.arm_apex
    beneath = polygon(
        [(resting.u, 0.0), (resting.u, resting.v), (apex.u, apex.v), (apex.u, 0.0)]
    )
    missing = (beneath - profile_at(tilt)).area()
    assert missing == pytest.approx(0.0, abs=1e-9), f"{missing:.4f} mm2 unfilled"


def test_a_reach_that_leaves_the_block_off_the_pad_is_refused():
    """The lean the pad cannot cover has to say so rather than build."""
    with pytest.raises(ValueError, match="resting corner"):
        replace(DESIGN, tilt=30.0)


def test_the_shallowest_lean_the_pad_covers_is_where_it_says_it_is():
    """Straddles the refusal rather than testing well inside it.

    The shipped lean clears the bound by about a third of a degree, which is
    close enough that a change to the channel's own numbers can cross it: half
    a millimetre more wall pushes the resting corner past the reach and refuses
    the shipped design itself. Pinning both sides of the edge means a change
    that moves it fails here, naming the lean, rather than somewhere further
    on.
    """
    boundary = 44.63
    replace(DESIGN, tilt=boundary + 0.05)
    with pytest.raises(ValueError, match="resting corner"):
        replace(DESIGN, tilt=boundary - 0.05)


def test_a_reach_that_leaves_no_tab_is_refused():
    with pytest.raises(ValueError, match="no tab"):
        replace(DESIGN, pad_outboard=DESIGN.base_depth)


def test_the_plate_reaches_from_the_tab_edge_to_its_given_outboard_reach():
    """The footprint is the whole plate, so the tab is what the reach leaves."""
    assert DESIGN.to_tab_edge + DESIGN.pad_outboard == pytest.approx(DESIGN.base_depth)


def test_the_arm_overhangs_the_pad_it_stands_on():
    """The channel leans out past the plate, which is why it aims off the TV."""
    assert DESIGN.to_outermost > DESIGN.pad_outboard


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
        profile(DESIGN).bounds(), abs=chord_inset(DESIGN, radius)
    )


@pytest.mark.parametrize("radius", RADII)
def test_the_facets_are_finer_than_the_printer_can_resolve(radius):
    """Which is what makes the inset above a curiosity rather than a defect."""
    assert chord_inset(DESIGN, radius) < NOZZLE_WIDTH / 10.0


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
PINNED_VERTICES = 14
PINNED_AREA = 172.446699
PINNED_DIGEST = "6d0787ef9da2002e"


def test_the_shipped_profile_is_unchanged():
    cross_section = profile(DESIGN)
    assert cross_section.num_vert() == PINNED_VERTICES
    assert cross_section.area() == pytest.approx(PINNED_AREA, abs=1e-6)
    assert contour_digest(cross_section) == PINNED_DIGEST
