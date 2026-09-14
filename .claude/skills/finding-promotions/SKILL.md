---
name: finding-promotions
description: Use when a change adds or alters a public helper inside a project package, and when a project is added or substantially reshaped. Turns "did anyone notice this belongs in the shared kit" from something remembered into something enumerated.
---

# Finding Promotions

## Why this exists

A helper starts in the project that needs it and moves into the shared kit when
a *second* project needs it. Half of that is already mechanical: two projects
defining the same helper name fails the suite, and so does a project rewriting
something the kit already has.

The other half is not. A helper that is domain-free but unmarked never reaches
the inventory, and a second project that writes the same thing under a
*different* name trips nothing. Both halves of that have already happened in
this repo. This procedure covers what a test cannot.

## When to run it

- **Any change that adds or alters a public helper in a project package.** The
  helper exists and the diff makes it cheap to find.
- **When a project is added or substantially reshaped.** That is when a
  single-caller helper can acquire its second caller.

**Not at "project completion".** A project is tuned for as long as it is
printed, so completion never quite arrives, and waiting leaves helpers unmarked
for however long that is.

## The procedure

Run all five steps. Steps 1, 3 and 4 are mechanical — do not skip them because
step 2 felt conclusive.

**Write each step's output down as you go**, one line per helper, rather than
carrying it to step 5 in your head:

```
<helper>  <verdict>  <marker? y/n>  <choices: n, and which>  <second caller?>
```

Sixty helpers across two projects is already near the limit of what anyone
holds at once, and the sweep is supposed to get longer as the repo does.

### 1. Enumerate

**Every public function and class in every project package** — not only the ones
this change touched. A helper written before this procedure existed is exactly
the one nobody has ever looked at, and sweeping everything costs one command.

```sh
rg -n '^\s*(def|class) [a-zA-Z_]' src/printing3d/*/*.py            # all of them
git diff main...HEAD -- 'src/printing3d/*/*.py' \
  | rg '^\+\s*(def|class) '                                       # what is new
```

Both details are load-bearing, and both were wrong here once:

- **Match indented definitions too.** Most of this repo's geometry lives inside
  classes, so a pattern anchored at column zero is blind to methods, properties
  and static methods — which is where the helpers actually are. One of the two
  helpers this procedure has found so far was a static method.
- **Spell the pathspec `*/*.py`.** Git's pathspecs do not cross `/` the way a
  shell glob does, so `'src/printing3d/*/'` matches no file and prints nothing.
  Empty output is indistinguishable from "this change added no helpers", so
  that mistake fails in the direction of reassurance — the worst direction.

**Private helpers are in scope here.** Enumerate everything and classify
everything; visibility is a question for step 5, not for the sweep. Under the
older reading a leading underscore excluded a helper twice over -- from the
list and from the classification -- and one of the two helpers this procedure
has found was private. The rule that settles it:

- A **promotion candidate must be public.** Promotion is about surface another
  project can call, so a private helper is made public as part of the move.
- A **coupling finding has no visibility requirement.** Depending on more than
  you need is a fact about behaviour, and it is just as true of a helper with
  one caller in the same file.

Not swept: `tests/`, whose helpers are fixtures for one project's suite, and
module constants, which move by being derived rather than by being shared.

Use the diff to decide what to look at *first*, never to decide what to look at
*at all*. This step has no judgement in it, and skipping it is how the last one
was missed.

### 2. Classify

**Judge the behaviour, never the name.** A name is the cheapest thing about a
helper, and renaming is part of a pure move — so "it would need a different name
in the kit" is not a reason to stop. `measure_cradle_walls` that takes two column
ranges and returns their highest points is domain in name only; it belongs in the
kit under a better one. The same function that *works out* which ranges to
measure from what a cradle is does not.

**A docstring is name, not behaviour.** Prose mentioning the crescent, the
cradle or the strip tells you what the author had in mind, not what the code
requires. Read the arithmetic with the identifiers and comments stripped away;
if what is left is plane geometry, it is plane geometry with a domain-flavoured
description, and the description is the cheap half.

For each, answer in order. The first **yes** settles it — with one deliberate
exception, marked below, because taking a project's type is a fact about a
signature and this table is about behaviour.

| Ask | If yes |
|---|---|
| Does its behaviour depend on a fact about what the project makes? | domain — stop |
| Does its signature take or return a type a project defines? | **not a verdict.** Note it and keep going — answer the rest about the behaviour, then see 2a |
| Would another project have to change its **behaviour** to use it? | not a pure move — see below |
| Could a project making something unrelated call it — as it stands, or as it would stand with that type narrowed away — and mean it? | **candidate** |

