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
output/trials/<project>/    parts still being tested, never committed
output/archive/<project>/   parts no longer declared, never committed
src/printing3d/            the shared kit -- never imports a project
  shapes.py                 2D construction (rect, polygon, fill, rounding)
  probes.py                 measuring built solids and profiles
  checks.py                 the pass/fail runner
  config.py                 reading a project's numbers into its own schema
  locks.py                  producing the two records of what a project ships
  stl.py                    binary STL writer
  parts.py                  what a Part is, where its file lands
  registry.py               the Project contract + discovery
  cli.py                    `build` / `verify`
  <project>/                one folder per 3D-printing project
    parts.toml              its measured and chosen numbers -- never its code
    trials.toml             parts being tested; optional, delete to retire them
    LOCKED.txt              the bytes it last shipped
    MEASURED.txt            what its checks read off those bytes
tests/
  test_*.py                 tests for the shared modules
  <project>/test_*.py       tests for one project
docs/                       how the system behaves, indexed by docs/README.md
.claude/skills/             project skills, invoked by name
.claude/agents/             the reviewers, and what each one looks for
```

## Commands

Always use `uv run`; never call `python`, `pip`, or `pytest` directly, and
never activate the venv by hand.

```sh
uv run build                     # generate every project's STLs
uv run build fishing-rod-mounts  # just one
uv run verify                    # geometric checks before printing
uv run relock <project>          # re-pin what a project ships, after a change
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
ruff and the test suite on **every** commit — not only ones touching Python.
That matters: since a project's numbers moved into config, the ordinary way to
change a part is to edit a `.toml` and rebuild, which stages no Python at all.
A commit that changes an STL's bytes is stopped before it lands. `ty check` is
CI-only — it is the one check the hooks do not cover.

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

A `refactor/` branch must leave **both** locks passing — the bytes and the
measurements. A shared-code refactor can leave every byte identical and still
change what the checks read; that is what the second lock is for, and a
refactor that trips it was not a refactor. Either fix it or rename the branch.

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
generated — **never hand-edit either**, and never edit a lock file to get a
test to pass. That goes for `MEASURED.txt` as much as `LOCKED.txt`: it is plain
readable text rather than digests, which makes it the easier one to fake and
the more tempting.

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

**A project may declare no parts while it is being designed.** Everything below
still applies — it is still built, checked and locked — but `parts.toml` may
list nothing while every part is still a trial. That is refused on a pull
request to `main` and nowhere else, so the suite stays runnable through exactly
the work that gets a project something to declare. Behavior:
[docs/build/project-contract.md](docs/build/project-contract.md).

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
   which is a pattern rather than something the contract provides. What those
   entries produce is built and checked like anything else but is written
   outside the committed output and covered by neither lock -- so adding or
   retiring a trial changes one config file and nothing else. Promote a trial
   by moving its entry into `parts.toml`; that is what makes it a part the
   project ships.

   Editing this file is the normal way to change a part, and a golden-master
   failure is its normal consequence — re-lock deliberately, as below.
3. `geometry.py` — the shape. Reuse `printing3d.shapes` rather than
   re-implementing 2D construction.
4. `catalog.py` — how a configured entry becomes a `printing3d.parts.Part`.
5. `verify.py` — physical checks, using `printing3d.checks.CheckRunner` and
   `printing3d.probes`. **Required**: the contract fails a project without them.
6. `LOCKED.txt` and `MEASURED.txt` — `uv run relock <project>` writes both,
   once the shape is settled. The first pins the bytes; the second pins what
   the checks read off them, which is the only thing that notices a shared
   helper quietly measuring differently.
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

A helper starts **in the project that needs it**. There are two ways it reaches
the kit, and most helpers take the first:

- **A second project needs it.** The usual route. The second caller is what
  tells you which parts of a helper's shape were essential and which were
  incidental, and abstracting before you know that is guessing.
- **It is spec-able.** Then it moves immediately, because there is nothing left
  for a second caller to teach you.

### Spec-able: when waiting buys nothing

"Generalising from one example is guessing what the second needs" is the entire
argument for waiting, and it is a good one — for a helper whose shape we chose.
It has no force when we chose nothing.

Meanwhile waiting costs something real. A helper in a project folder is found by
running a procedure; a helper in the kit is found by reading the kit, which is
what you do when starting a project. So the absence causes the duplication the
rule exists to prevent: the next project, not seeing a tangent solver, writes
one.

**Count the discretionary choices.** A helper is a general formula plus some
number of decisions nobody outside this repo made for you: which branch of a
quadratic, which sign, what tolerance, how to order the results, what to return
when there is nothing to return, what happens at the input that divides by zero.

