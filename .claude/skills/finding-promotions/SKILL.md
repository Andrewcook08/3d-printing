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

Every public function and class added or changed in the diff, inside a project
package. Not the kit, not tests.

```sh
git diff main...HEAD -- 'src/printing3d/*/' | rg '^\+(def|class) '
rg -n '^(def|class) ' src/printing3d/<project>/*.py    # if reviewing a whole project
```

List them. This step has no judgement in it, and skipping it is how the last
one was missed.

### 2. Classify

For each, answer in order. The first **yes** settles it.

| Ask | If yes |
|---|---|
| Does its signature take or return a type a project defines? | domain — stop |
| Does its name or docstring need a domain noun to make sense? | domain — stop |
| Would you have to rename it to move it to the kit? | domain — stop |
| Could a project making something unrelated call it and mean it? | **candidate** |

The last question is the real test, and it is about the *caller*, not the code.
"A future project might want this" is not a yes. "A project making a birdhouse
could call this today and it would do the right thing" is.

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

Report. Do not edit.

## What not to do

- **Do not promote on one caller.** A candidate is marked, not moved. The second
  caller is the trigger, and generalising from one example is guessing what the
  second needs.
- **Do not mark something because it looks generic.** Apply the test in step 2.
- **Do not rename a helper to make it promotable.** If it needs renaming to move,
  step 2 already answered: it is domain.
- **Do not flag the names every project is expected to define** — the contract
  roles and shared vocabulary. Those are roles, not duplication.

## How this fails

| Symptom | What went wrong |
|---|---|
| Everything comes back "domain" | Step 2 answered from the code's neighbourhood rather than from whether another project could call it |
| Something is promoted with one caller | The trigger was misread; a candidate is marked and left where it is |
| A second caller exists and nothing was found | Step 4 was skipped, or searched for the name rather than the job |
| A kit helper gets quietly widened | Step 3's caveat was ignored — that changes another project and is the owner's call |