Row two is the trap this table used to set for itself. Read as "domain — stop",
it fires on precisely the helpers 2a exists to rescue, and list 3 comes back
empty every time. A parochial signature is a finding, never a verdict.

The last question is the real test, and it is about the *caller*, not the code.
"A future project might want this" is not a yes. "A project making a birdhouse
could call this today and it would do the right thing" is.

### 2a. When the behaviour is general but the signature is not

A promotion may never change **behaviour**. It may freely narrow what a helper
**depends on**. Those are different things, and running them together is what
blocks the most valuable promotions there are.

A function computing geometry from two numbers, handed a whole design object to
mine those two numbers out of, is general behaviour behind a parochial
signature. It is not "unpromotable" — it is **over-coupled, today, with one
caller**, and that is a finding on its own terms whether or not a second project
ever appears. Pure geometry has no business knowing what a design is.

**So report it as coupling, not as a failed promotion.** Decoupling is its own
behaviour-preserving commit, justified by separation of concerns rather than by
reuse; the move then waits for a second caller as always. Tangling the two makes
the promotion unreviewable, because the lock can no longer say which change
moved the bytes.

| Situation | What it is |
|---|---|
| Two callers want the same behaviour on different types | **Promote.** Widening an annotation changes no behaviour. |
| It depends on more than it needs | **Report the coupling.** Decouple first as its own commit; move it when a second caller exists. |
| Two callers want *different* behaviour | **Two functions.** One with a mode argument is shallower than the two it replaced. |
| The second caller must pass something saying which kind it is | **Stop.** A flag argument means two jobs in one function. |
| One caller today, and a second imagined | **Stop** — unless 2b applies. Imagining a second caller is guessing; a closed-form helper has no second shape left to imagine. |
| A method reading its own object's fields | **Not over-coupling.** Taking a domain object as an *argument* is coupling; reading `self` is cohesion, and is why the object exists. Read literally, 2a would flag every property a design has. |
| A general algorithm with one domain call inside it | **Stop.** Hoisting that call out hands the caller a step it did not have, so the module got wider, not deeper. That is a redesign wanting its own justification, not a narrowing. |

**A kit entry costs something, so not everything true is worth reporting.** The
floor is not a line count: ask whether a second project calling it would be
reusing a *decision* someone could get wrong, or only a shorthand it could
rewrite correctly on the first try without thinking. Shared code exists to stop
a mistake being made twice. A two-field tuple and a one-line loop clear every
other test here and still belong where they are.

The test that settles it: after the change, does the **caller** have fewer things
to know, or more? Fewer means the module got deeper. More means it got wider, and
a wide shared helper costs every project that uses it.

### 2b. Move now, or mark and wait

Every candidate goes to the kit eventually. This decides whether it goes now.

**Do not reach for a verdict. Count.** List every decision in the helper that
nobody outside this repo made for you, and write the list down:

- which branch of a quadratic, which root, which sign
- what tolerance, and what counts as close enough
- how results are ordered
- what it returns when there is nothing to return
- what happens at the input where it divides by zero

Two conditions guard the count. **Nothing in its signature may be ours** — plain
values or types the kit owns — and **its tests must be writable without naming a
project**. Fail either and you counted too early.

**The check:** delete every word belonging to this repo from the docstring, then
ask two questions.

1. Does what is left still specify the function? If you cannot finish the
   sentence, stop.
2. Could a stranger reimplement it from what is left and get the same answers,
   bit for bit? If not, the docstring survived by being **vague**, and what it
   failed to mention goes on your list.

Question 2 is the one that does the work. Without it the check rewards
under-written prose — a docstring that never mentions its sign convention sails
through deletion *because* it was hiding one.

| Count | What it means |
|---|---|
| **Zero** | **Move it now.** Nothing is left for a second caller to settle, and waiting only hides it — the next project reads the kit, not a grep. |
| **One or more** | **Mark it, and name the choices in the marker.** They are exactly what a second caller will arrive wanting different, so recording them is what makes the wait useful rather than merely long. |

Expect the count to be one or more most of the time. Zero is rare, and a sweep
that promotes nothing is a normal result, not a failed sweep.

**The trap: a formula whose family is famous.** "It is Euclid" points at
something loudly enough to drown out the branch choice inside it. There are two
tangent lines from a point to a circle, not one. Check every behaviour, not the
pedigree of the maths.

CLAUDE.md carries the reasoning; this step is only where it gets applied.

### 3. Cross-check the kit

For each candidate, search the kit for something that already does the job
**under another name**. This is where the name-collision test is blind.

```sh
rg -n '^def ' src/printing3d/*.py
```

