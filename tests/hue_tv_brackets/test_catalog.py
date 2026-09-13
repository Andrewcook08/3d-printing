"""What the catalog ships, and how each bracket is named."""

import pytest

from printing3d.hue_tv_brackets.catalog import (
    LADDER_RADII,
    STRAIGHT_LENGTHS,
    CornerBracket,
    StraightBracket,
    parts,
)
from printing3d.hue_tv_brackets.geometry import TO_OUTERMOST, TO_TAB_EDGE

SHIPPED = list(parts())


def straights():
    return [part for part in SHIPPED if isinstance(part, StraightBracket)]


def corners():
    return [part for part in SHIPPED if isinstance(part, CornerBracket)]


def test_one_straight_ships_for_each_length():
    assert [part.length for part in straights()] == STRAIGHT_LENGTHS


def test_one_corner_ships_for_each_rung_of_the_ladder():
    assert [part.radius for part in corners()] == LADDER_RADII


def test_a_brackets_name_says_what_it_is():
    """The name is written into the STL header, so it is how a printed bracket
    is told apart from its neighbours on the ladder."""
    assert all(f"{part.length:g}mm" in part.name for part in straights())
    assert all(f"r{part.radius:g}" in part.name for part in corners())


def test_no_two_brackets_share_a_name():
    names = [part.name for part in SHIPPED]
    assert len(names) == len(set(names))


@pytest.mark.parametrize("part", corners(), ids=lambda part: part.name)
def test_a_corner_reports_the_arc_its_material_sweeps(part):
    assert part.inner_radius == pytest.approx(part.radius - TO_TAB_EDGE)
    assert part.outer_radius == pytest.approx(part.radius + TO_OUTERMOST)


@pytest.mark.parametrize("part", corners(), ids=lambda part: part.name)
def test_a_corner_leaves_room_inside_its_own_turn(part):
    """A corner whose inner edge reached the axis would fold through itself."""
    assert part.inner_radius > 0.0
