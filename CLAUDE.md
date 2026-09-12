# CLAUDE.md

Guidance for AI assistants working in this repo. Conventions follow the
[Modern Python Project Setup Guide](https://pydevtools.com/handbook/explanation/modern-python-project-setup-guide-for-ai-assistants/).

## What this repo is

Parametric 3D-printable parts, written as Python and exported as STL. Each
project is a subpackage of `printing3d`; every project writes its STLs into
`output/<project-name>/`.

Geometry is built with [manifold3d](https://github.com/elalish/manifold) — a
mesh boolean library, not a parametric CAD kernel. Parts are typically a 2D
`CrossSection` extruded into a `Manifold`, then drilled with boolean
subtraction.

## Layout

```
pyproject.toml              one package, one lockfile, one dependency set
output/<project>/           generated STLs, committed
src/printing3d/
  stl.py                    binary STL writer (shared)
  parts.py                  what a Part is, where its file lands (shared)
  cli.py                    `build` / `verify` commands + project registry
  <project>/                one folder per 3D-printing project
tests/
  test_*.py                 tests for the shared modules
  <project>/test_*.py       tests for one project
```

## Commands

Always use `uv run`; never call `python`, `pip`, or `pytest` directly, and
never activate the venv by hand.

```sh
uv run build                     # generate every project's STLs
uv run build fishing-rod-mounts  # just one
uv run verify                    # geometric checks before printing
uv run pytest                    # tests
uv run ruff check --fix .        # lint
uv run ruff format .             # format
uv run ty check                  # type check
uv add <package>                 # add a runtime dependency
uv add --dev <package>           # add a dev dependency
uv sync                          # sync the environment
```

Run `ruff check`, `ruff format`, `ty check`, and `pytest` before claiming work
is done. CI runs all four.

Git hooks (`uvx pre-commit install`, already set up in this working copy) run
ruff and the test suite on every commit, so a commit that changes an STL's
bytes is blocked before it lands. `ty check` is CI-only — it is the one check
the hooks do not cover.

All four run again in CI, where they gate every pull request. See
[Branching and pull requests](#branching-and-pull-requests) below: `main`
takes no direct pushes.

## Branching and pull requests

**`main` is protected and rejects direct pushes, including from the repo
owner.** Every change goes through a branch and a PR whose CI has passed.

Before making any edit, check you are not on `main`:

```sh
git branch --show-current
```

If you are, create a branch first. Name it `<type>/<short-description>` in
kebab-case:

| Type | For |
|---|---|
| `part/` | A new 3D-printing project |
| `feat/` | New capability in an existing project or the shared code |
| `fix/` | Correcting something that is wrong |
| `refactor/` | Restructuring with no change to any STL |
| `docs/` | Documentation only |
| `test/` | Tests only |
| `chore/` | Dependencies, tooling, CI |

A `refactor/` branch must leave every `LOCKED.txt` check passing. If a refactor
changes an STL, it was not a refactor — either fix it or rename the branch.

The full cycle:

```sh
git switch -c fix/tip-mount-lip
# ...work...
git commit                          # pre-commit hooks run here
git push -u origin fix/tip-mount-lip
gh pr create --fill
gh pr merge --squash --auto         # merges once CI is green
```

Notes:

- **No reviewer approval is required.** You can merge your own PR once `test`
  passes. Do not ask for a reviewer.
- The branch must be up to date with `main` before merging; if `main` has moved,
  rebase or merge it in and push again.
- Branches are deleted automatically on merge. Afterwards, `git switch main &&
  git pull`.
- Never use `--no-verify` or force-push to `main`; both are blocked server-side
  anyway.

## Dependency management

`pyproject.toml` declares constraints; `uv.lock` pins the exact versions
installed. Both are generated — never hand-edit either.

```sh
uv add <package>                    # runtime dependency
uv add --dev <package>              # dev dependency
uv remove <package>
uv lock --upgrade                   # upgrade everything
uv lock --upgrade-package <package> # upgrade one
uv tree --outdated --depth 1        # what newer versions exist
```

Ask before adding a runtime dependency; this repo deliberately has one.

### Why upgrades need their own check

CI runs `uv sync --locked`, so it installs exactly what `uv.lock` pins. That
hermeticity is what makes the STLs reproducible — and it means CI can never
notice that a newer release exists. Two things cover the gap:

- **Dependabot** opens PRs. They go through the normal gate, so a bump that
  changes an STL fails the golden master and cannot merge.
- **The upgrade canary** (`.github/workflows/upgrade-canary.yml`) runs weekly,
  resolves the newest versions the constraints allow, and runs every check. It
  commits nothing. It exists because Dependabot may open no PR at all when a
  new release already satisfies a `>=` constraint — a silent gap.

Neither names a package. Both derive the list from `pyproject.toml`, so a new
dependency is covered the moment it is added. To probe one package on demand:
`gh workflow run "Upgrade canary" -f packages=<package>`.

### Reading a red canary

A red canary is a decision, not a build to fix. The failing **step** names the
category:

| Failing step | Means |
|---|---|
| `Tests`, golden master only (profile tests pass) | A geometry library changed how it meshes. Your geometry is untouched. |
| `Tests`, profile *and* golden master | The geometry itself moved. Investigate before accepting anything. |
| `Format` | A formatter release restyles the code. Reformat in its own `chore/` PR. |
| `Lint` / `Types` | A newer linter or type checker sees something new. |

Then choose deliberately, in a PR:

- **Accept** — upgrade the lock, re-lock any changed STL, and say in the PR
  that the shape changed and why that is acceptable.
- **Hold** — tighten the constraint in `pyproject.toml` with a comment giving
  the reason.

Never let it drift unnoticed, and never re-lock an STL just to get to green.

## Adding a new 3D-printing project

1. `mkdir src/printing3d/<new_project>` with an `__init__.py`.
2. Write the geometry. Put shape construction in its own module (`geometry.py`)
   and the catalog of what actually gets printed in another (`catalog.py`).
   The catalog yields `printing3d.parts.Part` objects.
3. Give it a `build_all()` that calls `printing3d.parts.build_project(...)`.
4. Register it in `PROJECTS` in `src/printing3d/cli.py` — one entry.
5. Add `tests/<new_project>/`.
6. Write a `README.md` in the project folder covering print settings and
   assembly. Reference images and source meshes go in `<project>/reference/`.

The package name must be a legal Python identifier (`fishing_rod_mounts`),
while the project's public name — its output folder and CLI argument — is
kebab-case (`fishing-rod-mounts`). Keep both in sync via the `PROJECT`
constant in the project's catalog module.

## Rules specific to generated geometry

**STL output is deterministic and hash-locked.** Each project keeps a
`LOCKED.txt` of `shasum -a 256` digests for the STLs it has printed. The tests
rebuild the parts and compare. This is the safety net for every refactor — it
has already caught nothing-should-change claims and survived a manifold3d
version bump unchanged.

- **Never edit `LOCKED.txt` to make a test pass.** A golden-master failure means
  the exported shape changed. If that was intentional, say so explicitly, then
  re-lock with `shasum -a 256 output/<project>/*.stl > src/printing3d/<pkg>/LOCKED.txt`.
- **When refactoring geometry, preserve the exact sequence of boolean
  operations.** Union is not associative in the output mesh: `(a + b) + c` can
  tessellate differently from `a + (b + c)`, changing the STL bytes even though
  the solid is geometrically identical. This is why supports return a *list* of
  pieces to be unioned in order rather than one combined shape.
- **Preserve exact float expressions.** Reordering `a - b - c` into `a - (b + c)`
  can shift the last bit and move a vertex.
- Part names are written into the STL's 80-byte header, so renaming a part
  changes its hash.

## Testing

Tests are behavioral and named as sentences:
`test_the_countersink_opens_out_on_the_front_face`. Three layers, in order of
how specifically they localise a failure:

1. **Unit tests** on derived values — assert the *property*, not a magic
   number. The wedge test checks the line is genuinely tangent to the crescent,
   rather than pinning `32.60°`.
2. **Profile characterization** — vertex-count, area, and a vertex digest for
   each shipped 2D profile, so a geometry change names the profile that moved.
3. **Golden master** — the STL bytes.

`uv run verify` is a separate tool from the test suite: it measures the built
solids for physical soundness (does the rod lift out, is it trapped sideways,
are the bores countersunk on the right face) and prints the measurements. Run
it before printing.

## Code style

- Line length 88, double quotes, enforced by `ruff format`. Don't hand-align
  trailing comments in columns — the formatter strips the alignment. Multi-line
  explanations go *above* the definition, not trailing after it.
- Comments explain *why*, particularly the physical constraint behind a
  dimension. The existing geometry comments are a good model: they record the
  reasoning (`screws must sit ABOVE the rod: the load always tries to peel the
  TOP off the wall`), not the arithmetic.
- Prefer named constants over literals, and derive dimensions from each other
  rather than restating them. If a value is forced by geometry, compute it and
  say so — don't hardcode the result.

## Don't

- Don't commit to `main`, or open a PR without checking `git branch --show-current` first.
- Don't add a dependency without asking; this repo deliberately has one.
- Don't commit `.venv/`, caches, or slicer project files.
- Don't move or rename generated STLs by hand — `uv run build` owns `output/`.
