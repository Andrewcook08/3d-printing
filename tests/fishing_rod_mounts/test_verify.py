"""That the pre-print checks can report a failure, not only a pass.

`verify` returning True says the checks did not object. It says nothing about
whether they are capable of objecting, and a check that cannot fail reads as a
guarantee while providing none. So each one is handed something wrong.
"""

from dataclasses import replace

import pytest

from printing3d.checks import CheckRunner
from printing3d.fishing_rod_mounts import geometry
from printing3d.fishing_rod_mounts.catalog import parts
from printing3d.fishing_rod_mounts.verify import (
    check_derived_angles,
    check_pair_seats_rod_level,
    check_rod_is_trapped_sideways,
    check_rod_seats_and_releases,
    check_screw,
    check_solid_is_printable,
)

SHIPPED = list(parts())


@pytest.fixture
def butt():
    return next(part for part in SHIPPED if part.kind == "butt")


def objections_to(check, *arguments):
    """What a check complains about when handed `arguments`."""
    runner = CheckRunner()
    check(runner, *arguments)
    return runner.failures


def test_the_checks_pass_the_mounts_that_ship(butt):
    """Guards every test below: they must fail for the reason intended, not
    because these checks object to everything."""
    assert objections_to(check_rod_seats_and_releases, butt) == []
    assert objections_to(check_rod_is_trapped_sideways, butt) == []
    assert objections_to(check_screw, butt, butt.spec.design.screw.heights[0]) == []


def test_a_rod_too_fat_for_its_cradle_is_caught(butt):
    """The solid is the one that ships; the rod it is measured against is not
    the one it was built for."""
    oversized = replace(butt, spec=replace(butt.spec, rod_dia=butt.spec.rod_dia + 4.0))
    assert objections_to(check_rod_seats_and_releases, oversized)


def test_a_rod_that_falls_out_sideways_is_caught(butt):
    """Shrink the rod and the cradle no longer bites it in either direction."""
    undersized = replace(butt, spec=replace(butt.spec, rod_dia=2.0))
    assert objections_to(check_rod_is_trapped_sideways, undersized)


def test_a_screw_placed_into_the_cradle_is_caught(butt):
    """A screw below the rod is in compression and holds nothing, and its
    countersink would open into the curve."""
    assert objections_to(check_screw, butt, 5.0)


def test_a_screw_placed_off_the_top_of_the_plate_is_caught(butt):
    beyond = butt.spec.design.plate_height + 5.0
    assert objections_to(check_screw, butt, beyond)


def test_a_pair_that_would_hang_the_rod_crooked_is_caught():
    """The two mounts agreeing on where the rod sits is the whole reason a butt
    and a tip mount can be built for very different diameters. Lift one and the
    rod hangs out of level, which is the check that has to notice."""
    pair = [part for part in SHIPPED if part.rod == SHIPPED[0].rod]
    tip = next(part for part in pair if part.kind == "tip")
    lifted = replace(tip, solid=tip.solid.translate((0.0, 5.0, 0.0)))
    crooked = [part for part in pair if part.kind != "tip"] + [lifted]

    objections = objections_to(check_pair_seats_rod_level, crooked)

    # Both halves, named separately: the height disagreement and the tilt it
    # produces. Demanding only one lets the other's limit be opened up without
    # anything noticing.
    assert any("same height" in objection for objection in objections), objections
    assert any("tilt" in objection for objection in objections), objections


def test_a_mount_in_two_pieces_is_caught(butt):
    """An arm that has come adrift from its plate is watertight and prints as
    two objects, which a slicer will do without complaint."""
    adrift = replace(butt, solid=butt.solid + butt.solid.translate((100.0, 0.0, 0.0)))
    assert objections_to(check_solid_is_printable, adrift)


def test_a_wedge_whose_diagonals_are_not_parallel_is_caught(monkeypatch):
    """The wedge's two diagonals are parallel because the tangent solver makes
    them so -- nothing sets the angle directly. This check exists to notice if
    that solver ever stops working, so that is what is broken here.

    Patching the derivation is sound where patching a constant the check reads
    would not be: the check measures the profile that comes out, so a wrong
    solver and the check cannot move together.
    """
    tip = next(part for part in SHIPPED if part.kind == "tip")
    monkeypatch.setattr(
        geometry,
        "tangent_slope_from_corner",
        lambda outer_radius, corner_u, design: 0.9,
    )
    assert objections_to(check_derived_angles, tip)


def test_a_rod_missing_one_of_its_mounts_is_reported_not_crashed(butt):
    """Drop a style from the config and the pair is half a pair. That has to
    come back as a failed check naming what is missing, not as a traceback
    naming neither the rod nor the kind."""
    objections = objections_to(check_pair_seats_rod_level, [butt])
    assert any("tip" in objection for objection in objections), objections
