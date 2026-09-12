"""Shared 2D construction."""

import pytest

from printing3d.shapes import (
    filled,
    polygon,
    rect,
    rounded_convex_corners,
    signed_area,
    without_enclosed_voids,
)

SQUARE = [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0)]


def test_the_rectangle_covers_exactly_the_given_corners():
    assert rect(1.0, 2.0, 4.0, 6.0).bounds() == (1.0, 2.0, 4.0, 6.0)


def test_a_polygon_spans_its_points():
    assert polygon(SQUARE).bounds() == (0.0, 0.0, 4.0, 4.0)


def test_a_counterclockwise_contour_is_solid():
    assert signed_area(SQUARE) > 0


def test_a_clockwise_contour_is_a_void():
    assert signed_area(list(reversed(SQUARE))) < 0


def test_signed_area_is_twice_the_enclosed_area():
    assert signed_area(SQUARE) == pytest.approx(2 * 4.0 * 4.0)


def a_square_with_a_hole():
    """A 10mm square with a 4mm square punched out of the middle."""
    return rect(0.0, 0.0, 10.0, 10.0) - rect(3.0, 3.0, 7.0, 7.0)


def test_an_enclosed_pocket_is_closed():
    assert a_square_with_a_hole().area() == pytest.approx(100.0 - 16.0)
    assert without_enclosed_voids(a_square_with_a_hole()).area() == pytest.approx(100.0)


def test_filling_keeps_a_shape_that_has_no_pocket():
    solid = rect(0.0, 0.0, 10.0, 10.0)
    assert without_enclosed_voids(solid).area() == pytest.approx(solid.area())


def test_rounding_removes_area_from_convex_corners():
    square = rect(0.0, 0.0, 10.0, 10.0)
    rounded = rounded_convex_corners(square, 1.0)
    assert rounded.area() < square.area()
    # Four corners, each losing a square minus its quarter circle.
    lost = 4 * (1.0**2 - 3.14159 / 4)
    assert square.area() - rounded.area() == pytest.approx(lost, abs=0.01)


def test_rounding_leaves_the_overall_size_alone():
    assert rounded_convex_corners(rect(0.0, 0.0, 10.0, 10.0), 1.0).bounds() == (
        pytest.approx(0.0),
        pytest.approx(0.0),
        pytest.approx(10.0),
        pytest.approx(10.0),
    )


def test_filled_builds_from_plain_tuples():
    assert filled([SQUARE]).area() == pytest.approx(16.0)
