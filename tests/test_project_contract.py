"""The contract every 3D-printing project must satisfy.

Parameterised over every declared project, so a new project is covered by
existing rather than by copying tests. Nothing here knows what any project
makes — only what all of them must guarantee.

A project's own tests assert what is true of *that* project's shape. These
assert what is true of *every* project.
"""

import pytest

from printing3d.parts import output_dir
from printing3d.registry import Project, discover
from printing3d.stl import write_stl
from tests.support import locked_hashes, sha256_of

PROJECTS = discover()


@pytest.fixture(params=list(PROJECTS.values()), ids=list(PROJECTS))
def project(request) -> Project:
    return request.param


@pytest.fixture
def shipped(project):
    return list(project.parts())


@pytest.fixture
def locked(project):
    return locked_hashes(project.lock)


def test_at_least_one_project_is_declared():
    """Guards every other test here from passing vacuously."""
    assert PROJECTS


def test_the_project_declares_everything_the_repo_needs(project):
    assert project.name and project.summary
    assert callable(project.parts) and callable(project.build)
    assert callable(project.verify), "every project must ship physical checks"
    assert project.lock.is_file(), f"{project.lock} is missing"


def test_the_project_ships_at_least_one_part(shipped):
    assert shipped


def test_part_names_are_unique(shipped):
    names = [part.name for part in shipped]
    assert len(names) == len(set(names))


def test_every_part_is_a_single_watertight_body(shipped):
    unsound = [part.name for part in shipped if not part.is_sound]
    assert not unsound, f"not printable: {unsound}"


def test_every_locked_file_is_still_produced(shipped, locked):
    assert {part.filename for part in shipped} == set(locked)


def test_rebuilt_bytes_match_the_lock(shipped, locked, tmp_path):
    for part in shipped:
        path = tmp_path / part.filename
        write_stl(part.solid, path, part.name)
        assert sha256_of(path) == locked[part.filename], (
            f"{part.filename} is no longer byte-identical"
        )


def test_the_committed_output_matches_the_lock(project, locked):
    """The files sitting in the output directory are the ones the lock
    describes, so you can print from a clone without regenerating."""
    for filename, digest in locked.items():
        path = output_dir(project.name) / filename
        assert path.exists(), f"{path} is missing; run `build`"
        assert sha256_of(path) == digest


def test_building_writes_exactly_the_declared_parts(
    project, shipped, monkeypatch, tmp_path
):
    monkeypatch.setenv("PRINTING3D_OUTPUT", str(tmp_path))
    assert project.build()
    written = {path.name for path in (tmp_path / project.name).iterdir()}
    assert written == {part.filename for part in shipped}


def test_verification_passes(project, monkeypatch, tmp_path):
    monkeypatch.setenv("PRINTING3D_OUTPUT", str(tmp_path))
    assert project.verify()
