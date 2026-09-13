"""The `build` and `verify` commands.

Two levels. Most tests call the entry points in-process, which is fast and
covers argument handling through to the written files. A couple run the
*installed* console scripts as real subprocesses, because that wiring is what a
user actually invokes and nothing else exercises it.
"""

import os
import shutil
import subprocess

import pytest

from printing3d.cli import build, verify
from printing3d.registry import discover
from tests.support import sha256_of

PROJECTS = discover()
SOME_PROJECT = sorted(PROJECTS)[0]


@pytest.fixture(autouse=True)
def _isolated_output(monkeypatch, tmp_path):
    """Never let the CLI tests write over the committed STLs."""
    monkeypatch.setenv("PRINTING3D_OUTPUT", str(tmp_path))


def stl_hashes(root):
    """Every STL under `root`, as {path relative to root: sha256}."""
    return {
        str(path.relative_to(root)): sha256_of(path)
        for path in sorted(root.rglob("*.stl"))
    }


def run_installed(name, output_dir):
    """Run an installed console script, writing its STLs to `output_dir`."""
    script = shutil.which(name)
    if script is None:
        pytest.skip(f"console script {name!r} is not installed; run `uv sync`")
    return subprocess.run(
        [script],
        capture_output=True,
        text=True,
        env={**os.environ, "PRINTING3D_OUTPUT": str(output_dir)},
    )


# ---------------------------------------------------------------------------
# In-process
# ---------------------------------------------------------------------------


def test_every_discovered_project_is_keyed_by_its_own_name():
    for name, project in PROJECTS.items():
        assert project.name == name


def test_building_with_no_arguments_builds_every_project(tmp_path):
    assert build([]) == 0
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(PROJECTS)


def test_building_one_project_by_name(tmp_path):
    assert build([SOME_PROJECT]) == 0
    assert [p.name for p in tmp_path.iterdir()] == [SOME_PROJECT]


def test_the_build_reports_where_the_files_went(capsys, tmp_path):
    build([SOME_PROJECT])
    assert str(tmp_path / SOME_PROJECT) in capsys.readouterr().out


def test_verifying_runs_every_projects_checks(capsys):
    assert verify([]) == 0
    reported = capsys.readouterr().out
    for name in PROJECTS:
        assert f"=== {name} ===" in reported


def test_an_unknown_project_is_rejected_with_the_valid_names(capsys):
    with pytest.raises(SystemExit) as exit_info:
        build(["no-such-project"])
    assert exit_info.value.code == 2
    assert SOME_PROJECT in capsys.readouterr().err


# ---------------------------------------------------------------------------
# The installed commands
#
# These own one claim: the shipped command does what the library does. The
# golden master separately owns "the library produces the locked bytes", so the
# two together say the command produces the locked bytes -- without this test
# knowing anything about a lockfile.
# ---------------------------------------------------------------------------


def test_the_installed_command_produces_what_the_library_produces(
    tmp_path, monkeypatch
):
    via_command = tmp_path / "command"
    via_library = tmp_path / "library"

    result = run_installed("build", via_command)
    assert result.returncode == 0, result.stderr

    monkeypatch.setenv("PRINTING3D_OUTPUT", str(via_library))
    assert build([]) == 0

    produced = stl_hashes(via_command)
    assert produced, "the installed command produced no STLs"
    assert produced == stl_hashes(via_library)


def test_the_installed_verify_command_reports_success(tmp_path):
    result = run_installed("verify", tmp_path)
    assert result.returncode == 0, result.stderr


def test_the_build_command_exits_nonzero_when_a_part_is_not_printable(
    monkeypatch, capsys
):
    """The exit code is the only thing an automated caller sees, and nothing
    else exercises the path where a build reports a geometry problem."""
    from printing3d.registry import Project

    broken = Project(
        name="broken",
        summary="a project whose geometry does not hold together",
        parts=lambda: iter([]),
        build=lambda: False,
        verify=lambda: True,
        lock=PROJECTS[SOME_PROJECT].lock,
        config=PROJECTS[SOME_PROJECT].config,
    )
    monkeypatch.setattr("printing3d.cli.discover", lambda: {"broken": broken})

    assert build([]) == 1
    assert "GEOMETRY PROBLEM" in capsys.readouterr().out


def test_the_build_command_exits_zero_when_everything_is_sound(monkeypatch):
    from printing3d.registry import Project

    sound = Project(
        name="sound",
        summary="a project that builds cleanly",
        parts=lambda: iter([]),
        build=lambda: True,
        verify=lambda: True,
        lock=PROJECTS[SOME_PROJECT].lock,
        config=PROJECTS[SOME_PROJECT].config,
    )
    monkeypatch.setattr("printing3d.cli.discover", lambda: {"sound": sound})
    assert build([]) == 0
