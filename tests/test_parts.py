"""Where parts come from and where their STLs land."""

import pytest
from manifold3d import Manifold

from printing3d.parts import (
    DEFAULT_OUTPUT_DIR,
    OUTPUT_DIR_ENV,
    Part,
    archive_dir,
    build_project,
    output_dir,
    repo_root,
)


def a_part(name="demo-part"):
    return Part(name=name, solid=Manifold.cube((10.0, 10.0, 10.0), False))


def test_the_filename_is_the_part_name_with_an_stl_suffix():
    assert a_part("widget-v2").filename == "widget-v2.stl"


def test_a_cube_is_a_single_sound_body():
    assert a_part().is_sound


def test_the_summary_reports_size_volume_and_soundness():
    summary = a_part().summary()
    assert "demo-part.stl" in summary
    assert "10.0 x  10.0 x  10.0 mm" in summary
    assert "watertight" in summary


def test_the_repo_root_is_the_directory_holding_pyproject_toml():
    assert (repo_root() / "pyproject.toml").is_file()


def test_each_project_writes_under_the_shared_output_directory():
    assert output_dir("widgets") == repo_root() / DEFAULT_OUTPUT_DIR / "widgets"


def test_the_output_root_can_be_redirected(monkeypatch, tmp_path):
    monkeypatch.setenv(OUTPUT_DIR_ENV, str(tmp_path))
    assert output_dir("widgets") == tmp_path / "widgets"


def test_building_a_project_writes_one_stl_per_part(monkeypatch, tmp_path):
    monkeypatch.setenv(OUTPUT_DIR_ENV, str(tmp_path))
    assert build_project("widgets", [a_part("one"), a_part("two")])
    written = sorted(p.name for p in (tmp_path / "widgets").iterdir())
    assert written == ["one.stl", "two.stl"]


def test_building_creates_the_output_directory_if_it_is_missing(monkeypatch, tmp_path):
    monkeypatch.setenv(OUTPUT_DIR_ENV, str(tmp_path / "nested" / "deeper"))
    assert build_project("widgets", [a_part()])
    assert (tmp_path / "nested" / "deeper" / "widgets" / "demo-part.stl").exists()


