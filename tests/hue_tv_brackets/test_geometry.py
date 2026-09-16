"""The parametric shape: the channel, the lean, and the two sweeps."""

import math
from dataclasses import replace

import pytest

from printing3d.hue_tv_brackets.catalog import shipping
from printing3d.hue_tv_brackets.geometry import (
    CORNER_SEGMENTS,
    corner,
    led_corner,
    profile,
    straight,
    twisting,
)
from printing3d.hue_tv_brackets.verify import (
    PROBE_BAND,
    slot_width_at,
    upright_section,
)
from printing3d.shapes import polygon, rect, signed_area
from tests.support import contour_digest

# The shape these tests measure is the one the project ships, so its numbers
# come from the same place the build gets them.
DESIGN = shipping().design
UPRIGHT = replace(DESIGN, tilt=90.0)  # how a corner stands, as parts.toml asks
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
    so it describes what must be solid without assuming how. It stops at the
    plate's edge: past that the block deliberately overhangs, because an arm
    following it out would stand on the TV outboard of the pad.
    """
    leaning = replace(DESIGN, tilt=tilt)
    resting = leaning.leaned(leaning.block_width / 2, -leaning.floor_thickness)
    apex = leaning.arm_apex
    beneath = polygon(
        [(resting.u, 0.0), (resting.u, resting.v), (apex.u, apex.v), (apex.u, 0.0)]
    )
    over_the_plate = rect(
        min(apex.u, resting.u), 0.0, leaning.pad_outboard, max(apex.v, resting.v)
    )
    missing = ((beneath ^ over_the_plate) - profile_at(tilt)).area()
    assert missing == pytest.approx(0.0, abs=1e-9), f"{missing:.4f} mm2 unfilled"


def test_a_lean_that_would_come_apart_is_refused():
    """The block has to sit into the plate, not rest a line on it.

    Shallow enough and the block floats clear of the plate's top surface, and
    the only thing left joining them is the arm meeting the block along a line.
    A line of contact is not a join: the profile comes out as two separate
    pieces.
    """
    with pytest.raises(ValueError, match="separate pieces"):
        replace(DESIGN, tilt=30.0)


def test_the_shallowest_lean_that_holds_together_is_where_it_says_it_is():
    """Straddles the refusal rather than testing well inside it, so a change
    that moves the edge fails here and names the lean."""
    boundary = 41.91
    replace(DESIGN, tilt=boundary + 0.05)
    with pytest.raises(ValueError, match="separate pieces"):
        replace(DESIGN, tilt=boundary - 0.05)


@pytest.mark.parametrize("tilt", EVERY_LEAN)
def test_the_profile_is_one_connected_piece(tilt):
    """The failure the bound above guards is silent in every other measure:
    two pieces, no enclosed void, each bed its full width."""
    assert len(profile_at(tilt).to_polygons()) == 1


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
PINNED_VERTICES = 15
PINNED_AREA = 172.272601
PINNED_DIGEST = "619ddd5f80795cab"


def test_the_shipped_profile_is_unchanged():
    cross_section = profile(DESIGN)
    assert cross_section.num_vert() == PINNED_VERTICES
    assert cross_section.area() == pytest.approx(PINNED_AREA, abs=1e-6)
    assert contour_digest(cross_section) == PINNED_DIGEST


# ---------------------------------------------------------------------------
# A run that twists from one lean to another
# ---------------------------------------------------------------------------

TWIST_LENGTH = 76.2  # 3 in, the run the trial turns over
ALONG_THE_TWIST = (0.1, 0.25, 0.4, 0.55, 0.7, 0.85)

# How far either side of a face to look for material. Small enough that a bed
# 0.3 mm out of place would put the wrong answer in one of these windows.
PROBE = 0.02
CLEAR_OF_THE_FACE = 0.15

# What `material_at` reads for a window entirely inside the plastic, and one
# entirely in the air. Compared with a tolerance because it is a ratio of two
# measured areas, not a count.
SOLID, AIR = 1.0, 0.0


def twisting_run(length=TWIST_LENGTH, to_tilt=90.0):
    """A twisting run stood back up, so it can be sliced across the strip.

    It is built lying down like every other part, which puts the strip along
    Y; sections across the strip are what these tests read, so it goes back up
    and the run's own length becomes the height sliced through.
    """
    run = twisting(DESIGN, length, to_tilt)
    return run.translate((0.0, -length, 0.0)).rotate((-90.0, 0.0, 0.0))


def lean_at(fraction, to_tilt=90.0):
    """The lean a twisting run has reached this far along itself."""
    return DESIGN.tilt + (to_tilt - DESIGN.tilt) * fraction


def material_at(section, point):
    """How much of a small window around `point` is solid: 1 all, 0 none."""
    u, v = point
    window = rect(u - PROBE, v - PROBE, u + PROBE, v + PROBE)
    return (section ^ window).area() / window.area()


def off_the_seat(lean, across, above):
    """A point `across` and `above` the strip's seat, in the leaned frame.

    The seat is the middle of the bed. Everything the strip cares about is
    measured from there along the bed and normal to it, which is the frame
    that turns with the lean -- so these tests can ask about the bed's own
    faces without knowing where the lean has carried them to.
    """
    radians = math.radians(lean)
    return (
        across * math.cos(radians) + above * math.sin(radians),
        DESIGN.floor_height - across * math.sin(radians) + above * math.cos(radians),
    )


@pytest.mark.parametrize("fraction", ALONG_THE_TWIST)
def test_the_strip_sits_in_the_same_place_all_the_way_through_a_twist(fraction):
    """The promise the whole part exists to keep.

    The lean stops moving the strip, and the twist must not move it either.
    Asked of the built solid at its own seat rather than of a measured outline:
    a bed sliced out of a stack of slabs arrives as several collinear pieces
    and no single edge to measure, but whether there is plastic just under the
    bed and air just above it is exact however the mesh was cut.

    All four faces, because three of them can be right while the strip has
    slid sideways along the fourth.
    """
    section = twisting_run().slice(fraction * TWIST_LENGTH)
    lean = lean_at(fraction)
    half_bed = DESIGN.channel_width / 2.0
    beneath = material_at(section, off_the_seat(lean, 0.0, -CLEAR_OF_THE_FACE))
    above = material_at(section, off_the_seat(lean, 0.0, CLEAR_OF_THE_FACE))
    assert beneath == pytest.approx(SOLID), "the bed has nothing under it"
    assert above == pytest.approx(AIR), "the bed is buried"
    for side in (-1.0, 1.0):
        inside = off_the_seat(lean, side * (half_bed - 0.3), CLEAR_OF_THE_FACE)
        outside = off_the_seat(lean, side * (half_bed + 0.3), CLEAR_OF_THE_FACE)
        assert material_at(section, inside) == pytest.approx(AIR), f"blocked at {side}"
        assert material_at(section, outside) == pytest.approx(SOLID), f"no wall {side}"


@pytest.mark.parametrize("to_tilt", [90.0, 67.5])
def test_a_twisting_run_ends_at_the_leans_it_joins(to_tilt):
    """A run is only useful if its ends are the profile of what it meets.

    They are not free to be approximately right: a neighbour joined to a lip
    sitting at the wrong angle has its mouth roofed over, and the open channel
    becomes a closed tunnel.
    """
    run = twisting_run(to_tilt=to_tilt)
    for fraction, lean in ((0.0, DESIGN.tilt), (1.0, to_tilt)):
        # Just inside, because a slice exactly on the end face is ambiguous.
        section = run.slice(fraction * TWIST_LENGTH + (1.0 - 2.0 * fraction) * 0.001)
        assert section.area() == pytest.approx(profile_at(lean).area(), abs=1e-2)


@pytest.mark.parametrize("to_tilt", [90.0, 67.5, 50.0])
def test_a_twisting_run_is_one_solid_piece(to_tilt):
    """Stacked slabs come apart into one body per slab unless they overlap,
    and thin features left in them tunnel. Both show up here."""
    run = twisting(DESIGN, TWIST_LENGTH, to_tilt)
    assert len(run.decompose()) == 1
    assert run.genus() == 0


def test_a_run_that_turns_through_nothing_is_the_straight_it_started_from():
    """Pins the twisting machinery to the sweep that was already trusted.

    With no turn to make there is one right answer and it is already built by
    another route, so the two are compared against each other rather than the
    new one being asked to agree with itself.
    """
    turned = twisting(DESIGN, 50.0, DESIGN.tilt)
    plain = straight(DESIGN, 50.0)
    assert (turned - plain).volume() == pytest.approx(0.0, abs=1e-4)
    assert (plain - turned).volume() == pytest.approx(0.0, abs=1e-4)


# ---------------------------------------------------------------------------
# A corner with runs led into it
# ---------------------------------------------------------------------------

LEAD = 101.6  # 4 in
LEAD_TWIST = 76.2  # of which 3 in turns


def test_a_corner_with_leads_is_one_solid_piece():
    """Five sweeps unioned: the turn, and a twisting run and a straight either
    side of it. Any seam that failed to take shows up as a second body or a
    tunnel."""
    part = led_corner(UPRIGHT, 38.1, LEAD, LEAD_TWIST, DESIGN.tilt)
    assert len(part.decompose()) == 1
    assert part.genus() == 0


def test_a_corner_with_leads_sits_on_the_tv_back_the_whole_way_round():
    """Anything below the plane is plastic the bracket would rock on, and a
    run joined on at the wrong angle is exactly how that happens."""
    part = led_corner(UPRIGHT, 38.1, LEAD, LEAD_TWIST, DESIGN.tilt)
    assert part.bounding_box()[2] == pytest.approx(0.0, abs=1e-9)


def test_a_corner_puts_a_run_on_both_sides_of_its_turn():
    """A corner has an entry and an exit, and they are the same shape laid
    down either side of the turn.

    Reaching the same distance along both axes is what says so. Built by
    mirroring one run, and a mirror about the wrong plane drops the exit on
    top of the entry -- which leaves the part one sound solid, sitting flat,
    with its channel unbroken, and wrong.
    """
    part = led_corner(UPRIGHT, 38.1, LEAD, LEAD_TWIST, DESIGN.tilt)
    low_x, low_y = part.bounding_box()[0], part.bounding_box()[1]
    assert low_x == pytest.approx(-LEAD, abs=1e-6)
    assert low_y == pytest.approx(-LEAD, abs=1e-6)


def test_the_runs_leave_a_corner_at_the_lean_the_straights_are_drawn_at():
    """The far end of each run is what a straight section butts against, so it
    has to be that straight's own section."""
    part = led_corner(UPRIGHT, 38.1, LEAD, LEAD_TWIST, DESIGN.tilt)
    # Stood up with the entry run along Z, its open end at the bottom.
    entry = part.rotate((-90.0, 0.0, 0.0)).translate((-38.1, 0.0, 0.0))
    assert entry.slice(LEAD - 0.001).area() == pytest.approx(
        profile_at(DESIGN.tilt).area(), abs=1e-6
    )


def test_a_twist_longer_than_the_lead_it_turns_within_is_refused():
    """The turn has to finish before the corner starts, so it cannot be longer
    than the run it happens in."""
    with pytest.raises(ValueError, match="longer than"):
        led_corner(UPRIGHT, 38.1, 50.8, 76.2, DESIGN.tilt)


@pytest.mark.parametrize(("lead", "twist"), [(0.0, 10.0), (10.0, 0.0), (10.0, -1.0)])
def test_a_lead_or_twist_that_is_not_a_length_is_refused(lead, twist):
    with pytest.raises(ValueError, match="positive"):
        led_corner(UPRIGHT, 38.1, lead, twist, DESIGN.tilt)
