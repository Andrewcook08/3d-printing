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
    parts.toml              its measured and chosen numbers -- never its code
    trials.toml             parts being tested; optional, delete to retire them
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
   summary, its config file, its lock file, and callables for parts/build/verify.
   Every one is required. Import the heavy modules *inside* those callables, so
   listing projects stays cheap.
2. `parts.toml` — every number you measured or chose. **Required**: the
   contract fails a project without one, and checks that the project actually
   reads it. Anything derivable from what is already in it is derived in code
   instead; write it down here and the file is refused.

   Read it with `printing3d.config.read`, handing it a frozen dataclass. **That
   dataclass is the schema** — its fields name what the file may contain, its
   annotations say what those must be, its defaults say what may be left out.
   Put the shape's own numbers with the shape in `geometry.py`, and the parts
   being asked for with `catalog.py`.

   Optional extra files are read with `read_if_present`. That is how a project
   keeps parts it is still testing in a `trials.toml` it can delete wholesale,
   which is a pattern rather than something the contract provides.

   Editing this file is the normal way to change a part, and a golden-master
   failure is its normal consequence — re-lock deliberately, as below.
3. `geometry.py` — the shape. Reuse `printing3d.shapes` rather than
   re-implementing 2D construction.
4. `catalog.py` — how a configured entry becomes a `printing3d.parts.Part`.
5. `verify.py` — physical checks, using `printing3d.checks.CheckRunner` and
   `printing3d.probes`. **Required**: the contract fails a project without them.
6. `LOCKED.txt` — generate it once the shape is settled.
7. `tests/<new_project>/` — only what is specific to this project. The contract
   suite already covers building, locking, soundness and verification.
   Before writing a helper of your own, run the grep in
   [Growing the shared kit](#growing-the-shared-kit).
8. A `README.md` — this project's design document, not only its print sheet:
   what the part solves, what forced each dimension, print settings, assembly.
   Reference images and source meshes in `<project>/reference/`.

The package name must be a legal Python identifier (`fishing_rod_mounts`); the
project's public name is kebab-case (`fishing-rod-mounts`).

Behavior: [docs/build/project-contract.md](docs/build/project-contract.md).

## Growing the shared kit

A helper starts **in the project that needs it**. When a *second* project needs
the same thing, it moves into the kit.

**What a promotion may and may not change:**

- **Behaviour: never.** The first project must get the same numbers out
  afterwards, and the hash lock is what proves it rather than your say-so.
- **What it depends on: narrow it freely.** Swapping a domain object for the two
  plain values it was being mined for is the *canonical* promotion, not a
  redesign. A rename is part of it too — a name is the cheapest thing about a
  helper.
- **What a caller must know: never grow it.** An argument that selects between
  behaviours means two functions, not one. A wide shared helper costs every
  project that touches it.

**Decouple first, move second.** If a helper has to stop depending on a
project's types before it can be shared, that is its own behaviour-preserving
commit, justified on its own terms — pure geometry has no business knowing what
a design is, whether it has one caller or ten. Then the move really is pure.
Tangling the two is what makes a promotion unreviewable, because the lock can no
longer tell you which of the changes moved the bytes.

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
def upright_section(solid, degrees=0.0):
    """The cross-section of `solid` on the vertical plane `degrees` about Z.

    Promotable: domain-free measurement, currently only <project>.
    """
```

Mark a helper when you **write** it, not when you promote it. The marker records
the judgement that it carries no project's assumptions — which you are making
right then, and will not remember later.

Because that depends on remembering, it is also checked rather than trusted: the
`finding-promotions` skill enumerates the helpers a change added and classifies
each, and it is one of the reviews run before work is finished. It catches the
two things the test cannot — a domain-free helper nobody marked, and a second
project that wrote the same thing under a different name.

If two projects end up defining the same helper name, the test suite fails and
names both. That is the promotion trigger firing: move it into the kit, or
rename one if they were never the same thing. Names every project is expected to
define are exempt — those are roles, not duplication.

## Where a number lives

**A number you measured or chose goes in `parts.toml`. A number you computed
stays in code.**

That is the existing "derive, never restate" rule with a file attached. A value
the code can work out from what is already configured has no business being
written down again, and writing it down anyway is refused when the file is read
— an unknown key is an error, not a shrug.

Construction details are not parameters. A segment count, an overshoot that
keeps a boolean clean, a throwaway cutting body — none of those are things
anyone tunes a part with, and they stay in code. The test is whether changing
it is a design decision or an implementation one.

Behavior: [docs/build/configuration.md](docs/build/configuration.md).

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
`test_the_countersink_opens_out_on_the_front_face`. The layers, in order of
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

## Review

**Before work is called finished, three subagents review it.** Fresh context is
the point — each is given the skills it needs, this file, and the existing
projects as the house style, and each **reports findings rather than editing**.

**When: once, after the gates already pass** — lint, types, tests, verification,
and the locks. Not before. A reviewer reading a tree with failing tests spends
its findings on what you already know. Launch all three **in parallel**; they are
independent enough, and three sequential waits is only slower.

| Review | Rubric | Looking for |
|---|---|---|
| The code | `code-craftsmanship:clean-code`, plus `software-design-philosophy` and `refactoring-patterns` where the work restructures | Naming, function size, duplication, error handling, tests that cannot fail, anything over-built for the projects that exist |
| The documentation | the `maintaining-docs` skill | Every claim traced to its source, every reference live, the framework followed, the rename test applied to each doc |
| Promotions | the `finding-promotions` skill | A helper that belongs in the shared kit, enumerated rather than remembered |

Each runs only when its precondition is met — and the documentation one is
broader than it looks:

| Review | Runs when | Reads |
|---|---|---|
| The code | the change touched code | the change |
| The documentation | the change touched a doc **or changed behaviour a doc describes** | the change, and any doc describing what moved |
| Promotions | the change added or altered a helper, **or added or reshaped a project** | the whole repo — the second caller may be old code nobody touched |

"Did I edit a doc" is the wrong question. A code change with no doc edit
falsifies docs regularly: make a build construct everything before writing, and
a guarantee about when failures surface goes stale without the doc being opened.

The documentation one is not covered by the documentation tests. Those check
that references resolve; whether a claim is still *true* is a question only a
reader can settle, and the tests have already passed over a wrong measurement, a
contradicted count and a missing project.

**Then judge what comes back.** A reviewer that has not run the code can be
wrong, and has been — including once where the recommended fix would have
shipped a silent dispatch bug. Verify each finding against the code before
acting on it, and say which ones you are rejecting and why.

Three things this catches often enough to expect: a fix that would change a
hash-locked STL; a finding whose repair turns up something more interesting than
the finding did; and a finding already fixed since the reviewer read the tree.

**Each review reads a snapshot, and acting on one makes the others stale.** That
is not hypothetical — it has happened three times in one sitting: a review
reporting assertions already replaced, another noticing a file change underneath
it mid-audit, a third flagging a doc claim a different fix had already made true.
So: act on all three, re-run the gates, and if you substantially reworked an area
another review covered, **re-run that one**. Its verdict was about code that no
longer exists.

## Don't

- Don't commit to `main`, or open a PR without checking `git branch --show-current` first.
- Prefer not to add a dependency, and ask first. The runtime set is
  deliberately small — but it is a preference, not a rule, and the lockfile
  exists so that adding one is a decision rather than a hazard.
- Don't commit `.venv/`, caches, or slicer project files.
- Don't move or rename generated STLs by hand — `uv run build` owns `output/`.
- Don't touch `docs/` in a refactor that preserves behavior. If a doc needs
  editing, it was coupled to the code — fix the doc, not the refactor.
