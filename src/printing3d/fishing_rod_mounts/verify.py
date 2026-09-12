"""Geometric checks on the generated mounts. Run before printing.

These measure the built solids rather than reading the parameters back, so a
mistake anywhere between a dimension and the exported shape still shows up.
They cover the things that are easy to break and hard to spot by eye: that the
rod still lifts straight out, that it is trapped sideways in both directions,
that the screw bores are open and countersunk on the front only, and that both
mounts of a pair seat the rod centerline at the same height.
"""

import math

import manifold3d as m

from printing3d.fishing_rod_mounts.catalog import RODS, parts
from printing3d.fishing_rod_mounts.geometry import (
    AXIS_U,
    AXIS_V,
    CSINK_D,
    PLATE_THK,
    RIB,
    WEDGE,
    profile,
    signed_area,
)

PROBE_SIZE = 0.6  # side of the test cube used to ask "material here?"
FINE_PROBE_SIZE = 0.05  # for locating a surface, not just sampling
TOUCHING = 1e-6  # volumes below this count as no contact at all
NUDGE = 1.0  # how far the rod is pushed to test its retention
BITE = 1.0  # mm3 of interference that counts as a real stop
LIFT_HEIGHT = 200.0  # far enough that the rod is clear of everything
SPAN = 1250.0  # distance between the two mounts of a pair
MAX_SEAT_MISMATCH = 0.15  # mm of height difference between paired mounts
MAX_TILT = 0.02  # degrees of rod tilt across the span
MAX_WALL_STEP = 0.35  # mm of height difference between cradle walls
MAX_DIAGONAL_SPREAD = 0.5  # degrees; the wedge's two diagonals must agree
MIN_EDGE_LENGTH = 4.0  # ignore short edges when measuring diagonals
MIN_WALL_CLEARANCE = 0.5  # mm of air between the rod and the wall
PLATE_ABOVE_SCREW = 1.5  # mm of plate that must remain above a countersink


class CheckRunner:
    """Runs named checks, prints each result, and remembers the failures."""

    def __init__(self):
        self.failures = []

    def section(self, title):
        print(f"\n{title}")

    def check(self, name, passed, detail=""):
        mark = "PASS" if passed else "FAIL"
        print(f"  [{mark}] {name}{'  -- ' + detail if detail else ''}")
        if not passed:
            self.failures.append(name)

    @property
    def all_passed(self):
        return not self.failures


# ---------------------------------------------------------------------------
# Probes: questions asked of a finished solid
# ---------------------------------------------------------------------------


def has_material_at(solid, u, v, w, size=PROBE_SIZE):
    """Is there material at this point? (tiny cube intersection)"""
    cube = m.Manifold.cube((size, size, size), True).translate((u, v, w))
    return (solid ^ cube).volume() > TOUCHING


def rod_at(spec, du=0.0, dv=0.0):
    """The rod, as a solid, displaced from its nominal seat."""
    return (
        m.CrossSection.circle(spec.rod_dia / 2.0, 256)
        .translate((AXIS_U + du, AXIS_V + dv))
        .extrude(spec.width)
    )


def lift_sweep(spec):
    """Everything the rod passes through as it is lifted straight up and out."""
    radius = spec.rod_dia / 2.0
    disc = m.CrossSection.circle(radius, 256).translate((AXIS_U, AXIS_V))
    chute = m.CrossSection.square((2 * radius, LIFT_HEIGHT), False).translate(
        (AXIS_U - radius, AXIS_V)
    )
    return (disc + chute).extrude(spec.width)


def overlap(solid, other):
    return (solid ^ other).volume()


def seat_height(solid, spec):
    """Cradle floor + rod radius, measured off the solid.

    Scans DOWN the cradle centerline from the nominal axis: scanning up from
    v=0 would be wrong, since the tip mount's underside is open air below the
    part.
    """

    def material(v):
        return has_material_at(solid, AXIS_U, v, spec.width / 2.0, size=FINE_PROBE_SIZE)

    air, floor = _first_material_below(material, AXIS_V)
    for _ in range(40):
        midpoint = (air + floor) / 2.0
        if material(midpoint):
            floor = midpoint
        else:
            air = midpoint
    return (air + floor) / 2.0 + spec.rod_dia / 2.0


def _first_material_below(material, start_v, step=0.25, limit=-5.0):
    """Bracket the cradle floor: the last known air height and the first
    height at which the probe hits material."""
    air, v = start_v, start_v
    while v > limit:
        if material(v):
            return air, v
        air, v = v, v - step
    raise AssertionError("no cradle floor found")


def straight_edge_angles(cross_section, min_len=MIN_EDGE_LENGTH):
    """Angles of the straight edges in a profile, longest first.

    Used to check that the two diagonals really are parallel, rather than
    trusting that the same slope constant was used in both places.
    """
    edges = []
    for contour in cross_section.to_polygons():
        for i in range(len(contour)):
            (u0, v0), (u1, v1) = contour[i], contour[(i + 1) % len(contour)]
            length = math.hypot(u1 - u0, v1 - v0)
            if length >= min_len:
                angle = math.degrees(math.atan2(v1 - v0, u1 - u0)) % 180.0
                edges.append((length, angle))
    return sorted(edges, reverse=True)


def cradle_wall_tops(cross_section, cradle_radius):
    """Height of the cradle's wall-side wall and of the outer lip."""
    walls = (
        (AXIS_U - cradle_radius - RIB, AXIS_U - cradle_radius),
        (AXIS_U + cradle_radius, AXIS_U + cradle_radius + RIB),
    )
    tops = []
    for u0, u1 in walls:
        column = cross_section ^ m.CrossSection.square(
            (u1 - u0, 300.0), False
        ).translate((u0, 0.0))
        tops.append(
            max(point[1] for contour in column.to_polygons() for point in contour)
        )
    return tops


