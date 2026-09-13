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


def straight_edge_angles(cross_section, min_len):
    """Angles of the straight edges in a profile, longest first.

    Lets a check confirm two faces really are parallel by measuring the built
    profile, rather than trusting that the same constant was used in both
    places.
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


def enclosed_void_count(cross_section):
    """How many fully enclosed pockets the profile contains."""
    return sum(1 for contour in cross_section.to_polygons() if signed_area(contour) < 0)


def highest_point_between(cross_section, u0, u1, ceiling=300.0):
    """Top of the material in the vertical slice from u0 to u1."""
    column = cross_section ^ m.CrossSection.square((u1 - u0, ceiling), False).translate(
        (u0, 0.0)
    )
    return max(point[1] for contour in column.to_polygons() for point in contour)
