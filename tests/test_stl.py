"""The shared binary STL writer."""

import struct

import pytest
from manifold3d import Manifold

from printing3d.stl import HEADER_BYTES, triangle_count, write_stl

TRIANGLE_BYTES = 50
COUNT_BYTES = 4


@pytest.fixture
def solid():
    return Manifold.cube((10.0, 20.0, 30.0), False)


def written(solid, tmp_path, label, filename="part.stl"):
    path = tmp_path / filename
    write_stl(solid, path, label)
    return path.read_bytes()


def test_the_file_layout_matches_the_triangle_count(solid, tmp_path):
    data = written(solid, tmp_path, "demo")
    (count,) = struct.unpack("<I", data[HEADER_BYTES : HEADER_BYTES + COUNT_BYTES])
    assert count == triangle_count(solid)
    assert len(data) == HEADER_BYTES + COUNT_BYTES + count * TRIANGLE_BYTES


def test_the_header_carries_the_part_name(solid, tmp_path):
    data = written(solid, tmp_path, "spinning-85in-tip-5.80mm-v3")
    assert data[:HEADER_BYTES].rstrip(b"\0") == b"spinning-85in-tip-5.80mm-v3"


def test_an_overlong_name_is_truncated_rather_than_overflowing(solid, tmp_path):
    data = written(solid, tmp_path, "x" * 200)
    assert len(data[:HEADER_BYTES]) == HEADER_BYTES
    assert data[HEADER_BYTES - 1] == 0


def test_the_same_solid_always_writes_the_same_bytes(solid, tmp_path):
    """Projects hash-lock their STLs, which only works if output is stable."""
    first = written(solid, tmp_path, "demo", "first.stl")
    second = written(solid, tmp_path, "demo", "second.stl")
    assert first == second