def enclosed_void_count(cross_section):
    return sum(1 for contour in cross_section.to_polygons() if signed_area(contour) < 0)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_part(runner, part):
    spec = part.spec
    runner.section(
        f"{part.name}  (rod {spec.rod_dia} mm, "
        f"{len(spec.screw_heights)} screw"
        f"{'s' if len(spec.screw_heights) > 1 else ''}, "
        f"{spec.width:.0f} mm wide)"
    )
    check_rod_seats_and_releases(runner, part)
    check_rod_is_trapped_sideways(runner, part)
    for height in spec.screw_heights:
        check_screw(runner, part, height)
    check_solid_is_printable(runner, part)
    check_derived_angles(runner, part)


def check_rod_seats_and_releases(runner, part):
    spec = part.spec
    fit = overlap(part.solid, rod_at(spec))
    runner.check(
        "rod fits the cradle without interference", fit < TOUCHING, f"{fit:.4f} mm3"
    )
    clash = overlap(part.solid, lift_sweep(spec))
    runner.check("rod lifts straight out", clash < TOUCHING, f"{clash:.4f} mm3")
    clearance = AXIS_U - spec.rod_dia / 2.0
    runner.check(
        "rod clears the wall", clearance > MIN_WALL_CLEARANCE, f"{clearance:.2f} mm"
    )


def check_rod_is_trapped_sideways(runner, part):
    backward = overlap(part.solid, rod_at(part.spec, du=-NUDGE))
    forward = overlap(part.solid, rod_at(part.spec, du=+NUDGE))
    runner.check(
        "rod cannot roll back toward the wall",
        backward > BITE,
        f"{backward:.1f} mm3 interference",
    )
    runner.check(
        "rod cannot roll forward off the lip",
        forward > BITE,
        f"{forward:.1f} mm3 interference",
    )


def check_screw(runner, part, height):
    spec = part.spec
    mid_width = spec.width / 2.0
    bore_is_open = not has_material_at(
        part.solid, PLATE_THK / 2.0, height, mid_width, size=0.4
    )
    back_is_flat = not has_material_at(
        part.solid, PLATE_THK - 0.5, height, mid_width + 3.0, size=0.4
    )
    front_is_countersunk = has_material_at(
        part.solid, 0.4, height, mid_width + 3.0, size=0.4
    )
    runner.check(
        f"screw {height:.1f}: bore open, countersunk front only",
        bore_is_open and back_is_flat and front_is_countersunk,
    )

    csink_r = CSINK_D / 2.0
    runner.check(
        f"screw {height:.1f}: clear of the cradle, on flat plate",
        height > AXIS_V + spec.lip_rise + csink_r,
    )
    headroom = spec.plate_h - height - csink_r
    runner.check(
        f"screw {height:.1f}: fits under the plate top",
        height + csink_r + PLATE_ABOVE_SCREW < spec.plate_h,
        f"{headroom:.1f} mm of plate above it",
    )


def check_solid_is_printable(runner, part):
    runner.check("single connected body", len(part.solid.decompose()) == 1)
    voids = enclosed_void_count(profile(part.spec))
    runner.check("no enclosed voids in the profile", voids == 0, f"{voids} found")


def check_derived_angles(runner, part):
    """The two angles nothing in the code is allowed to set directly: the
    wedge's parallel diagonals, and the level top of a lipless cradle."""
    spec = part.spec
    cross_section = profile(spec)
    if spec.support is WEDGE:
        longest = [angle for _, angle in straight_edge_angles(cross_section)][:4]
        diagonals = sorted(a for a in longest if 5.0 < a < 85.0)
        spread = abs(diagonals[0] - diagonals[-1]) if len(diagonals) >= 2 else None
        runner.check(
            "the wedge's two diagonals are parallel",
            spread is not None and spread < MAX_DIAGONAL_SPREAD,
            ", ".join(f"{a:.2f}" for a in diagonals) + " deg",
        )
    if spec.lip_rise == 0.0:
        wall_side, outer = cradle_wall_tops(cross_section, spec.cradle.radius)
        runner.check(
            "cradle walls level with each other",
            abs(wall_side - outer) < MAX_WALL_STEP,
            f"wall side {wall_side:.2f} mm, outer {outer:.2f} mm",
        )


def check_pair_seats_rod_level(runner, parts):
    """The two mounts must agree on where the rod is, or it will not be level
    or parallel to the wall. Measured off the real solids, not the parameters."""
    butt, tip = (next(p for p in parts if p.kind == kind) for kind in ("butt", "tip"))
    butt_seat = seat_height(butt.solid, butt.spec)
    tip_seat = seat_height(tip.solid, tip.spec)
    mismatch = abs(butt_seat - tip_seat)
    tilt = math.degrees(math.atan2(mismatch, SPAN))
    runner.check(
        "butt + tip seat the rod at the same height",
        mismatch < MAX_SEAT_MISMATCH,
        f"butt {butt_seat:.2f} mm vs tip {tip_seat:.2f} mm",
    )
    runner.check(
        f"rod tilt over a {SPAN:.0f} mm span", tilt < MAX_TILT, f"{tilt:.4f} deg"
    )


def verify_all():
    """Run every check against every mount. True if all pass."""
    runner = CheckRunner()
    for rod in RODS:
        pair = list(parts([rod]))
        for part in pair:
            check_part(runner, part)
        runner.section(f"cross-part alignment: {rod.name}")
        check_pair_seats_rod_level(runner, pair)
    print(
        "\nALL CHECKS PASSED" if runner.all_passed else f"\nFAILURES: {runner.failures}"
    )
    return runner.all_passed
