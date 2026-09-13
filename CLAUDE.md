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
src/printing3d/            the shared kit -- never imports a project
  shapes.py                 2D construction (rect, polygon, fill, rounding)
  probes.py                 measuring built solids and profiles
  checks.py                 the pass/fail runner
  stl.py                    binary STL writer
  parts.py                  what a Part is, where its file lands
  registry.py               the Project contract + discovery
  cli.py                    `build` / `verify`
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
this file only routes to it, so the rules have exactly one home. It also settles
where a given piece of writing belongs — `docs/`, a project README, or a
comment — and that there is no fourth place.

Docs live in `docs/`, indexed by [docs/README.md](docs/README.md). They
describe behavior, never implementation, which is why a refactor that preserves
behavior must not touch them.

## Adding a new 3D-printing project

Projects are **discovered, not registered** — never edit a shared file to add
one. Everything goes in `src/printing3d/<new_project>/`:

1. `__init__.py` declares the project: its name (kebab-case), a one-line
   summary, its lock file, and callables for parts/build/verify. Import the
   heavy modules *inside* those callables, so listing projects stays cheap.
2. `geometry.py` — the shape. Reuse `printing3d.shapes` rather than
   re-implementing 2D construction.
3. `catalog.py` — what actually gets printed, yielding `printing3d.parts.Part`.
4. `verify.py` — physical checks, using `printing3d.checks.CheckRunner` and
   `printing3d.probes`. **Required**: the contract fails a project without them.
5. `LOCKED.txt` — generate it once the shape is settled.
6. `tests/<new_project>/` — only what is specific to this project. The contract
   suite already covers building, locking, soundness and verification.
   Before writing a helper of your own, run the grep in
   [Growing the shared kit](#growing-the-shared-kit).
7. A `README.md` — this project's design document, not only its print sheet:
   what the part solves, what forced each dimension, print settings, assembly.
   Reference images and source meshes in `<project>/reference/`.

The package name must be a legal Python identifier (`fishing_rod_mounts`); the
project's public name is kebab-case (`fishing-rod-mounts`).

Behavior: [docs/build/project-contract.md](docs/build/project-contract.md).

## Growing the shared kit

A helper starts **in the project that needs it**. When a *second* project needs
the same thing, promote it into the kit — a pure move, behavior unchanged, docs
untouched.

- Only **domain-free** utilities are eligible. Anything shaped around what a
  project makes stays with that project; generalising from one example is
  guessing what the second needs.
- **The kit never imports a project.** Enforced by a test, so don't work around
  it — if shared code needs a project's knowledge, it isn't shared code.
- Promoted code must arrive with its own tests.

Don't pre-build abstractions for projects that don't exist yet.

### Finding what already exists

Before writing a helper, check whether one of the projects already has it:

```sh
rg -n "Promotable:" src/printing3d/
```

A domain-free helper carries one line in its docstring saying so, and that grep
is the entire inventory — there is no list to keep in step, because the marker
lives on the thing it describes:

```python
def radial_section(solid, degrees):
    """The cross-section of `solid` at `degrees` about the Z axis.

    Promotable: domain-free measurement, currently only <project>.
    """
```

Mark a helper when you **write** it, not when you promote it. The marker records
the judgement that it carries no project's assumptions — which you are making
right then, and will not remember later.

If two projects end up defining the same helper name, the test suite fails and
names both. That is the promotion trigger firing: move it into the kit, or
rename one if they were never the same thing. Names every project is expected to
define are exempt — those are roles, not duplication.

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
`test_the_countersink_opens_out_on_the_front_face`. Five layers, in order of
how specifically they localise a failure:

1. **Contract tests** (`tests/test_project_contract.py`) — run over every
   discovered project. Never add project-specific assertions here, and never
   copy them into a project: a new project is covered by existing.
2. **Property tests** on derived values — assert the *relationship*, not a
   magic number. The wedge test checks the line is genuinely tangent to the
   crescent, rather than pinning `32.60°`.
3. **Profile characterization** — vertex-count, area, and a vertex digest for
   each shipped 2D profile, so a geometry change names the profile that moved.
4. **Golden master** — the STL bytes, against `LOCKED.txt`. Lives in the
   contract suite, so every project gets it.
5. **Command tests** — the installed console scripts run as subprocesses and
   compared against the library. Keep these free of project names: they own
   "the command matches the library", while the golden master owns "the library
   matches the lock".

`tests/test_architecture.py` enforces that the shared kit never imports a
project, that no helper is defined by two projects at once, and that no project
rewrites a helper the kit already offers.

Warnings are errors (`filterwarnings`), so a dependency's deprecation warning
fails the suite. Don't silence one — act on it.

`uv run verify` is a separate tool from the test suite: it measures the built
solids for physical soundness (does the rod lift out, is it trapped sideways,
are the bores countersunk on the right face) and prints the measurements. Run
it before printing.

Full behavior: [docs/quality/testing.md](docs/quality/testing.md).

## Code style

**Before writing or changing any code, load the `code-craftsmanship:clean-code`
skill.** It owns naming, function size, error handling and test quality; the
rules below are only what is specific to this repo. Reach for its siblings when
the work matches them — `refactoring-patterns` when restructuring existing code,
`software-design-philosophy` when deciding what a module should hide.

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
