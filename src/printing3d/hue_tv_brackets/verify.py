"""Geometric checks on the generated brackets. Run before printing.

These measure the built solids rather than reading the parameters back, so a
mistake anywhere between a dimension and the exported shape still shows up.
They cover what is easy to get wrong and hard to see: that the channel still
necks down to a clip rather than an open trough, that it still aims out at its
lean, that the pad the adhesive holds is genuinely flat, that a corner turns a
full quarter and no further -- and that a corner and a straight are still the
same bracket, which is the claim the whole design rests on.
"""

from printing3d.checks import CheckRunner
from printing3d.hue_tv_brackets.catalog import corners, parts, straights, trial_parts
from printing3d.hue_tv_brackets.geometry import QUARTER_TURN, straight
from printing3d.probes import enclosed_void_count, straight_runs
from printing3d.shapes import rect


def lip_taper_slack(design):
    """How wide the mouth reads when measured a sliver below the block's face.

    The lip has not finished closing there, so the reading runs wide by that
    much of the taper.
    """
    return 2 * PROBE_BAND * design.lip_reach / design.lip_height + MAX_EDGE_ERROR


def leaned_floor_angle(design):
    """Where the slot floor ends up once the channel is leaned.

    Stated from the design's intent rather than computed by the code that does
    the leaning: a check that asks the drawing code where it drew is not a
    check.
    """
    return (-design.tilt) % 180.0


# Half-thickness of the sliver used to read a width off the profile. Small
# enough that the lip's taper does not smear the reading, wide enough to
# survive floating point.
PROBE_BAND = 0.05

CLEAR_OF_THE_END = 1.0  # degrees inside a corner's ends, to sample or to miss
REFERENCE_LENGTH = 10.0  # any length: a straight's section does not vary along it
MAX_EDGE_ERROR = 0.05  # mm, on a length read off the built profile
MAX_ANGLE_ERROR = 0.01  # degrees
MAX_SECTION_DRIFT = 1e-6  # mm2 between a corner's section and a straight's