If the kit has it: call it. If the kit *nearly* has it, say so plainly — whether
to widen the kit's version or keep a separate one is a judgement for the owner,
and it changes the other project's behaviour, so it is never a silent fix.

### 4. Cross-check the other projects

For each candidate, search every other project for something doing the same job
under another name. **That is the promotion trigger, even though no test fired
and the names differ.**

Reading every pair does not survive a third project, and this is both the most
valuable step and the first one anybody skips. **Group by what a helper returns**
— a length, an angle, a point, a section — and compare only within a group. Two
functions doing the same job almost always agree about what comes out of them,
long before they agree about anything else.

Search the candidate's **own** project too. Three copies of one idea in one
package is the same finding with a different remedy: extract it locally, which
is what makes it a single thing to promote later instead of three.

### 5. Report

For each helper: its name, the verdict, the reason in one line, whether it
carries a `Promotable:` marker, and — for candidates — its choice count, what
those choices are, and whether a second caller now exists.

**Read what an existing marker actually says, not just that it is there.** A
marker is prose, and prose goes stale: one here notes that promoting a helper
would mean teaching a kit function to merge its results first. Change that kit
function and the sentence is quietly false, with nothing failing. A marker
whose caveat no longer holds belongs in the second list below.

**Four lists matter most**, and none exists anywhere else:

- **candidates whose choice-count is zero** — these move now, no second caller
  needed. Expect this list to be empty often; that is not a failure
- **candidates carrying no marker** — the discovery gap, and the reason this
  procedure exists
- **marked helpers that are not actually candidates** — a marker claiming more
  than the helper delivers, which sends the next reader looking for reuse that
  is not there. A marker that does not name the choices it waits on belongs
  here too: silence reads as readiness
- **helpers depending on more than they need** — general behaviour behind a
  parochial signature. Worth fixing on its own terms, and what would otherwise
  keep a genuinely reusable helper locked in one project forever

**Say what a promotion would owe.** Promoted code arrives in the kit with its
own tests, and a helper reached until now only through a project's parts has
none of its own. That is part of the cost of the move, so it belongs in the
report rather than being discovered by whoever acts on it.

Report. Do not edit.

## What not to do

- **Do not promote on one caller unless 2b says spec-able.** A candidate whose
  shape we chose is marked, not moved — the second caller is what settles that
  shape, and generalising from one example is guessing. A candidate whose shape
  nobody chose has nothing left to settle.
- **Do not stretch 2b to cover something you like.** It is a count you write
  down, not a feeling. Every helper looks obvious to whoever just wrote it, and
  that is exactly how a kit becomes a junk drawer.
- **Do not mark something because it looks generic.** Apply the test in step 2.
- **Do not stop at a domain-sounding name.** Renaming is part of a pure move.
  What disqualifies a helper is domain knowledge in its behaviour, not in its
  spelling.
- **Do not widen a helper's signature to make it promotable.** Narrowing what it
  depends on is a promotion; adding a way to ask for something different is a
  redesign, and needs its own justification.
- **Do not decouple and move in one commit.** Each is reviewable alone and the
  lock can verify each; together, neither.
- **Do not flag the names every project is expected to define** — the contract
  roles and shared vocabulary. Those are roles, not duplication.

## How this fails

| Symptom | What went wrong |
|---|---|
| Everything comes back "domain" | Step 2 answered from the code's neighbourhood rather than from whether another project could call it |
| A helper whose shape we chose is promoted on one caller | The trigger was misread. 2b applies only where nothing about the shape is ours |
| A spec-able helper is marked instead of moved | 2b was skipped, and the inventory now holds something that belonged in the kit already |
| A helper moves on "it is standard maths" | The family was checked instead of the behaviour. A famous formula still has branches, signs and degenerate inputs, and every one of them is a choice |
| A marker says a helper is waiting but not for what | The count was taken and thrown away. The choices are the useful half |
| A second caller exists and nothing was found | Step 4 was skipped, or searched for the name rather than the job |
| A kit helper gets quietly widened | Step 3's caveat was ignored — that changes another project and is the owner's call |
| A promoted helper grows a mode argument | Step 2a was skipped: two behaviours were forced into one function |
| A general helper is dismissed for taking a domain type | Step 2a was read as a verdict rather than as a coupling finding |
| Only helpers from this change were examined | Step 1 was read as "the diff" instead of "every project package" |
| Step 1 printed nothing and that was taken as good news | The pathspec or the pattern matched no file. An empty sweep of a repo with helpers in it is a broken command, never a clean bill |
| A marked helper's caveat is no longer true | Step 5 checked that a marker exists instead of reading what it claims |