- **Zero → move it now.** There is nothing left for a second caller to settle.
- **One or more → mark it, and name them in the marker.** Those choices are
  precisely what a second caller will turn up wanting different, so writing them
  down is what makes the wait productive instead of merely long.

The count is the whole test. Two conditions guard it:

- **Nothing in its signature is ours** — plain values, or types the kit already
  owns. A project type going in or out means the count was taken too early.
- **Its tests can be written without naming a project.** If a wrong answer is
  only wrong given what some project happens to make, you are not counting the
  choices you think you are.

**The check, and it is falsifiable:** write the helper's docstring with every
word belonging to this repo deleted, then ask **two** questions.

1. Does what is left still specify the function? If you cannot finish the
   sentence, it is not spec-able.
2. Could a stranger reimplement it from what is left and get the same answers,
   bit for bit? If not, the docstring survived by being **vague**, and whatever
   it failed to mention is your count.

The second question is not optional garnish. Without it the check rewards
under-written prose: a docstring that never mentions a sign convention sails
through deletion precisely because it was hiding one.

**The example this rule was first written around fails it.** "There is one
tangent line from a point to a circle" — there are two. The helper takes one
root of a quadratic, and nothing outside this repo says which root. It returns a
slope, which does not exist for a vertical tangent, and it divides by a quantity
that is zero at exactly that input. Three choices, not zero. Its docstring
survives deletion reading "slope of the line from a point tangent to a circle,
from below" — with *from below* standing in the open, unexplained. That is the
count making itself visible.

**Zero is rarer than it sounds**, and that is fine. Most helpers are a formula
plus one or two choices and most will still wait. The day-to-day value of this
rule is the count, not the move: it turns "does this feel promotable" into
something you enumerate, and it tells the next reader exactly what a second
caller would be arriving to settle.

This bar is deliberately higher than **domain-free**, because this is the route
that skips the evidence. A helper can pass the birdhouse test — an unrelated
project could call it today and mean it — and still have a count above zero.
Those wait, and they are what the `Promotable:` marker is for.

Beware of a formula whose *family* is famous. "It is Euclid" points at something
loudly enough to drown out the branch choice sitting inside it, and that is the
one way this route moves code it should not have.

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

- Only **domain-free** utilities are eligible by either route. Anything shaped
  around what a project makes stays with that project.
- **The kit never imports a project.** Enforced by a test, so don't work around
  it — if shared code needs a project's knowledge, it isn't shared code.
- Promoted code must arrive with its own tests.

Don't pre-build abstractions for projects that don't exist yet. Moving a closed
piece of mathematics is not pre-building one: the abstraction already exists,
and the only question is which folder it sits in.

### Changing something already in the kit

Everything above is about getting code *into* the kit. This is the other half,
and it is the dangerous one: a kit helper has every project downstream of it,
and a promotion does not settle the judgement calls inside it — it multiplies
who is affected by them.

A real example, from the helper that measures the straight faces of a profile.
It carries four decisions nobody outside this repo made: a collinearity
threshold, angles folded modulo 180, an ordering, and how a zero-length segment
is treated. One project used to live with those. Every project does now.

So when a project finds one of them wrong, there are three different answers,
and picking the wrong one breaks something silently:

| The situation | The move |
|---|---|
| A caller needs a different **number**, same behaviour | Add a parameter whose default is the value it has now. Existing callers do not change and never learn it happened |
| A caller needs a different **behaviour** | A second function. **Never a flag** — an argument selecting between behaviours makes every caller read a branch it does not use |
| The behaviour is wrong **for everyone**, and parts already shipped were verified with it | A bug fix, and **not yours to make alone** — see below |
| The behaviour is wrong for everyone but **no shipped part was affected** — right on every input produced so far, wrong on one a config change would produce | Fix it, and say in the commit that it is a correctness fix and what it was latently wrong about |

A tolerance is not a flag. The rule that a caller's knowledge may never grow is
about arguments that *select between behaviours*; a number dimensioning a single
behaviour is not one of those, and parameterising it changes nothing for anyone
already calling.

**The move that is always wrong: editing a kit constant because a new project
needed it.** That is the third row taken while you are actually in the first,
and it changes every other project without saying so.

**Wrong for everyone means stop and ask.** Do not correct it and report
afterwards. A behaviour wrong for every project has been wrong in every part
those projects have already printed, and what that means for parts already in
someone's hands is the user's call, not a detail of the fix. Bring the evidence,
say what would change, and wait.

**What the locks settle, and what they do not.** `MEASURED.txt` names any
measurement that moved, which is what makes a real change impossible to miss.
But a clean run is a *necessary* condition, not a sufficient one: it proves
nothing moved on the inputs the existing projects build today, and says nothing
about a third project or about what a config change would produce tomorrow. A
tolerance here can move four orders of magnitude and pin clean, because neither
project has an edge shallow enough to notice.

