"""What the catalog ships, and what it calls the files."""

from dataclasses import replace

import pytest

from printing3d.fishing_rod_mounts.catalog import Rod, catalogue, parts, standoff_line
from printing3d.fishing_rod_mounts.geometry import WEDGE, support_named


@pytest.fixture(scope="module")
def shipped():
    return catalogue()


@pytest.fixture
def demo(shipped):
    """The shipped design, asked to hold a different rod."""
    return replace(
        shipped, rod=[Rod(name="demo", butt_diameter=20.0, tip_diameter=6.0)]
    )


def test_a_rod_yields_one_butt_and_one_tip_mount(demo):
    assert [part.kind for part in parts(demo)] == ["butt", "tip"]


def test_the_filename_records_rod_end_and_diameter(demo):
    assert [part.filename for part in parts(demo)] == [
        "demo-butt-20.00mm-v3.stl",
        "demo-tip-6.00mm-v3.stl",
    ]


def test_each_mount_is_built_for_the_diameter_at_its_own_end(demo):
    assert [part.spec.rod_dia for part in parts(demo)] == [20.0, 6.0]


def test_a_rod_reports_the_diameter_at_each_end():
    rod = Rod(name="demo", butt_diameter=20.0, tip_diameter=6.0)
    assert (rod.diameter_at("butt"), rod.diameter_at("tip")) == (20.0, 6.0)


def test_a_mount_kind_the_rod_was_not_measured_at_is_refused():
    """A config file naming a third end would otherwise build something the
    rod was never measured for."""
    rod = Rod(name="demo", butt_diameter=20.0, tip_diameter=6.0)
    with pytest.raises(ValueError, match="middle"):
        rod.diameter_at("middle")


def test_a_support_the_code_does_not_have_is_refused_by_name():
    """Config picks a support from what exists; it cannot describe a new one."""
    with pytest.raises(ValueError, match="buttress"):
        support_named("buttress")


def test_a_support_the_code_does_have_is_the_one_it_returns():
    assert support_named("wedge") is WEDGE


def test_the_standoff_line_reports_both_derived_depths(shipped):
    butt, _tip = parts(shipped)
    line = standoff_line(butt)
    assert "butt" in line
    assert "4.62 mm" in line  # material between wall and grip
    assert "35.38 mm" in line  # projection from the wall
