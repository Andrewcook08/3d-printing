# Output and locking

Where generated files land, and how they are held to a known state.

## What it does

Every project writes its STLs to a shared output location, one directory per
project:

```
output/<project>/<part-name>.stl
```

These files are **committed**. You can print straight from a clone without
generating anything first.

**Parts still being tested are not.** A project trying shapes it has not
committed to writes them apart from what it ships:

```
output/trials/<project>/<part-name>.stl
```

They are built and checked exactly like the rest — you are going to print one —
but they are not committed and neither lock covers them. A trial is a question
rather than an artifact: printed once, answering something, then deleted.
Committing them would fill the repo with the shapes that lost, and pinning them
would make retiring one a change to the record of what the project ships.

So retiring every trial is deleting one config file, and nothing leaves the
repository because nothing entered it. When a trial wins, it is moved into the
shipped configuration and becomes an ordinary part — committed, locked,
measured.

## Retiring a part

Building makes each directory hold exactly what its configuration declares —
the committed one and the trials one alike. A part whose entry has been removed
from [configuration](configuration.md) is moved aside on the next build rather
than deleted, wherever it was written:

```
output/archive/<project>/<part-name>.stl
```

The archive is not committed. The two uncommitted directories answer different
questions and a shape can pass through both: **trials** is where something is
written because the project has not committed to it, and **archive** is where
anything goes once its entry is gone. A trial that is printed, answered and
deleted is built into the first and retired into the second.

What the archive is worth differs accordingly. A retired *shipped* part is in
version control either way, so the archived copy is a convenience. A retired
*trial* was never committed, so the archived copy is the only file of that
shape — recoverable otherwise only by restoring its entry and rebuilding, which
works because the build is deterministic, but is work rather than a copy.

**Nothing in the archive is overwritten.** A part retired, brought back at a
different size, and retired again keeps both shapes — the second is set apart by
what is actually different about it. An identical shape archived twice is kept
once, since there is nothing to lose by not keeping a second copy.

**The lock is never touched by this.** A retired part leaves the lock describing
a file that is no longer there, and the conformance tests fail until it is
re-locked deliberately — the same as any other change to what a project ships. A
build that could edit its own lock could not be a golden master.

## Redirecting the output

Setting `PRINTING3D_OUTPUT` replaces the root that projects write beneath.
Projects still get their own subdirectory under it, and the archive moves with
them. This is how tests and experiments generate parts without touching the
committed ones.

## Guarantees

**Determinism.** The same source produces byte-identical files on every run,
on any machine. That is not incidental — it is the property everything below
depends on.

Because the lock is written on a developer's machine and re-checked by
automation running a different operating system, a passing check is also
evidence of that "on any machine" claim: the two would disagree the moment the
output became platform-dependent.

**Each project is hash-locked.** A project keeps a `LOCKED.txt` recording the
sha256 of every STL it has shipped. The test suite regenerates the parts and
compares. Anything that moves a single vertex fails immediately.

**The committed files match the lock.** The STLs sitting in the output
directory are the ones the lock describes, so printing from the repo without
regenerating is safe.

## Contract

| | |
|---|---|
| Output root | `output/`, or `PRINTING3D_OUTPUT` when set |
| Per project | One subdirectory named for the project |
| Lock files | Two per project: one listing a sha256 per shipped file, one holding what the pre-print checks measured of those files |
| Output written by | The build command only — never by hand |
| Locks written by | The re-locking command only — never by hand, and only when the build is sound and its checks pass |

## Re-locking

A lock mismatch means **the exported shape changed**. That is a decision, not a
build error:

- If the change was **unintentional**, fix the cause. Never re-lock to get to
  green.
- If it was **intentional**, re-lock the project with the re-locking command
  and say in the pull request what changed about the shape and why that is
  acceptable. It rebuilds first and rewrites both records together, so they
  cannot drift apart, and it refuses to pin anything the build or the checks
  reject — re-locking is the answer to a change you meant, never to a failure
  you did not expect.

Both records are equally off limits to hand-editing. The measured one is plain
readable text, which makes it the easier of the two to fake and the more
tempting; faking it is the same act as faking a digest.

A locked part that has already been printed is a physical object someone owns.
Changing its bytes silently means the next print no longer matches it.

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