So green tests end the question of *what already broke*. They do not end the
question of *which row you are in* — if you changed something that already
existed, that is still yours to answer.

The `changing-shared-code` skill walks this as a procedure, including the
promotion and deletion cases. Load it before touching anything under
`src/printing3d/`.

### Finding what already exists

Before writing a helper, check whether one of the projects already has it:

```sh
rg -n "Promotable:" src/printing3d/
```

A domain-free helper **that is waiting for a second caller** carries one line in
its docstring saying so, and that grep is the entire inventory — there is no list to keep in step, because the marker
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

**A spec-able helper is moved, not marked**, and a marker that stays **names the
choices it is waiting on**. The marker means "domain-free, but N of its
decisions are ours" — so say which, or the next reader takes it as ready to go:

```python
    Promotable: domain-free plane geometry, currently only <project>.
    Waiting on one choice nobody outside this repo made: <the choice>.
```

Because that depends on remembering, it is also checked rather than trusted: the
`finding-promotions` skill enumerates the helpers a change added and classifies
each, and it is one of the reviews run before work is finished. It catches the
three things the test cannot — a domain-free helper nobody marked, a spec-able
one marked instead of moved, and a second project that wrote the same thing
under a different name.

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

- **Never edit either lock to make a test pass** — not `LOCKED.txt`, and not
  `MEASURED.txt`, which being readable text is the easier one to fudge. A
  golden-master failure means the exported shape changed; a measurement failure
  means something reads differently off an unchanged shape. If it was
  intentional, say so explicitly, then
  re-lock with `uv run relock <project>`, which rebuilds first and rewrites
  both records together.
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
`test_the_countersink_opens_out_on_the_front_face`.

**[docs/quality/testing.md](docs/quality/testing.md) owns the layers** — what
each asserts, what each catches, and how to read a given failure pattern. It is
not repeated here; a list that has to be kept in step with another list is how
this one came to be two layers behind.

What is specific to writing them:

- **Never add project-specific assertions to the contract suite**, and never
  copy one into a project. A new project is covered by what already exists.
- **Assert the relationship, not the number.** The wedge test checks the line
  is genuinely tangent to the crescent rather than pinning `32.60°`.
- **Keep the command tests free of project names.** They own "the command
  matches the library"; the golden master owns "the library matches the lock".

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

**Before work is called finished, subagents review it.** Fresh context is the
point, and each **reports findings rather than editing**.

They are defined in `.claude/agents/`, so what each one loads, looks for and
reports lives with the agent rather than here:

| Agent | Runs when | Reads |
|---|---|---|
| `code-reviewer` | the change touched code | the change |
| `docs-reviewer` | the change touched a doc **or changed behaviour a doc describes** | the change, and any doc describing what moved |
| `promotion-sweeper` | the change added or altered a helper, **or added or reshaped a project** | the whole repo — the second caller may be old code nobody touched |

**When: once, after the gates already pass** — lint, types, tests, verification,
and the locks. Not before. A reviewer reading a tree with failing tests spends
its findings on what you already know. Launch them **in parallel**.

"Did I edit a doc" is the wrong question for the second row. A code change with
no doc edit falsifies docs regularly: make a build construct everything before
writing, and a guarantee about when failures surface goes stale without the doc
being opened.

That one is also not covered by the documentation tests. Those check that
references resolve; whether a claim is still *true* is a question only a reader
can settle, and the tests have already passed over a wrong measurement, a
contradicted count and a missing project.

**Then judge what comes back.** A reviewer that has not run the code can be
wrong, and has been — including once where the recommended fix would have
shipped a silent dispatch bug, and once where the right finding came with the
wrong reason. Verify each finding against the code before acting on it, and say
which ones you are rejecting and why.

Three things this catches often enough to expect: a fix that would change a
hash-locked STL; a finding whose repair turns up something more interesting than
the finding did; and a finding already fixed since the reviewer read the tree.

**Each review reads a snapshot, and acting on one makes the others stale.** That
is not hypothetical — it has happened three times in one sitting. So: act on all
of them, re-run the gates, and if you substantially reworked an area another
review covered, **re-run that one**. Its verdict was about code that no longer
exists.

## Don't

- Don't commit to `main`, or open a PR without checking `git branch --show-current` first.
- Prefer not to add a dependency, and ask first. The runtime set is
  deliberately small — but it is a preference, not a rule, and the lockfile
  exists so that adding one is a decision rather than a hazard.
- Don't commit `.venv/`, caches, or slicer project files.
- Don't move or rename generated STLs by hand — `uv run build` owns `output/`.
- Don't touch `docs/` in a refactor that preserves behavior. If a doc needs
  editing, it was coupled to the code — fix the doc, not the refactor.
