"""How a configured entry becomes a bracket.

The tests that used to live here compared the catalog against the constants it
was built from. Both sides now read the same file, so those would assert that
config equals config -- they are gone rather than left to look like coverage.
What is left is what the code actually decides: how an entry's own lean beats
the design's, and what a corner's radius implies about the arc it sweeps.
"""

from dataclasses import replace

import pytest

from printing3d.hue_tv_brackets.catalog import (
    CornerEntry,
    StraightEntry,
    corners,
    parts,
    shipping,
    straights,
    trial_parts,
    trials,
)


@pytest.fixture(scope="module")
def design():
    return shipping().design


@pytest.fixture(scope="module")
def built():
    """Everything the project builds -- what ships and what is being tested.

    Both, because these tests are about how an entry becomes a bracket, which
    is the same question either side of that line. Only the corners are trials
    today, so the shipped catalogue alone would make half of them vacuous.
    """
    return [*parts(), *trial_parts()]


def only(design, **entries):
    """The brackets a catalogue holding just these entries would produce."""
    catalogue = replace(
        shipping(), design=design, **{"straight": [], "corner": [], **entries}
    )
    return list(parts(catalogue))


# ---------------------------------------------------------------------------
# What the shipped configuration produces
# ---------------------------------------------------------------------------


def test_the_catalog_ships_both_shapes(built):
    """Guards the tests below from passing by measuring nothing."""
    assert straights(built)
    assert corners(built)


def test_an_entry_may_override_the_lean_and_nothing_else(built, design):
    """Every bracket carries the design it was built from, and the only thing
    an entry is allowed to change about it is how far the channel leans."""
    assert all(replace(part.design, tilt=design.tilt) == design for part in built)


# ---------------------------------------------------------------------------
# An entry's own lean
# ---------------------------------------------------------------------------


def test_an_entry_without_a_lean_takes_the_designs(design):
    entry = StraightEntry(name="plain", length=10.0)
    (built,) = only(design, straight=[entry])
    assert built.design.tilt == design.tilt


def test_an_entry_with_a_lean_overrides_the_design(design):
    entry = CornerEntry(name="rolled", radius=101.0, tilt=65.0)
    (built,) = only(design, corner=[entry])
    assert built.design.tilt == 65.0


def test_overriding_the_lean_changes_nothing_else(design):
    entry = CornerEntry(name="rolled", radius=101.0, tilt=65.0)
    (built,) = only(design, corner=[entry])
    assert replace(built.design, tilt=design.tilt) == design


# ---------------------------------------------------------------------------
# What a corner's radius implies
# ---------------------------------------------------------------------------


def test_a_corner_reports_the_arc_its_material_sweeps(built):
    for part in corners(built):
        assert part.inner_radius == pytest.approx(part.radius - part.design.to_tab_edge)
        assert part.outer_radius == pytest.approx(
            part.radius + part.design.to_outermost
        )


def test_a_corner_leaves_room_inside_its_own_turn(built):
    """A corner whose inner edge reached the axis would fold through itself."""
    assert all(part.inner_radius > 0.0 for part in corners(built))


# ---------------------------------------------------------------------------
# The notes an entry carries
# ---------------------------------------------------------------------------


def test_a_note_reaches_the_build_output(design):
    entry = StraightEntry(name="noted", length=10.0, note="why this exists")
    (built,) = only(design, straight=[entry])
    assert "why this exists" in built.footprint_line()


def test_a_bracket_without_a_note_says_nothing_extra(design):
    entry = StraightEntry(name="plain", length=10.0)
    (built,) = only(design, straight=[entry])
    assert "--" not in built.footprint_line()


# ---------------------------------------------------------------------------
# The files themselves
# ---------------------------------------------------------------------------


def test_the_shipped_design_describes_a_channel_that_clips(design):
    """Read from the file rather than asserted about the code: a mouth wider
    than its bed would be a trough, and the strip would lift straight out."""
    assert design.mouth_width < design.channel_width


def test_every_trial_corner_is_wider_than_the_part_reaching_into_it(design):
    """A radius below the floor cannot be built at all. Checking the file says
    so before a print does."""
    for entry in trials().corner:
        leaning = design if entry.tilt is None else replace(design, tilt=entry.tilt)
        assert entry.radius > leaning.min_corner_radius, entry.name