def test_a_project_can_announce_its_own_line_per_part(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv(OUTPUT_DIR_ENV, str(tmp_path))
    build_project("widgets", [a_part()], announce=lambda part: f"-> {part.name}")
    assert "-> demo-part" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Retiring a part it no longer declares
# ---------------------------------------------------------------------------


def test_the_archive_sits_beside_the_projects_under_the_same_root():
    assert (
        archive_dir("widgets")
        == repo_root() / DEFAULT_OUTPUT_DIR / "archive" / "widgets"
    )


def test_redirecting_the_output_redirects_the_archive_with_it(monkeypatch, tmp_path):
    """Or a test writing somewhere temporary would litter the real archive."""
    monkeypatch.setenv(OUTPUT_DIR_ENV, str(tmp_path))
    assert archive_dir("widgets") == tmp_path / "archive" / "widgets"


def test_a_part_no_longer_declared_is_moved_to_the_archive(monkeypatch, tmp_path):
    monkeypatch.setenv(OUTPUT_DIR_ENV, str(tmp_path))
    build_project("widgets", [a_part("kept"), a_part("retired")])

    build_project("widgets", [a_part("kept")])

    assert [path.name for path in output_dir("widgets").glob("*.stl")] == ["kept.stl"]
    assert (archive_dir("widgets") / "retired.stl").is_file()


def test_the_archived_bytes_are_the_ones_that_were_built(monkeypatch, tmp_path):
    """Archiving moves the file rather than regenerating it, so what lands
    there is what was last printed from."""
    monkeypatch.setenv(OUTPUT_DIR_ENV, str(tmp_path))
    build_project("widgets", [a_part("retired")])
    was = (output_dir("widgets") / "retired.stl").read_bytes()

    build_project("widgets", [a_part("kept")])

    assert (archive_dir("widgets") / "retired.stl").read_bytes() == was


def test_nothing_is_archived_when_every_part_is_still_declared(monkeypatch, tmp_path):
    monkeypatch.setenv(OUTPUT_DIR_ENV, str(tmp_path))
    build_project("widgets", [a_part("kept")])
    build_project("widgets", [a_part("kept")])
    assert not archive_dir("widgets").exists()


def test_the_archive_is_announced_so_a_move_is_never_silent(
    monkeypatch, tmp_path, capsys
):
    monkeypatch.setenv(OUTPUT_DIR_ENV, str(tmp_path))
    build_project("widgets", [a_part("retired")])
    capsys.readouterr()

    build_project("widgets", [a_part("kept")])

    assert "archived retired.stl" in capsys.readouterr().out


def test_two_parts_with_one_name_is_refused_rather_than_written_twice(
    monkeypatch, tmp_path
):
    """The second would overwrite the first, leaving one file where the project
    declared two and no sign that anything was lost."""
    monkeypatch.setenv(OUTPUT_DIR_ENV, str(tmp_path))
    with pytest.raises(ValueError, match="more than once"):
        build_project("widgets", [a_part("twin"), a_part("twin")])


# ---------------------------------------------------------------------------
# A solid that is not printable
# ---------------------------------------------------------------------------


def a_broken_part(name="broken-part"):
    """Two cubes with a gap between them: watertight, but not one body.

    A mount whose arm has come adrift from its plate looks exactly like this,
    and a slicer will happily print the pieces separately.
    """
    near = Manifold.cube((10.0, 10.0, 10.0), False)
    far = Manifold.cube((10.0, 10.0, 10.0), False).translate((100.0, 0.0, 0.0))
    return Part(name=name, solid=near + far)


def test_two_disjoint_bodies_are_not_a_printable_part():
    assert not a_broken_part().is_sound


def test_the_summary_says_so_rather_than_calling_it_watertight():
    assert "CHECK GEOMETRY" in a_broken_part().summary()


def test_building_an_unsound_part_reports_failure(monkeypatch, tmp_path):
    """The file is still written -- you may want to look at it -- but the build
    says it is not printable, which is what the command turns into an exit code."""
    monkeypatch.setenv(OUTPUT_DIR_ENV, str(tmp_path))
    assert build_project("widgets", [a_broken_part()]) is False
    assert (output_dir("widgets") / "broken-part.stl").is_file()


def test_one_unsound_part_condemns_the_whole_build(monkeypatch, tmp_path):
    monkeypatch.setenv(OUTPUT_DIR_ENV, str(tmp_path))
    assert build_project("widgets", [a_part("fine"), a_broken_part()]) is False


def a_bigger_part(name="demo-part"):
    """The same name, a different shape -- a part brought back resized."""
    return Part(name=name, solid=Manifold.cube((40.0, 40.0, 40.0), False))


def test_retiring_a_part_twice_does_not_destroy_its_earlier_shape(
    monkeypatch, tmp_path
):
    """Retire a part, bring it back at a different size, retire it again. The
    first shape is the one someone would go to the archive for."""
    monkeypatch.setenv(OUTPUT_DIR_ENV, str(tmp_path))
    build_project("widgets", [a_part("twice")])
    build_project("widgets", [])
    was = (archive_dir("widgets") / "twice.stl").read_bytes()

    build_project("widgets", [a_bigger_part("twice")])
    build_project("widgets", [])

    archived = {path.read_bytes() for path in archive_dir("widgets").glob("*.stl")}
    assert was in archived, "the earlier shape was overwritten"
    assert len(archived) == 2


def test_retiring_the_same_shape_twice_keeps_one_copy(monkeypatch, tmp_path):
    """Nothing is lost by not keeping a second identical file."""
    monkeypatch.setenv(OUTPUT_DIR_ENV, str(tmp_path))
    for _ in range(2):
        build_project("widgets", [a_part("same")])
        build_project("widgets", [])
    assert len(list(archive_dir("widgets").glob("*.stl"))) == 1
