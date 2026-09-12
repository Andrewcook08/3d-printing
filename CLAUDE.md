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
docs/                       how the system behaves, indexed by docs/README.md
.claude/skills/             project skills, invoked by name
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

`pyproject.toml` declares constraints; `uv.lock` pins exact versions. Both are
generated — **never hand-edit either**, and never edit a `LOCKED.txt` to get a
test to pass.

```sh
uv add <package>                    # runtime dependency — ask first
uv add --dev <package>              # dev dependency
uv remove <package>
uv lock --upgrade                   # upgrade everything
uv lock --upgrade-package <package> # upgrade one
uv tree --outdated --depth 1        # what newer versions exist
```

After any dependency change: `uv sync`, then run the gates.

### The cycle

CI installs strictly from the lock, so it cannot see new releases. Two things
watch from outside, and each produces work of a different shape:

**A bot pull request is open.** Rebase it if it is behind or conflicted, then
read the result. Green — merge it. Red — the failing gate names the category;
fix the cause or close the PR with a reason. Never widen a constraint or
re-lock a part just to turn it green.

**The scheduled upgrade check is red.** This one commits nothing, so there is
nothing to merge; it is a decision. Either **accept** (move the lock in a PR,
re-lock anything whose bytes changed, and say in the PR what changed about the
shape and why that is acceptable) or **hold** (tighten the constraint in
`pyproject.toml` with a comment giving the reason). Never let it drift
unnoticed.

Warnings are errors in the test suite, so a dependency's deprecation warning
fails the run. That is signal, not breakage: act on it while the removal is
still in the future.

Full behavior: [docs/automation/dependencies.md](docs/automation/dependencies.md).

## Documentation

**Before any documentation work — writing, updating, restructuring, or
reviewing a doc — use the `maintaining-docs` skill.** It owns the framework;
this file only routes to it, so the rules have exactly one home.

Docs live in `docs/`, indexed by [docs/README.md](docs/README.md). They
describe behavior, never implementation, which is why a refactor that preserves
behavior must not touch them.

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
7. If it introduces behavior the existing docs do not cover, add a doc under
   `docs/` and link it from the index — using the `maintaining-docs` skill.

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
`test_the_countersink_opens_out_on_the_front_face`. Four layers, in order of
how specifically they localise a failure:

1. **Property tests** on derived values — assert the *relationship*, not a
   magic number. The wedge test checks the line is genuinely tangent to the
   crescent, rather than pinning `32.60°`.
2. **Profile characterization** — vertex-count, area, and a vertex digest for
   each shipped 2D profile, so a geometry change names the profile that moved.
3. **Golden master** — the STL bytes, against `LOCKED.txt`.
4. **Command tests** — the installed console scripts run as subprocesses and
   compared against the library. Keep these free of project names: they own
   "the command matches the library", while the golden master owns "the library
   matches the lock".

Warnings are errors (`filterwarnings`), so a dependency's deprecation warning
fails the suite. Don't silence one — act on it.

`uv run verify` is a separate tool from the test suite: it measures the built
solids for physical soundness (does the rod lift out, is it trapped sideways,
are the bores countersunk on the right face) and prints the measurements. Run
it before printing.

Full behavior: [docs/quality/testing.md](docs/quality/testing.md).

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
- Don't touch `docs/` in a refactor that preserves behavior. If a doc needs
  editing, it was coupled to the code — fix the doc, not the refactor.
