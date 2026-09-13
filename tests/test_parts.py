"""Where parts come from and where their STLs land."""

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
