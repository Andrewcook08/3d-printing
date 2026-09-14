"""Shared interrogation of built solids and profiles."""

import pytest
from manifold3d import Manifold

from printing3d.probes import (
    FINE_PROBE_SIZE,
    enclosed_void_count,
    has_material_at,
    highest_point_between,
    overlap,
    straight_runs,
    surface_height_below,
)
from printing3d.shapes import polygon, rect


@pytest.fixture
def cube():
    """A 10mm cube with its near corner at the origin."""
    return Manifold.cube((10.0, 10.0, 10.0), False)


def test_material_is_found_inside_the_solid(cube):
    assert has_material_at(cube, 5.0, 5.0, 5.0)


def test_no_material_is_found_outside_the_solid(cube):
    assert not has_material_at(cube, 50.0, 5.0, 5.0)


def test_overlap_is_zero_for_separated_solids(cube):
    assert overlap(cube, cube.translate((100.0, 0.0, 0.0))) == 0.0


def test_overlap_measures_the_shared_volume(cube):
    half = cube.translate((5.0, 0.0, 0.0))
    assert overlap(cube, half) == pytest.approx(5.0 * 10.0 * 10.0)


def test_the_surface_below_is_the_top_face(cube):
    """Scanning down from above the cube finds its top at v=10.

    Within half a probe width: the sampling cube is centred on the point, so it
    touches the surface fractionally before its centre reaches it.
    """
    assert surface_height_below(cube, 5.0, 5.0, 20.0) == pytest.approx(
        10.0, abs=FINE_PROBE_SIZE
    )


def test_scanning_where_there_is_nothing_raises(cube):
    with pytest.raises(ValueError, match="no surface"):
        surface_height_below(cube, 50.0, 5.0, 20.0)


def test_a_solid_profile_has_no_enclosed_voids():
    assert enclosed_void_count(rect(0.0, 0.0, 10.0, 10.0)) == 0


def test_a_punched_profile_reports_its_pocket():
    assert (
        enclosed_void_count(rect(0.0, 0.0, 10.0, 10.0) - rect(3.0, 3.0, 7.0, 7.0)) == 1
    )


def test_edge_angles_come_back_longest_first():
    lengths = [length for length, _ in straight_runs(rect(0.0, 0.0, 8.0, 3.0), 1.0)]
    assert lengths == sorted(lengths, reverse=True)


def test_a_right_triangle_reports_its_slope():
    ramp = polygon([(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)])
    angles = [angle for _, angle in straight_runs(ramp, 1.0)]
    assert any(angle == pytest.approx(45.0) for angle in angles)


def test_a_face_split_by_a_seam_is_measured_as_one_face():
    """The reason this exists. Two shapes butted together leave vertices along
    the join, so one flat face arrives as several collinear pieces -- and each
    piece then reads shorter than the face actually is."""
    butted = rect(0.0, 0.0, 5.0, 3.0) + rect(5.0, 0.0, 10.0, 3.0)
    assert [length for length, _ in straight_runs(butted, 1.0)] == [
        10.0,
        10.0,
        3.0,
        3.0,
    ]


def test_a_face_shorter_than_the_minimum_only_counts_once_merged():
    """A face is measured before the length filter, not after: three 2 mm
    pieces of one 6 mm face survive a 5 mm floor, where separately none would."""
    strip = (
        rect(0.0, 0.0, 2.0, 1.0) + rect(2.0, 0.0, 4.0, 1.0) + rect(4.0, 0.0, 6.0, 1.0)
    )
    assert [length for length, _ in straight_runs(strip, 5.0)] == [6.0, 6.0]


def test_a_face_and_its_reverse_read_as_the_same_angle():
    """Angles fold modulo 180, so which way round the outline was traversed
    does not change what a face measures."""
    angles = {angle for _, angle in straight_runs(rect(0.0, 0.0, 8.0, 3.0), 1.0)}
    assert angles == {0.0, 90.0}


def test_short_edges_are_ignored():
    assert straight_runs(rect(0.0, 0.0, 1.0, 1.0), min_length=5.0) == []


def test_the_highest_point_is_found_within_the_slice():
    stepped = rect(0.0, 0.0, 5.0, 2.0) + rect(5.0, 0.0, 10.0, 8.0)
    assert highest_point_between(stepped, 0.0, 5.0) == pytest.approx(2.0)
    assert highest_point_between(stepped, 5.0, 10.0) == pytest.approx(8.0)
