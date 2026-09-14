# Locking

How a project is held to the shape it last shipped, and to what that shape
measured.

## What it does

Each project keeps two records of what it produces, and the test suite
regenerates the parts and compares against both. They answer different
questions, and the second exists because the first cannot see everything.

| Record | Holds | Catches |
|---|---|---|
| The byte lock | A digest of every file the project ships | Anything that moves a single vertex |
| The measurement lock | What the pre-print checks reported about those files | Shared code reading something different off a shape that did not move |

The second is the one that is easy to miss the point of. A change in shared
code can alter what a check *measures* while every byte stays identical and
every check still passes — a tolerance widened, a face merged differently. No
other gate in the repo can see that.

**Parts still being tested are covered by neither.** They are checked like
anything else, because you are about to print one, but they are not a record of
what the project ships. See [output](../build/output.md).

## Guarantees

**Determinism.** The same source produces byte-identical files on every run, on
any machine. That is not incidental — it is the property both records depend on.

Because a lock is written on a developer's machine and re-checked by automation
running a different operating system, a passing check is also evidence of that
"on any machine" claim: the two would disagree the moment the output became
platform-dependent. It is what lets the measurement lock pin numbers as fine as
it does.

**The committed files match the lock.** The STLs in the output directory are the
ones the lock describes, so printing from a clone without regenerating is safe.

**A lock only ever records something that passed.** Re-locking refuses when the
build is unsound or its checks fail, so neither record can come to describe a
state nobody would accept.

## Re-locking

A mismatch means **what the project produces changed**. That is a decision, not
a build error:

- If the change was **unintentional**, fix the cause. Never re-lock to get to
  green.
- If it was **intentional**, re-lock and say in the pull request what changed
  and why that is acceptable.

Re-locking is a command, and it names the project — there is no form that
re-pins everything, because the accident that would cause is silent. It rebuilds
first, then rewrites both records together so they cannot drift apart.

Both records are equally off limits to hand-editing. The measured one is plain
readable text, which makes it the easier of the two to fake and the more
tempting; faking it is the same act as faking a digest.

A locked part that has already been printed is a physical object someone owns.
Changing its bytes silently means the next print no longer matches it.

## Contract

| | |
|---|---|
| Input | What the project currently builds, and what its checks report |
| Output | Two records per project, beside that project's source |
| Written by | The re-locking command only — never by hand, and only when the build is sound and the checks pass |
| Invariant | A record describes a state that was built, checked and accepted |

## How it fails

The checks that assert *relationships* are the discriminator: while those pass,
the design is still correct however much the bytes moved.

| Symptom | Meaning |
|---|---|
| Hash mismatch, everything else passing | Something below the geometry changed how the solid is meshed. The design is untouched. |
| Hash mismatch, the pinned outline also failing, relationships still holding | The outline's vertices moved but the design holds — typically a change in how finely curves are divided, or an intended reshape. |
| Hash mismatch, a relationship failing | The design itself is wrong. Investigate before accepting anything. |
| A locked file is missing | The output was never generated, or was redirected. |
| Bytes match but a measurement moved | Shared code now reads something different off an unchanged shape. Nothing else can see this — the parts are identical and every check may still pass. |
| Re-locking refuses | The build is unsound, its checks fail, or the output directory is redirected. Fix the cause; the records are left as they were. |
