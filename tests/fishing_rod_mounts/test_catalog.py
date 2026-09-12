"""What the catalog ships, and what it calls the files."""

import pytest

from printing3d.fishing_rod_mounts.catalog import (
    RODS,
    WEDGE,
    MountStyle,
    Rod,
    parts,
    standoff_line,
)


@pytest.fixture
def demo_rod():
    return Rod("demo", butt_dia=20.0, tip_dia=6.0)


def test_a_rod_yields_one_butt_and_one_tip_mount(demo_rod):
    assert [part.kind for part in parts([demo_rod])] == ["butt", "tip"]


def test_the_filename_records_rod_end_and_diameter(demo_rod):
    assert [part.filename for part in parts([demo_rod])] == [
        "demo-butt-20.00mm-v3.stl",
        "demo-tip-6.00mm-v3.stl",
    ]


@pytest.mark.parametrize("kind", ["butt", "tip"])
def test_each_mount_is_built_for_the_diameter_at_its_own_end(demo_rod, kind):
    assert demo_rod.diameter_at(kind) == {"butt": 20.0, "tip": 6.0}[kind]


def test_a_style_takes_its_diameter_from_the_rod(demo_rod):
    style = MountStyle(kind="tip", support=WEDGE, lip_rise=0.0)
    spec = style.spec_for(demo_rod)
    assert spec.rod_dia == 6.0
    assert spec.support is WEDGE


def test_the_standoff_line_reports_both_derived_depths():
    butt, _tip = parts([RODS[0]])
    line = standoff_line(butt)
    assert "butt" in line
    assert "4.62 mm" in line  # material between wall and grip
    assert "35.38 mm" in line  # projection from the wall
