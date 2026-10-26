# Output

Where generated files land, and which of them the repository keeps.

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

**Neither lock is touched by this.** A retired part leaves the byte lock
describing a file that is no longer there, and the conformance tests fail until
it is re-locked deliberately — the same as any other change to what a project
ships. A build that could edit its own lock could not be a golden master. See
[locking](../quality/locking.md).

## Redirecting the output

Setting `PRINTING3D_OUTPUT` replaces the root that projects write beneath.
Projects still get their own subdirectory under it, and the archive moves with
them. This is how tests and experiments generate parts without touching the
committed ones.

## Contract

| | |
|---|---|
| Output root | `output/`, or `PRINTING3D_OUTPUT` when set |
| Per project | One subdirectory named for the project, committed |
| Parts under test | A separate root beside it, never committed |
| Retired parts | An archive root beside both, never committed |
| Written by | The build command only — never by hand |

## How it fails

| Symptom | Meaning |
|---|---|
| A part is missing from the output directory | Its entry was removed from the configuration, and the build archived it |
| A part appears in neither the output nor the trials directory | Nothing declares it; the build only writes what a configuration asks for |
| The output directory holds a file no configuration mentions | The build has not run since that entry was removed |
| Files land somewhere unexpected | `PRINTING3D_OUTPUT` is set |

For a lock that no longer matches what is here, see
[locking](../quality/locking.md).
