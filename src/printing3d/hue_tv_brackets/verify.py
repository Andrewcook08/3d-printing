"""Geometric checks on the generated brackets. Run before printing.

These measure the built solids rather than reading the parameters back, so a
mistake anywhere between a dimension and the exported shape still shows up.
They cover what is easy to get wrong and hard to see: that the channel still
necks down to a clip rather than an open trough, that it still aims out at its
lean, that the pad the adhesive holds is genuinely flat, that a corner turns a
full quarter and no further -- and that a corner and a straight are still the
same bracket, which is the claim the whole design rests on.
"""

import math

from printing3d.checks import CheckRunner
from printing3d.hue_tv_brackets.catalog import corners, parts, straights
from printing3d.hue_tv_brackets.geometry import (
    BASE_DEPTH,
    BLOCK_W,
    CHANNEL_D,
    CHANNEL_W,
    LIP_REACH,
    LIP_RISE,
    MOUTH_W,
    QUARTER_TURN,
    TILT,
    floor_height,
)
from printing3d.probes import enclosed_void_count
from printing3d.shapes import rect


def leaned_floor_angle(tilt):
    """Where the slot floor ends up once the channel is leaned.

    Stated from the design's intent rather than computed by the code that does
    the leaning: a check that asks the drawing code where it drew is not a
    check.
    """
    return (-tilt) % 180.0


# Half-thickness of the sliver used to read a width off the profile. Small
# enough that the lip's taper does not smear the reading, wide enough to
# survive floating point.
PROBE_BAND = 0.05

CLEAR_OF_THE_END = 1.0  # degrees inside a corner's ends, to sample or to miss
MAX_EDGE_ERROR = 0.05  # mm, on a length read off the built profile
MAX_ANGLE_ERROR = 0.01  # degrees
COLLINEAR = 1e-6  # sine of the turn below which two segments are one face
MAX_SECTION_DRIFT = 1e-6  # mm2 between a corner's section and a straight's

# The mouth is read a sliver below the block's face, where the lip has not
# finished closing, so the reading runs wide by that much of the taper.
LIP_TAPER_SLACK = 2 * PROBE_BAND * LIP_REACH / LIP_RISE + MAX_EDGE_ERROR


def upright_section(solid, degrees=0.0):
    """The cross-section of `solid` on the vertical plane `degrees` about Z.

    Promotable: domain-free measurement, currently only hue-tv-brackets.
    """
    return solid.rotate((0.0, 0.0, -degrees)).rotate((-90.0, 0.0, 0.0)).slice(0.0)


def straight_section(part):
    """A straight run's cross-section, taken halfway along it."""
    centred = part.solid.translate((0.0, -part.length / 2.0, 0.0))
    return upright_section(centred, 0.0)


def corner_section(part):
    """A corner's cross-section, taken mid-arc and brought home to the
    profile's own frame.

    A corner's section comes out at the radius it was swept to. Translating it
    back is what lets the same checks measure it, and lets it be compared
    against a straight's.
    """
    turned = upright_section(part.solid, QUARTER_TURN / 2.0)
    return turned.translate((-part.radius, 0.0))


def in_channel_frame(section, tilt):
    """The section turned back upright, so the channel is axis-aligned."""
    return section.translate((0.0, -floor_height(tilt))).rotate(tilt)


def slot_width_at(section, up, tilt=TILT):
    """The gap between the channel's walls, `up` from the slot floor.

    The gap straddling the channel's centre is what a strip has to pass, so
    that is the one measured -- material further out belongs to the plate.
    """
    sliver = rect(-BLOCK_W, up - PROBE_BAND, BLOCK_W, up + PROBE_BAND)
    spans = [
        (min(x for x, _ in contour), max(x for x, _ in contour))
        for contour in (in_channel_frame(section, tilt) ^ sliver).to_polygons()
    ]
    left = max((high for _, high in spans if high <= 0.0), default=None)
    right = min((low for low, _ in spans if low >= 0.0), default=None)
    if left is None or right is None:
        raise ValueError(f"no channel walls found {up} mm above the slot floor")
    return right - left


def straight_runs(section, min_length):
    """Straight runs of the outline, collinear segments merged, longest first.

    Promotable: domain-free measurement, currently only hue-tv-brackets. It
    supersedes the kit's un-merged edge probe rather than sitting beside it --
    promoting this means teaching that one to merge, and re-checking what the
    other project's angle check then measures.

    A section cut from a mesh carries vertices wherever the triangulation put
    them, so one flat face arrives as several collinear segments. Merging them
    is what makes a measured face comparable to the face as drawn.
    """
    runs = []
    for contour in section.to_polygons():
        corners = _corners_of([tuple(point) for point in contour])
        for start, end in zip(corners, corners[1:] + corners[:1], strict=True):
            length = math.hypot(end[0] - start[0], end[1] - start[1])
            if length >= min_length:
                angle = math.degrees(math.atan2(end[1] - start[1], end[0] - start[0]))
                runs.append((length, angle % 180.0))
    return sorted(runs, reverse=True)


def _corners_of(points):
    """The points where the outline actually turns, collinear ones dropped."""
    return [
        point
        for index, point in enumerate(points)
        if _turns_at(points[index - 1], point, points[(index + 1) % len(points)])
    ]


