---
name: changing-shared-code
description: Use before adding, changing, or deleting one of the shared kit's own modules — the .py files directly in src/printing3d/ — including carrying out a promotion. Separates the edits that cannot break another project from the ones that silently can.
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

**You are about to add, change, or delete one of the kit's own modules** — the
`.py` files sitting directly in `src/printing3d/`, not the ones inside a project
package. That trigger is mechanical, which is the point; "am I doing something
risky" is not a trigger anyone applies reliably.

`ls src/printing3d/*.py` lists exactly those. **Do not hand that same pattern to
git** — a shell glob stops at a `/` and a git pathspec does not, so
`git ls-files -- 'src/printing3d/*.py'` quietly includes every project file too.

Finding *what* should be promoted is a different job — that is
`finding-promotions`, run as a review. This skill is what you do once you are
holding the edit.

## The tree

Answer in order. Q1 is decided from the edit in front of you; Q2 is measured;
Q3 and Q4 are judgement, narrowed by what Q2 found.

### Q1 — What kind of edit is this?

The locks cannot answer this one, because it is about what you are doing rather
than about what happened.

| The edit | Where it goes |
|---|---|
| **Adding** something that did not exist — a new function, or a parameter whose default is the value in use now | Nothing existing can change, by construction. Confirm that at Q2 and you are done |
| **Changing** the body, or the value, of something that already exists | Q2 — and then **Q3 regardless of what Q2 says** |
| **Deleting** something | See *Deleting from the kit*, below |
| **Moving** a helper in from a project | See *Carrying out a promotion*, below |

### Q2 — Run the locks. What did they catch?

```sh
uv run pytest
```

| Result | What it means |
|---|---|
| Everything passes | **No pinned measurement moved, on the inputs the existing projects produce today.** That is narrower than "nothing changed" — read the next paragraph before you believe it |
| A `MEASURED.txt` test fails | Something moved, and the failure names the measurement. On to Q3 |
| A `LOCKED.txt` test fails | You changed geometry, not just a measurement. Re-lock deliberately or undo it — and you are past the scope of this skill |
| Both fail | Treat it as the geometry change first; the measurements moved because the shape did |

**What a clean run does and does not prove.** It proves no *shipped* measurement
moved, on the profiles two projects happen to build today. It proves nothing
about a third project, and nothing about what a config change would produce
tomorrow. A tolerance can move four orders of magnitude here and pin clean,
because neither existing project has an edge shallow enough to notice — that is
a fact about the coverage, not about the constant.

So a clean Q2 is a **necessary** condition, never a sufficient one. If you
changed something that already existed, you still owe Q3.

### Q3 — Who is today's behaviour wrong for?

| | What to do |
|---|---|
| **Nobody.** It is right for its callers; the newcomer wants something else | Q4 |
| **Everyone — and parts already shipped were verified with the wrong answer** | **Stop. Ask the user.** |
| **Everyone, but no shipped part was affected.** Right on every input produced so far, wrong on inputs a config change would produce | Fix it. Say plainly in the commit that it is a correctness fix and what it was latently wrong about. No stop — nothing in anyone's hands is affected |

That third row is the common one and it is easy to miss, because it looks
exactly like the first from inside the diff. Both real changes this skill was
tested against landed there: a kit helper that measured split faces as separate
short ones, right on every profile either project actually built, wrong the
moment a seam landed on an edge that mattered.

**The middle row is a hard stop, not a heads-up.** Do not fix it and report
afterwards. That behaviour has been wrong in every part those projects have
already printed — possibly parts on someone's wall. What that means is the
user's call, not a detail of your fix. Bring them: what the helper does now,
what it should do, which measurements move, and which shipped parts were
verified with the wrong answer. Then wait.

The line between the middle and bottom rows is exactly *did a part ship that was
verified with this?* — which is why the gate is there, and why it does not fire
when nothing shipped was affected.

### Q4 — Does the difference live in the verb, or in a number?

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

**Editing a kit constant because a new project needed it.** Almost always Q4's
parameter case done as if it were a correctness fix: the newcomer wants a
different number, and a number gets typed over the old one. Every other project
is changed without being told.

This is the move the tree is shaped to stop, and it is worth knowing how it gets
past: the tests come back green, because a constant that matters to a third
project need not matter to the two that exist. A clean run is why it *feels*
safe. That is Q2's caveat, and it is why editing something that already existed
owes Q3 no matter what Q2 says.

If you find yourself typing a new value over an old one in the kit, you are in
Q4 and the answer is a parameter.

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
| A kit constant has a new value and no other file changed | Q4's parameter case done as a correctness fix. This is the always-wrong move |
| A kit function grew a boolean argument | Q4 answered "number" for a difference that was in the verb |
| A behaviour was fixed for everyone and the user heard about it afterwards | Q3's stop was read as advice, or the middle and bottom rows were confused |
| A change to existing behaviour stopped at a green test run | Q2 was read as sufficient. It is necessary; Q3 is still owed |
| Everything landed in the bottom row of Q3 | "No shipped part was affected" was assumed rather than checked. Check which parts were verified with it |
| Both locks were re-pinned to make the tests pass | Re-locking is for a change you meant. It is never the fix for a failure you did not expect |
| A promotion and a decoupling landed in one commit | Neither can be reviewed; the locks cannot attribute what moved |
| A superseded kit helper was left in place "just in case" | The next project will find it by reading the kit |

## What not to do

- **Do not answer Q3 from the diff.** Whether a behaviour is wrong for everyone
  is not visible from the change; it is a question about the callers you have
  and the parts they shipped.
- **Do not let a green test run end the tree.** It ends Q2, and only for the
  inputs today's projects produce.
- **Do not widen a kit helper to make a new caller fit.** Narrowing what it
  depends on is free; growing what it can be asked for is a redesign.
- **Do not re-pin a lock to get to green.** A lock failure is information. Find
  out which row of Q2 you are in first.
- **Do not go looking for promotion candidates here.** That is
  `finding-promotions`; duplicating it is how the two would drift apart.
