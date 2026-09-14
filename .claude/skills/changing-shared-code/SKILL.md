---
name: changing-shared-code
description: Use before adding, changing, or deleting anything in the shared kit (src/printing3d/*.py) — including carrying out a promotion. Turns "will this break another project" from something you reason about into something a lock answers.
---

# Changing Shared Code

## Why this exists

A helper inside a project has one caller. A helper in the kit has every project,
including the ones nobody has written yet. Promotion does not settle the
judgement calls inside a helper — it multiplies who is affected by them.

The repo already has rules for getting code *into* the kit. This is the other
half, and the half where a mistake is quiet: the change looks local, the tests
are green, and another project now measures something different.

## When to run it

**You are about to add, change, or delete something under `src/printing3d/*.py`** —
the kit's own modules, not a project's. That trigger is mechanical, which is the
point; "am I doing something risky" is not a trigger anyone applies reliably.

Finding *what* should be promoted is a different job — that is
`finding-promotions`, run as a review. This skill is what you do once you are
holding the edit.

## The tree

Answer in order. Do not skip Q1 because you are confident.

### Q1 — Does this change what existing callers get?

**Do not reason about this. Measure it.** Make the change and run the tests.

| What happens | What it means |
|---|---|
| Everything passes | Existing callers get what they always got. Adding a function, or a parameter defaulting to the current value, lands here |
| A `MEASURED.txt` test fails | Something moved, and the failure names the measurement. Go to Q2 |
| A `LOCKED.txt` test fails | You changed geometry, not just a measurement. That is a different conversation — re-lock deliberately or undo it |

A clean run is the whole of Q1's answer. This is the only question here that has
a mechanical answer, which is why it is first.

### Q2 — Wrong for everyone, or unsuited to the new caller?

| | |
|---|---|
| **Unsuited to the new caller** — it does the right thing for who calls it today, and the newcomer wants something else | Go to Q3 |
| **Wrong for everyone** — the existing callers have been getting a bad answer too | **Stop. Ask the user.** |

**Wrong for everyone is a hard stop, not a heads-up.** Do not fix it and report
afterwards. A behaviour wrong for every project has been wrong in every part
those projects have already printed — possibly parts sitting on someone's wall.
What that means is the user's call, not a detail of your fix.

Bring them: what the helper does now, what it should do, which measurements move,
and which shipped parts were verified with the wrong answer. Then wait.

### Q3 — Does the difference live in the verb, or in a number?

| The difference | The move |
|---|---|
| A **number** — a tolerance, a threshold, a floor | Add a parameter whose default is the current value. Existing callers do not change and never learn it happened |
| A **verb** — merge or don't, raise or return empty, include or exclude | **A second function.** Both may be perfectly good kit functions; they are two jobs |

The test: write one sentence describing what each caller wants. If the sentences
differ only where a number appears, it is a parameter. If they differ in what the
function *does*, it is two functions.

**Never a flag.** An argument that selects between behaviours makes every caller
read a branch it does not use, and the two halves drift because nothing forces
them to stay comparable. A defaulted tolerance is not a flag — it dimensions one
behaviour rather than choosing between two.

## The move that is always wrong

**Editing a kit constant because a new project needed it.** That is Q2's
wrong-for-everyone path taken while you are actually in Q3's parameter case. It
changes every other project without saying so, and before the measurement lock
existed nothing would have caught it.

If you find yourself typing a new value over an old one in the kit, stop and
re-read Q2.

## Two cases with their own shape

### Carrying out a promotion

The decision to promote belongs to `finding-promotions`. Executing it:

1. **Decouple first, move second, as separate commits.** If the helper must stop
   depending on a project's types before it can be shared, that is its own
   behaviour-preserving change, justified on its own terms. Tangled together,
   neither is reviewable — the locks can no longer say which change moved what.
2. **Behaviour never changes.** Prove it by diffing, not by asserting: both locks
   clean means the move is a move.
3. **It arrives with its own tests**, and they pin the reason it exists rather
   than its incidentals.
4. **Its `Promotable:` marker comes off** — it is promoted now. The choices that
   marker named stay written down, because the move did not settle them. Every
   caller inherits them now.

### Deleting from the kit

When a kit helper's last caller leaves, delete it rather than leaving it
available. A subtly wrong helper that nobody calls is a trap for the next
project, which will find it by reading the kit and have no way to know it was
superseded. Its tests move to whatever replaced it.

## How this fails

| Symptom | What went wrong |
|---|---|
| A kit constant has a new value and no other file changed | Q2 was skipped entirely. This is the always-wrong move |
| A kit function grew a boolean argument | Q3 answered "number" for a difference that was in the verb |
| A behaviour was fixed for everyone and the user heard about it afterwards | Q2's stop was read as advice |
| Q1 was answered by reading the code | The locks answer Q1; reasoning about it is how the quiet case stays quiet |
| Both locks were re-pinned to make the tests pass | Re-locking is for a change you meant. It is never the fix for a failure you did not expect |
| A promotion and a decoupling landed in one commit | Neither can be reviewed; the locks cannot attribute what moved |
| A superseded kit helper was left in place "just in case" | The next project will find it by reading the kit |

## What not to do

- **Do not answer Q1 from the diff.** A shared helper's blast radius is not
  visible from the change itself; that is the entire reason it is dangerous.
- **Do not widen a kit helper to make a new caller fit.** Narrowing what it
  depends on is free; growing what it can be asked for is a redesign.
- **Do not re-pin a lock to get to green.** A lock failure is information. Find
  out which row of Q2 you are in first.
- **Do not go looking for promotion candidates here.** That is
  `finding-promotions`; duplicating it is how the two would drift apart.
