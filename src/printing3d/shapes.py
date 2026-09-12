"""Two-dimensional construction, shared by every project.

A part is usually described as a flat profile before it becomes a solid, so
these are the primitives that profile is assembled from. Nothing here knows
what a part is -- only points, contours and areas.
"""

import manifold3d as m

MITER_LIMIT = 2.0  # offset() join limit; unused for round joins
ROUND_SEGMENTS = 64  # facets around a rounded corner


def rect(u0, v0, u1, v1):
    """An axis-aligned rectangle from corner (u0, v0) to corner (u1, v1)."""
    return m.CrossSection.square((u1 - u0, v1 - v0), False).translate((u0, v0))


def polygon(points):
    """A closed shape through `points`, in order."""
    return filled([points])


def filled(contours):
    """A CrossSection from plain (u, v) tuples, filled by winding direction.

    manifold3d's stubs ask for numpy arrays here, but the runtime takes
    sequences of tuples -- which is what geometry is written in, and far more
    readable. Routing every construction through this one place keeps that
    mismatch from spreading.
    """
    return m.CrossSection(contours, m.FillRule.Positive)


def signed_area(contour):
    """Twice the signed area of a closed contour; negative means a void."""
    total = 0.0
    for i in range(len(contour)):
        u0, v0 = contour[i]
        u1, v1 = contour[(i + 1) % len(contour)]
        total += u0 * v1 - u1 * v0
    return total


def without_enclosed_voids(part):
    """Drop negative-winding contours, closing any fully enclosed pocket.

    An enclosed pocket is air the slicer would wall in for no benefit.
    """
    solid_contours = [
        [tuple(point) for point in contour]
        for contour in part.to_polygons()
        if signed_area(contour) > 0
    ]
    return filled(solid_contours)


def rounded_convex_corners(part, radius, segments=ROUND_SEGMENTS):
    """Soften convex corners by eroding then dilating with round joins.
    Concave features such as an interior arc come back unchanged."""
    return part.offset(-radius, m.JoinType.Round, MITER_LIMIT, segments).offset(
        radius, m.JoinType.Round, MITER_LIMIT, segments
    )
