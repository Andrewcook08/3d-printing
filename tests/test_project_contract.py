"""The contract every 3D-printing project must satisfy.

Parameterised over every declared project, so a new project is covered by
existing rather than by copying tests. Nothing here knows what any project
makes — only what all of them must guarantee.

A project's own tests assert what is true of *that* project's shape. These
assert what is true of *every* project.
"""

import tomllib
from pathlib import Path

import pytest

import printing3d
from printing3d import config
from printing3d.locks import measurements_from
from printing3d.parts import existing_stls, output_dir
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


def test_every_package_holding_a_config_is_a_discovered_project():
    """A project that stops declaring itself does not fail -- it vanishes.

    Every test here is parameterised over what discovery found, so a project
    that drops out takes its own coverage with it: its lock goes unchecked, its
    output unverified, its geometry unbuilt, and the suite still passes with
    fewer tests than before. Asserting the set is non-empty does not catch that;
    asserting it is complete does.
    """
    kit = Path(printing3d.__file__).parent
    configured = {path.parent.name for path in kit.glob("*/parts.toml")}
    discovered = {project.config.parent.name for project in PROJECTS.values()}
    assert discovered == configured, (
        f"packages holding a config but not discovered: {configured - discovered}"
    )


def test_the_project_declares_everything_the_repo_needs(project):
    assert project.name and project.summary
    assert callable(project.parts) and callable(project.build)
    assert callable(project.verify), "every project must ship physical checks"
    assert project.lock.is_file(), f"{project.lock} is missing"
    assert project.measured.is_file(), (
        f"{project.measured} is missing; a project pins what its checks "
        f"measured as well as what its parts weigh -- run `relock`"
    )
    assert project.config.is_file(), (
        f"{project.config} is missing; a project's measured numbers live in a "
        f"config file, not in its code"
    )


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


def test_the_checks_still_measure_what_they_measured(project):
    """The byte lock cannot see this.

    A shared helper can change what a check *measures* without moving a single
    vertex -- a tolerance widened, a face merged differently -- and every other
    gate passes. This is the one that notices, so it pins the numbers rather
    than the verdicts: a check still passing is not the same claim as a check
    still reading 15.000 mm.
    """
    _, measured = measurements_from(project.verify)
    assert measured == project.measured.read_text(), (
        f"{project.measured.name} no longer matches what {project.name} "
        f"measures; if the change was intended, run `relock`"
    )


def test_the_committed_output_matches_the_lock(project, locked):
    """The files sitting in the output directory are the ones the lock
    describes, so you can print from a clone without regenerating."""
    for filename, digest in locked.items():
        path = output_dir(project.name) / filename
        assert path.exists(), f"{path} is missing; run `build`"
        assert sha256_of(path) == digest


def test_the_project_actually_reads_the_config_it_declares(project, monkeypatch):
    """Shipping a config file and ignoring it would pass every other check here.

    A project could declare a parts.toml, hardcode every dimension in its code,
    and be discovered, built, locked and verified exactly as if it had not --
    which is the one thing the config framework is supposed to prevent. So the
    files a project opens while producing its parts are recorded, and the one
    it points at has to be among them.

    Patched at the single place every read funnels through, so that it catches
    a project however it chose to import the reader.
    """
    opened = []
    original = config._parsed

    def recording(path):
        opened.append(Path(path))
        return original(path)

    monkeypatch.setattr(config, "_parsed", recording)
    list(project.parts())
    assert project.config in opened, (
        f"{project.name} never opened {project.config}; its numbers are somewhere else"
    )


def test_the_declared_config_has_something_in_it(project):
    """An empty file would satisfy the check above without saying anything."""
    with project.config.open("rb") as handle:
        assert tomllib.load(handle), f"{project.config} is empty"


def test_the_output_holds_nothing_the_project_no_longer_declares(project, shipped):
    """A part dropped from config is archived by the next build. An STL still
    sitting in output without an entry behind it means that never happened,
    and it would be printed from in good faith."""
    on_disk = {path.name for path in existing_stls(project.name)}
    declared = {part.filename for part in shipped}
    assert on_disk == declared, (
        f"orphaned: {sorted(on_disk - declared)}; run `build` to archive them"
    )


def test_building_writes_exactly_the_declared_parts(
    project, shipped, monkeypatch, tmp_path
):
    monkeypatch.setenv("PRINTING3D_OUTPUT", str(tmp_path))
    assert project.build()
    written = {path.name for path in (tmp_path / project.name).iterdir()}
    assert written == {part.filename for part in shipped}


def test_verification_measures_every_part_it_was_given(
    project, shipped, capsys, monkeypatch, tmp_path
):
    """Returning True is not the same as having looked.

    A project whose checks iterate an empty list reports success, and the only
    other assertion about verification is that it returned True -- so the gate
    before printing can be entirely disconnected and nothing notices.

    Every part has to appear in what was reported. Counting checks alone is not
    enough: a project with more straights than corners passes a count while
    never having looked at a corner.
    """
    monkeypatch.setenv("PRINTING3D_OUTPUT", str(tmp_path))
    assert project.verify()
    reported = capsys.readouterr().out
    unmeasured = [part.name for part in shipped if part.name not in reported]
    assert not unmeasured, f"{project.name} never measured {unmeasured}"
    assert reported.count("[PASS]") >= len(shipped), (
        f"{project.name} ran {reported.count('[PASS]')} checks for {len(shipped)} parts"
    )


def test_verification_passes(project, monkeypatch, tmp_path):
    monkeypatch.setenv("PRINTING3D_OUTPUT", str(tmp_path))
    assert project.verify()
