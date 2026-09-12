# 3d-printing

Parametric 3D-printable parts, written as Python and exported as STL. Geometry
is built with [manifold3d](https://github.com/elalish/manifold); every project
writes its STLs into `output/<project>/`, ready to drop into a slicer.

## Projects

| Project | What it is |
|---|---|
| [`fishing-rod-mounts`](src/printing3d/fishing_rod_mounts/README.md) | Low-profile wall mounts for horizontal fishing rod storage |

## Getting started

You need [uv](https://docs.astral.sh/uv/). Everything else is handled for you:

```sh
uv sync
```

## Generating parts

```sh
uv run build                     # every project
uv run build fishing-rod-mounts  # just one
```

STLs land in `output/<project>/` and are committed, so you can print straight
from the repo without generating anything.

## Before you print

```sh
uv run verify
```

This measures the generated solids — not the parameters they came from — and
reports whether each part is physically sound. Each project defines its own
checks.

## Development

```sh
uv run pytest              # tests
uv run ruff check --fix .  # lint
uv run ruff format .       # format
uv run ty check            # type check
```

In a fresh clone, install the git hooks once:

```sh
uvx pre-commit install
```

They run ruff, a few file-hygiene checks, and the test suite before each
commit. If a hook reformats a file the commit stops and the fix is left
unstaged — `git add` and commit again. Use `git commit --no-verify` to skip
them for a one-off, or `uvx pre-commit uninstall` to remove them.

Every project hash-locks its shipped STLs in a `LOCKED.txt`, and the test suite
rebuilds the parts and compares. A failure there means the exported shape
changed — see [CLAUDE.md](CLAUDE.md) for what to do about it, and for how to
add a new project.
