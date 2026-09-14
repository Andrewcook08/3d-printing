"""That the pre-print checks can report a failure, not only a pass.

`verify` returning True says the checks did not object. It says nothing about
whether they are capable of objecting, and a check that cannot fail is worse
than no check: it reads as a guarantee. So each one is handed something wrong
and has to notice.
"""

from dataclasses import replace

import pytest

from printing3d.checks import CheckRunner
from printing3d.hue_tv_brackets.catalog import CornerBracket, shipping
from printing3d.hue_tv_brackets.geometry import CORNER_SEGMENTS, corner, profile
from printing3d.hue_tv_brackets.verify import (
    check_base_is_flat,
    check_channel_aims_out,
    check_channel_clips,
    check_corner_matches_the_straight,
    check_corner_turns_a_quarter,
    check_profile_is_solid,
    corner_section,
)
from printing3d.shapes import rect

DESIGN = shipping().design


def objections_to(check, *arguments):
    """What a check complains about when handed `arguments`."""
    runner = CheckRunner()
    check(runner, *arguments)
    return runner.failures


def test_the_checks_pass_the_shape_that_ships():
    """Guards every test below: they must fail for the reason intended, not
    because these checks object to everything."""
    assert objections_to(check_channel_clips, profile(DESIGN), DESIGN) == []
    assert objections_to(check_channel_aims_out, profile(DESIGN), DESIGN) == []
    assert objections_to(check_base_is_flat, profile(DESIGN), DESIGN) == []


def test_a_channel_with_no_lips_is_caught():
    """Reach the lips nowhere and the mouth is as wide as the bed: a trough,
    which the strip would lift straight out of."""
    troughed = replace(DESIGN, lip_reach=0.0)
    assert objections_to(check_channel_clips, profile(troughed), troughed)


def test_a_channel_necked_shut_is_NOT_caught():
    """Pins a known hole rather than a guarantee, so it cannot be forgotten.

    A 0.60 mm mouth admits nothing and passes every check, because catching it
    needs a floor under the mouth and the strip's bow has never been measured.
    If someone measures it and adds that floor, this test fails and is deleted
    -- which is the point of writing it down as a test instead of a comment.
    """
    shut = replace(DESIGN, lip_reach=7.2)  # a 0.60 mm mouth for a 14.4 mm strip
    assert objections_to(check_channel_clips, profile(shut), shut) == []


def test_a_channel_too_narrow_for_its_strip_is_caught():
    """The bed has to carry the strip, not merely be a bed."""
    skinny = replace(DESIGN, strip_width=DESIGN.channel_width + 1.0)
    assert objections_to(check_channel_clips, profile(skinny), skinny)


def test_a_channel_leaning_the_wrong_way_is_caught():
    """The section is built at one lean and measured against another."""
    rolled = replace(DESIGN, tilt=65.0)
    assert objections_to(check_channel_aims_out, profile(rolled), DESIGN)


def test_a_pad_lifted_off_the_mounting_plane_is_caught():
    assert objections_to(
        check_base_is_flat, profile(DESIGN).translate((0.0, 3.0)), DESIGN
    )


def test_a_corner_that_does_not_match_its_straight_is_caught():
    """The claim the whole design rests on has to be falsifiable."""
    mismatched = replace(DESIGN, channel_width=DESIGN.channel_width + 2.0)
    assert objections_to(
        check_corner_matches_the_straight, profile(mismatched), profile(DESIGN)
    )


@pytest.mark.parametrize("turn", [45.0, 200.0])
def test_a_corner_that_does_not_turn_a_quarter_is_caught(turn):
    """Swept through the wrong angle, the arc either stops short or runs on.

    Built by revolving directly rather than by patching the constant the check
    reads: patched, the sweep and the check would move together and agree
    forever, which is a test that cannot fail wearing the clothes of one that
    can.
    """
    part = CornerBracket(
        name="wrong-sweep",
        solid=profile(DESIGN).translate((101.0, 0.0)).revolve(CORNER_SEGMENTS, turn),
        design=DESIGN,
        note="",
        radius=101.0,
    )
    assert objections_to(check_corner_turns_a_quarter, part)


def test_a_profile_with_a_pocket_walled_into_it_is_caught():
    """Air the slicer would wall in for no benefit. The shipped profile has
    none, so one is put there."""
    pocketed = profile(DESIGN) - rect(-10.0, 0.5, -9.0, 1.5)
    assert objections_to(check_profile_is_solid, pocketed)


def test_a_corner_section_comes_home_to_the_profiles_frame():
    """Otherwise every corner would be compared against the straight while
    still displaced by its own radius, and none of them would match."""
    part = CornerBracket(
        name="probe", solid=corner(DESIGN, 101.0), design=DESIGN, note="", radius=101.0
    )
    assert corner_section(part).bounds() == pytest.approx(
        profile(DESIGN).bounds(), abs=1e-6
    )
