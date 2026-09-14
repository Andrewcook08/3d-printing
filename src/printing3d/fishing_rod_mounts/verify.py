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

from printing3d.checks import CheckRunner
from printing3d.fishing_rod_mounts.catalog import catalogue, parts
from printing3d.fishing_rod_mounts.geometry import WEDGE, profile
from printing3d.probes import (
    TOUCHING,
    enclosed_void_count,
    has_material_at,
    highest_point_between,
    overlap,
    straight_runs,
    surface_height_below,
)

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

# Probing the screw bore. The probe is smaller than the bore so it fits inside
# one; the back is sampled just inside the face, where a countersink would show
# if it had been cut from the wrong side; and the off-axis distance is far
# enough out to miss the shank while still inside the countersink's cone.
BORE_PROBE_SIZE = 0.4
JUST_INSIDE_THE_BACK = 0.5
OFF_THE_BORE_AXIS = 3.0


# ---------------------------------------------------------------------------
# Probes: questions asked of a finished solid
# ---------------------------------------------------------------------------


def rod_at(spec, du=0.0, dv=0.0):
    """The rod, as a solid, displaced from its nominal seat."""
    return (
        m.CrossSection.circle(spec.rod_dia / 2.0, 256)
        .translate((spec.design.axis_from_wall + du, spec.design.axis_height + dv))
        .extrude(spec.design.slab_width)
    )


def lift_sweep(spec):
    """Everything the rod passes through as it is lifted straight up and out."""
    radius = spec.rod_dia / 2.0
    axis_u, axis_v = spec.design.axis_from_wall, spec.design.axis_height
    disc = m.CrossSection.circle(radius, 256).translate((axis_u, axis_v))
    chute = m.CrossSection.square((2 * radius, LIFT_HEIGHT), False).translate(
        (axis_u - radius, axis_v)
    )
    return (disc + chute).extrude(spec.design.slab_width)


def seat_height(solid, spec):
    """Cradle floor + rod radius, measured off the solid.

    Scans DOWN the cradle centerline: scanning up from v=0 would be wrong,
    since the tip mount's underside is open air below the part.
    """
    floor = surface_height_below(
        solid,
        spec.design.axis_from_wall,
        spec.design.slab_width / 2.0,
        spec.design.axis_height,
    )
    return floor + spec.rod_dia / 2.0


def cradle_wall_tops(cross_section, cradle_radius, design):
    """Height of the cradle's wall-side wall and of the outer lip."""
    axis_u, rib = design.axis_from_wall, design.rib
    walls = (
        (axis_u - cradle_radius - rib, axis_u - cradle_radius),
        (axis_u + cradle_radius, axis_u + cradle_radius + rib),
    )
    return [highest_point_between(cross_section, u0, u1) for u0, u1 in walls]


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_part(runner, part):
    spec = part.spec
    runner.section(
        f"{part.name}  (rod {spec.rod_dia} mm, "
        f"{len(spec.design.screw.heights)} screw"
        f"{'s' if len(spec.design.screw.heights) > 1 else ''}, "
        f"{spec.design.slab_width:.0f} mm wide)"
    )
    check_rod_seats_and_releases(runner, part)
    check_rod_is_trapped_sideways(runner, part)
    for height in spec.design.screw.heights:
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
    clearance = spec.design.axis_from_wall - spec.rod_dia / 2.0
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
    mid_width = spec.design.slab_width / 2.0
    plate_thickness = spec.design.plate_thickness
    bore_is_open = not has_material_at(
        part.solid, plate_thickness / 2.0, height, mid_width, size=BORE_PROBE_SIZE
    )
    back_is_flat = not has_material_at(
        part.solid,
        plate_thickness - JUST_INSIDE_THE_BACK,
        height,
        mid_width + OFF_THE_BORE_AXIS,
        size=BORE_PROBE_SIZE,
    )
    front_is_countersunk = has_material_at(
        part.solid,
        BORE_PROBE_SIZE,
        height,
        mid_width + OFF_THE_BORE_AXIS,
        size=BORE_PROBE_SIZE,
    )
    runner.check(
        f"screw {height:.1f}: bore open, countersunk front only",
        bore_is_open and back_is_flat and front_is_countersunk,
    )

    csink_r = spec.design.screw.countersink_diameter / 2.0
    runner.check(
        f"screw {height:.1f}: clear of the cradle, on flat plate",
        height > spec.design.axis_height + spec.lip_rise + csink_r,
    )
    headroom = spec.design.plate_height - height - csink_r
    runner.check(
        f"screw {height:.1f}: fits under the plate top",
        height + csink_r + PLATE_ABOVE_SCREW < spec.design.plate_height,
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
        # Faces are merged before they are ranked, so a face split by a
        # boolean seam cannot read short and push a real diagonal out of the
        # longest four.
        longest = [angle for _, angle in straight_runs(cross_section, MIN_EDGE_LENGTH)][
            :4
        ]
        diagonals = sorted(a for a in longest if 5.0 < a < 85.0)
        spread = abs(diagonals[0] - diagonals[-1]) if len(diagonals) >= 2 else None
        runner.check(
            "the wedge's two diagonals are parallel",
            spread is not None and spread < MAX_DIAGONAL_SPREAD,
            ", ".join(f"{a:.2f}" for a in diagonals) + " deg",
        )
    if spec.lip_rise == 0.0:
        wall_side, outer = cradle_wall_tops(
            cross_section, spec.cradle.radius, spec.design
        )
        runner.check(
            "cradle walls level with each other",
            abs(wall_side - outer) < MAX_WALL_STEP,
            f"wall side {wall_side:.2f} mm, outer {outer:.2f} mm",
        )


def check_pair_seats_rod_level(runner, parts):
    """The two mounts must agree on where the rod is, or it will not be level
    or parallel to the wall. Measured off the real solids, not the parameters."""
    by_kind = {part.kind: part for part in parts}
    missing = [kind for kind in ("butt", "tip") if kind not in by_kind]
    if missing:
        runner.check(
            f"a {' and a '.join(missing)} mount ships to compare against", False
        )
        return
    butt, tip = by_kind["butt"], by_kind["tip"]
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
    built = list(parts())
    for rod in catalogue().rod:
        pair = [part for part in built if part.rod == rod.name]
        for part in pair:
            check_part(runner, part)
        runner.section(f"cross-part alignment: {rod.name}")
        check_pair_seats_rod_level(runner, pair)
    return runner.report()
