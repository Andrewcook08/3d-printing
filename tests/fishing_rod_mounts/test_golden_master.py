"""The golden master: the shipped STLs must stay byte-for-byte identical.

LOCKED.txt records the sha256 of both files this project has printed. The
generator is deterministic, so any change that moves a single vertex fails
here. If you are changing the shape on purpose, re-lock with:

    shasum -a 256 output/fishing-rod-mounts/*.stl \\
        > src/printing3d/fishing_rod_mounts/LOCKED.txt
"""

import pytest

from printing3d.fishing_rod_mounts.catalog import LOCKED, PROJECT, parts
from printing3d.parts import output_dir
from printing3d.stl import write_stl
from tests.support import locked_hashes, sha256_of


@pytest.fixture(scope="module")
def shipped():
    return list(parts())


@pytest.fixture(scope="module")
def expected():
    return locked_hashes(LOCKED)


def test_every_locked_file_is_still_produced(shipped, expected):
    assert {part.filename for part in shipped} == set(expected)


def test_stl_bytes_match_the_locked_hashes(shipped, expected, tmp_path):
    for part in shipped:
        path = tmp_path / part.filename
        write_stl(part.solid, path, part.name)
        assert sha256_of(path) == expected[part.filename], (
            f"{part.filename} is no longer byte-identical"
        )


def test_the_committed_output_matches_the_lock(expected):
    """The STLs sitting in output/ are the ones LOCKED.txt describes, so you
    can print straight from the repo without regenerating first."""
    for filename, digest in expected.items():
        path = output_dir(PROJECT) / filename
        assert path.exists(), f"{path} is missing; run `uv run build`"
        assert sha256_of(path) == digest


def test_both_mounts_are_single_watertight_bodies(shipped):
    assert all(part.is_sound for part in shipped)
