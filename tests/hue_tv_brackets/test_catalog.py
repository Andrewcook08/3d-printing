"""How a configured entry becomes a bracket.

The tests that used to live here compared the catalog against the constants it
was built from. Both sides now read the same file, so those would assert that
config equals config -- they are gone rather than left to look like coverage.
What is left is what the code actually decides: how an entry's own lean beats
the design's, and what a corner's radius implies about the arc it sweeps.
"""

import math
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
from printing3d.hue_tv_brackets.geometry import QUARTER_TURN, corner


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


# What an entry is allowed to say about the shape itself, as opposed to about
# the part cut from it. Deliberately short: everything outside this list is
# one design shared by every part, and that is what stops two brackets
# disagreeing about a channel they are both supposed to fit.
AN_ENTRY_MAY_CHANGE = ("tilt", "lip_reach")


def test_an_entry_may_change_only_the_lean_and_the_lip_reach(built, design):
    """Every bracket carries the design it was built from, and an entry may
    change how far its channel leans and whether its lips catch the strip --
    nothing else, or parts meant to join would stop sharing a channel."""
    for part in built:
        taken_back = replace(
            part.design,
            **{field: getattr(design, field) for field in AN_ENTRY_MAY_CHANGE},
        )
        assert taken_back == design, part.name


# One case per field an entry may change, each asking for a value the shipped
# design does not already have -- otherwise a field could stop being read and
# the case would still pass.
A_CHANGE_EACH = (
    ("tilt", 60.0, CornerEntry(name="x", radius=38.1, tilt=60.0)),
    ("lip_reach", 0.0, CornerEntry(name="x", radius=38.1, lip_reach=0.0)),
)


@pytest.mark.parametrize(("field", "wanted", "entry"), A_CHANGE_EACH)
def test_every_field_an_entry_may_change_really_does_change_it(
    design, field, wanted, entry
):
    """Otherwise the list above could name a field nothing reads, and the
    test that leans on it would be guarding a rule it had stopped enforcing."""
    (built,) = only(design, corner=[entry])
    assert getattr(built.design, field) == wanted
    assert getattr(built.design, field) != getattr(design, field)


def test_each_field_an_entry_may_change_is_covered_above():
    """Keeps the list and the cases that exercise it from drifting apart."""
    assert {field for field, _, _ in A_CHANGE_EACH} == set(AN_ENTRY_MAY_CHANGE)


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


# ---------------------------------------------------------------------------
# Runs led into a corner, which an entry may ask for and need not
# ---------------------------------------------------------------------------


def test_a_corner_naming_no_runs_is_the_bare_turn(design):
    """The constraint that keeps every corner already shipped buildable.

    An entry saying nothing about runs has to come out as the turn on its own,
    through the path it always took. Compared as solids rather than by trusting
    the branch: what ships is pinned by its hash, and this says why that hash
    is allowed to be unchanged.
    """
    entry = CornerEntry(name="bare", radius=38.1, tilt=90.0)
    (built,) = only(design, corner=[entry])
    bare = corner(replace(design, tilt=90.0), 38.1)
    assert (built.solid - bare).volume() == pytest.approx(0.0, abs=1e-9)
    assert (bare - built.solid).volume() == pytest.approx(0.0, abs=1e-9)


def test_a_corner_naming_runs_is_bigger_than_the_bare_turn(design):
    """Otherwise the entry could be read and quietly ignored."""
    led = CornerEntry(
        name="led", radius=38.1, tilt=90.0, lead=101.6, run_tilt=45.0, twist=76.2
    )
    (built,) = only(design, corner=[led])
    bare = corner(replace(design, tilt=90.0), 38.1)
    assert built.solid.volume() > bare.volume()


def test_a_corner_extends_at_its_own_lean_when_told_nothing_else(design):
    """A lead on its own is the thing that asks for straight bits, and they
    hold the corner's own lean -- so it means something at every angle, not
    only at the one the straights happen to use."""
    for tilt in (90.0, 75.0, 45.0):
        entry = CornerEntry(name="tails", radius=38.1, tilt=tilt, lead=25.4)
        (built,) = only(design, corner=[entry])
        assert len(built.solid.decompose()) == 1
        assert built.solid.genus() == 0


