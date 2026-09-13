"""What the catalog ships, and how each bracket is named."""

import pytest

from printing3d.hue_tv_brackets.catalog import (
    LADDER_RADII,
    STRAIGHT_LENGTHS,
    TRIAL_CORNERS,
    TRIAL_LEANS,
    corners,
    parts,
    straights,
)
from printing3d.hue_tv_brackets.geometry import TILT, to_outermost, to_tab_edge


@pytest.fixture(scope="module")
def shipped():
    return list(parts())


@pytest.fixture(scope="module")
def by_radius(shipped):
    return {part.radius: part for part in corners(shipped)}


def test_the_catalog_ships_both_shapes(shipped):
    """Guards every test below from passing by collecting nothing, which is how
    pruning the ladder to one radius would otherwise go unnoticed."""
    assert straights(shipped)
    assert corners(shipped)


def shipping(brackets):
    """The brackets at the lean this project ships, trials excluded."""
    return [part for part in brackets if part.tilt == TILT]


def trials(brackets):
    """The brackets at a lean still under test."""
    return [part for part in brackets if part.tilt != TILT]


def test_one_straight_ships_for_each_length(shipped):
    assert [part.length for part in shipping(straights(shipped))] == STRAIGHT_LENGTHS


def test_one_corner_ships_for_each_rung_of_the_ladder(shipped):
    assert [part.radius for part in shipping(corners(shipped))] == LADDER_RADII


def test_a_trial_corner_and_a_matching_straight_ship_for_each_lean(shipped):
    """A trial corner is only meaningful beside a straight at its own lean,
    which is what verify compares it against."""
    assert [(p.tilt, p.radius) for p in trials(corners(shipped))] == TRIAL_CORNERS
    assert [p.tilt for p in trials(straights(shipped))] == TRIAL_LEANS


def test_a_brackets_name_says_what_it_is(shipped):
    """The name is written into the STL header, so it is how a printed bracket
    is told apart from its neighbours on the ladder."""
    assert all(f"{part.length:g}mm" in part.name for part in straights(shipped))
    assert all(f"r{part.radius:g}" in part.name for part in corners(shipped))


def test_no_two_brackets_share_a_name(shipped):
    names = [part.name for part in shipped]
    assert len(names) == len(set(names))


@pytest.mark.parametrize("radius", LADDER_RADII)
def test_a_corner_reports_the_arc_its_material_sweeps(by_radius, radius):
    part = by_radius[radius]
    assert part.inner_radius == pytest.approx(radius - to_tab_edge(part.tilt))
    assert part.outer_radius == pytest.approx(radius + to_outermost(part.tilt))


@pytest.mark.parametrize("radius", LADDER_RADII)
def test_a_corner_leaves_room_inside_its_own_turn(by_radius, radius):
    """A corner whose inner edge reached the axis would fold through itself."""
    assert by_radius[radius].inner_radius > 0.0
