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

## Redirecting the output

Setting `PRINTING3D_OUTPUT` replaces the root that projects write beneath.
Projects still get their own subdirectory under it. This is how tests and
experiments generate parts without touching the committed ones.

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
| Lock file | One per project, listing sha256 per shipped file |
| Written by | The build command only — never by hand |

## Re-locking

A lock mismatch means **the exported shape changed**. That is a decision, not a
build error:

- If the change was **unintentional**, fix the cause. Never re-lock to get to
  green.
- If it was **intentional**, regenerate, update the lock, and say in the pull
  request what changed about the shape and why that is acceptable.

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