def test_runs_described_without_a_lead_to_put_them_on_are_refused(design):
    """Otherwise the numbers would be read and quietly dropped."""
    for entry in (
        CornerEntry(name="nowhere", radius=38.1, tilt=90.0, run_tilt=45.0),
        CornerEntry(name="nowhere", radius=38.1, tilt=90.0, twist=76.2),
    ):
        with pytest.raises(ValueError, match="no lead"):
            only(design, corner=[entry])


def test_a_corner_with_runs_spends_the_strip_they_carry(design):
    """A led corner takes the strip through its runs as well as its turn, so
    what it spends has to count both -- that is the number a run is cut to."""
    led = CornerEntry(
        name="led", radius=38.1, tilt=90.0, lead=101.6, run_tilt=45.0, twist=76.2
    )
    (built,) = only(design, corner=[led])
    bare_turn = math.radians(QUARTER_TURN) * 38.1
    assert built.strip_spent == pytest.approx(bare_turn + 2 * 101.6)


# ---------------------------------------------------------------------------
# A corner whose channel is open
# ---------------------------------------------------------------------------


def test_a_corner_may_open_its_channel_without_the_straights_opening_theirs(design):
    """The point of putting it on the entry: one part is filled from above
    while every other part still catches the strip."""
    entry = CornerEntry(name="open", radius=38.1, tilt=90.0, lip_reach=0.0)
    (built,) = only(design, corner=[entry])
    assert not built.design.clips
    assert built.design.mouth_width == built.design.channel_width
    assert design.clips, "the shipped design still catches the strip"


def test_an_open_corner_is_a_sound_solid(design):
    entry = CornerEntry(name="open", radius=38.1, tilt=90.0, lip_reach=0.0)
    (built,) = only(design, corner=[entry])
    assert len(built.solid.decompose()) == 1
    assert built.solid.genus() == 0


def test_an_open_corner_has_more_room_in_it_than_a_lipped_one(design):
    """Otherwise the key could be read and quietly dropped."""
    (lipped,) = only(design, corner=[CornerEntry(name="a", radius=38.1, tilt=90.0)])
    (opened,) = only(
        design,
        corner=[CornerEntry(name="b", radius=38.1, tilt=90.0, lip_reach=0.0)],
    )
    assert opened.solid.volume() < lipped.solid.volume()


# ---------------------------------------------------------------------------
# A straight run may shorten its lips too
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("reach", [0.8, 0.4])
def test_a_straight_may_shorten_its_lips_and_still_catch_the_strip(design, reach):
    """A shallower lip is one the strip pops past rather than is fed along,
    which is what a run already on the wall wants. It is still a clip."""
    entry = StraightEntry(name="shallow", length=50.8, lip_reach=reach)
    (built,) = only(design, straight=[entry])
    assert built.design.lip_reach == reach
    assert built.design.clips
    assert built.design.mouth_width < design.strip_width, "would not retain the strip"


def test_a_straight_may_open_its_channel_entirely(design):
    entry = StraightEntry(name="open", length=50.8, lip_reach=0.0)
    (built,) = only(design, straight=[entry])
    assert not built.design.clips
    assert len(built.solid.decompose()) == 1
    assert built.solid.genus() == 0


def test_shortening_a_straights_lips_widens_its_mouth(design):
    """Otherwise the key could be read and quietly dropped."""
    (shipped,) = only(design, straight=[StraightEntry(name="a", length=50.8)])
    (shallow,) = only(
        design, straight=[StraightEntry(name="b", length=50.8, lip_reach=0.4)]
    )
    assert shallow.design.mouth_width > shipped.design.mouth_width
    assert shallow.solid.volume() < shipped.solid.volume()


def test_one_straights_lips_do_not_reach_into_another(design):
    """The override is per entry, so a run built shallow leaves the rest of
    the catalogue catching the strip exactly as it did."""
    entries = [
        StraightEntry(name="shallow", length=50.8, lip_reach=0.4),
        StraightEntry(name="shipped", length=50.8),
    ]
    shallow, shipped = only(design, straight=entries)
    assert shallow.design.lip_reach == 0.4
    assert shipped.design.lip_reach == design.lip_reach