def upright_section(solid, degrees=0.0):
    """The cross-section of `solid` on the vertical plane `degrees` about Z.

    Promotable: domain-free measurement, currently only hue-tv-brackets.
    Waiting on two choices nobody outside this repo made. The sense of
    `degrees` is ours -- the solid turns by its negative, so the opposite
    convention returns a mirrored section and silently inverts every
    comparison drawn from it. And the plane passes through the origin, with no
    offset to say otherwise, so a caller wanting it elsewhere translates first
    and nothing here says which way.
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


def in_channel_frame(section, design):
    """The section turned back upright, so the channel is axis-aligned."""
    return section.translate((0.0, -design.floor_height)).rotate(design.tilt)


def slot_width_at(section, up, design):
    """The gap between the channel's walls, `up` from the slot floor.

    The gap straddling the channel's centre is what a strip has to pass, so
    that is the one measured -- material further out belongs to the plate.
    """
    reach = design.block_width
    sliver = rect(-reach, up - PROBE_BAND, reach, up + PROBE_BAND)
    spans = [
        (min(x for x, _ in contour), max(x for x, _ in contour))
        for contour in (in_channel_frame(section, design) ^ sliver).to_polygons()
    ]
    left = max((high for _, high in spans if high <= 0.0), default=None)
    right = min((low for low, _ in spans if low >= 0.0), default=None)
    if left is None or right is None:
        raise ValueError(f"no channel walls found {up} mm above the slot floor")
    return right - left


def longest_face_at(section, angle):
    """Length of the longest flat face lying at `angle`, or zero if none does.

    Promotable: domain-free measurement, currently only hue-tv-brackets.
    Waiting on four choices nobody outside this repo made: MAX_ANGLE_ERROR as
    the match tolerance and MAX_EDGE_ERROR as the length floor, both read from
    module scope where no caller can reach them; zero returned for "no such
    face", where slot_width_at above raises for its own empty case; and a
    comparison that does not wrap, so a face measured at 179.99 never matches
    one asked for at 0.0 even though straight_runs folded them together.
    """
    for length, found in straight_runs(section, MAX_EDGE_ERROR):
        if abs(found - angle) < MAX_ANGLE_ERROR:
            return length
    return 0.0


def check_channel_clips(runner, section, design):
    """A mouth wider than its bed is a trough: the strip would lift straight
    back out, which is the whole failure this bracket exists to prevent.

    Bounded from the other side too. Every check here compared the built
    channel against the design's own derived numbers, which a channel necked
    shut satisfies perfectly -- a 0.60 mm mouth passed all of them. Measuring
    against the strip is what makes the question physical instead of circular.

    A channel necked SHUT still passes, and saying so is better than pretending
    otherwise. Catching it needs a floor under the mouth, and the floor is how
    far the strip bows to pass the neck -- which nobody here has measured. The
    shipped 12.0 mm works on a 14.4 mm strip: one data point, not a limit.
    Guessing a fraction of the strip width would put an invented number in
    front of a check and make it read as verified.
    """
    try:
        bed = slot_width_at(section, PROBE_BAND, design)
        mouth = slot_width_at(section, design.channel_depth - PROBE_BAND, design)
    except ValueError as unmeasurable:
        # A channel that cannot be found is a failed check, not a crashed run.
        # Raising here took down every part queued behind this one, which is
        # the moment the rest of the report is worth most.
        runner.check("the channel necks down to a clip", False, str(unmeasurable))
        return
    runner.check(
        "the channel necks down to a clip",
        mouth < bed,
        f"bed {bed:.2f} mm, mouth {mouth:.2f} mm",
    )
    runner.check(
        "the bed is the full channel width",
        abs(bed - design.channel_width) < MAX_EDGE_ERROR,
        f"{bed:.3f} mm",
    )
    runner.check(
        "the lips close over the bed as drawn",
        abs(mouth - design.mouth_width) < lip_taper_slack(design),
        f"{mouth:.3f} mm against {design.mouth_width:.3f} mm at the face",
    )
    runner.check(
        "the bed carries the strip",
        bed >= design.strip_width,
        f"bed {bed:.2f} mm for a {design.strip_width:.1f} mm strip",
    )
    runner.check(
        "the mouth necks below the strip",
        mouth < design.strip_width,
        f"mouth {mouth:.2f} mm against a {design.strip_width:.1f} mm strip",
    )


def check_channel_aims_out(runner, section, design):
    """The lean is what throws light along the wall instead of at it.

    Looks for a face of the bed's width at the bed's angle, rather than for the
    longest face at that angle. Stand the channel upright and its walls become
    parallel to its floor, so the longest face at that angle is one of them --
    the floor is still exactly where it should be, and the older reading found
    a 16 mm wall instead of the 15 mm bed.
    """
    angle = leaned_floor_angle(design)
    at_angle = [
        length
        for length, found in straight_runs(section, MAX_EDGE_ERROR)
        if abs(found - angle) < MAX_ANGLE_ERROR
    ]
    bed = [
        length
        for length in at_angle
        if abs(length - design.channel_width) < MAX_EDGE_ERROR
    ]
    runner.check(
        f"the channel still lies at {design.tilt:.0f} degrees",
        bool(bed),
        f"faces at {angle:.1f} deg: "
        + (", ".join(f"{length:.2f}" for length in at_angle) or "none")
        + f" mm, wanted one of {design.channel_width:.2f}",
    )


def check_base_is_flat(runner, section, design):
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
        abs(pad - design.base_depth) < MAX_EDGE_ERROR,
        f"{pad:.2f} mm against {design.base_depth:.2f} mm",
    )


def check_profile_is_solid(runner, section):
    """An enclosed pocket is air the slicer would wall in for no benefit."""
    pockets = enclosed_void_count(section)
    runner.check("the profile encloses no pockets", pockets == 0, f"{pockets} found")


def check_the_channel(runner, section, design):
    """Every check that reads the profile, which both shapes share."""
    check_channel_clips(runner, section, design)
    check_channel_aims_out(runner, section, design)
    check_base_is_flat(runner, section, design)
    check_profile_is_solid(runner, section)


def check_corner_carries_the_quarter(runner, part):
    """Measured by cutting just inside each end of the arc."""
    inside = [CLEAR_OF_THE_END, QUARTER_TURN - CLEAR_OF_THE_END]
    carries = all(upright_section(part.solid, deg).area() > 0.0 for deg in inside)
    runner.check("the corner carries the strip across the quarter", carries)


def check_corner_stops_at_the_quarter(runner, part):
    """Measured by cutting just outside each end, where there must be nothing."""
    outside = [-CLEAR_OF_THE_END, QUARTER_TURN + CLEAR_OF_THE_END]
    stops = all(upright_section(part.solid, deg).area() == 0.0 for deg in outside)
    runner.check("the corner stops at the quarter", stops)


def check_leads_run_out_straight(runner, part):
    """A corner with runs led into it does not stop at the quarter.

    It leaves along the tangent at each end, so instead of nothing outside the
    arc there is a straight run reaching exactly its lead beyond the turn.
    Both sides, which is what catches a run mirrored about the wrong plane and
    so laid down over its own entry.

    How far the part reaches says nothing about whether it is continuous on
    the way there -- a run built short leaves a gap and still reaches, and it
    is being one connected solid that catches that instead.
    """
    # One run leaves along each axis, so how far the part reaches back along
    # both is how far each of them goes.
    low_x, low_y = part.solid.bounding_box()[0], part.solid.bounding_box()[1]
    along_x, along_y = -low_x, -low_y
    runner.check(
        "the runs reach their full length past the corner",
        abs(along_x - part.lead) < MAX_EDGE_ERROR
        and abs(along_y - part.lead) < MAX_EDGE_ERROR,
        f"{along_x:.2f} mm and {along_y:.2f} mm against {part.lead:.2f} mm",
    )


def check_corner_matches_the_straight(runner, section, reference):
    """The point of the design: a corner and a straight are the same bracket,
    so a section through one must be a section through the other."""
    drift = abs(section.area() - reference.area())
    bounds = max(
        abs(mine - theirs)
        for mine, theirs in zip(section.bounds(), reference.bounds(), strict=True)
    )
    runner.check(
        "the corner's section is the straight's section",
        drift < MAX_SECTION_DRIFT and bounds < MAX_SECTION_DRIFT,
        f"area off by {drift:.2e} mm2, outline by {bounds:.2e} mm",
    )


def verify_all() -> bool:
    """Run every check against every bracket this project ships."""
    return _checked(list(parts()))


def verify_trials() -> bool:
    """Run every check against the brackets still being tested.

    Kept out of `verify_all` so that what the measurement lock pins is exactly
    what the project ships. A trial is checked because you are about to print
    it; it is not part of the record of what this project produces, and
    retiring one should cost a config file and nothing else.
    """
    tried = list(trial_parts())
    return _checked(tried) if tried else True


def _checked(brackets) -> bool:
    """Check these brackets, and report."""
    runner = CheckRunner()
    for part in straights(brackets):
        runner.section(part.name)
        check_the_channel(runner, straight_section(part), part.design)

    for part in corners(brackets):
        runner.section(part.name)
        section = corner_section(part)
        check_the_channel(runner, section, part.design)
        check_corner_carries_the_quarter(runner, part)
        if part.lead:
            check_leads_run_out_straight(runner, part)
        else:
            check_corner_stops_at_the_quarter(runner, part)
        check_corner_matches_the_straight(
            runner, section, reference_section(part.design)
        )
    return runner.report()


def reference_section(design):
    """A straight's cross-section at this lean, built for the comparison.

    Built rather than looked up among the parts. The claim being tested is that
    a corner is the same profile as a straight at the same lean -- true whether
    or not the project happens to ship such a straight, and requiring one tied
    a corner's check to an unrelated entry in the catalogue. It broke the
    moment corners and straights were wanted at different leans.
    """
    run = straight(design, REFERENCE_LENGTH)
    return upright_section(run.translate((0.0, -REFERENCE_LENGTH / 2.0, 0.0)), 0.0)
