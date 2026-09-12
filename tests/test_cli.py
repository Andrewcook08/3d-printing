"""The `build` and `verify` commands."""

import pytest

from printing3d.cli import PROJECTS, build, verify


@pytest.fixture(autouse=True)
def _isolated_output(monkeypatch, tmp_path):
    """Never let the CLI tests write over the committed STLs."""
    monkeypatch.setenv("PRINTING3D_OUTPUT", str(tmp_path))


def test_every_registered_project_can_be_looked_up():
    for name, load in PROJECTS.items():
        assert load().name == name


def test_building_with_no_arguments_builds_every_project(tmp_path):
    assert build([]) == 0
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(PROJECTS)


def test_building_one_project_by_name(tmp_path):
    assert build(["fishing-rod-mounts"]) == 0
    assert [p.name for p in tmp_path.iterdir()] == ["fishing-rod-mounts"]


def test_the_build_reports_where_the_files_went(capsys, tmp_path):
    build(["fishing-rod-mounts"])
    assert str(tmp_path / "fishing-rod-mounts") in capsys.readouterr().out


def test_verifying_runs_every_projects_checks(capsys):
    assert verify([]) == 0
    assert "ALL CHECKS PASSED" in capsys.readouterr().out


def test_an_unknown_project_is_rejected_with_the_valid_names(capsys):
    with pytest.raises(SystemExit) as exit_info:
        build(["no-such-project"])
    assert exit_info.value.code == 2
    assert "fishing-rod-mounts" in capsys.readouterr().err
