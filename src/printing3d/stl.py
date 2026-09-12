"""Binary STL output, shared by every project in this repo.

Written by hand rather than via a mesh library so the generator has exactly one
dependency. The format is fixed: an 80-byte header, a triangle count, then 50
bytes per triangle (a normal, three vertices, and an unused attribute word).

Output is deterministic: the same solid and label always produce the same
bytes. Projects rely on that to hash-lock their shipped STLs.
"""

import math
import struct

HEADER_BYTES = 80
ATTRIBUTE_BYTE_COUNT = 0


def write_stl(solid, path, label):
    """Write `solid` to `path` as binary STL, labelled in the file header."""
    mesh = solid.to_mesh()
    vertices = mesh.vert_properties[:, :3]
    triangles = mesh.tri_verts
    with open(path, "wb") as stl:
        stl.write(_header(label))
        stl.write(struct.pack("<I", len(triangles)))
        for a, b, c in triangles:
            _write_triangle(stl, vertices[a], vertices[b], vertices[c])


def triangle_count(solid):
    return len(solid.to_mesh().tri_verts)


def _header(label):
    return label.encode()[: HEADER_BYTES - 1].ljust(HEADER_BYTES, b"\0")


def _write_triangle(stl, p0, p1, p2):
    stl.write(struct.pack("<3f", *_unit_normal(p0, p1, p2)))
    for point in (p0, p1, p2):
        stl.write(struct.pack("<3f", *point))
    stl.write(struct.pack("<H", ATTRIBUTE_BYTE_COUNT))


def _unit_normal(p0, p1, p2):
    ux, uy, uz = p1 - p0
    vx, vy, vz = p2 - p0
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return nx / length, ny / length, nz / length