def _turns_at(before, point, after):
    """Does the outline change direction here, or run straight through?"""
    into = (point[0] - before[0], point[1] - before[1])
    away = (after[0] - point[0], after[1] - point[1])
    into_len = math.hypot(*into)
    away_len = math.hypot(*away)
    if into_len == 0.0 or away_len == 0.0:
        return False
    cross = into[0] * away[1] - into[1] * away[0]
    return abs(cross) / (into_len * away_len) > COLLINEAR


def longest_face_at(section, angle):
    """Length of the longest flat face lying at `angle`, or zero if none does."""
    for length, found in straight_runs(section, MAX_EDGE_ERROR):
        if abs(found - angle) < MAX_ANGLE_ERROR:
            return length
    return 0.0


def check_channel_clips(runner, section, tilt):
    """A mouth wider than its bed is a trough: the strip would lift straight
    back out, which is the whole failure this bracket exists to prevent."""
    bed = slot_width_at(section, PROBE_BAND, tilt)
    mouth = slot_width_at(section, CHANNEL_D - PROBE_BAND, tilt)
    runner.check(
        "the channel necks down to a clip",
        mouth < bed,
        f"bed {bed:.2f} mm, mouth {mouth:.2f} mm",
    )
    runner.check(
        "the bed is the full channel width",
        abs(bed - CHANNEL_W) < MAX_EDGE_ERROR,
        f"{bed:.3f} mm",
    )
    runner.check(
        "the lips close over the bed as drawn",
        abs(mouth - MOUTH_W) < LIP_TAPER_SLACK,
        f"{mouth:.3f} mm against {MOUTH_W:.3f} mm at the face",
    )


def check_channel_aims_out(runner, section, tilt):
    """The lean is what throws light along the wall instead of at it."""
    angle = leaned_floor_angle(tilt)
    length = longest_face_at(section, angle)
    runner.check(
        f"the channel still lies at {tilt:.0f} degrees",
        abs(length - CHANNEL_W) < MAX_EDGE_ERROR,
        f"floor edge {length:.2f} mm at {angle:.1f} deg in the profile",
    )


def check_base_is_flat(runner, section):
    """The adhesive holds on one unbroken pad; a pad that is not flat holds on
    its corners, which is how the strip's own adhesive let go."""
    _, low_v, _, _ = section.bounds()
    pad = longest_face_at(section, 0.0)
    runner.check(
        "the pad lies in the mounting plane",
        abs(low_v) < MAX_EDGE_ERROR,
        f"{low_v:.3f} mm",
    )
    runner.check(
        "the pad is the full base depth",
        abs(pad - BASE_DEPTH) < MAX_EDGE_ERROR,
        f"{pad:.2f} mm",
    )


def check_profile_is_solid(runner, section):
    """An enclosed pocket is air the slicer would wall in for no benefit."""
    pockets = enclosed_void_count(section)
    runner.check("the profile encloses no pockets", pockets == 0, f"{pockets} found")


def check_the_channel(runner, section, tilt):
    """Every check that reads the profile, which both shapes share."""
    check_channel_clips(runner, section, tilt)
    check_channel_aims_out(runner, section, tilt)
    check_base_is_flat(runner, section)
    check_profile_is_solid(runner, section)


def check_corner_turns_a_quarter(runner, part):
    """Measured by cutting just inside each end of the arc, and just outside."""
    inside = [CLEAR_OF_THE_END, QUARTER_TURN - CLEAR_OF_THE_END]
    outside = [-CLEAR_OF_THE_END, QUARTER_TURN + CLEAR_OF_THE_END]
    carries = all(upright_section(part.solid, deg).area() > 0.0 for deg in inside)
    stops = all(upright_section(part.solid, deg).area() == 0.0 for deg in outside)
    runner.check("the corner carries the strip across the quarter", carries)
    runner.check("the corner stops at the quarter", stops)


def check_corner_matches_the_straight(runner, section, straight_section):
    """The point of the design: a corner and a straight are the same bracket,
    so a section through one must be a section through the other."""
    drift = abs(section.area() - straight_section.area())
    bounds = max(
        abs(mine - theirs)
        for mine, theirs in zip(
            section.bounds(), straight_section.bounds(), strict=True
        )
    )
    runner.check(
        "the corner's section is the straight's section",
        drift < MAX_SECTION_DRIFT and bounds < MAX_SECTION_DRIFT,
        f"area off by {drift:.2e} mm2, outline by {bounds:.2e} mm",
    )


def verify_all():
    """Run every check against every bracket. True if all pass."""
    runner = CheckRunner()
    brackets = list(parts())
    runs = straights(brackets)
    if not runs:
        runner.check("a straight ships for the corners to be measured against", False)
        return runner.report()
    for part in runs:
        runner.section(part.name)
        check_the_channel(runner, straight_section(part), part.tilt)

    # A corner is compared against a straight at its OWN lean: "the same
    # bracket bent" only means anything between two brackets aimed alike.
    references = {part.tilt: straight_section(part) for part in runs}
    for part in corners(brackets):
        runner.section(part.name)
        section = corner_section(part)
        check_the_channel(runner, section, part.tilt)
        check_corner_turns_a_quarter(runner, part)
        reference = references.get(part.tilt)
        runner.check(
            f"a {part.tilt:g}-degree straight ships to compare it against",
            reference is not None,
        )
        if reference is not None:
            check_corner_matches_the_straight(runner, section, reference)
    return runner.report()
