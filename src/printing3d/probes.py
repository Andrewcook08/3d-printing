"""Questions asked of a built solid or a flat profile.

Verification measures the finished geometry rather than the parameters it came
from, so a mistake anywhere in between still shows up. These are the
measurement primitives that makes that possible. Nothing here knows what a
part is.
"""

import math

import manifold3d as m

from printing3d.shapes import signed_area

TOUCHING = 1e-6  # volumes below this count as no contact at all
PROBE_SIZE = 0.6  # side of the test cube used to ask "material here?"
FINE_PROBE_SIZE = 0.05  # for locating a surface, not just sampling


def has_material_at(solid, u, v, w, size=PROBE_SIZE):
    """Is there material at this point? (tiny cube intersection)"""
    cube = m.Manifold.cube((size, size, size), True).translate((u, v, w))
    return (solid ^ cube).volume() > TOUCHING


def overlap(solid, other):
    """Volume the two solids share. Zero means they do not touch."""
    return (solid ^ other).volume()


def surface_height_below(solid, u, w, start_v, step=0.25, limit=-5.0, rounds=40):
    """Height of the first surface found scanning DOWN from `start_v`.

    Scanning down rather than up matters wherever a part is open underneath:
    scanning up from below would find the underside, not the floor you meant.

    Resolution is half the probe width: the sampling cube is centred on the
    point, so it registers material fractionally before its centre reaches the
    surface. Raises if no surface is found before `limit`.
    """

    def material(v):
        return has_material_at(solid, u, v, w, size=FINE_PROBE_SIZE)

    if material(start_v):
        raise ValueError(
            f"v={start_v} at (u={u}, w={w}) is already inside material; "
            f"there is no surface below a point that is not above one"
        )

    air, v = start_v, start_v
    while v > limit:
        if material(v):
            floor = v
            break
        air, v = v, v - step
    else:
        raise ValueError(
            f"no surface below v={start_v} at (u={u}, w={w}), scanned to {limit}"
        )

    for _ in range(rounds):
        midpoint = (air + floor) / 2.0
        if material(midpoint):
            floor = midpoint
        else:
            air = midpoint
    return (air + floor) / 2.0


COLLINEAR = 1e-6  # sine of the turn below which two segments are one face


def straight_runs(section, min_length):
    """Straight runs of the outline, collinear segments merged, longest first.

    A section cut from a mesh carries vertices wherever the triangulation put
    them, so one flat face arrives as several collinear segments. Merging them
    is what makes a measured face comparable to the face as drawn.

    Four things here nobody outside this repo decided, and every caller
    inherits all four: COLLINEAR as the turn below which two segments are one
    face; angles folded modulo 180, so a face and its reverse read alike;
    longest first, with ties falling out of the tuple order rather than from
    any decision; and a zero-length segment counted as running straight
    through.
    """
    runs = []
    for contour in section.to_polygons():
        turning_points = _corners_of([tuple(point) for point in contour])
        for start, end in zip(
            turning_points, turning_points[1:] + turning_points[:1], strict=True
        ):
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


def enclosed_void_count(cross_section):
    """How many fully enclosed pockets the profile contains."""
    return sum(1 for contour in cross_section.to_polygons() if signed_area(contour) < 0)


def highest_point_between(cross_section, u0, u1, ceiling=300.0):
    """Top of the material in the vertical slice from u0 to u1."""
    column = cross_section ^ m.CrossSection.square((u1 - u0, ceiling), False).translate(
        (u0, 0.0)
    )
    return max(point[1] for contour in column.to_polygons() for point in contour)
