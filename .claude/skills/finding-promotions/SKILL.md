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

### 1. Enumerate

**Every public function and class in every project package** — not only the ones
this change touched. A helper written before this procedure existed is exactly
the one nobody has ever looked at, and sweeping everything costs one command.

```sh
rg -n '^(def|class) [a-z_A-Z]' src/printing3d/*/                  # all of them
git diff main...HEAD -- 'src/printing3d/*/' | rg '^\+(def|class) '  # what is new
```

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

For each, answer in order. The first **yes** settles it.

| Ask | If yes |
|---|---|
| Does its behaviour depend on a fact about what the project makes? | domain — stop |
| Does its signature take or return a type a project defines? | domain — stop |
| Would another project have to change its signature or behaviour to use it? | not a pure move — see below |
| Could a project making something unrelated call it **as it stands** and mean it? | **candidate** |

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
| One caller today, and a second imagined | **Stop.** That is guessing what the second needs. |

The test that settles it: after the change, does the **caller** have fewer things
to know, or more? Fewer means the module got deeper. More means it got wider, and
a wide shared helper costs every project that uses it.

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

### 5. Report

For each helper: its name, the verdict, the reason in one line, whether it
carries a `Promotable:` marker, and — for candidates — whether a second caller
now exists.

**Three lists matter most**, and none exists anywhere else:

- **candidates carrying no marker** — the discovery gap, and the reason this
  procedure exists
- **marked helpers that are not actually candidates** — a marker claiming more
  than the helper delivers, which sends the next reader looking for reuse that
  is not there
- **helpers depending on more than they need** — general behaviour behind a
  parochial signature. Worth fixing on its own terms, and what would otherwise
  keep a genuinely reusable helper locked in one project forever

Report. Do not edit.

## What not to do

- **Do not promote on one caller.** A candidate is marked, not moved. The second
  caller is the trigger, and generalising from one example is guessing what the
  second needs.
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
| Something is promoted with one caller | The trigger was misread; a candidate is marked and left where it is |
| A second caller exists and nothing was found | Step 4 was skipped, or searched for the name rather than the job |
| A kit helper gets quietly widened | Step 3's caveat was ignored — that changes another project and is the owner's call |
| A promoted helper grows a mode argument | Step 2a was skipped: two behaviours were forced into one function |
| A general helper is dismissed for taking a domain type | Step 2a was read as a verdict rather than as a coupling finding |
| Only helpers from this change were examined | Step 1 was read as "the diff" instead of "every project package" |
